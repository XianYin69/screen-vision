# planned_tasks（计划任务声明）

本目录声明**由 SMS 调度器到期执行**的计划任务；技能自身不得执行任何计划任务。

## 规则
- 一任务一文件：`pt-screen-vision-<slug>.json`。
- 字段名与 SMS 读取端一致，不得改动：
  `id / title / skill / input / schedule / session / status / created / next_run`。
- `schedule.mode` 仅 `at | cron | interval`（interval 用 `every_min`）。
- `status` 仅 `pending / running / done / paused / failed`。
- 时间一律本地 ISO（`YYYY-MM-DDTHH:MM:SS`）。
- 原子写（临时文件 + rename）；删除文件即注销该任务。
- 到期由 SMS 调度器读取执行并挂 session 关联链。

## 文件
- [`template.json`](template.json)：骨架模板（`<占位>` 不入库执行，调度器按名跳过）。

## 相关
[SKILL.md](../SKILL.md) · [resistance](../resistance/resistance.md)
