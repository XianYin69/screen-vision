# dependence（依赖清单）

SMS 安装本技能时按此清单同检同净化：只检查、不自动安装。

## 软件
- Windows 10/11（`EnumWindows` / `ImageGrab` / `shcore` DPI API）。
- Python 3.14.5（实测；3.10+ 应可用，未验证）。

## Python 包（必装才可用）
| 包 | 用途 | 缺失表现 |
|---|---|---|
| `pygetwindow` | 窗口枚举与 bbox | `sw.py` 启动即 exit 2 |
| `pillow` | `PIL.ImageGrab` 截屏 | `capture/ask` exit 2 |
| `requests` | 送网关 | `recognize.py` exit 2 |

建议命令（用户自行确认后执行，技能不代跑）：
`python -m pip install pygetwindow pillow requests`

## Python 包（可选）
- `numpy`：调用方自行做像素统计时用；本技能链路不依赖。
- `mss` / `pywin32`：本机未安装，代码已避开（见 [依赖与产物约束](../resistance/依赖与产物约束.md)）。

## 上游服务
- SMS 原生大模型网关：`config.json` → `llm_gateway.base_url`（实测
  `http://127.0.0.1:31415/v1`，`model=auto`，需视觉能力）。
  网关未启动 → 请求失败即报错退出，不重试。

## 仓库地址
- pygetwindow: https://github.com/PyGetWindow/PyGetWindow
- Pillow: https://github.com/python-pillow/Pillow
- requests: https://github.com/psf/requests
