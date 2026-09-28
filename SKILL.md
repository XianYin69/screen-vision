---
name: screen-vision
description: >
  基本屏幕图像识别技能：枚举任意窗口、截取指定窗口 PNG、并把图送 SMS 原生大模型网关做视觉识别。
  入口 scripts/sw.py（list / capture）与 scripts/recognize.py（ask / batch）；
  依赖缺失只报错不自动安装；产物只写平台缓存目录或 --out；敏感值只报类别不复述；失败即停不重试。
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
python $S/sw.py list [--filter 子串]                               # z-order 窗口表
python $S/sw.py capture --title 子串|--index N [--minimize-safe] [--out PATH]
python $S/recognize.py ask --title SMSH --prompt "这窗口在讲什么？"
python $S/recognize.py batch --spec tasks.json                     # 多图多问
```

## 流程
定位窗口 → 截取（DPI/负坐标/最小化守护）→ base64 内嵌送 `config.json` 的
`llm_gateway` → 结构化回复 `{reply, usage, model, window, image, prompt}`。

## 边界（能力面）
截的是**屏幕那块矩形的像素**（非 PrintWindow）：被遮挡会截进遮挡内容、
最小化窗口须 `--minimize-safe` 显式还原（会短暂抢焦点）；`index` 随 z-order
实时漂移，跨命令请用 `--title`。见 [窗口截取原理](knowledge/窗口截取原理.md)。

## 红线（禁止面）
不装依赖、不写技能目录、不重试、不占位黑图、不复述敏感值、不复制/重建网关配置。
见 [红线约束](resistance/红线约束.md)、[依赖与产物约束](resistance/依赖与产物约束.md)、
[敏感信息约束](resistance/敏感信息约束.md)。

## 目录
- 脚本：`scripts/`（sw / recognize / grab / winscan / gw / deps / _cli）
- 知识：[网关视觉调用](knowledge/网关视觉调用.md)、[DPI与多屏注意](knowledge/DPI与多屏注意.md)
- 约束：[resistance](resistance/resistance.md) · 契约：[schemas/](schemas/schemas.md) 四份
- 资产与依赖：[asset/](asset/asset.md)、[dependence/](dependence/dependence.md)
