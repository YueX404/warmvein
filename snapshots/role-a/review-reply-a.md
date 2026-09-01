# Task-2 审查回复（角色A）

**分支：** `dev-2/feature/task2-alarm-map`  
**对照：** `docs/审查报告-Dev-2-task2-alarm-map.md`  
**处理时间：** 2026-09-01

开发窗口先核对报告再改代码。P1-1 关闭按钮 reject `"close"`、P2-2 清空变 `null`、P1-2 的 rowcount=changed 三条在本栈不成立，其余按报告处理。

## P1

| 编号 | 处理 | 说明 |
|---|---|---|
| P1-1 | 修复 | `cancel`/`close` 都 return。API 失败不改 `item.status`、不弹 success。仅 `usingMock===true` 时本地确认。Element Plus 2.14.5 默认关闭按钮也是 `"cancel"`，仍同时识别 `"close"`。commit `3eeea88` |
| P1-2 | 修复 | `WHERE alarm_id AND status=0`。`rowcount==0` 再按主键查：无行 40002，终态 40001。SQLAlchemy 使用 FOUND_ROWS，原「changed 行误报 40002」不成立，加 `status=0` 后才需要二次查询。commit `9a2f8e9` |

## P2

| 编号 | 处理 | 说明 |
|---|---|---|
| P2-1 | 修复 | 仅 `import.meta.env.DEV` 且 axios 无响应/5xx 才回落 Mock；业务错误与生产路径空列表。拦截器已 `ElMessage.error`。 |
| P2-2 | 防御 | EP 2.14.5 `valueOnClear` 默认 `undefined`，清空链不是必现。params 改为 `typeof === "number"`。 |
| P2-3 | 修复 | `LIMIT 200`，不做分页包装。 |
| P2-4 | 修复 | 站点 = mock 换热站 ∪ 当前告警 `stationId`，缺经纬度用占位卡片。 |
| P2-5 | 修复 | `watch([levelFilter, statusFilter], loadAlarms)`。 |

P2 合入 commit `1fec805`。

## P3

| 编号 | 处理 | 说明 |
|---|---|---|
| P3-1 | 修复 | Commit 表补齐自验证与审查修复 hash。 |
| P3-2 | 修复 | 本文件覆盖 Task 1 残留的 `review-reply-a.md`。 |
| P3-3 | 修复 | 非法 `status`；ack id 断言收为 `40001`；终态 ack `40001`。 |
| P3-4 | 保留 | FastAPI 422 需改 `main.py` 全局校验处理，F0 冻结，记 follow-up。 |
| P3-5 | 确认 | 列表 `data` 锁定为数组，与计划和功能开发文档 `alarm[]` 一致，不对齐 api-guide 的 `{total, alarms}`。 |

## 验证

`pytest tests/test_alarm_routes.py -v` → 11 passed  
`vue-tsc && vite build` → 通过
