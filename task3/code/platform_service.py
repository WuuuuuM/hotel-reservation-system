from datetime import date, datetime, timedelta

from auth_service import hash_password
from database import get_connection


DEMO_ADMIN_USERNAME = "desti_admin"
DEMO_ADMIN_PASSWORD = "DestiAdmin123"

DEMO_REVIEWER_USERNAME = "desti_reviewer"
DEMO_REVIEWER_PASSWORD = "DestiReview123"


def ensure_platform_support():
    """准备平台规则、代操作审批表和两个演示管理员账号。"""
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

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS platform_rules (
                rule_key TEXT PRIMARY KEY,
                rule_value TEXT NOT NULL,
                description TEXT NOT NULL,
                updated_by INTEGER,
                updated_at TEXT
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS delegated_operation_approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                order_number TEXT NOT NULL,
                reason TEXT NOT NULL,
                requested_by INTEGER NOT NULL,
                reviewed_by INTEGER,
                review_status TEXT NOT NULL DEFAULT 'pending',
                review_note TEXT,
                created_at TEXT NOT NULL,
                reviewed_at TEXT
            )
            """
        )

        now = datetime.now().isoformat(timespec="seconds")

        connection.execute(
            """
            INSERT OR IGNORE INTO platform_rules
                (rule_key, rule_value, description, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                "require_hotel_approval",
                "false",
                "新订单是否需要酒店工作人员审核",
                now,
            ),
        )

        connection.execute(
            """
            INSERT OR IGNORE INTO platform_rules
                (rule_key, rule_value, description, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                "pending_timeout_minutes",
                "10",
                "普通待确认订单的超时时间，单位为分钟",
                now,
            ),
        )

        _ensure_admin_user(
            connection,
            DEMO_ADMIN_USERNAME,
            "13800000003",
            DEMO_ADMIN_PASSWORD,
        )
        _ensure_admin_user(
            connection,
            DEMO_REVIEWER_USERNAME,
            "13800000004",
            DEMO_REVIEWER_PASSWORD,
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def _ensure_admin_user(connection, username, phone, password):
    """如果管理员账号不存在，就创建账号。"""
    user = connection.execute(
        """
        SELECT id, role
        FROM users
        WHERE username = ?
        """,
        (username,),
    ).fetchone()

    if user is not None:
        if user[1] != "platform_admin":
            raise ValueError(
                f"用户名 {username} 已被其他角色使用，请修改演示管理员用户名。"
            )
        return user[0]

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
            username,
            phone,
            hash_password(password),
            "platform_admin",
            1,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )

    user = connection.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,),
    ).fetchone()

    return user[0]


def _require_platform_admin(connection, admin_user_id):
    """检查当前账号是否为启用状态的平台管理员。"""
    user = connection.execute(
        """
        SELECT role, is_active
        FROM users
        WHERE id = ?
        """,
        (admin_user_id,),
    ).fetchone()

    if user is None:
        raise ValueError("找不到当前用户。")

    if user[0] != "platform_admin":
        raise PermissionError("当前账号不是平台管理员。")

    if not user[1]:
        raise PermissionError("当前管理员账号已停用。")


def _write_log(connection, operator_id, booking_id, action, details):
    """写入系统操作日志。"""
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


def list_accounts(admin_user_id):
    """查询系统账号列表。"""
    connection = get_connection()

    try:
        _require_platform_admin(connection, admin_user_id)

        cursor = connection.execute(
            """
            SELECT id, username, phone, role, is_active, created_at
            FROM users
            ORDER BY id
            """
        )
        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


def create_account(
    admin_user_id,
    username,
    phone,
    password,
    role,
):
    """创建顾客、酒店员工或平台管理员账号。"""
    allowed_roles = ("customer", "hotel_staff", "platform_admin")

    username = username.strip()
    phone = phone.strip()

    if not username or not phone or not password:
        raise ValueError("用户名、手机号和密码都不能为空。")

    if role not in allowed_roles:
        raise ValueError("账号角色不正确。")

    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")
        _require_platform_admin(connection, admin_user_id)

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
                username,
                phone,
                hash_password(password),
                role,
                1,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

        user = connection.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        user_id = user[0]

        if role == "hotel_staff":
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
                raise ValueError("数据库里还没有营业中的酒店。")

            connection.execute(
                """
                INSERT OR REPLACE INTO hotel_staff_permissions (
                    user_id,
                    hotel_id,
                    created_at
                )
                VALUES (?, ?, ?)
                """,
                (
                    user_id,
                    hotel[0],
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )

        _write_log(
            connection,
            admin_user_id,
            None,
            "create_account",
            f"创建账号：{username}，角色：{role}",
        )

        connection.commit()
        return "账号已创建。"

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def set_account_active(admin_user_id, account_id, is_active):
    """启用或停用账号。"""
    is_active = int(bool(is_active))
    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")
        _require_platform_admin(connection, admin_user_id)

        account = connection.execute(
            """
            SELECT username, role, is_active
            FROM users
            WHERE id = ?
            """,
            (account_id,),
        ).fetchone()

        if account is None:
            raise ValueError("找不到这个账号。")

        username, role, old_is_active = account

        if account_id == admin_user_id and not is_active:
            raise ValueError("不能停用当前正在使用的管理员账号。")

        if role == "platform_admin" and old_is_active and not is_active:
            active_admin_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM users
                WHERE role = 'platform_admin' AND is_active = 1
                """
            ).fetchone()[0]

            if active_admin_count <= 1:
                raise ValueError("系统至少需要保留一个启用状态的平台管理员。")

        connection.execute(
            "UPDATE users SET is_active = ? WHERE id = ?",
            (is_active, account_id),
        )

        action = "activate_account" if is_active else "deactivate_account"
        state_text = "启用" if is_active else "停用"

        _write_log(
            connection,
            admin_user_id,
            None,
            action,
            f"{state_text}账号：{username}",
        )

        connection.commit()
        return f"账号“{username}”已{state_text}。"

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def list_platform_rules(admin_user_id):
    """查询平台规则。"""
    connection = get_connection()

    try:
        _require_platform_admin(connection, admin_user_id)

        cursor = connection.execute(
            """
            SELECT rule_key, rule_value, description, updated_at
            FROM platform_rules
            ORDER BY rule_key
            """
        )
        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


