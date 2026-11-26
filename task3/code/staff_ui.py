import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date

from auth_service import login
import staff_service


TEAL = "#67BAC6"
DEEP_TEAL = "#276F78"
PALE_BLUE = "#E8F7F8"
MINT = "#EAF6EF"
WHITE = "#FFFFFF"
TEXT = "#254E50"
SUBTEXT = "#6D8988"
BORDER = "#D5E7E1"
BACKGROUND = "#F5F9F6"

STATUS_TEXT = {
    "pending": "待确认",
    "confirmed": "已确认",
    "checked_in": "已入住",
    "checked_out": "已退房",
    "cancelled": "已取消",
    "rejected": "已拒绝",
}

STATUS_FILTERS = {
    "全部订单": None,
    "待确认": "pending",
    "已确认": "confirmed",
    "已入住": "checked_in",
    "已退房": "checked_out",
    "已拒绝": "rejected",
}


class StaffApp(tk.Tk):
    """Desti 酒店员工工作台。"""

    def __init__(self):
        super().__init__()

        self.title("Desti 酒店员工工作台")
        self.geometry("1120x760")
        self.minsize(950, 650)
        self.configure(bg=BACKGROUND)

        self.staff_user = None
        self.orders = []
        self.room_types = []
        self.room_type_by_label = {}

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
            rowheight=32,
            font=("Microsoft YaHei UI", 10),
        )
        style.configure(
            "Desti.Treeview.Heading",
            background=PALE_BLUE,
            foreground=TEXT,
            font=("Microsoft YaHei UI", 10, "bold"),
            padding=(7, 7),
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
        card.place(relx=0.5, rely=0.5, anchor="center", width=420, height=440)

        tk.Label(
            card,
            text="Desti",
            bg=WHITE,
            fg=TEAL,
            font=("Microsoft YaHei UI", 26, "bold"),
        ).pack(pady=(30, 2))

        tk.Label(
            card,
            text="酒店员工工作台",
            bg=WHITE,
            fg=TEXT,
            font=("Microsoft YaHei UI", 17, "bold"),
        ).pack(pady=(0, 8))

        tk.Label(
            card,
            text="登录后处理订单、库存与房价",
            bg=WHITE,
            fg=SUBTEXT,
            font=("Microsoft YaHei UI", 10),
        ).pack(pady=(0, 22))

        form = tk.Frame(card, bg=WHITE)
        form.pack(fill="x", padx=42)

        tk.Label(form, text="员工账号", bg=WHITE, fg=TEXT).pack(anchor="w")
        username_entry = ttk.Entry(form)
        username_entry.insert(0, "desti_staff")
        username_entry.pack(fill="x", pady=(5, 14))

        tk.Label(form, text="密码", bg=WHITE, fg=TEXT).pack(anchor="w")
        password_entry = ttk.Entry(form, show="*")
        password_entry.pack(fill="x", pady=(5, 16))

        def do_login():
            username = username_entry.get().strip()
            password = password_entry.get()

            try:
                user = login(username, password)
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

            if user.role != "hotel_staff":
                messagebox.showerror(
                    "账号类型不符",
                    "这个账号不是酒店员工账号，请使用员工账号登录。",
                    parent=self,
                )
                return

            self.staff_user = user
            page.destroy()
            self._show_dashboard()

        tk.Button(
            form,
            text="登录工作台",
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
            text="演示账号：desti_staff    演示密码：DestiStaff123",
            bg=WHITE,
            fg=SUBTEXT,
            font=("Microsoft YaHei UI", 9),
        ).pack(pady=(0, 16))

        username_entry.focus_set()
        password_entry.bind("<Return>", lambda event: do_login())

    def _show_dashboard(self):
        header = tk.Frame(self, bg=WHITE, height=72)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Desti",
            bg=WHITE,
            fg=TEAL,
            font=("Microsoft YaHei UI", 22, "bold"),
        ).pack(side="left", padx=(22, 12), pady=15)

        tk.Label(
            header,
            text="酒店工作台",
            bg=WHITE,
            fg=TEXT,
            font=("Microsoft YaHei UI", 12),
        ).pack(side="left")

        tk.Label(
            header,
            text=f"员工：{self.staff_user.username}",
            bg=WHITE,
            fg=SUBTEXT,
            font=("Microsoft YaHei UI", 10),
        ).pack(side="right", padx=22)

        body = tk.Frame(self, bg=BACKGROUND)
        body.pack(fill="both", expand=True, padx=24, pady=20)

        title = tk.Label(
            body,
            text="酒店运营管理",
            bg=BACKGROUND,
            fg=TEXT,
            font=("Microsoft YaHei UI", 21, "bold"),
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            body,
            text="处理顾客订单，维护房型每日库存与价格",
            bg=BACKGROUND,
            fg=SUBTEXT,
            font=("Microsoft YaHei UI", 10),
        )
        subtitle.pack(anchor="w", pady=(5, 15))

        self.tabs = ttk.Notebook(body)
        self.tabs.pack(fill="both", expand=True)

        self.order_tab = tk.Frame(self.tabs, bg=BACKGROUND)
        self.room_tab = tk.Frame(self.tabs, bg=BACKGROUND)
        self.log_tab = tk.Frame(self.tabs, bg=BACKGROUND)

        self.tabs.add(self.order_tab, text="订单处理")
        self.tabs.add(self.room_tab, text="房型与库存")
        self.tabs.add(self.log_tab, text="统计与日志")

        self._build_order_tab()
        self._build_room_tab()
        self._build_log_tab()

        self._load_orders()
        self._load_room_types()
        self._load_stop_sales()
        self._load_logs()

    def _build_order_tab(self):
        top = tk.Frame(self.order_tab, bg=BACKGROUND)
        top.pack(fill="x", padx=12, pady=12)

        tk.Label(
            top,
            text="订单状态：",
            bg=BACKGROUND,
            fg=TEXT,
        ).pack(side="left")

        self.status_filter_var = tk.StringVar(value="全部订单")
        status_box = ttk.Combobox(
            top,
            textvariable=self.status_filter_var,
            values=list(STATUS_FILTERS.keys()),
            state="readonly",
            width=14,
        )
        status_box.pack(side="left", padx=(0, 10))
        status_box.bind(
            "<<ComboboxSelected>>",
            lambda event: self._load_orders(),
        )

        tk.Button(
            top,
            text="刷新",
            command=self._load_orders,
            bg=PALE_BLUE,
            fg=DEEP_TEAL,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=7,
        ).pack(side="left")

        table_frame = tk.Frame(
            self.order_tab,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        columns = (
            "order_number",
            "guest",
            "room",
            "dates",
            "guest_count",
            "amount",
            "status",
        )
        self.order_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Desti.Treeview",
            selectmode="browse",
        )

        headings = {
            "order_number": ("订单号", 180),
            "guest": ("联系人", 100),
            "room": ("房型", 140),
            "dates": ("入住 / 退房", 180),
            "guest_count": ("人数", 70),
            "amount": ("金额", 100),
            "status": ("状态", 90),
        }
        for column, (text, width) in headings.items():
            self.order_tree.heading(column, text=text)
            self.order_tree.column(column, width=width, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.order_tree.yview,
        )
        self.order_tree.configure(yscrollcommand=scrollbar.set)
        self.order_tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)

        buttons = tk.Frame(self.order_tab, bg=BACKGROUND)
        buttons.pack(fill="x", padx=12, pady=(0, 12))

        self._action_button(
            buttons, "确认订单", lambda: self._decide_order("confirmed")
        ).pack(side="left", padx=(0, 8))
        self._action_button(
            buttons, "拒绝订单", lambda: self._decide_order("rejected")
        ).pack(side="left", padx=(0, 8))
        self._action_button(
            buttons, "办理入住", lambda: self._change_order_flow("check_in")
        ).pack(side="right", padx=(8, 0))
        self._action_button(
            buttons, "办理退房", lambda: self._change_order_flow("check_out")
        ).pack(side="right")

    def _action_button(self, parent, text, command):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=DEEP_TEAL,
            fg=WHITE,
            activebackground=TEAL,
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 10, "bold"),
            padx=15,
            pady=9,
        )

    def _load_orders(self):
        if self.staff_user is None or not hasattr(self, "order_tree"):
            return

        status_label = self.status_filter_var.get()
        status = STATUS_FILTERS.get(status_label)

        try:
            self.orders = staff_service.list_staff_bookings(
                self.staff_user.id,
                status,
            )
        except Exception as error:
            messagebox.showerror(
                "读取订单失败",
                str(error),
                parent=self,
            )
            self.orders = []

        for item in self.order_tree.get_children():
            self.order_tree.delete(item)

        for index, order in enumerate(self.orders):
            self.order_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    order.get("order_number", ""),
                    order.get("contact_name", ""),
                    order.get("room_type_name", ""),
                    f'{order.get("check_in", "")} / {order.get("check_out", "")}',
                    f'{order.get("guest_count", "")} 人',
                    f'¥{float(order.get("total_amount", 0)):.2f}',
                    STATUS_TEXT.get(
                        order.get("status", ""),
                        order.get("status", ""),
                    ),
                ),
            )

    def _get_selected_order(self):
        selected = self.order_tree.selection()

        if not selected:
            messagebox.showinfo(
                "请先选择订单",
                "请先点击列表中的一笔订单。",
                parent=self,
            )
            return None

        return self.orders[int(selected[0])]

    def _decide_order(self, decision):
        order = self._get_selected_order()
        if order is None:
            return

        reason = ""
        if decision == "rejected":
            reason = simpledialog.askstring(
                "拒绝原因",
                "请输入拒绝原因：",
                parent=self,
            )
            if reason is None:
                return
            if not reason.strip():
                messagebox.showwarning(
                    "需要填写原因",
                    "拒绝订单时请填写原因。",
                    parent=self,
                )
                return

        try:
            result = staff_service.decide_booking(
                self.staff_user.id,
                order["order_number"],
                decision,
                reason,
            )
        except Exception as error:
            messagebox.showerror("操作失败", str(error), parent=self)
            return

        messagebox.showinfo("处理结果", result, parent=self)
        self._load_orders()
        self._load_logs()

    def _change_order_flow(self, action):
        order = self._get_selected_order()
        if order is None:
            return

        try:
            result = staff_service.update_booking_flow(
                self.staff_user.id,
                order["order_number"],
                action,
            )
        except Exception as error:
            messagebox.showerror("操作失败", str(error), parent=self)
            return

        messagebox.showinfo("处理结果", result, parent=self)
        self._load_orders()
        self._load_logs()

    def _build_room_tab(self):
        form = tk.Frame(
            self.room_tab,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        form.pack(fill="x", padx=12, pady=12)

        tk.Label(
            form,
            text="每日房价与库存",
            bg=WHITE,
            fg=TEXT,
            font=("Microsoft YaHei UI", 13, "bold"),
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=14, pady=(14, 10))

        tk.Label(form, text="房型", bg=WHITE, fg=SUBTEXT).grid(
            row=1, column=0, sticky="w", padx=14
        )
        self.room_type_var = tk.StringVar()
        self.room_type_box = ttk.Combobox(
            form,
            textvariable=self.room_type_var,
            state="readonly",
            width=24,
        )
        self.room_type_box.grid(row=2, column=0, sticky="ew", padx=14, pady=(5, 12))

        tk.Label(form, text="日期（YYYY-MM-DD）", bg=WHITE, fg=SUBTEXT).grid(
            row=1, column=1, sticky="w", padx=14
        )
        self.inventory_date_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(
            form,
            textvariable=self.inventory_date_var,
        ).grid(row=2, column=1, sticky="ew", padx=14, pady=(5, 12))

        tk.Label(form, text="总房间数", bg=WHITE, fg=SUBTEXT).grid(
            row=1, column=2, sticky="w", padx=14
        )
        self.total_rooms_var = tk.StringVar(value="6")
        ttk.Entry(
            form,
            textvariable=self.total_rooms_var,
        ).grid(row=2, column=2, sticky="ew", padx=14, pady=(5, 12))

        tk.Label(form, text="当日价格", bg=WHITE, fg=SUBTEXT).grid(
            row=1, column=3, sticky="w", padx=14
        )
        self.price_var = tk.StringVar(value="688")
        ttk.Entry(
            form,
            textvariable=self.price_var,
        ).grid(row=2, column=3, sticky="ew", padx=14, pady=(5, 12))

        for column in range(4):
            form.grid_columnconfigure(column, weight=1)

        actions = tk.Frame(form, bg=WHITE)
        actions.grid(row=3, column=0, columnspan=4, sticky="e", padx=14, pady=(0, 14))

        self._action_button(
            actions,
            "更新库存",
            self._update_inventory,
        ).pack(side="left", padx=(0, 8))

        self._action_button(
            actions,
            "更新房价",
            self._update_price,
        ).pack(side="left")

        sale_form = tk.Frame(
            self.room_tab,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        sale_form.pack(fill="x", padx=12, pady=(0, 12))

        tk.Label(
            sale_form,
            text="设置停售日期",
            bg=WHITE,
            fg=TEXT,
            font=("Microsoft YaHei UI", 12, "bold"),
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=14, pady=(12, 8))

        tk.Label(sale_form, text="开始日期", bg=WHITE, fg=SUBTEXT).grid(
            row=1, column=0, sticky="w", padx=14
        )
        self.sale_start_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(sale_form, textvariable=self.sale_start_var).grid(
            row=2, column=0, sticky="ew", padx=14, pady=(4, 12)
        )

        tk.Label(sale_form, text="结束日期", bg=WHITE, fg=SUBTEXT).grid(
            row=1, column=1, sticky="w", padx=14
        )
        self.sale_end_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(sale_form, textvariable=self.sale_end_var).grid(
            row=2, column=1, sticky="ew", padx=14, pady=(4, 12)
        )

        tk.Label(sale_form, text="停售原因", bg=WHITE, fg=SUBTEXT).grid(
            row=1, column=2, sticky="w", padx=14
        )
        self.sale_reason_var = tk.StringVar()
        ttk.Entry(sale_form, textvariable=self.sale_reason_var).grid(
            row=2, column=2, sticky="ew", padx=14, pady=(4, 12)
        )

        tk.Button(
            sale_form,
            text="设置停售",
            command=self._create_stop_sale,
            bg=DEEP_TEAL,
            fg=WHITE,
            activebackground=TEAL,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8,
        ).grid(row=2, column=3, padx=14, pady=(4, 12), sticky="e")

        for column in range(4):
            sale_form.grid_columnconfigure(column, weight=1)

        stop_header = tk.Frame(self.room_tab, bg=BACKGROUND)
        stop_header.pack(fill="x", padx=12, pady=(0, 5))

        tk.Label(
            stop_header,
            text="停售记录",
            bg=BACKGROUND,
            fg=TEXT,
            font=("Microsoft YaHei UI", 11, "bold"),
        ).pack(side="left")

        tk.Button(
            stop_header,
            text="删除选中停售",
            command=self._remove_stop_sale,
            bg=PALE_BLUE,
            fg=DEEP_TEAL,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
        ).pack(side="right")

        table_frame = tk.Frame(
            self.room_tab,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.stop_sale_tree = ttk.Treeview(
            table_frame,
            columns=("room", "start", "end", "reason"),
            show="headings",
            style="Desti.Treeview",
            selectmode="browse",
        )

        for column, text, width in (
            ("room", "房型", 180),
            ("start", "开始日期", 130),
            ("end", "结束日期", 130),
            ("reason", "停售原因", 330),
        ):
            self.stop_sale_tree.heading(column, text=text)
            self.stop_sale_tree.column(column, width=width, anchor="center")

        self.stop_sale_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def _load_room_types(self):
        try:
            self.room_types = staff_service.list_staff_room_types(
                self.staff_user.id
            )
        except Exception as error:
            messagebox.showerror("读取房型失败", str(error), parent=self)
            self.room_types = []

        self.room_type_by_label = {
            f'{room["name"]}（最多 {room["max_guests"]} 人）': room["id"]
            for room in self.room_types
        }

        labels = list(self.room_type_by_label.keys())
        self.room_type_box.configure(values=labels)

        if labels:
            self.room_type_var.set(labels[0])

    def _selected_room_type_id(self):
        label = self.room_type_var.get()

        if label not in self.room_type_by_label:
            messagebox.showwarning(
                "请选择房型",
                "请先选择要管理的房型。",
                parent=self,
            )
            return None

        return self.room_type_by_label[label]

    def _update_inventory(self):
        room_type_id = self._selected_room_type_id()
        if room_type_id is None:
            return

        try:
            result = staff_service.update_daily_inventory(
                self.staff_user.id,
                room_type_id,
                self.inventory_date_var.get().strip(),
                self.total_rooms_var.get().strip(),
            )
        except Exception as error:
            messagebox.showerror("更新失败", str(error), parent=self)
            return

        messagebox.showinfo("处理结果", result, parent=self)
        self._load_logs()

    def _update_price(self):
        room_type_id = self._selected_room_type_id()
        if room_type_id is None:
            return

        try:
            result = staff_service.update_daily_price(
                self.staff_user.id,
                room_type_id,
                self.inventory_date_var.get().strip(),
                self.price_var.get().strip(),
            )
        except Exception as error:
            messagebox.showerror("更新失败", str(error), parent=self)
            return

        messagebox.showinfo("处理结果", result, parent=self)
        self._load_logs()

    def _create_stop_sale(self):
        room_type_id = self._selected_room_type_id()
        if room_type_id is None:
            return

        try:
            result = staff_service.create_stop_sale(
                self.staff_user.id,
                room_type_id,
                self.sale_start_var.get().strip(),
                self.sale_end_var.get().strip(),
                self.sale_reason_var.get().strip(),
            )
        except Exception as error:
            messagebox.showerror("设置失败", str(error), parent=self)
            return

        messagebox.showinfo("处理结果", result, parent=self)
        self._load_stop_sales()
        self._load_logs()

    def _load_stop_sales(self):
        if self.staff_user is None or not hasattr(self, "stop_sale_tree"):
            return

        try:
            stop_sales = staff_service.list_staff_stop_sales(
                self.staff_user.id
            )
        except Exception as error:
            messagebox.showerror("读取停售记录失败", str(error), parent=self)
            return

        for item in self.stop_sale_tree.get_children():
            self.stop_sale_tree.delete(item)

        self.stop_sales = stop_sales

        for index, item in enumerate(stop_sales):
            self.stop_sale_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    item.get("room_type_name", ""),
                    item.get("start_date", ""),
                    item.get("end_date", ""),
                    item.get("reason", ""),
                ),
            )

    def _remove_stop_sale(self):
        selected = self.stop_sale_tree.selection()

        if not selected:
            messagebox.showinfo(
                "请先选择记录",
                "请先在停售记录列表中选择一条记录。",
                parent=self,
            )
            return

        item = self.stop_sales[int(selected[0])]

        confirmed = messagebox.askyesno(
            "确认删除",
            "确定删除选中的停售记录吗？",
            parent=self,
        )
        if not confirmed:
            return

        try:
            result = staff_service.remove_stop_sale(
                self.staff_user.id,
                item["id"],
            )
        except Exception as error:
            messagebox.showerror("删除失败", str(error), parent=self)
            return

        messagebox.showinfo("处理结果", result, parent=self)
        self._load_stop_sales()
        self._load_logs()

    def _build_log_tab(self):
        self.statistics_label = tk.Label(
            self.log_tab,
            text="",
            bg=MINT,
            fg=TEXT,
            anchor="w",
            padx=14,
            pady=12,
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        self.statistics_label.pack(fill="x", padx=12, pady=12)

        tk.Button(
            self.log_tab,
            text="刷新统计与日志",
            command=self._load_logs,
            bg=PALE_BLUE,
            fg=DEEP_TEAL,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=7,
        ).pack(anchor="e", padx=12, pady=(0, 8))

        table_frame = tk.Frame(
            self.log_tab,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.log_tree = ttk.Treeview(
            table_frame,
            columns=("time", "action", "details"),
            show="headings",
            style="Desti.Treeview",
        )

        for column, text, width in (
            ("time", "操作时间", 180),
            ("action", "操作类型", 160),
            ("details", "操作说明", 550),
        ):
            self.log_tree.heading(column, text=text)
            self.log_tree.column(column, width=width, anchor="w")

        self.log_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def _load_logs(self):
        if self.staff_user is None or not hasattr(self, "statistics_label"):
            return

        try:
            statistics = staff_service.get_staff_statistics(
                self.staff_user.id
            )
            logs = staff_service.list_staff_operation_logs(
                self.staff_user.id
            )
        except Exception as error:
            messagebox.showerror("读取统计或日志失败", str(error), parent=self)
            return

        counts = statistics["status_counts"]
        self.statistics_label.configure(
            text=(
                f'酒店：{statistics["hotel_name"]}    '
                f'订单总数：{statistics["total_bookings"]}    '
                f'待确认：{counts.get("pending", 0)}    '
                f'已确认：{counts.get("confirmed", 0)}    '
                f'已入住：{counts.get("checked_in", 0)}    '
                f'已退房：{counts.get("checked_out", 0)}'
            )
        )

        for item in self.log_tree.get_children():
            self.log_tree.delete(item)

        for index, log in enumerate(logs):
            self.log_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    log.get("created_at", ""),
                    log.get("action", ""),
                    log.get("details", ""),
                ),
            )