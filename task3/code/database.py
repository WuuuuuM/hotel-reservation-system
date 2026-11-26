from pathlib import Path
import sqlite3


# database.py 在 code 文件夹中。
# parents[1] 就是 task3 项目文件夹。
PROJECT_FOLDER = Path(__file__).resolve().parents[1]
DATA_FOLDER = PROJECT_FOLDER / "data"
DATABASE_FILE = DATA_FOLDER / "hotel.db"


def get_connection():
    """连接数据库，并打开外键检查。"""
    DATA_FOLDER.mkdir(exist_ok=True)

    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database():
    """第一次运行时创建酒店预订系统所需的数据表。"""
    create_tables_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        phone TEXT UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK (
            role IN ('customer', 'hotel_staff', 'platform_admin')
        ),
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS hotels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hotel_code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        address TEXT NOT NULL,
        contact_phone TEXT,
        is_active INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS room_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hotel_id INTEGER NOT NULL,
        room_code TEXT NOT NULL,
        name TEXT NOT NULL,
        max_guests INTEGER NOT NULL CHECK (max_guests > 0),
        description TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        UNIQUE (hotel_id, room_code),
        FOREIGN KEY (hotel_id) REFERENCES hotels(id)
    );

    CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_type_id INTEGER NOT NULL,
        room_number TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        UNIQUE (room_type_id, room_number),
        FOREIGN KEY (room_type_id) REFERENCES room_types(id)
    );

    CREATE TABLE IF NOT EXISTS daily_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_type_id INTEGER NOT NULL,
        stay_date TEXT NOT NULL,
        total_rooms INTEGER NOT NULL CHECK (total_rooms >= 0),
        booked_rooms INTEGER NOT NULL DEFAULT 0,
        UNIQUE (room_type_id, stay_date),
        CHECK (booked_rooms >= 0 AND booked_rooms <= total_rooms),
        FOREIGN KEY (room_type_id) REFERENCES room_types(id)
    );

    CREATE TABLE IF NOT EXISTS daily_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_type_id INTEGER NOT NULL,
        stay_date TEXT NOT NULL,
        price REAL NOT NULL CHECK (price >= 0),
        UNIQUE (room_type_id, stay_date),
        FOREIGN KEY (room_type_id) REFERENCES room_types(id)
    );

    CREATE TABLE IF NOT EXISTS stop_sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_type_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        reason TEXT,
        CHECK (end_date >= start_date),
        FOREIGN KEY (room_type_id) REFERENCES room_types(id)
    );

    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT NOT NULL UNIQUE,
        customer_id INTEGER NOT NULL,
        hotel_id INTEGER NOT NULL,
        room_type_id INTEGER NOT NULL,
        check_in TEXT NOT NULL,
        check_out TEXT NOT NULL,
        guest_count INTEGER NOT NULL CHECK (guest_count > 0),
        contact_name TEXT NOT NULL,
        contact_phone TEXT NOT NULL,
        total_amount REAL NOT NULL CHECK (total_amount >= 0),
        status TEXT NOT NULL DEFAULT 'pending',
        cancel_reason TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (check_out > check_in),
        FOREIGN KEY (customer_id) REFERENCES users(id),
        FOREIGN KEY (hotel_id) REFERENCES hotels(id),
        FOREIGN KEY (room_type_id) REFERENCES room_types(id)
    );

    CREATE TABLE IF NOT EXISTS operation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operator_id INTEGER,
        booking_id INTEGER,
        action TEXT NOT NULL,
        details TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (operator_id) REFERENCES users(id),
        FOREIGN KEY (booking_id) REFERENCES bookings(id)
    );
    """

    connection = get_connection()

    try:
        connection.executescript(create_tables_sql)
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
    print(f"数据库已准备好：{DATABASE_FILE}")