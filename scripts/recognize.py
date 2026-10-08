"""recognize.py - 截图→视觉网关识别（可选契约 v2 结构化输出）。
  ask   --title|--index|--image --prompt "问题" [--model] [--max-tokens]
        [--all-screens] [--structured]
  batch --spec tasks.json  每项 {"title"|"index"|"image","prompt","model",
        "max_tokens","structured"}
  --structured 默认关闭（旧输出逐字不变）；开启时并入 vision_descriptor v2：
  schema/schema_version/source/channels/objects/relations/usage/model/prompt。
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _cli, deps, describe, grab, gw, winscan

DEF = {"title": None, "index": None, "image": None, "all_screens": False,
       "model": None, "max_tokens": 800, "out": None, "minimize_safe": False,
       "structured": False}

STRUCT_TAIL = (
    "\n\n【输出格式】只输出一个 JSON 对象，不要解释、不要代码块围栏："
    '{"objects":[{"id":1,"type":"button|input|text|icon|image|list|dialog|'
    'checkbox|link|person|face|qr|captcha|other","label":"可见文字或语义名",'
    '"confidence":0.0,"bbox_norm":[x,y,w,h]（0~1，相对本图左上角）,"z_order":1,'
    '"depth_cues":{"occludes":[],"occluded_by":[],"relative_size":0.0,'
    '"baseline_y_norm":0.0},"actionable":true,"action_hint":"click|type|drag|'
    'scroll|none","affect":null,"emotion":null}]}。'
    "affect/emotion 仅人脸或内容语义可填，UI 控件一律 null，不得编造情绪。"
    "敏感值只报类别，不复述原文。")

EMOTIONS = {"neutral", "happy", "sad", "angry", "surprised", "fearful", "disgusted"}
TYPES = {"button", "input", "text", "icon", "image", "list", "dialog", "checkbox",
         "link", "person", "face", "qr", "captcha", "other", "region"}
HINTS = {"click", "type", "drag", "scroll", "none"}


def parse_model_json(txt):
    """从模型答复里抠出第一个 JSON 对象；失败回 None（不重试、不猜）。"""
    if not txt:
        return None
    s = re.sub(r"^```[a-zA-Z]*|```$", "", txt.strip(), flags=re.M).strip()
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        obj = json.loads(s[i:j + 1])
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _clamp(v, lo=0.0, hi=1.0):
    return min(hi, max(lo, v))


def _ints(seq):
    return [int(v) for v in (seq or []) if isinstance(v, (int, float))]


def _norm_box(b, w, h):
    """接受 0~1 归一化或像素口径，统一成 bbox_norm；非法回 None。"""
    vals = [_num(v, -1) for v in (b or [])[:4]]
    if len(vals) != 4 or min(vals) < 0 or max(w, h) <= 0:
        return None
    if max(vals) > 1.5:
        vals = [vals[0] / w, vals[1] / h, vals[2] / w, vals[3] / h]
    x, y = _clamp(vals[0]), _clamp(vals[1])
    return [round(x, 4), round(y, 4), round(_clamp(vals[2], 0, 1 - x), 4),
            round(_clamp(vals[3], 0, 1 - y), 4)]


def normalize_obj(raw, idx, w, h):
    """模型对象 -> 契约 v2 条目（缺字段补默认、越界裁剪、不编造情绪）。"""
    bn = _norm_box(raw.get("bbox_norm") or raw.get("bbox_px"), w, h)
    if not bn:
        return None
    x, y, bw, bh = bn
    typ = str(raw.get("type") or "other").strip().lower()
    if typ not in TYPES:
        typ = "other"
    hint = str(raw.get("action_hint") or "none").strip().lower()
    if hint not in HINTS:
        hint = "none"
    aff = raw.get("affect") if isinstance(raw.get("affect"), dict) else None
    emo = raw.get("emotion") if raw.get("emotion") in EMOTIONS else None
    dom = (aff or {}).get("domain")
    if typ in ("face", "person") and dom not in ("face", "content"):
        dom = "face"
    if dom not in ("face", "content"):
        aff, emo = None, None
    dc = raw.get("depth_cues") if isinstance(raw.get("depth_cues"), dict) else {}
    act = bool(raw.get("actionable")) if "actionable" in raw else hint != "none"
    return {"id": int(_num(raw.get("id"), idx + 1)), "type": typ,
            "label": str(raw.get("label") or "")[:120],
            "confidence": round(_clamp(_num(raw.get("confidence"))), 3),
            "bbox_norm": [x, y, bw, bh],
            "bbox_px": [round(x * w), round(y * h), round(bw * w), round(bh * h)],
            "center_px": [round((x + bw / 2) * w, 1), round((y + bh / 2) * h, 1)],
            "z_order": int(_num(raw.get("z_order"), 0)), "z_basis": "pixel_occlusion",
            "depth_cues": {"occludes": _ints(dc.get("occludes")),
                           "occluded_by": _ints(dc.get("occluded_by")),
                           "relative_size": round(_clamp(bw * bh), 4),
                           "baseline_y_norm": round(_clamp(y + bh), 4),
                           "blur": round(_clamp(_num(dc.get("blur"))), 3)},
            "affect": aff, "emotion": emo, "actionable": act, "action_hint": hint}


def build_relations(objs):
    """由遮挡互指 + 基线 y 推 pairs（多线索融合，不靠明暗）。"""
    pairs = []
    for a in objs:
        for b in objs:
            if a["id"] >= b["id"]:
                continue
            da, db = a["depth_cues"], b["depth_cues"]
            if b["id"] in da["occludes"]:
                pairs.append({"a": a["id"], "b": b["id"], "in_front": True,
                              "cues": ["occlusion"], "confidence": 0.7})
            elif a["id"] in db["occludes"]:
                pairs.append({"a": a["id"], "b": b["id"], "in_front": False,
                              "cues": ["occlusion"], "confidence": 0.7})
            elif abs(da["baseline_y_norm"] - db["baseline_y_norm"]) > 0.05:
                hi, lo = (a, b) if da["baseline_y_norm"] >= db["baseline_y_norm"] else (b, a)
                pairs.append({"a": hi["id"], "b": lo["id"], "in_front": True,
                              "cues": ["baseline_y"], "confidence": 0.3})
    return {"pairs": pairs,
            "note": "灰度仅边缘预处理，不代表深度；前后由遮挡/基线/相对大小融合"}


def structured(desc, reply, img, win_z=None):
    """像素描述 + 模型逐对象答复 -> 契约 v2（screen_xy 回映射物理像素）。"""
    w, h = img.size
    origin = desc["source"]["origin_screen_px"]
    sc = desc["source"]["dpi_scale"]
    objs, seen = [], set()
    raw = parse_model_json(reply) or {}
    for i, r in enumerate(raw.get("objects") or []):
        if not isinstance(r, dict):
            continue
        o = normalize_obj(r, i, w, h)
        if not o or o["id"] in seen:
            continue
        seen.add(o["id"])
        o["window_z"] = win_z
        sxy, lxy = describe.remap(o["center_px"][0], o["center_px"][1], origin, sc)
        o["screen_xy"] = sxy
        o["screen_xy_logical"] = lxy
        bx, by, bw, bh = o["bbox_px"]
        o["channel"] = describe.region_channel(img, (bx, by, bx + bw, by + bh))
        objs.append(o)
    objs.sort(key=lambda o: -o["z_order"])
    regions = desc.get("objects", [])
    base = max([o["id"] for o in objs], default=0)
    for j, rg in enumerate(regions):
        rg["id"] = base + 1 + j
    desc["objects"] = objs + regions
    if objs:
        desc["relations"] = build_relations(objs)
    desc["model_semantic"] = bool(objs)
    return desc


def ask(a):
    """取图→送网关；--structured 并入契约 v2（旧字段 reply/usage/model/window/image/prompt 保留）。"""
    if not getattr(a, "prompt", None):
        winscan.die("缺 --prompt（batch spec 每项须含 prompt）")
    w = None
    if getattr(a, "image", None):
        path, size, box, src = grab.source_png(a, a.out, a.minimize_safe)
    else:
        w = winscan.pick(a.title, a.index)
        path, size, box, src = grab.win_png(w, a.out, a.minimize_safe, a.all_screens)
    prompt = a.prompt + (STRUCT_TAIL if getattr(a, "structured", False) else "")
    res = gw.ask_image(prompt, path, a.model, a.max_tokens)
    out = {**res, "window": src, "image": path, "prompt": a.prompt}
    if not getattr(a, "structured", False):
        return out
    wz = describe.win_z_index(w) if w is not None else None
    desc = describe.describe(path, box, size, src, wz)
    with describe.Image.open(path) as im:
        out.update(structured(desc, res["reply"], im.convert("RGB"), wz))
    return out


def cmd_ask(a):
    deps.dpi_aware()
    print(json.dumps(ask(a), ensure_ascii=False, indent=2))


def cmd_batch(a):
    deps.dpi_aware()
    rows = [ask(argparse.Namespace(**{**DEF, **i}))
            for i in json.load(open(a.spec, encoding="utf-8"))]
    print(json.dumps(rows, ensure_ascii=False, indent=2))


p, s = _cli.sub("recognize.py", "截取窗口并送视觉网关识别（可选契约 v2 结构化）")
qa = s.add_parser("ask")
_cli.add_src(qa)
_cli.add_capture_opts(qa)
_cli.add_vision(qa)
qa.add_argument("--structured", action="store_true", help="输出并入 vision_descriptor v2")
qa.set_defaults(f=cmd_ask)
qb = s.add_parser("batch")
qb.add_argument("--spec", required=True)
_cli.add_src(qb)
_cli.add_capture_opts(qb)
_cli.add_vision(qb, False)
qb.add_argument("--structured", action="store_true", help="每项输出并入契约 v2")
qb.set_defaults(f=cmd_batch)

if __name__ == "__main__":
    _cli.run(p)
