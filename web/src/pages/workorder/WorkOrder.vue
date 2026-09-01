<template>
  <div class="workorder">
    <header class="mast">
      <p class="eyebrow">9.x 工单与巡检</p>
      <h1>派单台</h1>
      <p class="lede">由预警建单、按号查进度；巡检计划作为同一张班表上的另一个班次，不另开路由。</p>
    </header>

    <nav class="shift-tabs" aria-label="班次">
      <button type="button" :class="{ on: tab === 'order' }" @click="tab = 'order'">工单派发</button>
      <button type="button" :class="{ on: tab === 'patrol' }" @click="tab = 'patrol'">巡检计划</button>
    </nav>

    <section v-if="tab === 'order'" class="grid">
      <article class="panel">
        <h2>开单</h2>
        <el-form label-position="top" @submit.prevent="onCreate">
          <el-form-item label="预警编号">
            <el-input-number v-model="alarmId" :min="1" :controls="false" />
          </el-form-item>
          <el-form-item label="处置人">
            <el-input v-model="assignee" maxlength="32" placeholder="不超过 32 字" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="creating" native-type="submit">生成工单</el-button>
          </el-form-item>
        </el-form>
        <p class="mock-hint">示例工单（Mock，点选仅预览）</p>
        <ul class="catalog">
          <li
            v-for="item in orders"
            :key="item.orderId"
            role="button"
            tabindex="0"
            @click="previewOrder(item)"
            @keydown.enter="previewOrder(item)"
          >
            <span class="dot" :data-status="item.status" />
            <strong>#{{ item.orderId }} 预警 {{ item.alarmId }}</strong>
            <em>{{ item.statusName }}</em>
          </li>
        </ul>
      </article>

      <article class="panel">
        <h2>查单</h2>
        <div class="lookup">
          <el-input-number v-model="queryId" :min="1" :controls="false" placeholder="工单号" />
          <el-button :loading="loading" @click="onQuery">查询</el-button>
        </div>
        <p v-if="usingMock" class="mock-hint">后端未就绪，当前为 Mock 票根</p>
        <p v-if="!current" class="empty">输入工单号查询，或从左侧示例预览票根与流转。</p>
        <template v-else>
          <div class="ticket">
            <span class="ticket-label">工单号</span>
            <strong>#{{ current.orderId }}</strong>
            <span class="status" :data-status="current.status">{{ current.statusName }}</span>
            <dl class="meta">
              <div>
                <dt>预警</dt>
                <dd>#{{ current.alarmId }}</dd>
              </div>
              <div>
                <dt>处置人</dt>
                <dd>{{ current.assignee }}</dd>
              </div>
              <div>
                <dt>开单</dt>
                <dd>{{ current.createdAt || "—" }}</dd>
              </div>
            </dl>
          </div>
          <h3 class="steps-title">流转</h3>
          <ol v-if="current.trace?.length" class="steps">
            <li v-for="(row, idx) in current.trace" :key="`${row.time}-${idx}`">
              <span class="idx">{{ String(idx + 1).padStart(2, "0") }}</span>
              <div>
                <p class="action">{{ row.action }}</p>
                <p class="roles">
                  <span>{{ row.operator }}</span>
                  <span>{{ row.time }}</span>
                </p>
              </div>
            </li>
          </ol>
          <p v-else class="empty">暂无流转记录。</p>
        </template>
      </article>
    </section>

    <section v-else class="grid">
      <PatrolPanel />
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { ElMessage } from "element-plus";
import {
  createWorkOrder,
  getWorkOrder,
  isWorkorderBackendUnreachable,
  type WorkOrderRow,
} from "@/services/workorder.api";
import { findOrder, orders } from "@/mock/workorder.mock";
import PatrolPanel from "./Patrol.vue";

const tab = ref<"order" | "patrol">("order");
const alarmId = ref(1);
const assignee = ref("张三");
const queryId = ref(101);
const creating = ref(false);
const loading = ref(false);
const usingMock = ref(false);
const current = ref<WorkOrderRow | null>(null);

function previewOrder(item: WorkOrderRow) {
  usingMock.value = true;
  current.value = item;
  queryId.value = item.orderId;
}

async function onCreate() {
  const name = assignee.value.trim();
  if (!name) {
    ElMessage.error("请填写处置人");
    return;
  }
  creating.value = true;
  try {
    const data = await createWorkOrder(alarmId.value, name);
    usingMock.value = false;
    queryId.value = data.orderId;
    ElMessage.success(`工单 #${data.orderId} 已生成`);
    await loadOrder(data.orderId);
  } catch {
    /* interceptor already toasted */
  } finally {
    creating.value = false;
  }
}

async function onQuery() {
  await loadOrder(queryId.value);
}

