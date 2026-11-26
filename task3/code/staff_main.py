import sys
from pathlib import Path


CODE_FOLDER = str(Path(__file__).resolve().parent)

if CODE_FOLDER not in sys.path:
    sys.path.insert(0, CODE_FOLDER)


from hotel_service import add_demo_data
from staff_service import ensure_demo_staff_account
from staff_ui import StaffApp


if __name__ == "__main__":
    # 确保酒店、房型和员工演示账号都已准备好。
    add_demo_data()
    ensure_demo_staff_account()

    app = StaffApp()
    app.mainloop()