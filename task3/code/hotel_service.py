from datetime import date, timedelta

from database import get_connection


def add_demo_data():
    """添加一间上海酒店和三种房型的演示数据。"""
    connection = get_connection()

    try:
        existing_hotel = connection.execute(
            "SELECT id FROM hotels WHERE hotel_code = ?",
            ("SH-BUND-001",),
        ).fetchone()

        if existing_hotel:
            return "演示酒店已经存在，无需重复添加。"

        cursor = connection.execute(
            """
            INSERT INTO hotels (
                hotel_code, name, city, address, contact_phone
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "SH-BUND-001",
                "外滩澜庭酒店",
                "上海",
                "上海市黄浦区中山东一路附近",
                "021-55550001",
            ),
        )
        hotel_id = cursor.lastrowid

        room_types = [
            ("RV-K", "江景大床房", 2, "一张大床，可欣赏江景", 688),
            ("CT-T", "庭景双床房", 2, "两张单人床，庭院景观", 528),
            ("CT-S", "城景套房", 3, "宽敞套房，可住三位客人", 988),
        ]

        start_date = date.today()

        for code, name, max_guests, description, base_price in room_types:
            cursor = connection.execute(
                """
                INSERT INTO room_types (
                    hotel_id, room_code, name, max_guests, description
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (hotel_id, code, name, max_guests, description),
            )
            room_type_id = cursor.lastrowid

            for room_number in range(1, 7):
                connection.execute(
                    """
                    INSERT INTO rooms (room_type_id, room_number)
                    VALUES (?, ?)
                    """,
                    (room_type_id, f"{code}-{room_number:02d}"),
                )

            for day_offset in range(90):
                stay_date = start_date + timedelta(days=day_offset)
                date_text = stay_date.isoformat()
                price = base_price

                if stay_date.weekday() >= 5:
                    price += 50

                connection.execute(
                    """
                    INSERT INTO daily_inventory (
                        room_type_id, stay_date, total_rooms, booked_rooms
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (room_type_id, date_text, 6, 0),
                )

                connection.execute(
                    """
                    INSERT INTO daily_prices (
                        room_type_id, stay_date, price
                    )
                    VALUES (?, ?, ?)
                    """,
                    (room_type_id, date_text, price),
                )

        connection.commit()
        return "演示酒店、房型、库存和价格已经添加。"

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def search_room_types(city, check_in, check_out, guest_count):
    """按城市、日期和入住人数查找可预订房型。"""
    start = date.fromisoformat(check_in)
    end = date.fromisoformat(check_out)

    if end <= start:
        raise ValueError("退房日期必须晚于入住日期。")

    if guest_count <= 0:
        raise ValueError("入住人数必须大于 0。")

    connection = get_connection()
    results = []

    try:
        room_types = connection.execute(
            """
            SELECT
                hotels.name AS hotel_name,
                hotels.city,
                room_types.id AS room_type_id,
                room_types.name AS room_type_name,
                room_types.max_guests
            FROM room_types
            JOIN hotels ON hotels.id = room_types.hotel_id
            WHERE hotels.city LIKE ?
              AND hotels.is_active = 1
              AND room_types.is_active = 1
              AND room_types.max_guests >= ?
            ORDER BY hotels.name, room_types.name
            """,
            (f"%{city}%", guest_count),
        ).fetchall()

        for room_type in room_types:
            available_each_night = []
            total_price = 0
            can_book = True

            for day_offset in range((end - start).days):
                stay_date = start + timedelta(days=day_offset)
                date_text = stay_date.isoformat()

                inventory = connection.execute(
                    """
                    SELECT total_rooms - booked_rooms AS available_rooms
                    FROM daily_inventory
                    WHERE room_type_id = ? AND stay_date = ?
                    """,
                    (room_type["room_type_id"], date_text),
                ).fetchone()

                daily_price = connection.execute(
                    """
                    SELECT price
                    FROM daily_prices
                    WHERE room_type_id = ? AND stay_date = ?
                    """,
                    (room_type["room_type_id"], date_text),
                ).fetchone()

                stopped = connection.execute(
                    """
                    SELECT id
                    FROM stop_sales
                    WHERE room_type_id = ?
                      AND start_date <= ?
                      AND end_date >= ?
                    LIMIT 1
                    """,
                    (room_type["room_type_id"], date_text, date_text),
                ).fetchone()

                if inventory is None or daily_price is None or stopped:
                    can_book = False
                    break

                if inventory["available_rooms"] < 1:
                    can_book = False
                    break

                available_each_night.append(inventory["available_rooms"])
                total_price += daily_price["price"]

            if can_book:
                results.append(
                    {
                        "hotel_name": room_type["hotel_name"],
                        "city": room_type["city"],
                        "room_type_id": room_type["room_type_id"],
                        "room_type_name": room_type["room_type_name"],
                        "max_guests": room_type["max_guests"],
                        "available_rooms": min(available_each_night),
                        "total_price": total_price,
                    }
                )

        return results

    finally:
        connection.close()