async function loadOrder(orderId: number) {
  loading.value = true;
  try {
    current.value = await getWorkOrder(orderId);
    usingMock.value = false;
  } catch (err) {
    if (import.meta.env.DEV && isWorkorderBackendUnreachable(err)) {
      const found = findOrder(orderId);
      usingMock.value = true;
      current.value = found || null;
      if (!found) ElMessage.error("工单不存在");
    } else {
      current.value = null;
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.workorder {
  min-height: 100vh;
  padding: 28px 32px 48px;
  background:
    radial-gradient(1200px 400px at 10% -10%, #3a2a1c 0%, transparent 55%),
    #152028;
  color: #e7eef3;
  font-family: "Segoe UI Variable", "Bahnschrift", "Microsoft YaHei", sans-serif;
}
.mast {
  max-width: 1100px;
  margin-bottom: 20px;
}
.eyebrow {
  margin: 0 0 6px;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  font-size: 12px;
  color: #e08a3c;
}
h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 650;
  letter-spacing: 0.04em;
}
.lede {
  margin: 8px 0 0;
  max-width: 46em;
  color: #b7c4ce;
}
.shift-tabs {
  display: inline-flex;
  gap: 0;
  margin-bottom: 16px;
  border: 1px solid rgba(224, 138, 60, 0.35);
  border-radius: 6px;
  overflow: hidden;
}
.shift-tabs button {
  background: transparent;
  color: #b7c4ce;
  border: 0;
  padding: 8px 18px;
  cursor: pointer;
  font: inherit;
}
.shift-tabs button.on {
  background: #e08a3c;
  color: #152028;
  font-weight: 650;
}
.grid {
  display: grid;
  grid-template-columns: minmax(280px, 360px) 1fr;
  gap: 16px;
  max-width: 1100px;
}
.panel {
  background: rgba(21, 32, 40, 0.72);
  border: 1px solid rgba(224, 138, 60, 0.22);
  border-radius: 6px;
  padding: 18px 20px 22px;
}
h2 {
  margin: 0 0 14px;
  font-size: 15px;
  font-weight: 600;
  color: #e08a3c;
}
.mock-hint {
  margin: 0 0 8px;
  color: #8aa0ae;
  font-size: 12px;
}
.catalog {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}
.catalog li {
  display: grid;
  grid-template-columns: 10px 1fr auto;
  gap: 8px;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 13px;
  cursor: pointer;
}
.catalog li:hover,
.catalog li:focus {
  color: #e08a3c;
  outline: none;
}
.catalog em {
  font-style: normal;
  color: #8aa0ae;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #8aa0ae;
}
.dot[data-status="0"],
.dot[data-type="daily"] { background: #8aa0ae; }
.dot[data-status="1"],
.dot[data-type="special"] { background: #4db8c9; }
.dot[data-status="2"],
.dot[data-type="emergency"] { background: #e08a3c; }
.dot[data-status="4"] { background: #7dbe6c; }
.lookup {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.empty {
  color: #8aa0ae;
  margin: 0;
}
.ticket {
  display: grid;
  gap: 6px;
  padding: 16px 18px;
  border: 1px dashed rgba(224, 138, 60, 0.45);
  border-radius: 4px;
  background:
    repeating-linear-gradient(
      -12deg,
      transparent,
      transparent 10px,
      rgba(224, 138, 60, 0.04) 10px,
      rgba(224, 138, 60, 0.04) 11px
    );
}
.ticket-label {
  font-size: 12px;
  letter-spacing: 0.2em;
  color: #8aa0ae;
}
.ticket strong {
  font-size: 28px;
  letter-spacing: 0.06em;
}
.ticket-meta {
  color: #b7c4ce;
  font-size: 13px;
}
.status {
  justify-self: start;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  background: rgba(138, 160, 174, 0.2);
}
.status[data-status="1"] { background: rgba(77, 184, 201, 0.25); }
.status[data-status="2"] { background: rgba(224, 138, 60, 0.28); }
.status[data-status="4"] { background: rgba(125, 190, 108, 0.28); }
.meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 8px 0 0;
}
.meta dt {
  color: #8aa0ae;
  font-size: 12px;
}
.meta dd {
  margin: 4px 0 0;
}
.steps-title {
  margin: 18px 0 10px;
  font-size: 14px;
  color: #e08a3c;
}
.steps {
  list-style: none;
  margin: 0;
  padding: 0;
}
.steps li {
  display: grid;
  grid-template-columns: 40px 1fr;
  gap: 10px;
  padding: 10px 0;
  border-top: 1px dashed rgba(224, 138, 60, 0.28);
}
.idx {
  font-variant-numeric: tabular-nums;
  color: #e08a3c;
  font-weight: 700;
}
.action {
  margin: 0;
  font-size: 15px;
}
.roles {
  margin: 4px 0 0;
  display: flex;
  gap: 16px;
  color: #b7c4ce;
  font-size: 13px;
}
:deep(.el-form-item__label) {
  color: #b7c4ce;
}
:deep(.el-input-number) {
  width: 100%;
}
@media (max-width: 840px) {
  .grid,
  .meta {
    grid-template-columns: 1fr;
  }
}
</style>
