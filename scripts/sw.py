"""sw.py - 窗口枚举与截取。
  python sw.py list [--filter 子串]
  python sw.py capture --title 子串|--index N [--minimize-safe] [--all-screens] [--out PATH]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _cli, deps, grab, winscan


def cmd_list(a):
    deps.dpi_aware()
    print(json.dumps(winscan.scan(a.filter), ensure_ascii=False, indent=2))


def cmd_capture(a):
    deps.dpi_aware()
    path, size, box, title = grab.win_png(winscan.pick(a.title, a.index), a.out,
                                          a.minimize_safe, a.all_screens)
    print(json.dumps({"window": title, "image": path, "size": size, "bbox": box,
                      "dpi_mode": deps.DPI_MODE["v"],
                      "bytes": os.path.getsize(path)}, ensure_ascii=False))


p, s = _cli.sub("sw.py", "窗口枚举与截取")
pl = s.add_parser("list"); pl.add_argument("--filter"); pl.set_defaults(f=cmd_list)
pc = s.add_parser("capture"); _cli.add_src(pc); _cli.add_capture_opts(pc)
pc.set_defaults(f=cmd_capture)

if __name__ == "__main__":
    _cli.run(p)
