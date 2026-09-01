<template>
  <div class="sms-desk">
    <header class="mast">
      <p class="eyebrow">短信通知</p>
      <h1>调度短信台</h1>
      <p class="lede">点选模板、填变量、发出去；回执只显示脱敏号 138****1234。</p>
    </header>

    <section class="grid">
      <article class="panel">
        <h2>模板目录</h2>
        <p class="hint">目录来自 Mock 样例，点选后填入发送区。</p>
        <ul class="catalog">
          <li
            v-for="item in templates"
            :key="item.templateCode"
            :class="{ active: selected?.templateCode === item.templateCode }"
            role="button"
            tabindex="0"
            @click="pickTemplate(item)"
            @keydown.enter="pickTemplate(item)"
          >
            <span class="dot" :data-scene="item.scene" />
            <div>
              <strong>{{ item.templateCode }}</strong>
              <em>{{ sceneLabel(item.scene) }}</em>
            </div>
          </li>
        </ul>
      </article>

      <article class="panel compose">
        <h2>手动发送</h2>
        <el-form label-position="top" @submit.prevent="onSend">
          <el-form-item label="模板编码">
            <el-input v-model="templateCode" maxlength="32" placeholder="如 ALARM_RED" />
          </el-form-item>
          <p v-if="selected" class="preview">{{ previewContent }}</p>
          <el-form-item
            v-for="key in varKeys"
            :key="key"
            :label="`变量 {${key}}`"
          >
            <el-input v-model="vars[key]" :placeholder="key" />
          </el-form-item>
          <el-form-item label="手机号（每行一个）">
            <el-input
              v-model="phonesRaw"
              type="textarea"
              :rows="4"
              placeholder="13812341234"
            />
          </el-form-item>
          <p v-if="maskedPhones.length" class="masked-row">
            将发往
            <span v-for="phone in maskedPhones" :key="phone" class="chip">{{ phone }}</span>
          </p>
          <el-form-item>
            <el-button type="primary" native-type="submit" :loading="sending">
              发送短信
            </el-button>
            <span v-if="lastBatchId" class="exec">批次 {{ lastBatchId }}</span>
          </el-form-item>
        </el-form>
      </article>
    </section>

    <section class="panel tape">
      <div class="tape-head">
        <h2>发送记录</h2>
        <el-input
          v-model="batchFilter"
          placeholder="按 batchId 筛选"
          clearable
          style="max-width: 220px"
          @clear="loadLogs"
          @keyup.enter="loadLogs"
        />
        <el-button :loading="loadingLogs" @click="loadLogs">刷新</el-button>
        <span v-if="usingMock" class="hint">后端未就绪，当前为 Mock 回执</span>
      </div>
      <el-table :data="logs" stripe empty-text="暂无发送记录" class="log-table">
        <el-table-column prop="createdAt" label="时间" width="170" />
        <el-table-column prop="batchId" label="批次" width="160" />
        <el-table-column prop="templateCode" label="模板" width="140" />
        <el-table-column label="手机号" width="140">
          <template #default="{ row }">{{ maskPhone(row.phoneMasked) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="receipt" label="回执" />
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { getSmsLog, isSmsBackendUnreachable, maskPhone, sendSms, type SmsLogRow } from "@/services/sms.api";
import { filterLogs, templates, type SmsTemplate } from "@/mock/sms.mock";

const SCENE_LABEL: Record<string, string> = {
  alarm_red: "红色预警",
  shutdown: "停暖公告",
  frost: "冻堵防寒",
};

const STATUS_LABEL: Record<number, string> = {
  0: "待发送",
  1: "发送中",
  2: "成功",
  3: "失败",
  4: "限流跳过",
};

const selected = ref<SmsTemplate | null>(templates[0] ?? null);
const templateCode = ref(selected.value?.templateCode ?? "");
const vars = reactive<Record<string, string>>({});
const phonesRaw = ref("");
const sending = ref(false);
const lastBatchId = ref("");
const batchFilter = ref("");
const logs = ref<SmsLogRow[]>([]);
const loadingLogs = ref(false);
const usingMock = ref(false);

const varKeys = computed(() => extractVars(selected.value?.content ?? ""));
const previewContent = computed(() => fillVars(selected.value?.content ?? "", vars));
const phoneList = computed(() => parsePhones(phonesRaw.value));
const maskedPhones = computed(() => phoneList.value.map((phone) => maskPhone(phone)));

function sceneLabel(scene: string) {
  return SCENE_LABEL[scene] || scene;
}

function statusLabel(status: number) {
  return STATUS_LABEL[status] || String(status);
}

