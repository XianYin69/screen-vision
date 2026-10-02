# asset（技能包资产）

本技能的静态资产：可复用提示词模板与 batch 任务示例。运行时产物一律不入库
（见 [依赖与产物约束](../resistance/依赖与产物约束.md)）。

## 目录
- `prompts/` —— 视觉提示词模板（含敏感内容「分类不复述」口径）。
- `examples/` —— `recognize.py batch --spec` 的任务样例。

## prompts/识别通用.md
界面「是什么/在做什么」的通用问法，最省 token 的默认起点；末段附
「逐对象结构化」要点（类型/归一化坐标/前后/可操作性），配合 `--structured`。

## prompts/结构化描述.md
要求模型逐对象只输出 JSON（type/bbox_norm/z_order/depth_cues/action_hint）；
UI 控件 affect/emotion 恒 null、前后不得按明暗猜、敏感值只报类别。

## prompts/敏感内容脱敏.md
要求模型只报敏感项类别与位置，不输出值；用于登录页、钱包、IDE 设置页等。

## examples/batch_demo.json
两任务样例：一按标题子串、一按已有 PNG，喂给
`python scripts/recognize.py batch --spec examples/batch_demo.json`。

## 用法约定
模板是**起点不是硬编码**：调用方按场景改写 `--prompt`，但
[敏感信息约束](../resistance/敏感信息约束.md) 的「不复述具体值」始终生效。
