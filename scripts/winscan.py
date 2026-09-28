"""winscan - 窗口枚举与 bbox 选取；未命中/歧义立即报错（禁止重试风暴）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deps

deps.require(["pygetwindow"])
import pygetwindow as gw


def die(msg):
    print(f"[screen-vision] 错误：{msg}", file=sys.stderr)
    sys.exit(1)


def state(w):
    if getattr(w, "isMinimized", False):
        return "minimized"
    return "visible" if (w.width or 0) > 60 and (w.height or 0) > 60 else "tiny"


def scan(filt=None):
    """按 EnumWindows 的 z-order（顶层在前）出 JSON 行。"""
    rows = []
    for i, w in enumerate(gw.getAllWindows()):
        t = w.title or ""
        if filt and filt.lower() not in t.lower():
            continue
        rows.append({"index": i, "title": t, "handle": getattr(w, "_hWnd", None),
                     "box": [w.left, w.top, w.left + w.width, w.top + w.height],
                     "visible_state": state(w)})
    return rows


def pick(title=None, index=None):
    if index is not None:
        wins = gw.getAllWindows()
        if not 0 <= index < len(wins):
            die(f"--index {index} 越界（枚举 {len(wins)} 个窗口）")
        return wins[index]
    if not title:
        die("必须给 --title 子串或 --index 下标")
    hits = [w for w in gw.getAllWindows() if title.lower() in (w.title or "").lower()]
    if not hits:
        die(f"找不到标题含「{title}」的窗口；先看: python sw.py list --filter {title}")
    if len(hits) > 1:
        die(f"「{title}」命中 {len(hits)} 个窗口，请用 --index 指定 -> "
            + "; ".join(f"{i}:{w.title}" for i, w in enumerate(hits[:8])))
    return hits[0]
