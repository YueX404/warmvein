# Dev-2 Task 2 二次审查报告

> **审查日期：** 2026-09-01  
> **审查轮次：** 第 2 轮（对照首轮报告与修复提交）  
> **审查角色：** 审查窗口（只读，未改实现、未提交）  
> **分支：** `dev-2/feature/task2-alarm-map`（worktree：`D:\YY-task2`，HEAD `0c3b105`）  
> **对照基线：** `master` `ccaa50c` → 当前 HEAD `0c3b105`  
> **首轮审查 HEAD：** `00c0bd8`  
> **本轮修复提交：** `3eeea88` `9a2f8e9` `1fec805`；`0c3b105` 文档/快照  
> **首轮报告：** `docs/审查报告-Dev-2-task2-alarm-map.md`  
> **作者回复：** `snapshots/role-a/review-reply-a.md`  
> **阶段快照：** `修复完成，待二次审查`

---

## 一、总体结论

**首轮 P1 全部关闭，P2 均已落地。建议合入。**

相对首轮「暂不建议合入」，本轮已经把两处写路径假成功拿掉：对话框关闭/接口失败不再把卡片改成已确认；ack 只更新 `status=0`，终态返回 40001 且不 commit。列表失败在生产走空列表，Mock 仅限 `DEV` 且后端不可达。

当场验证：`pytest tests/test_alarm_routes.py -v` → **11 passed**。

本轮没有新的 P1/P2。P3 可记 follow-up，不阻塞合入。P3-4（FastAPI 422）与 P3-5（列表契约为数组）按回复接受。

---

## 二、首轮问题关闭表

| ID | 首轮结论 | 本轮状态 | 证据 |
|---|---|---|---|
| P1-1 | 确认失败/关对话框会本地改成已确认并 success | **已关闭** | `AlarmMap.vue:234-259`：`cancel`/`close` 直接 return；API 失败不改 `item.status`、不弹 success。仅 `usingMock===true` 时本地确认。作者称 EP 2.14.5 关闭钮也是 `"cancel"`，代码仍同时识别 `"close"`，可接受 |
| P1-2 | ack 无条件 `SET status=1`，终态会被打开 | **已关闭** | `routes_alarm.py:66-84`：`WHERE alarm_id AND status=0`；`rowcount==0` 再按主键查，无行 40002、有行 40001，且不 commit。单测 `test_alarm_ack_rejects_non_open_status` / `test_alarm_ack_not_found` |
| P2-1 | 任意列表失败灌 Mock 假预警 | **已关闭** | `loadAlarms` 仅 `import.meta.env.DEV && isAlarmBackendUnreachable` 才 Mock；业务错误（拦截器 `new Error`，非 AxiosError）与生产路径空列表 |
| P2-2 | 清空筛选 `null` 可能打 422 再灌 Mock | **已关闭** | `alarm.api.ts` 与页面 `asNumber` 均为 `typeof === "number"` 才带参。作者称 EP 默认 `valueOnClear` 为 `undefined`，防御仍在，可接受 |
| P2-3 | 列表无 LIMIT | **已关闭** | `LIMIT :limit`，`_LIST_LIMIT = 200`；`test_alarm_list_caps_result_size` |
| P2-4 | 地图/卡片写死 3 个 mock 站 | **已关闭** | `collectStations`：mock 站点 ∪ 当前告警 `stationId`，缺经纬度用占位卡片 |
| P2-5 | 工具栏下拉不自动刷新 | **已关闭** | `watch([levelFilter, statusFilter], loadAlarms)`；图例只改 filter，避免与 watch 双拉 |
| P3-1 | 开发记录缺自验证 commit | **已关闭** | 已列 `00c0bd8` 及三笔 fix；本轮文档 commit `0c3b105` 仍未入表，见 P3-R1 |
| P3-2 | Task 1 的 `review-reply-a.md` 残留 | **已关闭** | 已覆盖为 Task 2 回复 |
| P3-3 | 缺非法 status；ack id 断言过宽 | **已关闭** | `test_alarm_list_rejects_invalid_status`；ack id 断言为 `40001` |
| P3-4 | 框架 422 不是 40001 | **接受** | 改 `main.py` 违反 F0 冻结，记全站 follow-up |
| P3-5 | 列表形状与 api-guide 分页包装不一致 | **接受** | 锁定 `data` 为数组，与计划和功能开发文档 `alarm[]` 一致 |

