<template>
  <div class="alarm-map">
    <header class="page-header">
      <h1>预警一张图</h1>
      <p>蓝 / 黄 / 橙 / 红分级着色，确认后状态同步</p>
    </header>

    <section class="legend-row">
      <div
        v-for="item in levelStats"
        :key="item.level"
        class="legend-chip"
        :class="`level-${item.level}`"
        @click="toggleLevel(item.level)"
      >
        <span class="dot" />
        <strong>{{ item.label }}</strong>
        <em>{{ item.count }}</em>
      </div>
    </section>

    <section class="toolbar">
      <el-select v-model="levelFilter" clearable placeholder="预警级别" style="width: 140px">
        <el-option v-for="opt in levelOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
      <el-select v-model="statusFilter" clearable placeholder="处理状态" style="width: 140px">
        <el-option v-for="opt in statusOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
      <el-button type="primary" :loading="loading" @click="loadAlarms">刷新</el-button>
      <span v-if="usingMock" class="mock-hint">后端未就绪，当前为 Mock 数据</span>
    </section>

    <section class="map-layout">
      <div class="map-pane">
        <StationMap :stations="mapStations" />
        <div class="station-grid">
          <button
            v-for="station in stationCards"
            :key="station.stationId"
            class="station-card"
            :class="`level-${station.level}`"
            type="button"
            @click="focusStation(station.stationId)"
          >
            <span class="station-name">{{ station.name }}</span>
            <span class="station-meta">{{ station.label }}</span>
          </button>
        </div>
      </div>

      <div class="list-pane">
        <AlarmCard
          v-for="item in visibleAlarms"
          :key="item.alarmId"
          :level="item.level"
          :alarm-type="typeLabel(item.type)"
        >
          <div class="card-title">{{ item.title || typeLabel(item.type) }}</div>
          <div>换热站 #{{ item.stationId }} · {{ item.createdAt }}</div>
          <div v-if="item.rootCause">根因：{{ item.rootCause }}</div>
          <div class="card-actions">
            <el-tag size="small" :type="item.status === 0 ? 'warning' : 'info'">
              {{ item.statusName || statusLabel(item.status) }}
            </el-tag>
            <el-button
              v-if="item.status === 0"
              size="small"
              type="primary"
              @click="onAck(item)"
            >
              确认
            </el-button>
          </div>
        </AlarmCard>
        <el-empty v-if="!visibleAlarms.length" description="暂无预警" />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import AlarmCard from "@/components/AlarmCard.vue";
import StationMap from "@/components/StationMap.vue";
import {
  ackAlarm,
  getAlarms,
  isAlarmBackendUnreachable,
  type AlarmItem,
} from "@/services/alarm.api";
import { filterAlarms, stations } from "@/mock/alarm.mock";

const TYPE_LABEL: Record<string, string> = {
  freeze: "冻堵",
  leak: "泄漏",
  corrosion: "腐蚀",
  pressure: "压力",
  balance: "失衡",
  theft: "偷热",
  other: "其他",
};

const LEVEL_LABEL: Record<number, string> = {
  1: "蓝色",
  2: "黄色",
  3: "橙色",
  4: "红色",
};

const STATUS_LABEL: Record<number, string> = {
  0: "未确认",
  1: "已确认",
  2: "已处置",
  3: "已关闭",
};

const levelOptions = [
  { value: 4, label: "红色" },
  { value: 3, label: "橙色" },
  { value: 2, label: "黄色" },
  { value: 1, label: "蓝色" },
];

const statusOptions = [
  { value: 0, label: "未确认" },
  { value: 1, label: "已确认" },
  { value: 2, label: "已处置" },
  { value: 3, label: "已关闭" },
];

type StationPoint = {
  stationId: number;
  name: string;
  lng: number;
  lat: number;
  status: string;
};

function asNumber(value: number | undefined | null): number | undefined {
  return typeof value === "number" ? value : undefined;
}

function collectStations(items: AlarmItem[]): StationPoint[] {
  const byId = new Map<number, StationPoint>();
  for (const station of stations) {
    byId.set(station.stationId, { ...station });
  }
  for (const item of items) {
    if (byId.has(item.stationId)) continue;
    byId.set(item.stationId, {
      stationId: item.stationId,
      name: `换热站 #${item.stationId}`,
      lng: 0,
      lat: 0,
      status: "alarm",
    });
  }
  return [...byId.values()];
}
const alarms = ref<AlarmItem[]>([]);
const loading = ref(false);
const usingMock = ref(false);
const levelFilter = ref<number | undefined>();
const statusFilter = ref<number | undefined>();
const focusedStationId = ref<number | undefined>();

