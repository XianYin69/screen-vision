"""grab - 共享窗口截取：最小化守护、负 top clamp、跨屏、尺寸校验。"""
import ctypes
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deps, winscan

deps.require(["PIL"])
from PIL import ImageGrab


def restore(w):
    ctypes.windll.user32.ShowWindow(w._hWnd, 9)  # SW_RESTORE
    ctypes.windll.user32.SetForegroundWindow(w._hWnd)
    time.sleep(0.35)


def bbox(w):
    """(l,t,r,b)：top<0 贴顶时 clamp 到 0（跨屏负坐标）。"""
    return w.left, max(0, w.top), w.left + w.width, w.top + w.height


def win_png(w, out=None, minimize_safe=False, all_screens=False):
    if getattr(w, "isMinimized", False):
        if not minimize_safe:
            winscan.die(f"窗口「{w.title}」已最小化；加 --minimize-safe 先还原再截")
        restore(w)
    l, t, r, b = bbox(w)
    if r - l < 20 or b - t < 20:
        winscan.die(f"窗口「{w.title}」尺寸异常 {r-l}x{b-t}，放弃截取（不产占位黑图）")
    out = out or os.path.join(deps.cache_dir(), f"win_{int(time.time())}.png")
    img = ImageGrab.grab(bbox=(l, t, r, b), all_screens=bool(all_screens))
    img.save(out)
    return os.path.abspath(out), list(img.size), [w.left, w.top, r, b], w.title


def source_png(a, out=None, minimize_safe=False):
    """按 --image / --title / --index 取图，返回 (path, size, bbox, src_name)。"""
    if getattr(a, "image", None):
        if not os.path.exists(a.image):
            winscan.die(f"图片不存在: {a.image}")
        return a.image, [], [], os.path.basename(a.image)
    return win_png(winscan.pick(a.title, a.index), out, minimize_safe, a.all_screens)