### 关于作者对首轮三条技术判断的异议

- **关闭钮 `"close"`：** 即便当前 EP 默认 reject `"cancel"`，多识别 `"close"` 没有坏处，P1-1 以行为关闭，不纠缠版本细节。
- **清空变 `null`：** 不是必现，但 `typeof === "number"` 是正确防御，P2-2 关闭。
- **rowcount=changed：** 加了 `status=0` 之后首次确认一定改行，原误报路径不再构成 P1。二次查询区分 40002/40001 是正确补强。接受「本栈 FOUND_ROWS」的说明，不再要求改引擎参数。

---

## 三、本轮新问题

### P3 — 可记 follow-up，不阻塞合入

#### P3-R1 开发记录仍未登记本轮文档 commit

- **位置：** `snapshots/role-a/dev-record-a.md` Commit 表
- **问题：** 有 `1fec805`，没有 `0c3b105 docs(task-2): 审查回复，阶段改为待二次审查`。无功能影响。

#### P3-R2 终态拒绝文案漏了「已处置」

- **位置：** `src/python/routes_alarm.py:84`
- **问题：** `status=2`（已处置）与 `3`（已关闭）都走 40001，文案是「已确认或已关闭，不可重复确认」。
- **处理：** 改成「当前状态不可确认」即可，非必须。

#### P3-R3 生产列表成功时仍始终画出 3 个 mock 换热站

- **位置：** `web/src/pages/alarm/AlarmMap.vue:144-159`
- **问题：** `collectStations` 无论是否 Mock 都会并入夹具站 1/2/3。真实站号是 10/11 时，左侧会多出三个「无未确认预警」的安塞区演示站。
- **处理：** `usingMock` 为真才并入 mock 站点；实数只从当前 `alarms` 收集。可 follow-up。

#### P3-R4 筛选 `watch` 连续触发时，慢请求可能盖住快请求

- **位置：** `AlarmMap.vue:215-232`、`262`
- **问题：** 没有序号/AbortController。先改级别、再改状态，先发出的响应后到会覆盖新结果。
- **处理：** 合入后加请求序号即可，不是回归。

---

## 四、修复质量（本轮）

- `_apply_ack` 先更新再查，失败 `rollback` 且测试断言 `committed is False`，比首轮「rowcount=0 也 commit」干净。
- `isAlarmBackendUnreachable` 只认 Axios 网络/5xx；拦截器把业务 `code!==0` 收成普通 `Error`，因此 40001 不会误进 Mock。这条链路是对的。
- `toggleLevel` 不再自己 `loadAlarms`，避免和 `watch` 打两次。`watch` 无 `immediate`，与 `onMounted` 也不会双拉。
- 范围仍在 Task 2 独占文件 + 角色 A 快照内，未改 F0 冻结文件，未挂 forecast。

---

## 五、残留风险（与首轮相同，非本轮引入）

- 路由单测仍全部 mock `SessionLocal`，没有打到真实 `biz_alarm`。
- 前端无组件测试，P1-1 的关闭/失败路径靠读代码确认。
- 合入后 `tests/test_scaffold.py::test_all_seven_module_routers_exist` 仍会红，需 main 上单独 chore 放宽空桩断言。
- `StationMap` 仍是 F0 灰色占位。

---

## 六、审查结论

✅ **通过**

首轮阻断项已修，P2 已落地，本轮无新的必须修复项。可以合入 `dev-2/feature/task2-alarm-map`。P3-R1～R4 与脚手架空桩 chore 不挡本 PR。
