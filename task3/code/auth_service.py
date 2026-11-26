import hashlib
import hmac
import secrets
import sqlite3

from database import get_connection
from models import User


PASSWORD_ITERATIONS = 310_000


def hash_password(password):
    """把密码转换成加盐后的摘要，数据库里不保存原始密码。"""
    salt = secrets.token_bytes(16)
    password_bytes = password.encode("utf-8")

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt,
        PASSWORD_ITERATIONS,
    )

    return (
        f"pbkdf2_sha256${PASSWORD_ITERATIONS}"
        f"${salt.hex()}${digest.hex()}"
    )


def verify_password(password, saved_value):
    """检查输入的密码是否与保存的密码摘要匹配。"""
    try:
        algorithm, iterations_text, salt_text, digest_text = (
            saved_value.split("$")
        )

        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_text)
        saved_digest = bytes.fromhex(digest_text)

        entered_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )

        return hmac.compare_digest(entered_digest, saved_digest)

    except (ValueError, TypeError):
        return False


def register_customer(username, phone, password):
    """注册顾客账号，并返回新建的用户。"""
    username = username.strip()
    phone = phone.strip()

    if not username or not phone:
        raise ValueError("用户名和手机号不能为空。")

    if len(password) < 8:
        raise ValueError("密码至少需要 8 个字符。")

    connection = get_connection()

    try:
        password_hash = hash_password(password)

        cursor = connection.execute(
            """
            INSERT INTO users (username, phone, password_hash, role)
            VALUES (?, ?, ?, 'customer')
            """,
            (username, phone, password_hash),
        )

        connection.commit()

        return User(
            id=cursor.lastrowid,
            username=username,
            phone=phone,
            role="customer",
            is_active=True,
        )

    except sqlite3.IntegrityError as error:
        connection.rollback()
        raise ValueError("这个用户名或手机号已经注册。") from error

    finally:
        connection.close()


def login(username_or_phone, password, expected_role=None):
    """用用户名或手机号登录，验证失败时返回 None。"""
    connection = get_connection()

    try:
        user = connection.execute(
            """
            SELECT id, username, phone, password_hash, role, is_active
            FROM users
            WHERE username = ? OR phone = ?
            """,
            (username_or_phone.strip(), username_or_phone.strip()),
        ).fetchone()

        if user is None or not user["is_active"]:
            return None

        if expected_role and user["role"] != expected_role:
            return None

        if not verify_password(password, user["password_hash"]):
            return None

        return User(
            id=user["id"],
            username=user["username"],
            phone=user["phone"],
            role=user["role"],
            is_active=bool(user["is_active"]),
        )

    finally:
        connection.close()