def update_platform_rule(admin_user_id, rule_key, rule_value):
    """修改一条平台规则。"""
    allowed_rules = {
        "require_hotel_approval",
        "pending_timeout_minutes",
    }

    if rule_key not in allowed_rules:
        raise ValueError("不支持修改这条平台规则。")

    value = str(rule_value).strip()

    if rule_key == "require_hotel_approval":
        if value not in ("true", "false"):
            raise ValueError("是否需要酒店审核只能设置为 true 或 false。")

    if rule_key == "pending_timeout_minutes":
        try:
            timeout = int(value)
        except ValueError as error:
            raise ValueError("超时时间必须是整数。") from error

        if timeout <= 0:
            raise ValueError("超时时间必须大于 0 分钟。")

    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")
        _require_platform_admin(connection, admin_user_id)

        connection.execute(
            """
            UPDATE platform_rules
            SET rule_value = ?, updated_by = ?, updated_at = ?
            WHERE rule_key = ?
            """,
            (
                value,
                admin_user_id,
                datetime.now().isoformat(timespec="seconds"),
                rule_key,
            ),
        )

        _write_log(
            connection,
            admin_user_id,
            None,
            "update_platform_rule",
            f"规则 {rule_key} 修改为 {value}",
        )

        connection.commit()
        return "平台规则已保存。"

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def create_delegated_request(
    admin_user_id,
    order_number,
    reason,
):
    """创建一条代顾客取消订单的申请，等待另一名管理员复核。"""
    order_number = order_number.strip()
    reason = reason.strip()

    if not order_number:
        raise ValueError("请填写订单号。")

    if not reason:
        raise ValueError("请填写代操作原因。")

    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")
        _require_platform_admin(connection, admin_user_id)

        booking = connection.execute(
            """
            SELECT id, status
            FROM bookings
            WHERE order_number = ?
            """,
            (order_number,),
        ).fetchone()

        if booking is None:
            raise ValueError("找不到这笔订单。")

        if booking[1] not in ("pending", "confirmed"):
            raise ValueError("只有待确认或已确认订单可以申请代取消。")

        connection.execute(
            """
            INSERT INTO delegated_operation_approvals (
                action,
                order_number,
                reason,
                requested_by,
                review_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "cancel_booking",
                order_number,
                reason,
                admin_user_id,
                "pending",
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

        _write_log(
            connection,
            admin_user_id,
            booking[0],
            "create_delegated_request",
            f"申请代取消订单 {order_number}：{reason}",
        )

        connection.commit()
        return "代操作申请已提交，等待另一名平台管理员复核。"

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def list_delegated_requests(admin_user_id):
    """查询代操作申请及复核结果。"""
    connection = get_connection()

    try:
        _require_platform_admin(connection, admin_user_id)

        cursor = connection.execute(
            """
            SELECT
                a.id,
                a.action,
                a.order_number,
                a.reason,
                a.requested_by,
                a.reviewed_by,
                a.review_status,
                a.review_note,
                a.created_at,
                a.reviewed_at,
                requester.username AS requester_name,
                reviewer.username AS reviewer_name
            FROM delegated_operation_approvals AS a
            JOIN users AS requester ON requester.id = a.requested_by
            LEFT JOIN users AS reviewer ON reviewer.id = a.reviewed_by
            ORDER BY a.created_at DESC
            """
        )

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


def review_delegated_request(
    reviewer_id,
    approval_id,
    decision,
    review_note="",
):
    """
    复核代操作申请。

    decision 为 approved 或 rejected。
    发起申请的管理员不能复核自己的申请。
    """
    if decision not in ("approved", "rejected"):
        raise ValueError("复核结果只能是 approved 或 rejected。")

    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")
        _require_platform_admin(connection, reviewer_id)

        request = connection.execute(
            """
            SELECT
                action,
                order_number,
                reason,
                requested_by,
                review_status
            FROM delegated_operation_approvals
            WHERE id = ?
            """,
            (approval_id,),
        ).fetchone()

        if request is None:
            raise ValueError("找不到这条代操作申请。")

        action, order_number, reason, requester_id, current_status = request

        if current_status != "pending":
            raise ValueError("这条申请已经处理过。")

        if requester_id == reviewer_id:
            raise PermissionError("发起申请的管理员不能复核自己的申请。")

        booking = connection.execute(
            """
            SELECT id, room_type_id, check_in, check_out, status
            FROM bookings
            WHERE order_number = ?
            """,
            (order_number,),
        ).fetchone()

        if booking is None:
            raise ValueError("申请所关联的订单已经不存在。")

        booking_id = booking[0]

        if decision == "approved":
            if action != "cancel_booking":
                raise ValueError("暂不支持执行这类代操作。")

            self._cancel_booking_for_admin(
                connection,
                booking,
                reason,
            )

        connection.execute(
            """
            UPDATE delegated_operation_approvals
            SET
                reviewed_by = ?,
                review_status = ?,
                review_note = ?,
                reviewed_at = ?
            WHERE id = ?
            """,
            (
                reviewer_id,
                decision,
                review_note.strip(),
                datetime.now().isoformat(timespec="seconds"),
                approval_id,
            ),
        )

        _write_log(
            connection,
            reviewer_id,
            booking_id,
            "review_delegated_request",
            f"代操作申请 {approval_id} 的复核结果：{decision}。"
            f"说明：{review_note.strip()}",
        )

        connection.commit()

        if decision == "approved":
            return "申请已通过，订单已取消，房间库存已释放。"
        return "申请已拒绝，订单状态未更改。"

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def _cancel_booking_for_admin(connection, booking, reason):
    """在审批通过后取消订单并释放每晚库存。"""
    booking_id, room_type_id, check_in, check_out, status = booking

    if status not in ("pending", "confirmed"):
        raise ValueError("订单状态已变化，不能代为取消。")

    check_in_date = date.fromisoformat(check_in)
    if date.today() >= check_in_date:
        raise ValueError("订单已到入住日期，不能通过此代操作取消。")

    current_date = check_in_date
    check_out_date = date.fromisoformat(check_out)

    while current_date < check_out_date:
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
        SET status = ?, cancel_reason = ?
        WHERE id = ?
        """,
        (
            "cancelled",
            f"平台管理员代操作：{reason}",
            booking_id,
        ),
    )

    _write_log(
        connection,
        None,
        booking_id,
        "admin_delegate_cancel_booking",
        f"平台管理员代取消订单，原因：{reason}",
    )


def list_operation_logs(admin_user_id):
    """查询系统操作日志。"""
    connection = get_connection()

    try:
        _require_platform_admin(connection, admin_user_id)

        cursor = connection.execute(
            """
            SELECT
                logs.created_at,
                users.username AS operator_name,
                bookings.order_number,
                logs.action,
                logs.details
            FROM operation_logs AS logs
            LEFT JOIN users ON users.id = logs.operator_id
            LEFT JOIN bookings ON bookings.id = logs.booking_id
            ORDER BY logs.created_at DESC
            LIMIT 200
            """
        )

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()