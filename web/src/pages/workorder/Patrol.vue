<template>
  <article class="panel">
    <h2>生成巡检计划</h2>
    <el-form label-position="top" @submit.prevent="onGenerate">
      <el-form-item label="换热站编号">
        <el-input-number v-model="stationId" :min="1" :controls="false" />
      </el-form-item>
      <el-form-item label="巡检类型">
        <el-radio-group v-model="patrolType">
          <el-radio-button label="daily" value="daily">日常</el-radio-button>
          <el-radio-button label="special" value="special">专项</el-radio-button>
          <el-radio-button label="emergency" value="emergency">应急</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="巡检人">
        <el-input v-model="assignee" maxlength="32" placeholder="现场巡检员" />
      </el-form-item>
      <el-form-item label="计划日期">
        <el-date-picker
          v-model="planDate"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="选择日期"
        />
      </el-form-item>
      <el-form-item label="计划名称（可选）">
        <el-input v-model="planName" maxlength="64" placeholder="默认 auto" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="submitting" native-type="submit">
          生成计划
        </el-button>
      </el-form-item>
    </el-form>
  </article>

  <article class="panel">
    <h2>当日班表</h2>
    <p v-if="usingMock" class="mock-hint">后端未就绪，当前为 Mock 班表</p>
    <div v-if="result" class="ticket">
      <span class="ticket-label">计划号</span>
      <strong>#{{ result.patrolId }}</strong>
      <span class="ticket-meta">{{ typeLabel(result.patrolType) }} · {{ result.planDate }}</span>
      <span class="ticket-meta">{{ result.assignee }} · 站 #{{ result.stationId }}</span>
    </div>
    <p v-else class="empty">填写规则后生成，计划号将印在这张班次票上。</p>
    <p class="mock-hint">示例班表（Mock，点选仅预览）</p>
    <ul class="catalog">
      <li
        v-for="item in patrols"
        :key="item.patrolId"
        role="button"
        tabindex="0"
        @click="preview(item)"
        @keydown.enter="preview(item)"
      >
        <span class="dot" :data-type="item.patrolType" />
        <strong>{{ item.planName }}</strong>
        <em>{{ item.planDate }}</em>
      </li>
    </ul>
  </article>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { ElMessage } from "element-plus";
import { generatePatrolPlan } from "@/services/workorder.api";
import { patrols, type PatrolPlan } from "@/mock/workorder.mock";

const TYPE_LABEL: Record<string, string> = {
  daily: "日常",
  special: "专项",
  emergency: "应急",
};

const stationId = ref(1);
const patrolType = ref<PatrolPlan["patrolType"]>("daily");
const assignee = ref("王五");
const planDate = ref("2026-09-01");
const planName = ref("");
const submitting = ref(false);
const usingMock = ref(false);
const result = ref<PatrolPlan | null>(null);

function typeLabel(type: string) {
  return TYPE_LABEL[type] || type;
}

function preview(item: PatrolPlan) {
  usingMock.value = true;
  result.value = item;
}

async function onGenerate() {
  const name = planName.value.trim();
  if (!assignee.value.trim() || !planDate.value) {
    ElMessage.error("请填写巡检人与计划日期");
    return;
  }
  submitting.value = true;
  try {
    const data = await generatePatrolPlan({
      stationId: stationId.value,
      patrolType: patrolType.value,
      assignee: assignee.value.trim(),
      planDate: planDate.value,
      planName: name || undefined,
    });
    usingMock.value = false;
    result.value = {
      patrolId: data.patrolId,
      stationId: stationId.value,
      patrolType: patrolType.value,
      assignee: assignee.value.trim(),
      planDate: planDate.value,
      planName: name || "auto",
    };
    ElMessage.success(`巡检计划 #${data.patrolId} 已生成`);
  } catch {
    /* interceptor already toasted */
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
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
.mock-hint,
.empty {
  margin: 0 0 8px;
  color: #8aa0ae;
  font-size: 12px;
}
.empty {
  font-size: 14px;
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
.dot[data-type="special"] { background: #4db8c9; }
.dot[data-type="emergency"] { background: #e08a3c; }
.ticket {
  display: grid;
  gap: 6px;
  margin-bottom: 14px;
  padding: 16px 18px;
  border: 1px dashed rgba(224, 138, 60, 0.45);
  border-radius: 4px;
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
:deep(.el-form-item__label) {
  color: #b7c4ce;
}
:deep(.el-input-number) {
  width: 100%;
}
</style>
