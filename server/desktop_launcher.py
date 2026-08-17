"""桌面版启动入口：双击 exe 后启动本地服务，以 pywebview 原生窗口展示应用

行为：
- 固定端口（默认 5000，环境变量 NAV_PORT 可覆盖）；
- 单实例：检测到已在运行 → 本次启动直接退出，不重复启动；
- 端口被其他程序占用 → 弹出错误提示并退出；
- 关闭窗口即退出应用；页面右上角“退出”按钮亦可停止服务并关闭窗口；
- NAV_NO_WINDOW=1 时不创建窗口（无界面模式，便于自动化测试）。

打包命令（在 server/ 目录下执行）：
    pyinstaller --noconfirm --onefile --windowed --name NavApp \
        --icon "../web/public/favicon.ico" \
        --add-data "../web/dist;web/dist" desktop_launcher.py
"""

import ctypes
import json
import os
import socket
import sys
import threading
import urllib.request
from pathlib import Path

DEFAULT_PORT = 5000
MUTEX_NAME = "Local\\NavApp.SingleInstance"
WINDOW = None


def _app_root():
    """exe 同级目录（frozen）或脚本所在目录（源码运行）"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _ensure_dirs(root):
    for name in ("data", "log"):
        (root / name).mkdir(parents=True, exist_ok=True)


def _redirect_streams(log_dir):
    """windowed 模式下 stdout/stderr 为 None，重定向到日志文件便于排障"""
    if not getattr(sys, "frozen", False):
        return
    sys.stdout = open(log_dir / "desktop.out.log", "a", encoding="utf-8")
    sys.stderr = open(log_dir / "desktop.err.log", "a", encoding="utf-8")


def _force_utf8_stdio():
    """避免中文 Windows 控制台（GBK）打印 emoji 等字符时 UnicodeEncodeError"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _port():
    return int(os.environ.get("NAV_PORT", DEFAULT_PORT))


def _home_url(port):
    return f"http://127.0.0.1:{port}/#/home"


def _icon_path(root):
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", root)) / "web" / "dist" / "favicon.ico"
    return root.parent / "web" / "dist" / "favicon.ico"


def _error_box(message, title="NavApp"):
    try:
        ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)
    except Exception:
        print(f"[desktop] 错误: {message}", flush=True)


def _is_our_app_running(port):
    """探测端口上是否是本桌面应用（/appmode 返回 desktop:true）"""
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/appmode", timeout=2
        ) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body.get("data", {}).get("desktop") is True
    except Exception:
        return False


def _port_available(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _acquire_mutex():
    """Windows 命名互斥体：返回句柄表示本进程是唯一实例；返回 None 表示已有实例。

    用于极速双击竞态仲裁（Werkzeug 监听套接字默认 SO_REUSEADDR，
    Windows 下允许第二个实例也绑上同一端口，仅靠端口探测无法区分）。
    """
    if sys.platform != "win32":
        return object()
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(handle)
        return None
    return handle


def _activate_existing(port):
    """已有实例在运行：打印提示后退出（不重复启动）"""
    print(f"[desktop] 应用已在运行: {_home_url(port)}，本次启动退出", flush=True)
    sys.exit(0)


def _request_shutdown(shutdown_fn=None):
    """停止服务并关闭窗口；兜底 4s 后强制退出进程"""
    if callable(shutdown_fn):
        shutdown_fn()
    threading.Timer(0.5, _close_window).start()
    threading.Timer(4.0, os._exit, args=[0]).start()


def _close_window():
    """从 GUI 线程正常关闭 pywebview 窗口"""
    if WINDOW is not None:
        try:
            WINDOW.destroy()
        except Exception:
            pass


def main():
    _force_utf8_stdio()
    root = _app_root()
    _ensure_dirs(root)
    data_dir = root / "data"
    log_dir = root / "log"
    _redirect_streams(log_dir)

    # 必须在 import src.app 之前设置（Settings 实例化时读取环境变量）
    os.environ["INSTANCE_PATH"] = str(data_dir)
    os.environ["LOG_PATH"] = str(log_dir)
    if getattr(sys, "frozen", False):
        web_dist = Path(getattr(sys, "_MEIPASS", root)) / "web" / "dist"
    else:
        web_dist = root.parent / "web" / "dist"
    os.environ["WEB_FOLDER"] = str(web_dist)

    port = _port()
    mutex = _acquire_mutex()
    if mutex is None:
        _activate_existing(port)

    if not _port_available(port):
        if _is_our_app_running(port):
            _activate_existing(port)
        _error_box(f"端口 {port} 已被其他程序占用，请先关闭占用程序后再启动。")
        sys.exit(1)

    from src.app import create_app

    app = create_app()

    global WINDOW
    if os.environ.get("NAV_NO_WINDOW") == "1":
        window = None
    else:
        import webview

        icon = _icon_path(root)
        window = webview.create_window(
            "导航收藏系统",
            _home_url(port),
            width=1280,
            height=800,
            min_size=(960, 600),
        )
    WINDOW = window

    server = threading.Thread(
        target=app.run,
        kwargs={
            "host": "127.0.0.1",
            "port": port,
            "threaded": True,
            "use_reloader": False,
        },
        daemon=True,
        name="nav-server",
    )
    server.start()
    print(f"[desktop] 服务已启动: {_home_url(port)}", flush=True)

    if window is not None:
        # 主线程跑 GUI 事件循环，窗口关闭后退出进程
        webview.start(icon=str(icon) if icon.exists() else None)
        os._exit(0)
    else:
        # 无界面模式：阻塞到 /shutdown 停止服务
        server.join()


if __name__ == "__main__":
    main()