function statusType(status: number): "success" | "danger" | "warning" | "info" {
  if (status === 2) return "success";
  if (status === 3) return "danger";
  if (status === 4) return "warning";
  return "info";
}

function extractVars(content: string): string[] {
  const found = content.match(/\{([A-Za-z0-9_]+)\}/g) || [];
  return [...new Set(found.map((token) => token.slice(1, -1)))];
}

function fillVars(content: string, values: Record<string, string>): string {
  return content.replace(/\{([A-Za-z0-9_]+)\}/g, (_, key: string) => values[key] || `{${key}}`);
}

function parsePhones(raw: string): string[] {
  return raw
    .split(/[\s,，;；]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function pickTemplate(item: SmsTemplate) {
  selected.value = item;
  templateCode.value = item.templateCode;
  Object.keys(vars).forEach((key) => {
    delete vars[key];
  });
}

async function onSend() {
  const phones = phoneList.value;
  if (!templateCode.value.trim() || !phones.length) {
    ElMessage.warning("请填写模板编码和手机号");
    return;
  }
  sending.value = true;
  try {
    const data = await sendSms(templateCode.value.trim(), phones, { ...vars });
    lastBatchId.value = data?.batchId ?? "";
    ElMessage.success(`已提交，批次 ${lastBatchId.value}`);
    batchFilter.value = lastBatchId.value;
    await loadLogs();
  } catch {
    /* interceptor already toasted */
  } finally {
    sending.value = false;
  }
}

async function loadLogs() {
  loadingLogs.value = true;
  try {
    const data = await getSmsLog(batchFilter.value.trim() || undefined);
    logs.value = Array.isArray(data) ? data : [];
    usingMock.value = false;
  } catch (err) {
    if (import.meta.env.DEV && isSmsBackendUnreachable(err)) {
      logs.value = filterLogs(batchFilter.value.trim() || undefined);
      usingMock.value = true;
    } else {
      logs.value = [];
      usingMock.value = false;
    }
  } finally {
    loadingLogs.value = false;
  }
}

onMounted(loadLogs);
</script>

<style scoped>
.sms-desk {
  min-height: 100vh;
  padding: 28px 32px 48px;
  background:
    radial-gradient(1000px 360px at 88% -8%, #1c3a40 0%, transparent 50%),
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
  grid-template-columns: minmax(240px, 320px) 1fr;
  gap: 16px;
  max-width: 1100px;
  margin-bottom: 16px;
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
.hint {
  margin: 0 0 8px;
  color: #8aa0ae;
  font-size: 12px;
}
.catalog {
  list-style: none;
  margin: 0;
  padding: 0;
}
.catalog li {
  display: grid;
  grid-template-columns: 10px 1fr;
  gap: 10px;
  align-items: start;
  padding: 10px 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
}
.catalog li.active,
.catalog li:hover,
.catalog li:focus {
  color: #e08a3c;
  outline: none;
  background: rgba(224, 138, 60, 0.08);
}
.catalog em {
  display: block;
  font-style: normal;
  color: #8aa0ae;
  font-size: 12px;
}
.dot {
  width: 8px;
  height: 8px;
  margin-top: 6px;
  border-radius: 50%;
  background: #8aa0ae;
}
.dot[data-scene="alarm_red"] { background: #e23d3d; }
.dot[data-scene="shutdown"] { background: #e08a3c; }
.dot[data-scene="frost"] { background: #4db8c9; }
.preview {
  margin: 0 0 12px;
  padding: 10px 12px;
  border-left: 3px solid #4db8c9;
  background: rgba(77, 184, 201, 0.08);
  color: #d5eef2;
  font-size: 13px;
}
.masked-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin: 0 0 12px;
  color: #8aa0ae;
  font-size: 13px;
}
.chip {
  font-variant-numeric: tabular-nums;
  color: #e7eef3;
  background: rgba(255, 255, 255, 0.06);
  border: 1px dashed rgba(77, 184, 201, 0.4);
  padding: 2px 8px;
  border-radius: 3px;
}
.exec {
  margin-left: 10px;
  color: #7dbe6c;
  font-size: 13px;
}
.tape {
  max-width: 1100px;
}
.tape-head {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin-bottom: 12px;
}
.tape-head h2 {
  margin: 0 auto 0 0;
}
.log-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(255, 255, 255, 0.04);
  --el-table-text-color: #e7eef3;
  --el-table-header-text-color: #b7c4ce;
  --el-table-border-color: rgba(255, 255, 255, 0.08);
  --el-table-row-hover-bg-color: rgba(224, 138, 60, 0.08);
}
:deep(.el-form-item__label) {
  color: #b7c4ce;
}
@media (max-width: 840px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
