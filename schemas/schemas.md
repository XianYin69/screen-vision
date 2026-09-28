# schemas（契约目录）

四份 JSON Schema（draft-07），是脚本 stdout/stdin 的**唯一对账依据**：

| 文件 | 约束对象 |
|---|---|
| [sw_list.schema.json](sw_list.schema.json) | `sw.py list` 输出数组（z-order 行） |
| [sw_capture.schema.json](sw_capture.schema.json) | `sw.py capture` 输出（bytes>0 才算成功） |
| [recognize_output.schema.json](recognize_output.schema.json) | `recognize.py ask/batch` 单元结果 |
| [batch_spec.schema.json](batch_spec.schema.json) | `recognize.py batch --spec` 输入 |

## 约定
- 成功即打印**纯 JSON** 到 stdout；失败只写 stderr 并 `exit != 0`，两者不混流。
- `bytes` 为 0 或 `size` 为空 = 截取失败，调用方必须中止（见
  [红线约束](../resistance/红线约束.md)）。
- 字段只增不改语义；改语义即升技能版本并记 [CHANGELOG](../CHANGELOG.md)。

## 相关
[resistance](../resistance/resistance.md) ·
[网关视觉调用](../knowledge/网关视觉调用.md)
