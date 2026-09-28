# DPI 与多屏注意

## DPI
Win32 的窗口坐标是**物理像素**，但若进程是 DPI-unaware，系统会把返回值按缩放比例
**虚拟化成逻辑像素**，于是 `ImageGrab.grab(bbox=)` 截出来偏小、四周留白或错位
（125%/150% 缩放下尤其明显）。

对策：`deps.dpi_aware()` 在**任何取图/枚举前**调用，顺序尝试
1. `shcore.SetProcessDpiAwareness(2)` = Per-Monitor v2（首选）；
2. `user32.SetProcessDPIAware()` = System aware（降级）；
3. 都失败 → `none`，继续工作但在输出里如实标 `dpi_mode: "none"`，
   提示识别偏差可能来自缩放。

关键约束：DPI 意识**必须在进程内首次 GDI 调用前设定**，之后改不动。所以
`sw.py capture` / `recognize.py` 都在 main 入口先调，绝不在截图中途调。

## 多屏
- 副屏在主屏左侧/上方时坐标为**负**；跨屏窗口（如实测 `top=-7`）需 `--all-screens`
  让 `ImageGrab` 按虚拟屏幕裁剪，否则负坐标被截成空白。
- 混合 DPI 的多屏（主屏 100% + 副屏 150%）下，非 Per-Monitor v2 会让副屏区域
  尺寸失真；`dpi_mode != per-monitor-v2` 时优先怀疑此项，再怀疑识别模型。
- 出图的 `bbox` 字段给的是**窗口名义坐标**，`size` 给的是**实际像素**；两者不一致
  即说明发生了 clamp（顶边超出屏幕）或缩放，供调用方对账。

## 自检顺序
1. `python sw.py list --filter 目标` 看 box；
2. `python sw.py capture --index N --all-screens` 出 PNG，人眼看是否完整；
3. `python recognize.py ask --image 那张PNG --prompt "…"` 隔离「截取」与「识别」两段。

## 相关
[窗口截取原理](窗口截取原理.md) · [网关视觉调用](网关视觉调用.md)
