import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta

from auth_service import login, register_customer
from hotel_service import add_demo_data, search_room_types
from booking_service import (
    create_booking,
    list_customer_bookings,
    cancel_booking,
)


# Desti 的基础配色
TEAL = "#67BAC6"
DEEP_TEAL = "#276F78"
PALE_BLUE = "#E8F7F8"
MINT = "#EAF6EF"
CREAM = "#FDF196"
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


def format_price(value):
    """把价格显示成两位小数。"""
    try:
        return f"¥{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value)


def show_status(status):
    """把数据库中的英文订单状态转换为界面显示文字。"""
    return STATUS_TEXT.get(status, str(status))


class DestiApp(tk.Tk):
    """Desti 酒店预订系统的顾客端窗口。"""

    def __init__(self):
        super().__init__()

        self.title("Desti 酒店预订")
        self.geometry("1180x760")
        self.minsize(980, 650)
        self.configure(bg=BACKGROUND)

        self.current_user = None
        self.search_results = []
        self.search_params = None
        self.orders = []

        # 确保演示酒店和房型数据已写入数据库。
        add_demo_data()

        self._configure_styles()
        self._build_window()
        self.show_search_page()

    def _configure_styles(self):
        """设置表格和 ttk 控件的统一样式。"""
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
            rowheight=34,
            font=("Microsoft YaHei UI", 10),
        )
        style.configure(
            "Desti.Treeview.Heading",
            background=PALE_BLUE,
            foreground=TEXT,
            font=("Microsoft YaHei UI", 10, "bold"),
            padding=(8, 8),
        )
        style.map(
            "Desti.Treeview",
            background=[("selected", DEEP_TEAL)],
            foreground=[("selected", WHITE)],
        )
        style.configure(
            "TEntry",
            padding=(8, 7),
            font=("Microsoft YaHei UI", 10),
        )
        style.configure(
            "TSpinbox",
            padding=(8, 7),
            font=("Microsoft YaHei UI", 10),
        )

    def _build_window(self):
        """搭建顶部栏、左侧导航栏和主内容区域。"""
        header = tk.Frame(self, bg=WHITE, height=76)
        header.pack(fill="x")
        header.pack_propagate(False)

        # 简单绘制 Desti 图标：字母 D 与一扇门。
        logo = tk.Canvas(
            header,
            width=42,
            height=42,
            bg=WHITE,
            highlightthickness=0,
        )
        logo.pack(side="left", padx=(24, 8), pady=16)
        logo.create_rectangle(3, 3, 39, 39, fill=DEEP_TEAL, outline="")
        logo.create_rectangle(13, 10, 29, 34, fill=CREAM, outline="")
        logo.create_rectangle(17, 14, 29, 34, fill=WHITE, outline="")
        logo.create_oval(25, 23, 27, 25, fill=TEAL, outline="")

        tk.Label(
            header,
            text="Desti",
            bg=WHITE,
            fg=TEAL,
            font=("Microsoft YaHei UI", 23, "bold"),
        ).pack(side="left")

        tk.Frame(header, bg=BORDER, width=1, height=34).pack(
            side="left", padx=20
        )

        tk.Label(
            header,
            text="酒店预订",
            bg=WHITE,
            fg=TEXT,
            font=("Microsoft YaHei UI", 12),
        ).pack(side="left")

        self.profile_button = tk.Button(
            header,
            text="登录 / 注册",
            command=self._profile_action,
            bg=DEEP_TEAL,
            fg=WHITE,
            activebackground=TEAL,
            activeforeground=WHITE,
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 10, "bold"),
            padx=18,
            pady=9,
        )
        self.profile_button.pack(side="right", padx=24, pady=17)

        body = tk.Frame(self, bg=BACKGROUND)
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg=TEAL, width=218)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="旅客导航",
            bg=TEAL,
            fg=WHITE,
            font=("Microsoft YaHei UI", 12, "bold"),
        ).pack(anchor="w", padx=22, pady=(30, 16))

        self.nav_buttons = {}

        self.nav_buttons["search"] = self._make_nav_button(
            sidebar, "⌕   酒店搜索", self.show_search_page
        )
        self.nav_buttons["orders"] = self._make_nav_button(
            sidebar, "▤   我的订单", self.show_orders_page
        )

        tk.Label(
            sidebar,
            text="让每一次抵达\n都住得安心",
            bg=TEAL,
            fg="#E8FFFF",
            justify="left",
            font=("Microsoft YaHei UI", 10),
        ).pack(side="bottom", anchor="w", padx=22, pady=24)

        self.content = tk.Frame(body, bg=BACKGROUND)
        self.content.pack(side="left", fill="both", expand=True)

    def _make_nav_button(self, parent, text, command):
        button = tk.Button(
            parent,
            text=text,
            command=command,
            anchor="w",
            bg=TEAL,
            fg=WHITE,
            activebackground=DEEP_TEAL,
            activeforeground=WHITE,
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 11),
            padx=20,
            pady=13,
        )
        button.pack(fill="x", padx=12, pady=4)
        return button

    def _set_active_nav(self, active_name):
        for name, button in self.nav_buttons.items():
            if name == active_name:
                button.configure(bg=DEEP_TEAL, font=("Microsoft YaHei UI", 11, "bold"))
            else:
                button.configure(bg=TEAL, font=("Microsoft YaHei UI", 11))

    def _clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def _profile_action(self):
        if self.current_user is None:
            self._open_login_window()
            return

        should_logout = messagebox.askyesno(
            "退出登录",
            f"当前账号：{self.current_user.username}\n确定要退出登录吗？",
            parent=self,
        )
        if should_logout:
            self.current_user = None
            self.profile_button.configure(text="登录 / 注册")
            self.show_search_page()

    def _set_logged_in_user(self, user, window):
        self.current_user = user
        self.profile_button.configure(text=f"{user.username} · 退出")
        window.destroy()
        messagebox.showinfo(
            "登录成功",
            f"欢迎回来，{user.username}！",
            parent=self,
        )

    def _open_login_window(self):
        window = tk.Toplevel(self)
        window.title("登录 Desti")
        window.geometry("390x320")
        window.resizable(False, False)
        window.configure(bg=WHITE)
        window.transient(self)
        window.grab_set()

        tk.Label(
            window,
            text="欢迎来到 Desti",
            bg=WHITE,
            fg=DEEP_TEAL,
            font=("Microsoft YaHei UI", 19, "bold"),
        ).pack(pady=(25, 5))

        tk.Label(
            window,
            text="登录后即可提交预订和管理订单",
            bg=WHITE,
            fg=SUBTEXT,
            font=("Microsoft YaHei UI", 9),
        ).pack(pady=(0, 18))

        form = tk.Frame(window, bg=WHITE)
        form.pack(fill="x", padx=34)

        tk.Label(form, text="用户名", bg=WHITE, fg=TEXT).pack(anchor="w")
        username_entry = ttk.Entry(form)
        username_entry.pack(fill="x", pady=(5, 12))

        tk.Label(form, text="密码", bg=WHITE, fg=TEXT).pack(anchor="w")
        password_entry = ttk.Entry(form, show="*")
        password_entry.pack(fill="x", pady=(5, 14))

        def do_login():
            username = username_entry.get().strip()
            password = password_entry.get()

            if not username or not password:
                messagebox.showwarning(
                    "信息不完整",
                    "请输入用户名和密码。",
                    parent=window,
                )
                return

            try:
                user = login(username, password)
            except Exception as error:
                messagebox.showerror(
                    "登录失败",
                    f"登录时发生错误：\n{error}",
                    parent=window,
                )
                return

            if user is None:
                messagebox.showerror(
                    "登录失败",
                    "用户名或密码不正确。",
                    parent=window,
                )
                return

            self._set_logged_in_user(user, window)

        buttons = tk.Frame(window, bg=WHITE)
        buttons.pack(fill="x", padx=34, pady=(2, 18))

        tk.Button(
            buttons,
            text="登录",
            command=do_login,
            bg=DEEP_TEAL,
            fg=WHITE,
            activebackground=TEAL,
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 10, "bold"),
            padx=20,
            pady=9,
        ).pack(side="left", fill="x", expand=True)

        tk.Button(
            buttons,
            text="注册新账号",
            command=lambda: self._open_register_window(window),
            bg=PALE_BLUE,
            fg=DEEP_TEAL,
            activebackground=MINT,
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 10),
            padx=14,
            pady=9,
        ).pack(side="left", padx=(10, 0))

        username_entry.focus_set()
        window.bind("<Return>", lambda event: do_login())

    def _open_register_window(self, login_window=None):
        if login_window is not None:
            login_window.destroy()

        window = tk.Toplevel(self)
        window.title("注册 Desti 账号")
        window.geometry("410x390")
        window.resizable(False, False)
        window.configure(bg=WHITE)
        window.transient(self)
        window.grab_set()

        tk.Label(
            window,
            text="创建 Desti 账号",
            bg=WHITE,
            fg=DEEP_TEAL,
            font=("Microsoft YaHei UI", 18, "bold"),
        ).pack(pady=(24, 18))

        form = tk.Frame(window, bg=WHITE)
        form.pack(fill="x", padx=34)

        tk.Label(form, text="用户名", bg=WHITE, fg=TEXT).pack(anchor="w")
        username_entry = ttk.Entry(form)
        username_entry.pack(fill="x", pady=(4, 10))

        tk.Label(form, text="手机号", bg=WHITE, fg=TEXT).pack(anchor="w")
        phone_entry = ttk.Entry(form)
        phone_entry.pack(fill="x", pady=(4, 10))

        tk.Label(form, text="密码", bg=WHITE, fg=TEXT).pack(anchor="w")
        password_entry = ttk.Entry(form, show="*")
        password_entry.pack(fill="x", pady=(4, 10))

        tk.Label(form, text="确认密码", bg=WHITE, fg=TEXT).pack(anchor="w")
        confirm_entry = ttk.Entry(form, show="*")
        confirm_entry.pack(fill="x", pady=(4, 14))

        def do_register():
            username = username_entry.get().strip()
            phone = phone_entry.get().strip()
            password = password_entry.get()
            confirm_password = confirm_entry.get()

            if not username or not phone or not password:
                messagebox.showwarning(
                    "信息不完整",
                    "请填写用户名、手机号和密码。",
                    parent=window,
                )
                return

            if password != confirm_password:
                messagebox.showwarning(
                    "密码不一致",
                    "两次输入的密码不一致，请重新检查。",
                    parent=window,
                )
                return

            try:
                user = register_customer(username, phone, password)
                if user is None:
                    raise ValueError("注册没有成功，请检查输入信息。")
            except Exception as error:
                messagebox.showerror(
                    "注册失败",
                    f"注册时发生错误：\n{error}",
                    parent=window,
                )
                return

            self._set_logged_in_user(user, window)

        tk.Button(
            window,
            text="注册并登录",
            command=do_register,
            bg=DEEP_TEAL,
            fg=WHITE,
            activebackground=TEAL,
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 10, "bold"),
            padx=20,
            pady=10,
        ).pack(fill="x", padx=34, pady=(0, 20))

        username_entry.focus_set()

    def show_search_page(self):
        self._set_active_nav("search")
        self._clear_content()

        page = tk.Frame(self.content, bg=BACKGROUND)
        page.pack(fill="both", expand=True, padx=30, pady=26)

        tk.Label(
            page,
            text="找到下一段旅程的落脚点",
            bg=BACKGROUND,
            fg=TEXT,
            font=("Microsoft YaHei UI", 22, "bold"),
        ).pack(anchor="w")

        tk.Label(
            page,
            text="按目的地、入住日期和人数查找可预订房型",
            bg=BACKGROUND,
            fg=SUBTEXT,
            font=("Microsoft YaHei UI", 10),
        ).pack(anchor="w", pady=(5, 18))

        search_card = tk.Frame(
            page,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        search_card.pack(fill="x", pady=(0, 20))

        tk.Label(
            search_card,
            text="搜索酒店",
            bg=WHITE,
            fg=TEXT,
            font=("Microsoft YaHei UI", 13, "bold"),
        ).pack(anchor="w", padx=20, pady=(17, 12))

        form = tk.Frame(search_card, bg=WHITE)
        form.pack(fill="x", padx=13, pady=(0, 8))

        self.city_var = tk.StringVar(value="上海")
        self.check_in_var = tk.StringVar(
            value=(date.today() + timedelta(days=1)).isoformat()
        )
        self.check_out_var = tk.StringVar(
            value=(date.today() + timedelta(days=2)).isoformat()
        )
        self.guest_count_var = tk.StringVar(value="2")

        self._make_search_field(form, "目的地", self.city_var, 0)
        self._make_search_field(form, "入住日期（YYYY-MM-DD）", self.check_in_var, 1)
        self._make_search_field(form, "退房日期（YYYY-MM-DD）", self.check_out_var, 2)

        guest_frame = tk.Frame(form, bg=WHITE)
        guest_frame.grid(row=0, column=3, sticky="ew", padx=7, pady=4)
        tk.Label(
            guest_frame,
            text="入住人数",
            bg=WHITE,
            fg=SUBTEXT,
            font=("Microsoft YaHei UI", 9),
        ).pack(anchor="w", pady=(0, 5))
        ttk.Spinbox(
            guest_frame,
            from_=1,
            to=10,
            textvariable=self.guest_count_var,
            width=8,
        ).pack(fill="x")

        for column in range(4):
            form.grid_columnconfigure(column, weight=1)

        tk.Button(
            form,
            text="⌕  搜索房型",
            command=self._run_search,
            bg=DEEP_TEAL,
            fg=WHITE,
            activebackground=TEAL,
            activeforeground=WHITE,
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 10, "bold"),
            padx=18,
            pady=10,
        ).grid(row=1, column=0, columnspan=4, sticky="e", padx=7, pady=(12, 12))

        results_header = tk.Frame(page, bg=BACKGROUND)
        results_header.pack(fill="x", pady=(0, 8))

        tk.Label(
            results_header,
            text="可预订房型",
            bg=BACKGROUND,
            fg=TEXT,
            font=("Microsoft YaHei UI", 14, "bold"),
        ).pack(side="left")

        self.search_status = tk.Label(
            results_header,
            text="填写条件后点击“搜索房型”",
            bg=BACKGROUND,
            fg=SUBTEXT,
            font=("Microsoft YaHei UI", 9),
        )
        self.search_status.pack(side="right")

        table_frame = tk.Frame(
            page,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        table_frame.pack(fill="both", expand=True)

        columns = ("hotel", "room_type", "capacity", "available", "price")
        self.result_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Desti.Treeview",
            selectmode="browse",
        )

        headings = {
            "hotel": ("酒店", 210),
            "room_type": ("房型", 190),
            "capacity": ("最多入住", 110),
            "available": ("可订房间", 110),
            "price": ("所选日期总价", 150),
        }
        for column, (title, width) in headings.items():
            self.result_tree.heading(column, text=title)
            self.result_tree.column(column, width=width, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.result_tree.yview,
        )
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        self.result_tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)

        bottom = tk.Frame(page, bg=BACKGROUND)
        bottom.pack(fill="x", pady=(12, 0))

        tk.Label(
            bottom,
            text="选择一个房型后即可继续预订。提交预订前需要登录。",
            bg=BACKGROUND,
            fg=SUBTEXT,
            font=("Microsoft YaHei UI", 9),
        ).pack(side="left")

        tk.Button(
            bottom,
            text="预订选中房型  →",
            command=self._book_selected_room,
            bg=DEEP_TEAL,
            fg=WHITE,
            activebackground=TEAL,
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 10, "bold"),
            padx=18,
            pady=10,
        ).pack(side="right")

    def _make_search_field(self, parent, label_text, variable, column):
        field = tk.Frame(parent, bg=WHITE)
        field.grid(row=0, column=column, sticky="ew", padx=7, pady=4)

        tk.Label(
            field,
            text=label_text,
            bg=WHITE,
            fg=SUBTEXT,
            font=("Microsoft YaHei UI", 9),
        ).pack(anchor="w", pady=(0, 5))

        ttk.Entry(field, textvariable=variable).pack(fill="x")

    def _run_search(self):
        city = self.city_var.get().strip()
        check_in = self.check_in_var.get().strip()
        check_out = self.check_out_var.get().strip()

        try:
            guest_count = int(self.guest_count_var.get())
            check_in_date = date.fromisoformat(check_in)
            check_out_date = date.fromisoformat(check_out)
        except ValueError:
            messagebox.showwarning(
                "搜索条件有误",
                "请检查日期格式（YYYY-MM-DD）和入住人数。",
                parent=self,
            )
            return

        if not city:
            messagebox.showwarning("缺少目的地", "请输入城市名称。", parent=self)
            return

        if guest_count < 1:
            messagebox.showwarning("人数有误", "入住人数至少为 1 人。", parent=self)
            return

        if check_out_date <= check_in_date:
            messagebox.showwarning(
                "日期有误",
                "退房日期必须晚于入住日期。",
                parent=self,
            )
            return

        try:
            self.search_results = search_room_types(
                city,
                check_in,
                check_out,
                guest_count,
            )
        except Exception as error:
            messagebox.showerror(
                "搜索失败",
                f"查询酒店时发生错误：\n{error}",
                parent=self,
            )
            return

        self.search_params = {
            "city": city,
            "check_in": check_in,
            "check_out": check_out,
            "guest_count": guest_count,
        }

        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        for index, room in enumerate(self.search_results):
            self.result_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    room.get("hotel_name", ""),
                    room.get("room_type_name", ""),
                    f'{room.get("max_guests", "-")} 人',
                    f'{room.get("available_rooms", "-")} 间',
                    format_price(room.get("total_price", 0)),
                ),
            )

        if self.search_results:
            self.search_status.configure(
                text=f"找到 {len(self.search_results)} 个可预订房型"
            )
        else:
            self.search_status.configure(text="没有找到符合条件的房型")

    def _book_selected_room(self):
        selected = self.result_tree.selection()

        if not selected:
            messagebox.showinfo(
                "请先选择房型",
                "请先在列表中点击一个房型。",
                parent=self,
            )
            return

        if not self.search_params:
            messagebox.showinfo(
                "请先搜索",
                "请先填写搜索条件并搜索房型。",
                parent=self,
            )
            return

        if self.current_user is None:
            messagebox.showinfo(
                "需要登录",
                "登录或注册后才能提交预订。",
                parent=self,
            )
            self._open_login_window()
            return

        index = int(selected[0])
        room = self.search_results[index]
        self._open_booking_window(room)

    def _open_booking_window(self, room):
        params = self.search_params

        window = tk.Toplevel(self)
        window.title("确认预订")
        window.geometry("470x480")
        window.resizable(False, False)
        window.configure(bg=WHITE)
        window.transient(self)
        window.grab_set()

        tk.Label(
            window,
            text="确认预订信息",
            bg=WHITE,
            fg=DEEP_TEAL,
            font=("Microsoft YaHei UI", 18, "bold"),
        ).pack(anchor="w", padx=28, pady=(24, 14))

        summary = (
            f'{room.get("hotel_name", "")} · {room.get("room_type_name", "")}\n'
            f'入住：{params["check_in"]}    退房：{params["check_out"]}\n'
            f'入住人数：{params["guest_count"]} 人\n'
            f'房费合计：{format_price(room.get("total_price", 0))}'
        )
        tk.Label(
            window,
            text=summary,
            bg=MINT,
            fg=TEXT,
            justify="left",
            anchor="w",
            padx=14,
            pady=14,
            font=("Microsoft YaHei UI", 10),
        ).pack(fill="x", padx=28, pady=(0, 18))

        form = tk.Frame(window, bg=WHITE)
        form.pack(fill="x", padx=28)

        tk.Label(form, text="联系人姓名", bg=WHITE, fg=TEXT).pack(anchor="w")
        name_var = tk.StringVar(value=self.current_user.username)
        ttk.Entry(form, textvariable=name_var).pack(fill="x", pady=(5, 14))

        tk.Label(form, text="联系人手机号", bg=WHITE, fg=TEXT).pack(anchor="w")
        phone_var = tk.StringVar(value=self.current_user.phone)
        ttk.Entry(form, textvariable=phone_var).pack(fill="x", pady=(5, 16))

        def submit_booking():
            contact_name = name_var.get().strip()
            contact_phone = phone_var.get().strip()

            if not contact_name or not contact_phone:
                messagebox.showwarning(
                    "信息不完整",
                    "请填写联系人姓名和手机号。",
                    parent=window,
                )
                return

            try:
                booking = create_booking(
                    self.current_user.id,
                    room["room_type_id"],
                    params["check_in"],
                    params["check_out"],
                    params["guest_count"],
                    contact_name,
                    contact_phone,
                )
            except Exception as error:
                messagebox.showerror(
                    "预订失败",
                    f"提交预订时发生错误：\n{error}",
                    parent=window,
                )
                return

            order_number = getattr(booking, "order_number", "订单已创建")
            window.destroy()
            messagebox.showinfo(
                "提交成功",
                f"订单已提交。\n订单号：{order_number}\n当前状态：待确认",
                parent=self,
            )
            self.show_orders_page()

        tk.Button(
            window,
            text="确认提交预订",
            command=submit_booking,
            bg=DEEP_TEAL,
            fg=WHITE,
            activebackground=TEAL,
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 10, "bold"),
            padx=20,
            pady=11,
        ).pack(fill="x", padx=28, pady=(8, 22))

    def show_orders_page(self):
        if self.current_user is None:
            messagebox.showinfo(
                "需要登录",
                "登录后才能查看自己的订单。",
                parent=self,
            )
            self._open_login_window()
            return

        self._set_active_nav("orders")
        self._clear_content()

        page = tk.Frame(self.content, bg=BACKGROUND)
        page.pack(fill="both", expand=True, padx=30, pady=26)

        tk.Label(
            page,
            text="我的订单",
            bg=BACKGROUND,
            fg=TEXT,
            font=("Microsoft YaHei UI", 22, "bold"),
        ).pack(anchor="w")

        tk.Label(
            page,
            text="查看订单状态，或取消尚未入住的订单",
            bg=BACKGROUND,
            fg=SUBTEXT,
            font=("Microsoft YaHei UI", 10),
        ).pack(anchor="w", pady=(5, 18))

        try:
            self.orders = list_customer_bookings(self.current_user.id)
        except Exception as error:
            messagebox.showerror(
                "查询失败",
                f"读取订单时发生错误：\n{error}",
                parent=self,
            )
            self.orders = []

        table_frame = tk.Frame(
            page,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        table_frame.pack(fill="both", expand=True)

        columns = (
            "order_number",
            "hotel",
            "room_type",
            "dates",
            "guests",
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

        order_headings = {
            "order_number": ("订单号", 180),
            "hotel": ("酒店", 150),
            "room_type": ("房型", 140),
            "dates": ("入住 / 退房", 190),
            "guests": ("人数", 70),
            "amount": ("金额", 110),
            "status": ("状态", 100),
        }
        for column, (title, width) in order_headings.items():
            self.order_tree.heading(column, text=title)
            self.order_tree.column(column, width=width, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.order_tree.yview,
        )
        self.order_tree.configure(yscrollcommand=scrollbar.set)
        self.order_tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)

        for index, order in enumerate(self.orders):
            check_in = order.get("check_in", "")
            check_out = order.get("check_out", "")
            dates_text = f"{check_in} / {check_out}"

            self.order_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    order.get("order_number", ""),
                    order.get("hotel_name", ""),
                    order.get("room_type_name", ""),
                    dates_text,
                    f'{order.get("guest_count", "-")} 人',
                    format_price(order.get("total_amount", 0)),
                    show_status(order.get("status", "")),
                ),
            )

        bottom = tk.Frame(page, bg=BACKGROUND)
        bottom.pack(fill="x", pady=(14, 0))

        tk.Button(
            bottom,
            text="刷新订单",
            command=self.show_orders_page,
            bg=PALE_BLUE,
            fg=DEEP_TEAL,
            activebackground=MINT,
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 10),
            padx=18,
            pady=9,
        ).pack(side="left")

        tk.Button(
            bottom,
            text="取消选中订单",
            command=self._cancel_selected_order,
            bg=DEEP_TEAL,
            fg=WHITE,
            activebackground=TEAL,
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 10, "bold"),
            padx=18,
            pady=9,
        ).pack(side="right")

    def _cancel_selected_order(self):
        selected = self.order_tree.selection()

        if not selected:
            messagebox.showinfo(
                "请先选择订单",
                "请先在订单列表中点击一条订单。",
                parent=self,
            )
            return

        index = int(selected[0])
        order = self.orders[index]
        status = order.get("status", "")

        if status not in ("pending", "confirmed"):
            messagebox.showwarning(
                "暂不能取消",
                "当前状态的订单不能通过此页面取消。",
                parent=self,
            )
            return

        confirmed = messagebox.askyesno(
            "确认取消订单",
            f'确定取消订单 {order.get("order_number", "")} 吗？\n'
            "取消成功后，对应房间库存会释放。",
            parent=self,
        )
        if not confirmed:
            return

        try:
            result = cancel_booking(
                self.current_user.id,
                order["order_number"],
                "顾客通过“我的订单”页面申请取消",
            )
        except Exception as error:
            messagebox.showerror(
                "取消失败",
                f"取消订单时发生错误：\n{error}",
                parent=self,
            )
            return

        messagebox.showinfo("取消结果", str(result), parent=self)
        self.show_orders_page()