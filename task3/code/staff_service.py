from datetime import date, datetime, timedelta

from auth_service import hash_password
from database import get_connection


# 演示用员工账号。只用于课程原型，不要用于真实系统。
DEMO_STAFF_USERNAME = "desti_staff"
DEMO_STAFF_PASSWORD = "DestiStaff123"
DEMO_STAFF_PHONE = "13800000002"


def ensure_demo_staff_account():
    """
    为演示系统准备一名酒店员工，并将其关联到第一家营业中的酒店。

    当前演示数据只有一家酒店，因此员工账号关联到这家酒店。
    """
    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS hotel_staff_permissions (
                user_id INTEGER PRIMARY KEY,
                hotel_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (hotel_id) REFERENCES hotels(id)
            )
            """
        )

        hotel = connection.execute(
            """
            SELECT id
            FROM hotels
            WHERE is_active = 1
            ORDER BY id
            LIMIT 1
            """
        ).fetchone()

        if hotel is None:
            raise ValueError("数据库里还没有营业中的酒店，请先添加演示酒店数据。")

        hotel_id = hotel[0]

        user = connection.execute(
            """
            SELECT id, role
            FROM users
            WHERE username = ?
            """,
            (DEMO_STAFF_USERNAME,),
        ).fetchone()

        if user is None:
            password_hash = hash_password(DEMO_STAFF_PASSWORD)
            created_at = datetime.now().isoformat(timespec="seconds")

            connection.execute(
                """
                INSERT INTO users (
                    username,
                    phone,
                    password_hash,
                    role,
                    is_active,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    DEMO_STAFF_USERNAME,
                    DEMO_STAFF_PHONE,
                    password_hash,
                    "hotel_staff",
                    1,
                    created_at,
                ),
            )

            user = connection.execute(
                """
                SELECT id, role
                FROM users
                WHERE username = ?
                """,
                (DEMO_STAFF_USERNAME,),
            ).fetchone()

        if user[1] != "hotel_staff":
            raise ValueError(
                f"用户名 {DEMO_STAFF_USERNAME} 已被其他角色使用，"
                "请修改演示员工账号名称。"
            )

        user_id = user[0]

        connection.execute(
            """
            INSERT OR IGNORE INTO hotel_staff_permissions (
                user_id,
                hotel_id,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                hotel_id,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

        connection.commit()
        return {
            "user_id": user_id,
            "hotel_id": hotel_id,
            "username": DEMO_STAFF_USERNAME,
        }

    finally:
        connection.close()


def _get_staff_hotel_id(connection, staff_user_id):
    """检查账号是否为有效酒店员工，并返回该员工管理的酒店编号。"""
    user = connection.execute(
        """
        SELECT role, is_active
        FROM users
        WHERE id = ?
        """,
        (staff_user_id,),
    ).fetchone()

    if user is None:
        raise ValueError("找不到当前用户。")

    if user[0] != "hotel_staff":
        raise PermissionError("当前账号不是酒店工作人员账号。")

    if not user[1]:
        raise PermissionError("当前账号已停用。")

    permission = connection.execute(
        """
        SELECT hotel_id
        FROM hotel_staff_permissions
        WHERE user_id = ?
        """,
        (staff_user_id,),
    ).fetchone()

    if permission is None:
        raise PermissionError("当前员工账号还没有关联酒店。")

    return permission[0]


def list_staff_bookings(staff_user_id, status=None):
    """查询当前员工所管理酒店的订单。"""
    connection = get_connection()

    try:
        hotel_id = _get_staff_hotel_id(connection, staff_user_id)

        sql = """
            SELECT
                b.id,
                b.order_number,
                b.contact_name,
                b.contact_phone,
                b.check_in,
                b.check_out,
                b.guest_count,
                b.total_amount,
                b.status,
                b.created_at,
                h.name AS hotel_name,
                rt.name AS room_type_name
            FROM bookings AS b
            JOIN hotels AS h ON h.id = b.hotel_id
            JOIN room_types AS rt ON rt.id = b.room_type_id
            WHERE b.hotel_id = ?
        """
        parameters = [hotel_id]

        if status:
            sql += " AND b.status = ?"
            parameters.append(status)

        sql += " ORDER BY b.created_at DESC"

        cursor = connection.execute(sql, parameters)
        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


def decide_booking(staff_user_id, order_number, decision, reason=""):
    """
    审核待确认订单。

    decision 可填写 "confirmed" 或 "rejected"。
    拒绝订单时，会释放该订单占用的每日房间库存。
    """
    if decision not in ("confirmed", "rejected"):
        raise ValueError("审核结果只能是 confirmed 或 rejected。")

    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")
        hotel_id = _get_staff_hotel_id(connection, staff_user_id)

        booking = connection.execute(
            """
            SELECT id, room_type_id, check_in, check_out, status
            FROM bookings
            WHERE order_number = ? AND hotel_id = ?
            """,
            (order_number, hotel_id),
        ).fetchone()

        if booking is None:
            raise ValueError("找不到这笔订单，或当前员工没有权限处理它。")

        booking_id, room_type_id, check_in, check_out, old_status = booking

        if old_status != "pending":
            raise ValueError("只有待确认订单可以审核。")

        if decision == "rejected":
            current_date = date.fromisoformat(check_in)
            last_date = date.fromisoformat(check_out)

            while current_date < last_date:
                connection.execute(
                    """
                    UPDATE daily_inventory
                    SET booked_rooms =
                        CASE
                            WHEN booked_rooms > 0 THEN booked_rooms - 1
                            ELSE 0
                        END
                    WHERE room_type_id = ? AND stay_date = ?
                    """,
                    (room_type_id, current_date.isoformat()),
                )
                current_date += timedelta(days=1)

        connection.execute(
            """
            UPDATE bookings
            SET status = ?
            WHERE id = ?
            """,
            (decision, booking_id),
        )

        action = "approve_booking" if decision == "confirmed" else "reject_booking"
        details = reason.strip() or f"员工审核结果：{decision}"

        _write_operation_log(
            connection,
            staff_user_id,
            booking_id,
            action,
            details,
        )

        connection.commit()

        if decision == "confirmed":
            return "订单已确认。"
        return "订单已拒绝，对应房间库存已释放。"

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_booking_flow(staff_user_id, order_number, action):
    """
    办理入住或退房。

    action 可填写 "check_in" 或 "check_out"。
    """
    allowed_actions = {
        "check_in": ("confirmed", "checked_in"),
        "check_out": ("checked_in", "checked_out"),
    }

    if action not in allowed_actions:
        raise ValueError("操作只能是 check_in 或 check_out。")

    old_status, new_status = allowed_actions[action]
    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")
        hotel_id = _get_staff_hotel_id(connection, staff_user_id)

        booking = connection.execute(
            """
            SELECT id, status
            FROM bookings
            WHERE order_number = ? AND hotel_id = ?
            """,
            (order_number, hotel_id),
        ).fetchone()

        if booking is None:
            raise ValueError("找不到这笔订单，或当前员工没有权限处理它。")

        booking_id, current_status = booking

        if current_status != old_status:
            raise ValueError(
                f"当前订单状态是 {current_status}，不能执行这项操作。"
            )

        connection.execute(
            """
            UPDATE bookings
            SET status = ?
            WHERE id = ?
            """,
            (new_status, booking_id),
        )

        action_name = (
            "check_in" if action == "check_in" else "check_out"
        )
        details = (
            "酒店员工办理入住"
            if action == "check_in"
            else "酒店员工办理退房"
        )

        _write_operation_log(
            connection,
            staff_user_id,
            booking_id,
            action_name,
            details,
        )

        connection.commit()

        if action == "check_in":
            return "入住办理完成。"
        return "退房办理完成。"

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def list_staff_room_types(staff_user_id):
    """查询当前员工管理酒店的房型。"""
    connection = get_connection()

    try:
        hotel_id = _get_staff_hotel_id(connection, staff_user_id)

        cursor = connection.execute(
            """
            SELECT id, room_code, name, max_guests, description
            FROM room_types
            WHERE hotel_id = ? AND is_active = 1
            ORDER BY id
            """,
            (hotel_id,),
        )

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


def update_daily_inventory(
    staff_user_id,
    room_type_id,
    stay_date,
    total_rooms,
):
    """更新某个房型在指定日期的总房间数。"""
    try:
        date.fromisoformat(stay_date)
    except ValueError as error:
        raise ValueError("日期格式应为 YYYY-MM-DD。") from error

    total_rooms = int(total_rooms)

    if total_rooms < 0:
        raise ValueError("房间总数不能小于 0。")

    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")
        hotel_id = _get_staff_hotel_id(connection, staff_user_id)

        room_type = connection.execute(
            """
            SELECT id
            FROM room_types
            WHERE id = ? AND hotel_id = ?
            """,
            (room_type_id, hotel_id),
        ).fetchone()

        if room_type is None:
            raise PermissionError("当前员工不能管理这个房型。")

        inventory = connection.execute(
            """
            SELECT id, booked_rooms
            FROM daily_inventory
            WHERE room_type_id = ? AND stay_date = ?
            """,
            (room_type_id, stay_date),
        ).fetchone()

        if inventory is not None and total_rooms < inventory[1]:
            raise ValueError(
                f"当前已有 {inventory[1]} 间房被预订，"
                "总房间数不能低于已预订数量。"
            )

        if inventory is None:
            connection.execute(
                """
                INSERT INTO daily_inventory (
                    room_type_id,
                    stay_date,
                    total_rooms,
                    booked_rooms
                )
                VALUES (?, ?, ?, 0)
                """,
                (room_type_id, stay_date, total_rooms),
            )
        else:
            connection.execute(
                """
                UPDATE daily_inventory
                SET total_rooms = ?
                WHERE id = ?
                """,
                (total_rooms, inventory[0]),
            )

        _write_operation_log(
            connection,
            staff_user_id,
            None,
            "update_inventory",
            f"房型 {room_type_id}，日期 {stay_date}，总房间数改为 {total_rooms}",
        )

        connection.commit()
        return "库存已更新。"

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_daily_price(staff_user_id, room_type_id, stay_date, price):
    """更新某个房型在指定日期的价格。"""
    try:
        date.fromisoformat(stay_date)
        price = float(price)
    except ValueError as error:
        raise ValueError("请检查日期格式和价格。") from error

    if price < 0:
        raise ValueError("价格不能小于 0。")

    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")
        hotel_id = _get_staff_hotel_id(connection, staff_user_id)

        room_type = connection.execute(
            """
            SELECT id
            FROM room_types
            WHERE id = ? AND hotel_id = ?
            """,
            (room_type_id, hotel_id),
        ).fetchone()

        if room_type is None:
            raise PermissionError("当前员工不能管理这个房型。")

        price_row = connection.execute(
            """
            SELECT id
            FROM daily_prices
            WHERE room_type_id = ? AND stay_date = ?
            """,
            (room_type_id, stay_date),
        ).fetchone()

        if price_row is None:
            connection.execute(
                """
                INSERT INTO daily_prices (room_type_id, stay_date, price)
                VALUES (?, ?, ?)
                """,
                (room_type_id, stay_date, price),
            )
        else:
            connection.execute(
                """
                UPDATE daily_prices
                SET price = ?
                WHERE id = ?
                """,
                (price, price_row[0]),
            )

        _write_operation_log(
            connection,
            staff_user_id,
            None,
            "update_price",
            f"房型 {room_type_id}，日期 {stay_date}，价格改为 {price:.2f}",
        )

        connection.commit()
        return "房价已更新。"

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def create_stop_sale(
    staff_user_id,
    room_type_id,
    start_date,
    end_date,
    reason,
):
    """为某个房型设置停售日期范围。"""
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError as error:
        raise ValueError("日期格式应为 YYYY-MM-DD。") from error

    if end < start:
        raise ValueError("停售结束日期不能早于开始日期。")

    reason = reason.strip()
    if not reason:
        raise ValueError("请填写停售原因。")

    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")
        hotel_id = _get_staff_hotel_id(connection, staff_user_id)

        room_type = connection.execute(
            """
            SELECT id
            FROM room_types
            WHERE id = ? AND hotel_id = ?
            """,
            (room_type_id, hotel_id),
        ).fetchone()

        if room_type is None:
            raise PermissionError("当前员工不能管理这个房型。")

        connection.execute(
            """
            INSERT INTO stop_sales (
                room_type_id,
                start_date,
                end_date,
                reason
            )
            VALUES (?, ?, ?, ?)
            """,
            (room_type_id, start_date, end_date, reason),
        )

        _write_operation_log(
            connection,
            staff_user_id,
            None,
            "create_stop_sale",
            f"房型 {room_type_id}，{start_date} 至 {end_date}：{reason}",
        )

        connection.commit()
        return "停售日期已设置。"

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def list_staff_stop_sales(staff_user_id):
    """查询当前员工酒店的停售记录。"""
    connection = get_connection()

    try:
        hotel_id = _get_staff_hotel_id(connection, staff_user_id)

        cursor = connection.execute(
            """
            SELECT
                s.id,
                s.room_type_id,
                rt.name AS room_type_name,
                s.start_date,
                s.end_date,
                s.reason
            FROM stop_sales AS s
            JOIN room_types AS rt ON rt.id = s.room_type_id
            WHERE rt.hotel_id = ?
            ORDER BY s.start_date DESC
            """,
            (hotel_id,),
        )

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


def remove_stop_sale(staff_user_id, stop_sale_id):
    """删除一条当前员工有权管理的停售记录。"""
    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")
        hotel_id = _get_staff_hotel_id(connection, staff_user_id)

        stop_sale = connection.execute(
            """
            SELECT s.id
            FROM stop_sales AS s
            JOIN room_types AS rt ON rt.id = s.room_type_id
            WHERE s.id = ? AND rt.hotel_id = ?
            """,
            (stop_sale_id, hotel_id),
        ).fetchone()

        if stop_sale is None:
            raise ValueError("找不到这条停售记录，或当前员工无权操作。")

        connection.execute(
            "DELETE FROM stop_sales WHERE id = ?",
            (stop_sale_id,),
        )

        _write_operation_log(
            connection,
            staff_user_id,
            None,
            "remove_stop_sale",
            f"删除停售记录 {stop_sale_id}",
        )

        connection.commit()
        return "停售记录已删除。"

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_staff_statistics(staff_user_id):
    """统计当前员工酒店的订单状态数量。"""
    connection = get_connection()

    try:
        hotel_id = _get_staff_hotel_id(connection, staff_user_id)

        hotel = connection.execute(
            "SELECT name FROM hotels WHERE id = ?",
            (hotel_id,),
        ).fetchone()

        rows = connection.execute(
            """
            SELECT status, COUNT(*)
            FROM bookings
            WHERE hotel_id = ?
            GROUP BY status
            """,
            (hotel_id,),
        ).fetchall()

        status_counts = {row[0]: row[1] for row in rows}

        return {
            "hotel_name": hotel[0] if hotel else "",
            "status_counts": status_counts,
            "total_bookings": sum(status_counts.values()),
        }

    finally:
        connection.close()


def list_staff_operation_logs(staff_user_id):
    """查询当前员工自己的操作日志。"""
    connection = get_connection()

    try:
        _get_staff_hotel_id(connection, staff_user_id)

        cursor = connection.execute(
            """
            SELECT action, details, created_at
            FROM operation_logs
            WHERE operator_id = ?
            ORDER BY created_at DESC
            LIMIT 100
            """,
            (staff_user_id,),
        )

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


def _write_operation_log(
    connection,
    operator_id,
    booking_id,
    action,
    details,
):
    """向操作日志表写入一条记录。"""
    connection.execute(
        """
        INSERT INTO operation_logs (
            operator_id,
            booking_id,
            action,
            details,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            operator_id,
            booking_id,
            action,
            details,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )