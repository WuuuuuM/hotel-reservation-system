from datetime import date, datetime
import secrets

from database import get_connection
from models import Booking


def create_booking(
    customer_id,
    room_type_id,
    check_in,
    check_out,
    guest_count,
    contact_name,
    contact_phone,
):
    """创建一笔预订，并占用每晚一间房的库存。"""
    start = date.fromisoformat(check_in)
    end = date.fromisoformat(check_out)

    if end <= start:
        raise ValueError("退房日期必须晚于入住日期。")

    if start < date.today():
        raise ValueError("入住日期不能早于今天。")

    if guest_count <= 0:
        raise ValueError("入住人数必须大于 0。")

    contact_name = contact_name.strip()
    contact_phone = contact_phone.strip()

    if not contact_name or not contact_phone:
        raise ValueError("请填写联系人姓名和手机号。")

    connection = get_connection()

    try:
        # 先锁定这次写入，避免多人同时预订时超卖。
        connection.execute("BEGIN IMMEDIATE")

        customer = connection.execute(
            """
            SELECT id
            FROM users
            WHERE id = ? AND role = 'customer' AND is_active = 1
            """,
            (customer_id,),
        ).fetchone()

        if customer is None:
            raise ValueError("找不到有效的顾客账号，请重新登录。")

        room_type = connection.execute(
            """
            SELECT
                room_types.id,
                room_types.max_guests,
                hotels.id AS hotel_id
            FROM room_types
            JOIN hotels ON hotels.id = room_types.hotel_id
            WHERE room_types.id = ?
              AND room_types.is_active = 1
              AND hotels.is_active = 1
            """,
            (room_type_id,),
        ).fetchone()

        if room_type is None:
            raise ValueError("找不到可预订的房型。")

        if guest_count > room_type["max_guests"]:
            raise ValueError("入住人数超过该房型的最大接待人数。")

        nightly_records = []
        total_amount = 0

        # 逐晚检查库存、价格和停售状态。
        for day_offset in range((end - start).days):
            stay_date = start.fromordinal(start.toordinal() + day_offset)
            date_text = stay_date.isoformat()

            inventory = connection.execute(
                """
                SELECT total_rooms - booked_rooms AS available_rooms
                FROM daily_inventory
                WHERE room_type_id = ? AND stay_date = ?
                """,
                (room_type_id, date_text),
            ).fetchone()

            price = connection.execute(
                """
                SELECT price
                FROM daily_prices
                WHERE room_type_id = ? AND stay_date = ?
                """,
                (room_type_id, date_text),
            ).fetchone()

            stop_sale = connection.execute(
                """
                SELECT id
                FROM stop_sales
                WHERE room_type_id = ?
                  AND start_date <= ?
                  AND end_date >= ?
                LIMIT 1
                """,
                (room_type_id, date_text, date_text),
            ).fetchone()

            if inventory is None or price is None:
                raise ValueError(f"{date_text} 的库存或价格尚未设置。")

            if stop_sale:
                raise ValueError(f"{date_text} 已停售，暂时不能预订。")

            if inventory["available_rooms"] < 1:
                raise ValueError(f"{date_text} 已无可订房间。")

            nightly_records.append(date_text)
            total_amount += price["price"]

        # 检查全部通过后，再逐晚占用一间房。
        for date_text in nightly_records:
            result = connection.execute(
                """
                UPDATE daily_inventory
                SET booked_rooms = booked_rooms + 1
                WHERE room_type_id = ?
                  AND stay_date = ?
                  AND total_rooms - booked_rooms >= 1
                """,
                (room_type_id, date_text),
            )

            if result.rowcount != 1:
                raise ValueError(f"{date_text} 的库存刚刚发生变化，请重新查询。")

        order_number = (
            f"DT{datetime.now():%y%m%d%H%M%S}"
            f"{secrets.token_hex(2).upper()}"
        )

        cursor = connection.execute(
            """
            INSERT INTO bookings (
                order_number,
                customer_id,
                hotel_id,
                room_type_id,
                check_in,
                check_out,
                guest_count,
                contact_name,
                contact_phone,
                total_amount,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_number,
                customer_id,
                room_type["hotel_id"],
                room_type_id,
                check_in,
                check_out,
                guest_count,
                contact_name,
                contact_phone,
                total_amount,
                "pending",
            ),
        )
        booking_id = cursor.lastrowid

        connection.execute(
            """
            INSERT INTO operation_logs (
                operator_id, booking_id, action, details
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                customer_id,
                booking_id,
                "create_booking",
                f"顾客创建订单 {order_number}，状态为待确认。",
            ),
        )

        connection.commit()

        return Booking(
            id=booking_id,
            order_number=order_number,
            customer_id=customer_id,
            hotel_id=room_type["hotel_id"],
            room_type_id=room_type_id,
            check_in=check_in,
            check_out=check_out,
            guest_count=guest_count,
            contact_name=contact_name,
            contact_phone=contact_phone,
            total_amount=total_amount,
            status="pending",
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def list_customer_bookings(customer_id):
    """查询某位顾客的订单，最新订单排在前面。"""
    connection = get_connection()

    try:
        bookings = connection.execute(
            """
            SELECT
                bookings.id,
                bookings.order_number,
                hotels.name AS hotel_name,
                room_types.name AS room_type_name,
                bookings.check_in,
                bookings.check_out,
                bookings.guest_count,
                bookings.total_amount,
                bookings.status,
                bookings.cancel_reason
            FROM bookings
            JOIN hotels ON hotels.id = bookings.hotel_id
            JOIN room_types ON room_types.id = bookings.room_type_id
            WHERE bookings.customer_id = ?
            ORDER BY bookings.created_at DESC, bookings.id DESC
            """,
            (customer_id,),
        ).fetchall()

        return [dict(booking) for booking in bookings]

    finally:
        connection.close()


def cancel_booking(customer_id, order_number, reason):
    """取消本人尚未入住的订单，并释放每晚占用的库存。"""
    reason = reason.strip()

    if not reason:
        raise ValueError("请填写取消原因。")

    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")

        booking = connection.execute(
            """
            SELECT id, room_type_id, check_in, check_out, status
            FROM bookings
            WHERE order_number = ? AND customer_id = ?
            """,
            (order_number, customer_id),
        ).fetchone()

        if booking is None:
            raise ValueError("找不到属于当前顾客的这笔订单。")

        if booking["status"] not in ("pending", "confirmed"):
            raise ValueError("这笔订单当前状态不能取消。")

        if booking["check_in"] <= date.today().isoformat():
            raise ValueError("入住当天或入住后不能通过此功能取消订单。")

        start = date.fromisoformat(booking["check_in"])
        end = date.fromisoformat(booking["check_out"])

        for day_offset in range((end - start).days):
            stay_date = start.fromordinal(start.toordinal() + day_offset)

            result = connection.execute(
                """
                UPDATE daily_inventory
                SET booked_rooms = booked_rooms - 1
                WHERE room_type_id = ?
                  AND stay_date = ?
                  AND booked_rooms > 0
                """,
                (booking["room_type_id"], stay_date.isoformat()),
            )

            if result.rowcount != 1:
                raise ValueError(
                    f"{stay_date.isoformat()} 的库存记录异常，"
                    "取消操作已停止。"
                )

        connection.execute(
            """
            UPDATE bookings
            SET status = 'cancelled',
                cancel_reason = ?
            WHERE id = ?
            """,
            (reason, booking["id"]),
        )

        connection.execute(
            """
            INSERT INTO operation_logs (
                operator_id, booking_id, action, details
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                customer_id,
                booking["id"],
                "cancel_booking",
                f"顾客取消订单 {order_number}。原因：{reason}",
            ),
        )

        connection.commit()
        return f"订单 {order_number} 已取消，房间库存已释放。"

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()