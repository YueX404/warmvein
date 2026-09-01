<template>
  <div class="plan-manage">
    <header class="mast">
      <p class="eyebrow">5.1 应急调度</p>
      <h1>预案调度台</h1>
      <p class="lede">按预警类型与级别匹配冻堵 / 爆管 / 停暖 / 第三方破坏预案，核对步骤后启动执行。</p>
    </header>

    <section class="grid">
      <article class="panel match-panel">
        <h2>匹配条件</h2>
        <el-form label-position="top" @submit.prevent="onMatch">
          <el-form-item label="预警类型">
            <el-select v-model="alarmType" placeholder="选择预警类型">
              <el-option
                v-for="item in alarmTypes"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="预警级别">
            <el-radio-group v-model="level">
              <el-radio-button :label="1" :value="1">1 蓝</el-radio-button>
              <el-radio-button :label="2" :value="2">2 黄</el-radio-button>
              <el-radio-button :label="3" :value="3">3 橙</el-radio-button>
              <el-radio-button :label="4" :value="4">4 红</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="matching" native-type="submit">
              匹配预案
            </el-button>
          </el-form-item>
        </el-form>

        <p class="mock-hint">示例目录（Mock，非库内数据；点选仅预览步骤）</p>
        <ul class="catalog">
          <li
            v-for="item in plans"
            :key="item.planId"
            role="button"
            tabindex="0"
            @click="showMockPlan(item)"
            @keydown.enter="showMockPlan(item)"
          >
            <span class="dot" :data-type="item.planType" />
            <strong>{{ item.name }}</strong>
            <em>L{{ item.alarmLevel }}</em>
          </li>
        </ul>
      </article>

      <article class="panel result-panel">
        <h2>匹配结果</h2>
        <p v-if="!matched" class="empty">选择类型与级别后匹配，步骤将按动作 / 责任主体 / 资源展开。</p>
        <template v-else>
          <div class="result-head">
            <el-tag :type="tagType(matched.plan_type)" effect="dark">
              {{ typeLabel(matched.plan_type) }}
            </el-tag>
            <h3>{{ matched.name || "未登记预案" }}</h3>
          </div>
          <dl v-if="matched.plan_id" class="meta">
            <div>
              <dt>预案编号</dt>
              <dd>#{{ matched.plan_id }}</dd>
            </div>
            <div>
              <dt>匹配级别</dt>
              <dd>{{ matched.alarm_level ?? level }}</dd>
            </div>
            <div>
              <dt>触发条件</dt>
              <dd>{{ matched.trigger_condition || "—" }}</dd>
            </div>
          </dl>
          <p v-else class="empty">库中暂无对应启用预案，可核对类型映射后重试。</p>

          <h3 class="steps-title">处置步骤</h3>
          <ol v-if="steps.length" class="steps">
            <li v-for="step in steps" :key="step.step">
              <span class="idx">{{ String(step.step).padStart(2, "0") }}</span>
              <div>
                <p class="action">{{ step.action }}</p>
                <p class="roles">
                  <span>责任主体 {{ step.role }}</span>
                  <span>资源 {{ step.resource }}</span>
                </p>
              </div>
            </li>
          </ol>
          <p v-else class="empty">无结构化步骤。</p>

          <div class="activate-row">
            <el-input v-model="operator" placeholder="启动人（可选）" maxlength="32" style="max-width: 200px" />
            <el-button
              type="danger"
              :disabled="!canActivate"
              :loading="activating"
              @click="onActivate"
            >
              启动预案
            </el-button>
            <span v-if="fromMock" class="hint">Mock 预览不可启动，请先接口匹配</span>
            <span v-if="execId" class="exec">执行单 #{{ execId }} 已下达</span>
          </div>
        </template>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { activatePlan, matchPlan, type PlanRow } from "@/services/plan.api";
import { plans, type PlanStep } from "@/mock/plan.mock";

const alarmTypes = [
  { value: "frost", label: "冻堵 frost → freeze" },
  { value: "leak", label: "爆管 leak → burst" },
  { value: "shutdown", label: "停暖 shutdown" },
  { value: "steal", label: "第三方破坏 steal → third_party" },
];

const alarmType = ref("frost");
const level = ref(4);
const operator = ref("");
const matching = ref(false);
const activating = ref(false);
const matched = ref<PlanRow | null>(null);
const execId = ref<number | null>(null);
const fromMock = ref(false);

const steps = computed<PlanStep[]>(() => parseSteps(matched.value?.steps));
const canActivate = computed(() => Boolean(matched.value?.plan_id) && !fromMock.value);

function parseSteps(raw: unknown): PlanStep[] {
  if (Array.isArray(raw)) {
    return raw as PlanStep[];
  }
  if (typeof raw === "string" && raw.trim()) {
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }
  return [];
}

function typeLabel(planType: string): string {
  const map: Record<string, string> = {
    freeze: "冻堵",
    burst: "爆管",
    shutdown: "停暖",
    third_party: "第三方破坏",
  };
  return map[planType] || planType;
}

function tagType(planType: string): "danger" | "warning" | "info" | "success" {
  if (planType === "burst") return "danger";
  if (planType === "freeze") return "info";
  if (planType === "shutdown") return "warning";
  return "success";
}

function showMockPlan(item: (typeof plans)[number]) {
  fromMock.value = true;
  execId.value = null;
  matched.value = {
    plan_id: item.planId,
    name: item.name,
    plan_type: item.planType,
    alarm_level: item.alarmLevel,
    trigger_condition: item.triggerCondition,
    steps: item.steps,
  };
}

async function onMatch() {
  matching.value = true;
  execId.value = null;
  fromMock.value = false;
  try {
    matched.value = await matchPlan(alarmType.value, level.value);
  } catch {
    matched.value = null;
  } finally {
    matching.value = false;
  }
}

async function onActivate() {
  const planId = matched.value?.plan_id;
  if (!planId || fromMock.value) return;
  try {
    await ElMessageBox.confirm("确认启动该预案？将写入一条执行记录。", "启动预案", {
      type: "warning",
      confirmButtonText: "启动",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }
  activating.value = true;
  try {
    const data = await activatePlan(planId, undefined, operator.value);
    execId.value = data?.execId ?? null;
    ElMessage.success("预案已启动");
  } catch {
    /* interceptor already toasted */
  } finally {
    activating.value = false;
  }
}
</script>

<style scoped>
.plan-manage {
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
  margin-bottom: 24px;
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
.mock-hint,
.hint {
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
.dot[data-type="freeze"] { background: #4db8c9; }
.dot[data-type="burst"] { background: #e23d3d; }
.dot[data-type="shutdown"] { background: #e08a3c; }
.dot[data-type="third_party"] { background: #7dbe6c; }
.empty {
  color: #8aa0ae;
  margin: 0;
}
.result-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.result-head h3 {
  margin: 0;
  font-size: 20px;
}
.meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 0 0 18px;
}
.meta dt {
  color: #8aa0ae;
  font-size: 12px;
}
.meta dd {
  margin: 4px 0 0;
}
.steps-title {
  margin: 0 0 10px;
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
.activate-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 18px;
}
.exec {
  color: #7dbe6c;
  font-size: 13px;
}
:deep(.el-form-item__label) {
  color: #b7c4ce;
}
@media (max-width: 840px) {
  .grid,
  .meta {
    grid-template-columns: 1fr;
  }
}
</style>
