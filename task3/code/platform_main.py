import sys
from pathlib import Path


CODE_FOLDER = str(Path(__file__).resolve().parent)

if CODE_FOLDER not in sys.path:
    sys.path.insert(0, CODE_FOLDER)


from hotel_service import add_demo_data
from platform_service import ensure_platform_support
from platform_ui import PlatformApp


if __name__ == "__main__":
    add_demo_data()
    ensure_platform_support()

    app = PlatformApp()
    app.mainloop()