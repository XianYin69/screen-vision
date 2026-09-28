# CHANGELOG

## v1.0.0 — screen-vision 初版（create 路径）
新增「屏幕窗口 → 大模型视觉识别」技能，与 camera-vision 平级但不同域。

- `scripts/`：`sw.py`（list/capture）、`recognize.py`（ask/batch）、
  共用层 `grab.py`/`winscan.py`/`gw.py`/`deps.py`/`_cli.py`。
- `knowledge/`：窗口截取原理、网关视觉调用、DPI 与多屏注意。
- `resistance/`：红线约束（失败即停）、依赖与产物约束、敏感信息约束。
- `schemas/`：`sw_list` / `sw_capture` / `recognize_output` / `batch_spec` 四份契约。
- `asset/`：`prompts/识别通用.md`、`prompts/敏感内容脱敏.md`、`examples/batch_demo.json`。

### 技术选择与后果
- 本机 `mss`/`pywin32` 不可用 → 走 `PIL.ImageGrab` + `ctypes`，零新增依赖；
  代价是只能截**可见未遮挡**区域，故显式提供 `--minimize-safe` 而非静默还原。
- 实测窗口 `top=-7/-11`（贴顶超屏）→ bbox 顶边 clamp 到 0，跨屏需 `--all-screens`。
- DPI 意识在进程入口首调（`per-monitor-v2` 实测生效），否则高分屏截偏小。
- 依赖缺失只打印建议命令并 `exit 2`，全仓无 `subprocess`/自动 pip。
- 产物只写 `%LOCALAPPDATA%\SMS\cache\screen_vision\` 或 `--out`，技能目录零运行时文件。

### 验证
`sw.py list` / `capture`（2498x1611, 676KB）/ `recognize.py ask` / `batch`（两图两问）
全部实测通过；负路径（无此窗口、最小化、1x1 窗口、配置缺失、图片缺失）均即时报错。
