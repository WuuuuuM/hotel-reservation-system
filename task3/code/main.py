import sys
from pathlib import Path


# 把 code 文件夹加入 Python 的模块查找路径，
# 这样 main.py 才能找到 ui.py 和各个业务模块。
CODE_FOLDER = str(Path(__file__).resolve().parent)

if CODE_FOLDER not in sys.path:
    sys.path.insert(0, CODE_FOLDER)


from ui import DestiApp


if __name__ == "__main__":
    app = DestiApp()
    app.mainloop()