# 开发任务拆分 — 角色 B：前端与展现层（大屏 / 移动端 / 后台）

> 版本：v2026.08.31-任务拆分-B
> 配对文档：《开发任务拆分 — 角色 A：平台与智能底座》
> 对接契约：以《功能开发文档》§3 API 接口清单 为唯一冻结契约

---

## 1. 角色定位与边界

- **你负责**：Vue3 + TS + Vite + Element Plus + ECharts 全部前端代码——指挥大屏、运维移动端、管理后台、公共组件、API 请求层、Mock 服务。
- **你不管**：任何后端逻辑、算法、数据库、Kafka/Spark。这些全部归角色 A。
- **唯一对接面**：调用《功能开发文档》§3 的 REST API。不写任何后端服务，不碰数据库。

---

## 2. 代码所有权（目录隔离，避免 PR 冲突）

你独占以下目录，角色 A 不触碰：
```
web/
  src/
    pages/
      Dashboard.vue           # 指挥大屏
      mobile/                 # 运维 APP/移动端
        AlarmReceive.vue  WorkOrder.vue  Patrol.vue
      admin/                  # 管理后台
        MasterData.vue  PlanManage.vue  SmsTemplate.vue  UserSubscribe.vue  Report.vue
    components/
      AlarmCard.vue  StationMap.vue  LineChart.vue  GaugePanel.vue  SmsModal.vue
    services/                 # API 请求层（封装 axios/fetch）
      heat.api.ts  alarm.api.ts  workorder.api.ts  sms.api.ts  plan.api.ts  twin.api.ts
    mock/                     # 本地 Mock（按契约造数据）
      heat.mock.ts  alarm.mock.ts ...  mockServer.ts
    utils/  hooks/
  .env.development            # VITE_API_BASE=http://localhost:8000 (联调切真实)
  vite.config.ts
```
⚠ 不要修改 `src/python/`、`config/`、`docs/功能开发文档.md` 中的 API 契约表。契约变更需双方同步升级版本号。

---

## 3. 技术栈
Vue3 + TypeScript + Vite + Element Plus + ECharts；2 空格缩进；标识符英文（遵循 `.trae/rules/技术规范.md`）。

---

## 4. 并行开发约定（与角色 A 的协作）

1. **契约冻结**：《功能开发文档》§3 为唯一标准。你按此写 `services/*.api.ts` 与 `mock/*.mock.ts`，字段名/结构/code/message/data 必须一致。
2. **Mock 先行**：`web/mock/` 内置 JSON 夹具，覆盖每个接口的成功/异常返回。开发期 `VITE_API_BASE` 指向 mockServer，不依赖 A 的服务启动。
3. **零共享文件**：双方目录无交集，PR 无文件冲突。
4. **切换即对接**：A 完成后，仅改 `.env.development` 的 `VITE_API_BASE` 为真实地址（或在服务层加开关），**组件逻辑不改**。API 层做契约适配，页面只认 `data` 字段。
5. **联调时机**：各自 M3 结束后再端到端联调，此前互不阻塞。

---

## 5. 任务拆解（里程碑）

### M1 — 工程脚手架 + 监测大屏
- [ ] 初始化 Vue3+TS+Vite+Element Plus+ECharts 工程；配置 `services/` 请求层封装（统一拦截 `code/message`）。
- [ ] `web/mock/`：heat.mock（换热站列表、实时参数）、alarm.mock 基础夹具。
- [ ] `components/`：StationMap(GIS 点位)、LineChart、GaugePanel、AlarmCard。
- [ ] `pages/Dashboard.vue`：供热总览、换热站地图、实时参数卡片、能效榜。
- ✅ 验收：大屏用 Mock 数据完整渲染，可钻取 热源→换热站→管段→用户。

### M2 — 预警 / 能效 / 短信 界面
- [ ] mock：alarm.mock（四级预警）、energy.mock、sms.mock、forecast.mock。
- [ ] Dashboard 扩展：预警一张图（蓝/黄/橙/红分级着色）、能效对标图、预报列表。
- [ ] `pages/mobile/AlarmReceive.vue`：预警接收（与短信同步展示）、详情。
- [ ] `pages/admin/SmsTemplate.vue` + `SmsModal.vue`：短信模板管理、手动发送、发送记录查看（调用 `/sms/*`）。
- [ ] `pages/admin/UserSubscribe.vue`：用户订阅开关（手机号脱敏展示 138****1234）。
- ✅ 验收：预警分级展示正确；短信界面 mock 发送/记录/脱敏符合契约。

### M3 — 工单 / 巡检 / 预案 / 孪生
- [ ] mock：workorder.mock、plan.mock、patrol.mock、twin.mock。
- [ ] `pages/mobile/WorkOrder.vue`：接单→到场→处置→拍照上传→核验 全流程；超时标红。
- [ ] `pages/mobile/Patrol.vue`：巡检计划与路线、打卡。
- [ ] `pages/admin/PlanManage.vue`：预案结构化编辑、匹配/启动。
- [ ] `pages/Dashboard.vue` 孪生仿真面板：停暖恢复曲线（`/twin/simulate/recovery` 返回 tReach + chart 数据）。
- ✅ 验收：工单移动端闭环可用；预案/孪生面板 mock 数据正常。

### M4 — 收尾与联调
- [ ] `pages/admin/Report.vue`：运营/隐患/安全报表。
- [ ] `.env.development` 切换真实 `VITE_API_BASE`；与角色 A 端到端联调。
- [ ] 等保相关前端项：XSS 输出转义、敏感信息脱敏展示、操作确认防误触。
- [ ] 性能：大屏聚合查询 P95≤3s（依赖 A 接口性能）。
- ✅ 验收：联调通过；脱敏/转义合规；大屏流畅。

---

## 6. 验收标准（角色 B）
1. 所有页面调用的接口路径/字段与冻结契约一致。
2. Mock 阶段即可全功能演示（不依赖后端）。
3. 切换 `VITE_API_BASE` 后无需改组件即可对接真实后端。
4. 四级预警分级着色、工单状态流转、短信脱敏展示正确。
5. XSS 转义、敏感信息脱敏在前端落实。

---

## 7. 风险与解耦点
- **GIS/BIM 数据**：StationMap 在缺三维数据时降级为二维一张图，不阻塞。
- **真实接口延迟**：先用 Mock 保证 UI 进度；性能问题在 M4 联调暴露，由 A 侧优化接口。
- **契约变更**：唯一阻塞点，靠 §4 协议规避——A 改字段先升版本，你同步改 `services/` 与 `mock/`。
