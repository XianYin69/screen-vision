---
name: screen-vision
description: >
  基本屏幕图像识别技能：枚举任意窗口、截取指定窗口 PNG、把图送 SMS 原生大模型网关做视觉识别。
  入口 sw.py（list/capture）、recognize.py（ask/batch，--structured=视觉契约 v2）、
  describe.py（像素通道/边缘/候选框）。依赖缺失只报错不装；产物只写缓存目录或 --out；
  敏感值只报类别不复述；失败即停不重试。
license: MIT
metadata:
  category: vision
  subtype: screen
---

# screen-vision

使用 `screen-vision` skill 来完成用户请求。

## 快速用法
```bash
S=~/.kilocode/skills/screen-vision/scripts
python $S/sw.py list [--filter 子串]                        # z-order 窗口表（0=顶层）
python $S/sw.py capture --title 子串|--index N [--out PATH]
python $S/recognize.py ask --title SMSH --prompt "问题" [--structured]
python $S/recognize.py batch --spec tasks.json [--structured]
python $S/describe.py --image PATH|--title 子串 [--grid 4]  # 纯像素侧，不送网关
```

## 流程
定位窗口 → 截取（DPI/负坐标/最小化守护）→ base64 内嵌送 `llm_gateway`；默认输出
`{reply,usage,model,window,image,prompt}`；`--structured` 另并入契约 v2（只增不改名，向后兼容）。

## 对象与坐标（契约 v2）
- `objects[]`：type 枚举 + label（敏感值只报类别）+ bbox_px/bbox_norm/center_px + z_order/
  z_basis/depth_cues + channel + actionable/action_hint；**`affect`/`emotion` 对 UI 控件恒 null**。
- **坐标口径**：`screen_xy` = **屏幕物理像素绝对坐标**（窗口 rect 原点 + center_px，top<0 clamp
  已回推），safe-mouse-automation 可直接点击；`screen_xy_logical` = 逻辑像素（÷ `source.dpi_scale`）。
- 前后关系：窗口之间以 z-order 为准（`window_z`，0=顶层）；窗口内只能按像素遮挡
  （`z_basis:"pixel_occlusion"`）；**灰度只是边缘预处理，不代表深度**。

## 边界与红线
截的是屏幕矩形的像素（非 PrintWindow），被遮挡会截进遮挡内容；最小化须 `--minimize-safe`；`index` 随 z-order 漂移，跨命令用 `--title`。
不装依赖、不写技能目录、不重试、不占位黑图、不复述敏感值、不复制/重建网关配置、**不新增第三方依赖**（仅 Pillow/ctypes/requests）。
见 [窗口截取原理](knowledge/窗口截取原理.md)、[前后关系与遮挡线索](knowledge/前后关系与遮挡线索.md)、[DPI与多屏注意](knowledge/DPI与多屏注意.md)、[红线约束](resistance/红线约束.md)、[依赖与产物约束](resistance/依赖与产物约束.md)、[敏感信息约束](resistance/敏感信息约束.md)。

## 目录
- 脚本：`scripts/`（sw / recognize / describe / grab / winscan / gw / deps / _cli）
- 契约：[schemas/](schemas/schemas.md)（含 [vision_descriptor_v2](schemas/vision_descriptor_v2.schema.json)）
- 知识：[网关视觉调用](knowledge/网关视觉调用.md) · 资产：[asset/](asset/asset.md)（含[结构化描述](asset/prompts/结构化描述.md)）
- 约束：[resistance](resistance/resistance.md) · 依赖：[dependence/](dependence/dependence.md)
