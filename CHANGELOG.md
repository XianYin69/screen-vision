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

## v1.1.0 — 视觉描述契约 v2（modify 路径）
识别输出可被程序消费并直接驱动 safe-mouse-automation。

- 新增 `scripts/describe.py`：RGB 均值/饱和度/对比度 + `convert("L")`/`FIND_EDGES`
  边缘密度 + 网格热点候选框；零新增依赖（仅 Pillow/ctypes）。
- `recognize.py ask/batch` 增 `--structured`（默认关，旧输出逐字兼容）：模型逐对象
  答复与像素侧合并为 `vision_descriptor` v2（schema/source/channels/objects/relations）。
- 坐标回映射：窗口 rect 原点 + center_px → `screen_xy`（屏幕**物理像素**绝对坐标，
  top<0 clamp 已回推）；`source.dpi_scale`=GetDpiForSystem/96 如实记录，另给
  `screen_xy_logical`。窗口间 z 以 EnumWindows 为准（`window_z`），窗口内
  `z_basis:"pixel_occlusion"`；UI 控件 `affect/emotion` 恒 null（纠偏 §0.2/§0.3）。
- `schemas/`：新增 `vision_descriptor_v2.schema.json`（旧六字段仍必填的超集）；
  `batch_spec` 增可选 `structured`；索引更新。
- `asset/prompts/`：`识别通用.md` 附逐对象要点；新增 `结构化描述.md`。
- `knowledge/`：新增 `前后关系与遮挡线索.md`（灰度≠深度，多线索融合）。
- 初始化补齐：`LICENSE`（MIT）、`planned_tasks/`（README+template，本技能暂无任务）。

### 验证
镜像单测：merge（枚举清洗/情绪门控/id 重排/遮挡 pairs）、compat（旧六字段不变 +
screen_xy=[220,110] 手算对账）、schema 必填/枚举校验、`describe.py` 实图跑通、
`--help` 双入口；全部 .md ≤50 行、悬空链接 0。
