"""describe.py - 像素通道统计 + 灰度/边缘预处理 + 候选区域框（契约 v2 §3）。
  python describe.py --image PATH | --title 子串 | --index N
                     [--grid 4] [--top 6] [--out PATH]
  只用 Pillow / ctypes（不新增第三方依赖）；产物只写缓存目录，不写技能目录。
  灰度只用于边缘/遮挡边界检测，**不代表深度**；前后关系见 knowledge。
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deps, grab

deps.require(["PIL"])
from PIL import Image, ImageFilter

BINS = 8
SCHEMA = "vision_descriptor"
VERSION = 2


def dpi_scale():
    """物理/逻辑像素比：GetDpiForSystem/96；取不到如实回 1.0。"""
    import ctypes
    try:
        return round(ctypes.windll.user32.GetDpiForSystem() / 96.0, 4)
    except Exception:
        return 1.0


def mean_rgb(img):
    """RGB 三通道均值（直方图加权，无 numpy）。"""
    rgb = img.convert("RGB")
    hist = rgb.histogram()
    n = max(1, rgb.width * rgb.height)
    return [round(sum(v * hist[c * 256 + v] for v in range(256)) / n, 2)
            for c in range(3)]


def gray_stats(img):
    """灰度图 + 均值 / 对比度(标准差) / 8 分箱占比。"""
    g = img.convert("L")
    hist = g.histogram()
    n = max(1, g.width * g.height)
    mean = sum(v * hist[v] for v in range(256)) / n
    var = sum(((v - mean) ** 2) * hist[v] for v in range(256)) / n
    step = 256 // BINS
    bins = [round(sum(hist[b * step:(b + 1) * step]) / n, 4) for b in range(BINS)]
    return g, round(mean, 2), round(var ** 0.5, 2), bins


def saturation(img):
    """饱和度：convert("HSV") 的 S 通道均值 / 255。"""
    hsv = img.convert("HSV")
    hist = hsv.histogram()
    n = max(1, hsv.width * hsv.height)
    return round(sum(v * hist[256 + v] for v in range(256)) / n / 255.0, 4)


def edge_density(g):
    """FIND_EDGES 后非零像素占比（边缘密度）。"""
    e = g.filter(ImageFilter.FIND_EDGES)
    hist = e.histogram()
    n = max(1, e.width * e.height)
    return e, round((n - hist[0]) / n, 4)


def channels(img):
    """顶层 channels 块（契约 v2 §1）。"""
    g, gmean, contrast, bins = gray_stats(img)
    _e, dens = edge_density(g)
    return {"mode": "rgb", "preprocess": ["gray", "edge"], "mean_rgb": mean_rgb(img),
            "saturation": saturation(img), "contrast": contrast, "gray_mean": gmean,
            "edge_density": dens, "gray_hist_8": bins}, g


def region_channel(img, box):
    """候选区域的通道块（裁剪后统计）。"""
    crop = img.crop(box)
    g, gmean, _c, _b = gray_stats(crop)
    _e, dens = edge_density(g)
    return {"mean_rgb": mean_rgb(crop), "saturation": saturation(crop),
            "gray_mean": gmean, "edge_density": dens, "alpha": 1.0}


def _find(par, i):
    while par[i] != i:
        par[i] = par[par[i]]
        i = par[i]
    return i


def hotspots(edge_img, grid=4, top=6):
    """网格 + 边缘密度热点：高格并查集合并为候选框（图像像素坐标）。"""
    w, h = edge_img.size
    cw, ch = max(1, w // grid), max(1, h // grid)
    dens = []
    for gy in range(grid):
        for gx in range(grid):
            sub = edge_img.crop((gx * cw, gy * ch, min(w, (gx + 1) * cw),
                                 min(h, (gy + 1) * ch)))
            n = max(1, sub.width * sub.height)
            sh = sub.histogram()
            dens.append((sum(sh[1:]) / n, (gx, gy)))
    if not dens or sum(d for d, _c in dens) == 0:
        return []
    avg = sum(d for d, _c in dens) / len(dens)
    keep = {(gx, gy) for d, (gx, gy) in dens if d >= max(avg, 0.02)}
    idx = {c: i for i, c in enumerate(sorted(keep))}
    par = list(range(max(1, len(keep))))
    for gx, gy in keep:
        for nb in ((gx + 1, gy), (gx, gy + 1)):
            if nb in idx:
                a, b = _find(par, idx[(gx, gy)]), _find(par, idx[nb])
                if a != b:
                    par[a] = b
    groups = {}
    for c, i in idx.items():
        groups.setdefault(_find(par, i), []).append(c)
    out = []
    for cells in groups.values():
        x0 = min(c[0] for c in cells) * cw
        y0 = min(c[1] for c in cells) * ch
        x1 = min(w, (max(c[0] for c in cells) + 1) * cw)
        y1 = min(h, (max(c[1] for c in cells) + 1) * ch)
        out.append([x0, y0, x1 - x0, y1 - y0])
    out.sort(key=lambda b: -(b[2] * b[3]))
    return out[:top]


def origin_of(box, size):
    """图像 (0,0) 对应的屏幕物理坐标：top<0 被 clamp 时按实际出图高度回推。"""
    left, top_y, bot = box[0], box[1], box[3]
    oy = max(0, top_y)
    if size and len(size) == 2 and bot - max(0, top_y) >= size[1]:
        oy = bot - size[1]
    return [int(left), int(oy)]


def remap(cx, cy, origin, scale):
    """图像像素 -> 屏幕物理像素（screen_xy）/ 逻辑像素（screen_xy_logical）。"""
    sx = int(round(origin[0] + cx))
    sy = int(round(origin[1] + cy))
    s = scale or 1.0
    return [sx, sy], [round(sx / s, 1), round(sy / s, 1)]


def region_objects(img, origin, scale, win_z=None, grid=4, top=6):
    """候选区域 -> 契约 v2 objects[]（type=region；语义类型由模型补）。

    z_basis 固定 pixel_occlusion：窗口内元素只能按像素遮挡排序；
    窗口之间的前后由 source.window_z（EnumWindows 下标，0=顶层）表达。
    """
    g, _mean, _c, _b = gray_stats(img)
    e_img, _d = edge_density(g)
    w, h = img.size
    boxes = hotspots(e_img, grid=grid, top=top)
    objs = []
    for i, (x, y, bw, bh) in enumerate(boxes):
        cx, cy = x + bw / 2.0, y + bh / 2.0
        sxy, lxy = remap(cx, cy, origin, scale)
        objs.append({"id": i + 1, "type": "region", "label": "边缘热点区 %d" % (i + 1),
                     "confidence": 0.0, "bbox_px": [x, y, bw, bh],
                     "bbox_norm": [round(x / w, 4), round(y / h, 4),
                                   round(bw / w, 4), round(bh / h, 4)],
                     "center_px": [round(cx, 1), round(cy, 1)], "screen_xy": sxy,
                     "screen_xy_logical": lxy, "z_order": len(boxes) - i,
                     "z_basis": "pixel_occlusion", "window_z": win_z,
                     "depth_cues": {"occludes": [], "occluded_by": [],
                                    "relative_size": round((bw * bh) / float(w * h), 4),
                                    "baseline_y_norm": round((y + bh) / float(h), 4),
                                    "blur": 0.0},
                     "channel": region_channel(img, (x, y, x + bw, y + bh)),
                     "affect": None, "emotion": None,
                     "actionable": False, "action_hint": "none"})
    return objs


def describe(img_path, box=None, size=None, src_name="", win_z=None,
             grid=4, top=6, monitor="primary"):
    """整份契约 v2 像素侧描述（语义字段由 recognize --structured 合并）。"""
    img = Image.open(img_path)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    sc = dpi_scale()
    wh = [img.width, img.height]
    bx = box or [0, 0, img.width, img.height]
    origin = origin_of(bx, size or wh)
    blk, _g = channels(img)
    return {"schema": SCHEMA, "schema_version": VERSION,
            "source": {"kind": "screen", "window": src_name,
                       "image": os.path.abspath(img_path), "size_px": wh,
                       "dpi_scale": sc, "origin_screen_px": origin,
                       "monitor": monitor, "window_z": win_z},
            "channels": blk,
            "objects": region_objects(img, origin, sc, win_z, grid, top),
            "relations": {"pairs": [], "note": "灰度仅边缘预处理；前后需多线索融合"}}


def win_z_index(w):
    """该窗口在 EnumWindows z-order 中的下标（0=顶层）；取不到回 None。"""
    import winscan
    for i, row in enumerate(winscan.scan()):
        if row.get("handle") == getattr(w, "_hWnd", None):
            return i
    return None


def main():
    deps.dpi_aware()
    p = argparse.ArgumentParser(prog="describe.py",
                                description="像素通道/边缘/候选框（契约 v2）")
    p.add_argument("--image")
    p.add_argument("--title")
    p.add_argument("--index", type=int)
    p.add_argument("--all-screens", action="store_true")
    p.add_argument("--out")
    p.add_argument("--minimize-safe", action="store_true")
    p.add_argument("--grid", type=int, default=4)
    p.add_argument("--top", type=int, default=6)
    a = p.parse_args()
    if a.image:
        if not os.path.exists(a.image):
            print("[screen-vision] 错误：图片不存在 %s" % a.image, file=sys.stderr)
            sys.exit(1)
        path, box, size, src, wz = a.image, [], [], os.path.basename(a.image), None
    else:
        import winscan
        w = winscan.pick(a.title, a.index)
        path, size, box, src = grab.win_png(w, a.out, a.minimize_safe, a.all_screens)
        wz = win_z_index(w)
    out = describe(path, box, size, src, wz, a.grid, a.top)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