const visibleAlarms = computed(() => {
  if (focusedStationId.value === undefined) return alarms.value;
  return alarms.value.filter((item) => item.stationId === focusedStationId.value);
});

const levelStats = computed(() =>
  [4, 3, 2, 1].map((level) => ({
    level,
    label: LEVEL_LABEL[level],
    count: alarms.value.filter((item) => item.level === level && item.status === 0).length,
  }))
);

const stationViews = computed(() =>
  collectStations(alarms.value).map((station) => {
    const open = alarms.value.filter(
      (item) => item.stationId === station.stationId && item.status === 0
    );
    const maxLevel = open.reduce((acc, item) => Math.max(acc, item.level), 0);
    return {
      ...station,
      level: maxLevel || 0,
      status: maxLevel >= 3 ? "alarm" : maxLevel > 0 ? "warn" : "normal",
      label: maxLevel ? `${LEVEL_LABEL[maxLevel]} ×${open.length}` : "无未确认预警",
    };
  })
);

const mapStations = computed(() => stationViews.value);
const stationCards = computed(() => stationViews.value);

function typeLabel(type: string) {
  return TYPE_LABEL[type] || type;
}

function statusLabel(status: number) {
  return STATUS_LABEL[status] || String(status);
}

function toggleLevel(level: number) {
  levelFilter.value = levelFilter.value === level ? undefined : level;
}

function focusStation(stationId: number) {
  focusedStationId.value = focusedStationId.value === stationId ? undefined : stationId;
}

async function loadAlarms() {
  loading.value = true;
  try {
    const data = await getAlarms(asNumber(levelFilter.value), asNumber(statusFilter.value));
    alarms.value = Array.isArray(data) ? data : [];
    usingMock.value = false;
  } catch (err) {
    if (import.meta.env.DEV && isAlarmBackendUnreachable(err)) {
      alarms.value = filterAlarms(asNumber(levelFilter.value), asNumber(statusFilter.value));
      usingMock.value = true;
    } else {
      alarms.value = [];
      usingMock.value = false;
    }
  } finally {
    loading.value = false;
  }
}

function isDialogDismissed(err: unknown) {
  return err === "cancel" || err === "close";
}

async function onAck(item: AlarmItem) {
  try {
    const { value } = await ElMessageBox.prompt("请输入确认人", "确认预警", {
      inputPlaceholder: "操作人姓名",
      confirmButtonText: "确认",
      cancelButtonText: "取消",
      inputPattern: /\S+/,
      inputErrorMessage: "确认人不能为空",
    });
    const operator = String(value).trim();
    if (usingMock.value) {
      item.status = 1;
      item.statusName = "已确认";
      ElMessage.success("已本地确认（Mock）");
      return;
    }
    await ackAlarm(item.alarmId, operator);
    ElMessage.success("预警已确认");
    await loadAlarms();
  } catch (err) {
    if (isDialogDismissed(err)) return;
  }
}

watch([levelFilter, statusFilter], loadAlarms);

onMounted(loadAlarms);
</script>

<style scoped>
.alarm-map {
  padding: 24px;
  min-height: 100vh;
  background: #f5f7fa;
}
.page-header h1 {
  margin: 0 0 4px;
  font-size: 22px;
}
.page-header p {
  margin: 0 0 16px;
  color: #909399;
}
.legend-row,
.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.legend-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  cursor: pointer;
  min-width: 96px;
}
.legend-chip .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: currentColor;
}
.legend-chip em {
  font-style: normal;
  margin-left: auto;
  font-weight: 700;
}
.level-1 { color: #409eff; background: #ecf5ff; }
.level-2 { color: #e6a23c; background: #fdf6ec; }
.level-3 { color: #f56c6c; background: #fef0f0; }
.level-4 { color: #c00; background: #fde2e2; }
.level-0 { color: #67c23a; background: #f0f9eb; }
.mock-hint {
  color: #e6a23c;
  font-size: 13px;
}
.map-layout {
  display: grid;
  grid-template-columns: minmax(320px, 1.1fr) minmax(320px, 0.9fr);
  gap: 16px;
}
.map-pane,
.list-pane {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.station-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 8px;
}
.station-card {
  text-align: left;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  background: #fff;
}
.station-name {
  display: block;
  font-weight: 600;
}
.station-meta {
  font-size: 12px;
  color: #909399;
}
.card-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}
.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}
@media (max-width: 900px) {
  .map-layout {
    grid-template-columns: 1fr;
  }
}
</style>
