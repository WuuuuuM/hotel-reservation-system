import tkinter as tk
from tkinter import ttk, messagebox

from auth_service import login
import platform_service


WHITE = "#FFFFFF"
TEAL = "#67BAC6"
DEEP_TEAL = "#276F78"
PALE_BLUE = "#E8F7F8"
MINT = "#EAF6EF"
TEXT = "#254E50"
SUBTEXT = "#6D8988"
BORDER = "#D5E7E1"
BACKGROUND = "#F5F9F6"

ROLE_TEXT = {
    "customer": "顾客",
    "hotel_staff": "酒店员工",
    "platform_admin": "平台管理员",
}

APPROVAL_TEXT = {
    "pending": "待复核",
    "approved": "已通过",
    "rejected": "已拒绝",
}


class PlatformApp(tk.Tk):
    """Desti 平台管理员工作台。"""

    def __init__(self):
        super().__init__()

        self.title("Desti 平台管理后台")
        self.geometry("1120x760")
        self.minsize(950, 650)
        self.configure(bg=BACKGROUND)

        self.admin_user = None
        self.accounts = []
        self.delegated_requests = []

        self._configure_styles()
        self._show_login_page()

    def _configure_styles(self):
        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Desti.Treeview",
            background=WHITE,
            fieldbackground=WHITE,
            foreground=TEXT,
            rowheight=31,
            font=("Microsoft YaHei UI", 9),
        )
        style.configure(
            "Desti.Treeview.Heading",
            background=PALE_BLUE,
            foreground=TEXT,
            font=("Microsoft YaHei UI", 9, "bold"),
            padding=(6, 6),
        )
        style.map(
            "Desti.Treeview",
            background=[("selected", DEEP_TEAL)],
            foreground=[("selected", WHITE)],
        )

    def _show_login_page(self):
        page = tk.Frame(self, bg=BACKGROUND)
        page.pack(fill="both", expand=True)

        card = tk.Frame(
            page,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        card.place(relx=0.5, rely=0.5, anchor="center", width=430, height=445)

        tk.Label(
            card,
            text="Desti",
            bg=WHITE,
            fg=TEAL,
            font=("Microsoft YaHei UI", 26, "bold"),
        ).pack(pady=(28, 2))

        tk.Label(
            card,
            text="平台管理后台",
            bg=WHITE,
            fg=TEXT,
            font=("Microsoft YaHei UI", 17, "bold"),
        ).pack(pady=(0, 8))

        tk.Label(
            card,
            text="管理账号、平台规则与敏感代操作",
            bg=WHITE,
            fg=SUBTEXT,
            font=("Microsoft YaHei UI", 10),
        ).pack(pady=(0, 22))

        form = tk.Frame(card, bg=WHITE)
        form.pack(fill="x", padx=42)

        tk.Label(form, text="管理员账号", bg=WHITE, fg=TEXT).pack(anchor="w")
        username_entry = ttk.Entry(form)
        username_entry.insert(0, "desti_admin")
        username_entry.pack(fill="x", pady=(5, 14))

        tk.Label(form, text="密码", bg=WHITE, fg=TEXT).pack(anchor="w")
        password_entry = ttk.Entry(form, show="*")
        password_entry.pack(fill="x", pady=(5, 16))

        def do_login():
            try:
                user = login(
                    username_entry.get().strip(),
                    password_entry.get(),
                )
            except Exception as error:
                messagebox.showerror(
                    "登录失败",
                    f"登录时发生错误：\n{error}",
                    parent=self,
                )
                return

            if user is None:
                messagebox.showerror(
                    "登录失败",
                    "用户名或密码不正确。",
                    parent=self,
                )
                return

            if user.role != "platform_admin":
                messagebox.showerror(
                    "账号类型不符",
                    "请使用平台管理员账号登录。",
                    parent=self,
                )
                return

            self.admin_user = user
            page.destroy()
            self._show_dashboard()

        tk.Button(
            form,
            text="登录管理后台",
            command=do_login,
            bg=DEEP_TEAL,
            fg=WHITE,
            activebackground=TEAL,
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 11, "bold"),
            pady=11,
        ).pack(fill="x", pady=(2, 12))

        tk.Label(
            card,
            text="管理员：desti_admin / DestiAdmin123\n"
                 "复核员：desti_reviewer / DestiReview123",
            bg=WHITE,
            fg=SUBTEXT,
            font=("Microsoft YaHei UI", 9),
            justify="center",
        ).pack(pady=(0, 16))

        password_entry.bind("<Return>", lambda event: do_login())
        username_entry.focus_set()

    def _show_dashboard(self):
        header = tk.Frame(self, bg=WHITE, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Desti",
            bg=WHITE,
            fg=TEAL,
            font=("Microsoft YaHei UI", 22, "bold"),
        ).pack(side="left", padx=(22, 12), pady=14)

        tk.Label(
            header,
            text="平台管理后台",
            bg=WHITE,
            fg=TEXT,
            font=("Microsoft YaHei UI", 12),
        ).pack(side="left")

        tk.Label(
            header,
            text=f"管理员：{self.admin_user.username}",
            bg=WHITE,
            fg=SUBTEXT,
            font=("Microsoft YaHei UI", 10),
        ).pack(side="right", padx=22)

        body = tk.Frame(self, bg=BACKGROUND)
        body.pack(fill="both", expand=True, padx=22, pady=18)

        tk.Label(
            body,
            text="平台运营管理",
            bg=BACKGROUND,
            fg=TEXT,
            font=("Microsoft YaHei UI", 21, "bold"),
        ).pack(anchor="w")

        tk.Label(
            body,
            text="管理系统账号、配置业务规则，并复核敏感代操作",
            bg=BACKGROUND,
            fg=SUBTEXT,
            font=("Microsoft YaHei UI", 10),
        ).pack(anchor="w", pady=(5, 14))

        self.tabs = ttk.Notebook(body)
        self.tabs.pack(fill="both", expand=True)

        self.account_tab = tk.Frame(self.tabs, bg=BACKGROUND)
        self.rule_tab = tk.Frame(self.tabs, bg=BACKGROUND)
        self.approval_tab = tk.Frame(self.tabs, bg=BACKGROUND)
        self.log_tab = tk.Frame(self.tabs, bg=BACKGROUND)

        self.tabs.add(self.account_tab, text="账号管理")
        self.tabs.add(self.rule_tab, text="平台规则")
        self.tabs.add(self.approval_tab, text="代操作复核")
        self.tabs.add(self.log_tab, text="全局操作日志")

        self._build_account_tab()
        self._build_rule_tab()
        self._build_approval_tab()
        self._build_log_tab()

        self._load_accounts()
        self._load_rules()
        self._load_delegated_requests()
        self._load_logs()

    def _build_account_tab(self):
        form = tk.Frame(
            self.account_tab,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        form.pack(fill="x", padx=12, pady=12)

        tk.Label(
            form,
            text="创建账号",
            bg=WHITE,
            fg=TEXT,
            font=("Microsoft YaHei UI", 12, "bold"),
        ).grid(row=0, column=0, columnspan=5, sticky="w", padx=12, pady=(11, 7))

        tk.Label(form, text="用户名", bg=WHITE, fg=SUBTEXT).grid(
            row=1, column=0, sticky="w", padx=12
        )
        tk.Label(form, text="手机号", bg=WHITE, fg=SUBTEXT).grid(
            row=1, column=1, sticky="w", padx=12
        )
        tk.Label(form, text="初始密码", bg=WHITE, fg=SUBTEXT).grid(
            row=1, column=2, sticky="w", padx=12
        )
        tk.Label(form, text="角色", bg=WHITE, fg=SUBTEXT).grid(
            row=1, column=3, sticky="w", padx=12
        )

        self.new_username_var = tk.StringVar()
        self.new_phone_var = tk.StringVar()
        self.new_password_var = tk.StringVar()
        self.new_role_var = tk.StringVar(value="顾客")

        ttk.Entry(form, textvariable=self.new_username_var).grid(
            row=2, column=0, sticky="ew", padx=12, pady=(4, 11)
        )
        ttk.Entry(form, textvariable=self.new_phone_var).grid(
            row=2, column=1, sticky="ew", padx=12, pady=(4, 11)
        )
        ttk.Entry(form, textvariable=self.new_password_var, show="*").grid(
            row=2, column=2, sticky="ew", padx=12, pady=(4, 11)
        )

        ttk.Combobox(
            form,
            textvariable=self.new_role_var,
            values=["顾客", "酒店员工", "平台管理员"],
            state="readonly",
            width=14,
        ).grid(row=2, column=3, sticky="ew", padx=12, pady=(4, 11))

        tk.Button(
            form,
            text="创建",
            command=self._create_account,
            bg=DEEP_TEAL,
            fg=WHITE,
            activebackground=TEAL,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=7,
        ).grid(row=2, column=4, padx=12, pady=(4, 11))

        for column in range(4):
            form.grid_columnconfigure(column, weight=1)

        table_frame = tk.Frame(
            self.account_tab,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self.account_tree = ttk.Treeview(
            table_frame,
            columns=("username", "phone", "role", "active", "created"),
            show="headings",
            style="Desti.Treeview",
            selectmode="browse",
        )

        for column, text, width in (
            ("username", "用户名", 160),
            ("phone", "手机号", 150),
            ("role", "角色", 130),
            ("active", "账号状态", 100),
            ("created", "创建时间", 190),
        ):
            self.account_tree.heading(column, text=text)
            self.account_tree.column(column, width=width, anchor="center")

        self.account_tree.pack(fill="both", expand=True, padx=8, pady=8)

        actions = tk.Frame(self.account_tab, bg=BACKGROUND)
        actions.pack(fill="x", padx=12, pady=(0, 12))

        tk.Button(
            actions,
            text="刷新账号",
            command=self._load_accounts,
            bg=PALE_BLUE,
            fg=DEEP_TEAL,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=8,
        ).pack(side="left")

        tk.Button(
            actions,
            text="启用 / 停用选中账号",
            command=self._toggle_selected_account,
            bg=DEEP_TEAL,
            fg=WHITE,
            activebackground=TEAL,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8,
        ).pack(side="right")

    def _load_accounts(self):
        if self.admin_user is None or not hasattr(self, "account_tree"):
            return

        try:
            self.accounts = platform_service.list_accounts(self.admin_user.id)
        except Exception as error:
            messagebox.showerror("读取账号失败", str(error), parent=self)
            self.accounts = []

        for item in self.account_tree.get_children():
            self.account_tree.delete(item)

        for index, account in enumerate(self.accounts):
            active_text = "启用" if account["is_active"] else "停用"
            role_text = ROLE_TEXT.get(account["role"], account["role"])

            self.account_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    account["username"],
                    account["phone"],
                    role_text,
                    active_text,
                    account["created_at"],
                ),
            )

    def _create_account(self):
        role_map = {
            "顾客": "customer",
            "酒店员工": "hotel_staff",
            "平台管理员": "platform_admin",
        }

        try:
            result = platform_service.create_account(
                self.admin_user.id,
                self.new_username_var.get(),
                self.new_phone_var.get(),
                self.new_password_var.get(),
                role_map[self.new_role_var.get()],
            )
        except Exception as error:
            messagebox.showerror("创建失败", str(error), parent=self)
            return

        messagebox.showinfo("处理结果", result, parent=self)
        self.new_username_var.set("")
        self.new_phone_var.set("")
        self.new_password_var.set("")
        self._load_accounts()
        self._load_logs()

    def _toggle_selected_account(self):
        selected = self.account_tree.selection()

        if not selected:
            messagebox.showinfo(
                "请先选择账号",
                "请先在账号列表中选择一个账号。",
                parent=self,
            )
            return

        account = self.accounts[int(selected[0])]
        new_active = not bool(account["is_active"])

        try:
            result = platform_service.set_account_active(
                self.admin_user.id,
                account["id"],
                new_active,
            )
        except Exception as error:
            messagebox.showerror("操作失败", str(error), parent=self)
            return

        messagebox.showinfo("处理结果", result, parent=self)
        self._load_accounts()
        self._load_logs()

    def _build_rule_tab(self):
        card = tk.Frame(
            self.rule_tab,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        card.pack(fill="x", padx=12, pady=12)

        tk.Label(
            card,
            text="预订审核规则",
            bg=WHITE,
            fg=TEXT,
            font=("Microsoft YaHei UI", 13, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(14, 12))

        tk.Label(
            card,
            text="新订单是否需要酒店审核",
            bg=WHITE,
            fg=SUBTEXT,
        ).grid(row=1, column=0, sticky="w", padx=16, pady=8)

        self.require_approval_var = tk.StringVar(value="否")
        ttk.Combobox(
            card,
            textvariable=self.require_approval_var,
            values=["是", "否"],
            state="readonly",
            width=12,
        ).grid(row=1, column=1, sticky="w", padx=16, pady=8)

        tk.Label(
            card,
            text="普通待确认订单超时时间（分钟）",
            bg=WHITE,
            fg=SUBTEXT,
        ).grid(row=2, column=0, sticky="w", padx=16, pady=8)

        self.timeout_var = tk.StringVar(value="10")
        ttk.Entry(
            card,
            textvariable=self.timeout_var,
            width=16,
        ).grid(row=2, column=1, sticky="w", padx=16, pady=8)

        tk.Button(
            card,
            text="保存规则",
            command=self._save_rules,
            bg=DEEP_TEAL,
            fg=WHITE,
            activebackground=TEAL,
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=8,
        ).grid(row=1, column=2, rowspan=2, padx=20)

        tk.Label(
            card,
            text=(
                "规则用于记录平台的业务配置。"
                "当前原型保存配置项，后续可以让预订逻辑读取这些配置。"
            ),
            bg=WHITE,
            fg=SUBTEXT,
            wraplength=720,
            justify="left",
        ).grid(row=3, column=0, columnspan=3, sticky="w", padx=16, pady=(10, 15))

        table_frame = tk.Frame(
            self.rule_tab,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.rule_tree = ttk.Treeview(
            table_frame,
            columns=("key", "value", "description", "updated"),
            show="headings",
            style="Desti.Treeview",
        )

        for column, text, width in (
            ("key", "规则名称", 210),
            ("value", "当前值", 100),
            ("description", "说明", 390),
            ("updated", "更新时间", 180),
        ):
            self.rule_tree.heading(column, text=text)
            self.rule_tree.column(column, width=width, anchor="center")

        self.rule_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def _load_rules(self):
        if self.admin_user is None or not hasattr(self, "rule_tree"):
            return

        try:
            rules = platform_service.list_platform_rules(self.admin_user.id)
        except Exception as error:
            messagebox.showerror("读取规则失败", str(error), parent=self)
            return

        for item in self.rule_tree.get_children():
            self.rule_tree.delete(item)

        for index, rule in enumerate(rules):
            self.rule_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    rule["rule_key"],
                    rule["rule_value"],
                    rule["description"],
                    rule["updated_at"] or "",
                ),
            )

            if rule["rule_key"] == "require_hotel_approval":
                self.require_approval_var.set(
                    "是" if rule["rule_value"] == "true" else "否"
                )

            if rule["rule_key"] == "pending_timeout_minutes":
                self.timeout_var.set(rule["rule_value"])

    def _save_rules(self):
        require_value = (
            "true" if self.require_approval_var.get() == "是" else "false"
        )

        try:
            first_result = platform_service.update_platform_rule(
                self.admin_user.id,
                "require_hotel_approval",
                require_value,
            )
            second_result = platform_service.update_platform_rule(
                self.admin_user.id,
                "pending_timeout_minutes",
                self.timeout_var.get(),
            )
        except Exception as error:
            messagebox.showerror("保存失败", str(error), parent=self)
            return

        messagebox.showinfo(
            "处理结果",
            f"{first_result}\n{second_result}",
            parent=self,
        )
        self._load_rules()
        self._load_logs()

    def _build_approval_tab(self):
        form = tk.Frame(
            self.approval_tab,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        form.pack(fill="x", padx=12, pady=12)

        tk.Label(
            form,
            text="申请代顾客取消订单",
            bg=WHITE,
            fg=TEXT,
            font=("Microsoft YaHei UI", 12, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(12, 8))

        tk.Label(form, text="订单号", bg=WHITE, fg=SUBTEXT).grid(
            row=1, column=0, sticky="w", padx=14
        )
        tk.Label(form, text="申请原因", bg=WHITE, fg=SUBTEXT).grid(
            row=1, column=1, sticky="w", padx=14
        )

        self.request_order_var = tk.StringVar()
        self.request_reason_var = tk.StringVar()

        ttk.Entry(
            form,
            textvariable=self.request_order_var,
        ).grid(row=2, column=0, sticky="ew", padx=14, pady=(4, 12))

        ttk.Entry(
            form,
            textvariable=self.request_reason_var,
        ).grid(row=2, column=1, sticky="ew", padx=14, pady=(4, 12))

        tk.Button(
            form,
            text="提交复核申请",
            command=self._create_delegated_request,
            bg=DEEP_TEAL,
            fg=WHITE,
            activebackground=TEAL,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=7,
        ).grid(row=2, column=2, padx=14, pady=(4, 12))

        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=2)

        tk.Label(
            self.approval_tab,
            text=(
                "复核需要由另一名平台管理员完成。"
                "演示时可用 desti_admin 提交，再用 desti_reviewer 登录复核。"
            ),
            bg=BACKGROUND,
            fg=SUBTEXT,
            font=("Microsoft YaHei UI", 9),
        ).pack(anchor="w", padx=14, pady=(0, 8))

        table_frame = tk.Frame(
            self.approval_tab,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self.approval_tree = ttk.Treeview(
            table_frame,
            columns=("order", "reason", "requester", "status", "reviewer", "note"),
            show="headings",
            style="Desti.Treeview",
            selectmode="browse",
        )

        for column, text, width in (
            ("order", "订单号", 170),
            ("reason", "申请原因", 200),
            ("requester", "申请人", 100),
            ("status", "复核状态", 90),
            ("reviewer", "复核人", 100),
            ("note", "复核说明", 190),
        ):
            self.approval_tree.heading(column, text=text)
            self.approval_tree.column(column, width=width, anchor="center")

        self.approval_tree.pack(fill="both", expand=True, padx=8, pady=8)

        buttons = tk.Frame(self.approval_tab, bg=BACKGROUND)
        buttons.pack(fill="x", padx=12, pady=(0, 12))

        tk.Button(
            buttons,
            text="刷新申请",
            command=self._load_delegated_requests,
            bg=PALE_BLUE,
            fg=DEEP_TEAL,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=8,
        ).pack(side="left")

        tk.Button(
            buttons,
            text="拒绝申请",
            command=lambda: self._review_selected_request("rejected"),
            bg=PALE_BLUE,
            fg=DEEP_TEAL,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=8,
        ).pack(side="right")

        tk.Button(
            buttons,
            text="通过并执行",
            command=lambda: self._review_selected_request("approved"),
            bg=DEEP_TEAL,
            fg=WHITE,
            activebackground=TEAL,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=8,
        ).pack(side="right", padx=8)

    def _create_delegated_request(self):
        try:
            result = platform_service.create_delegated_request(
                self.admin_user.id,
                self.request_order_var.get(),
                self.request_reason_var.get(),
            )
        except Exception as error:
            messagebox.showerror("提交失败", str(error), parent=self)
            return

        messagebox.showinfo("处理结果", result, parent=self)
        self.request_order_var.set("")
        self.request_reason_var.set("")
        self._load_delegated_requests()
        self._load_logs()

    def _load_delegated_requests(self):
        if self.admin_user is None or not hasattr(self, "approval_tree"):
            return

        try:
            self.delegated_requests = (
                platform_service.list_delegated_requests(self.admin_user.id)
            )
        except Exception as error:
            messagebox.showerror("读取申请失败", str(error), parent=self)
            self.delegated_requests = []

        for item in self.approval_tree.get_children():
            self.approval_tree.delete(item)

        for index, request in enumerate(self.delegated_requests):
            self.approval_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    request["order_number"],
                    request["reason"],
                    request["requester_name"],
                    APPROVAL_TEXT.get(
                        request["review_status"],
                        request["review_status"],
                    ),
                    request["reviewer_name"] or "",
                    request["review_note"] or "",
                ),
            )

    def _review_selected_request(self, decision):
        selected = self.approval_tree.selection()

        if not selected:
            messagebox.showinfo(
                "请先选择申请",
                "请先在申请列表中选择一条记录。",
                parent=self,
            )
            return

        request = self.delegated_requests[int(selected[0])]

        try:
            result = platform_service.review_delegated_request(
                self.admin_user.id,
                request["id"],
                decision,
                "管理员复核",
            )
        except Exception as error:
            messagebox.showerror("复核失败", str(error), parent=self)
            return

        messagebox.showinfo("处理结果", result, parent=self)
        self._load_delegated_requests()
        self._load_logs()

    def _build_log_tab(self):
        tk.Button(
            self.log_tab,
            text="刷新日志",
            command=self._load_logs,
            bg=PALE_BLUE,
            fg=DEEP_TEAL,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=7,
        ).pack(anchor="e", padx=12, pady=10)

        table_frame = tk.Frame(
            self.log_tab,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.log_tree = ttk.Treeview(
            table_frame,
            columns=("time", "operator", "order", "action", "details"),
            show="headings",
            style="Desti.Treeview",
        )

        for column, text, width in (
            ("time", "时间", 160),
            ("operator", "操作人", 110),
            ("order", "订单号", 170),
            ("action", "操作类型", 170),
            ("details", "操作说明", 320),
        ):
            self.log_tree.heading(column, text=text)
            self.log_tree.column(column, width=width, anchor="center")

        self.log_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def _load_logs(self):
        if self.admin_user is None or not hasattr(self, "log_tree"):
            return

        try:
            logs = platform_service.list_operation_logs(self.admin_user.id)
        except Exception as error:
            messagebox.showerror("读取日志失败", str(error), parent=self)
            return

        for item in self.log_tree.get_children():
            self.log_tree.delete(item)

        for index, log in enumerate(logs):
            self.log_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    log["created_at"],
                    log["operator_name"] or "系统",
                    log["order_number"] or "",
                    log["action"],
                    log["details"],
                ),
            )