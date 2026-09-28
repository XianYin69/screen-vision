"""_cli - 共用 argparse 骨架（源选择 + 提示词），供 sw.py / recognize.py 复用。"""
import argparse


def add_src(q):
    """图片来源：--image 已有图 / --title 子串 / --index 枚举下标。"""
    q.add_argument("--title")
    q.add_argument("--index", type=int)
    q.add_argument("--image")
    q.add_argument("--all-screens", action="store_true")


def add_vision(q, need_prompt=True):
    q.add_argument("--prompt", required=need_prompt)
    q.add_argument("--model")
    q.add_argument("--max-tokens", type=int, default=800)


def add_capture_opts(q):
    q.add_argument("--out")
    q.add_argument("--minimize-safe", action="store_true")


def sub(prog, desc):
    p = argparse.ArgumentParser(prog=prog, description=desc)
    return p, p.add_subparsers(dest="cmd", required=True)


def run(p):
    a = p.parse_args()
    a.f(a)
    return a
