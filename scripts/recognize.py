"""recognize.py - 截图→视觉网关识别。
  ask   --title|--index|--image --prompt "问题" [--model] [--max-tokens] [--all-screens]
  batch --spec tasks.json  每项 {"title"|"index"|"image","prompt","model","max_tokens"}
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _cli, deps, grab, gw, winscan

DEF = {"title": None, "index": None, "image": None, "all_screens": False,
       "model": None, "max_tokens": 800, "out": None, "minimize_safe": False}


def ask(a):
    """取图→送网关；返回 {reply,usage,model,window,image,prompt}。"""
    if not getattr(a, "prompt", None):
        winscan.die("缺 --prompt（batch spec 每项须含 prompt）")
    path, _size, _box, src = grab.source_png(a, a.out, a.minimize_safe)
    res = gw.ask_image(a.prompt, path, a.model, a.max_tokens)
    return {**res, "window": src, "image": path, "prompt": a.prompt}


def cmd_ask(a):
    deps.dpi_aware()
    print(json.dumps(ask(a), ensure_ascii=False, indent=2))


def cmd_batch(a):
    deps.dpi_aware()
    rows = [ask(argparse.Namespace(**{**DEF, **i}))
            for i in json.load(open(a.spec, encoding="utf-8"))]
    print(json.dumps(rows, ensure_ascii=False, indent=2))


p, s = _cli.sub("recognize.py", "截取窗口并送视觉网关识别")
qa = s.add_parser("ask"); _cli.add_src(qa); _cli.add_capture_opts(qa)
_cli.add_vision(qa); qa.set_defaults(f=cmd_ask)
qb = s.add_parser("batch"); qb.add_argument("--spec", required=True)
_cli.add_src(qb); _cli.add_capture_opts(qb); _cli.add_vision(qb, False)
qb.set_defaults(f=cmd_batch)

if __name__ == "__main__":
    _cli.run(p)
