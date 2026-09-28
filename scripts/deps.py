"""deps - 依赖守门与平台路径：缺包只报错给建议命令，绝不自动安装。"""
import importlib
import os
import sys

SUGGEST = {"PIL": "pillow", "pygetwindow": "pygetwindow", "requests": "requests"}
DPI_MODE = {"v": "none"}


def require(modules):
    """导入失败 -> 打印缺哪个包 + 手动安装建议 + exit 2（红线：不自动 pip）。"""
    missing = []
    for n in modules:
        try:
            importlib.import_module(n)
        except ImportError:
            missing.append(n)
    if missing:
        pkgs = " ".join(SUGGEST.get(m, m) for m in missing)
        print(f"[screen-vision] 缺少依赖: {', '.join(missing)}\n"
              f"[screen-vision] 请自行确认后手动执行: python -m pip install {pkgs}\n"
              "[screen-vision] 本技能不自动安装依赖。", file=sys.stderr)
        sys.exit(2)


def sms_home():
    """SMS 根目录（config/config.json 的上游）。"""
    return os.environ.get("SMS_HOME") or os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "SMS")


def cache_dir():
    """产物目录＝平台缓存，永不写技能目录。"""
    d = os.path.join(sms_home(), "cache", "screen_vision")
    os.makedirs(d, exist_ok=True)
    return d


def dpi_aware():
    """PMv2 -> system -> none；须在首次 GDI 调用前执行。"""
    import ctypes
    u = ctypes.windll.user32
    try:
        u.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)); DPI_MODE["v"] = "per-monitor-v2"
    except Exception:
        try:
            u.SetProcessDPIAware(); DPI_MODE["v"] = "system"
        except Exception:
            DPI_MODE["v"] = "none"
    return DPI_MODE["v"]
