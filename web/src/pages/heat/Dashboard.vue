<template>
  <div class="dashboard">
    <div class="page-head">
      <h1>供暖运行监测大屏</h1>
      <el-select v-model="stationId" style="width: 220px" @change="loadStation">
        <el-option
          v-for="item in stations"
          :key="item.stationId"
          :label="item.name"
          :value="item.stationId"
        />
      </el-select>
    </div>

    <el-row :gutter="16" class="block">
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>换热站分布</template>
          <StationMap :stations="mapStations" />
          <svg class="station-plot" viewBox="0 0 420 160" role="img" aria-label="换热站点位">
            <rect width="420" height="160" fill="#e8eef5" />
            <g v-for="s in mapStations" :key="s.stationId">
              <circle :cx="plotX(s.lng)" :cy="plotY(s.lat)" r="8" fill="#1d6fa5" />
              <text :x="plotX(s.lng) + 10" :y="plotY(s.lat) + 4" font-size="11" fill="#1f2d3d">
                {{ s.name }}
              </text>
            </g>
          </svg>
          <el-table :data="stations" size="small" style="margin-top: 12px">
            <el-table-column prop="stationId" label="ID" width="70" />
            <el-table-column prop="name" label="站名" />
            <el-table-column prop="supplyTemp" label="供水 ℃" width="90" />
            <el-table-column prop="returnTemp" label="回水 ℃" width="90" />
            <el-table-column prop="pressure" label="压力 MPa" width="110" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">{{ row.status === 1 ? "运行" : "停用" }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>{{ realtime.stationName || "实时参数" }}</template>
          <div class="gauges">
            <GaugePanel :value="realtime.supplyTemp" :max="90" title="供水" unit="℃" />
            <GaugePanel :value="realtime.healthScore" :max="100" title="健康度" unit="" />
          </div>
          <el-descriptions :column="2" size="small" border>
            <el-descriptions-item label="回水">{{ realtime.returnTemp }} ℃</el-descriptions-item>
            <el-descriptions-item label="温差">{{ realtime.tempDiff }} ℃</el-descriptions-item>
            <el-descriptions-item label="压力">{{ realtime.pressure }} MPa</el-descriptions-item>
            <el-descriptions-item label="流量">{{ realtime.flowRate }} t/h</el-descriptions-item>
            <el-descriptions-item label="室温">{{ realtime.roomTemp }} ℃</el-descriptions-item>
            <el-descriptions-item label="室外">{{ realtime.outdoorTemp }} ℃</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="block">
      <el-col :span="16">
        <el-card shadow="never">
          <LineChart
            title="供回水温度趋势"
            :x-data="hours"
            :series="tempSeries"
          />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>能效指标 {{ energy.date }}</template>
          <el-statistic title="供热量 GJ" :value="energy.totalHeatEnergy" />
          <el-statistic title="热损耗 kWh" :value="energy.totalHeatLoss" />
          <el-statistic title="热损率 %" :value="energy.heatLossRate" />
          <el-statistic title="单位能耗" :value="energy.unitEnergy" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="block">
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            水力平衡
            <el-tag v-if="balance.unbalancedCount" type="warning" size="small">
              失衡 {{ balance.unbalancedCount }} 条
            </el-tag>
          </template>
          <el-table :data="balance.branches" size="small">
            <el-table-column prop="branchName" label="支路" />
            <el-table-column prop="actualFlow" label="实际流量" />
            <el-table-column prop="designFlow" label="设计流量" />
            <el-table-column prop="beta" label="β" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.unbalanced ? 'danger' : 'success'" size="small">
                  {{ row.unbalanced ? "失衡" : "正常" }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="suggestOpen" label="建议开度 %" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>气候补偿</template>
          <el-form label-width="88px" @submit.prevent="onClimate">
            <el-form-item label="室外温度">
              <el-input-number v-model="tw" :min="-40" :max="20" :step="0.5" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" native-type="submit">计算并下发</el-button>
            </el-form-item>
          </el-form>
          <el-descriptions v-if="climate" :column="1" size="small" border>
            <el-descriptions-item label="供水设定">{{ climate.TgSet }} ℃</el-descriptions-item>
            <el-descriptions-item label="回水设定">{{ climate.thSet }} ℃</el-descriptions-item>
            <el-descriptions-item label="指令号">{{ climate.actionId }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import StationMap from "@/components/StationMap.vue";
import LineChart from "@/components/LineChart.vue";
import GaugePanel from "@/components/GaugePanel.vue";
import { hours, supplyTempTrend, returnTempTrend } from "@/mock/heat.mock";
import { climateCompensate, getBalance, getEnergy, getRealtime, getStations } from "@/services/heat.api";

const stationId = ref(1);
const tw = ref(-5);
const stations = ref<Array<Record<string, any>>>([]);
const realtime = reactive<Record<string, any>>({
  stationName: "",
  supplyTemp: 0,
  returnTemp: 0,
  tempDiff: 0,
  pressure: 0,
  flowRate: 0,
  roomTemp: 0,
  outdoorTemp: 0,
  healthScore: 0,
});
const balance = reactive<{ branches: any[]; unbalancedCount: number }>({
  branches: [],
  unbalancedCount: 0,
});
const energy = reactive<Record<string, any>>({
  date: "",
  totalHeatEnergy: 0,
  totalHeatLoss: 0,
  heatLossRate: 0,
  unitEnergy: 0,
});
const climate = ref<Record<string, any> | null>(null);

const mapStations = computed(() =>
  stations.value.map((s) => ({
    stationId: s.stationId,
    name: s.name,
    lng: s.lng,
    lat: s.lat,
    status: s.status === 1 ? "运行" : "停用",
  }))
);

const tempSeries = [
  { name: "供水", data: supplyTempTrend },
  { name: "回水", data: returnTempTrend },
];

function plotX(lng: number) {
  return ((lng - 109.315) / 0.016) * 380 + 20;
}

function plotY(lat: number) {
  return 140 - ((lat - 36.86) / 0.01) * 120;
}

async function loadStation() {
  const [rt, bal] = await Promise.all([
    getRealtime(stationId.value),
    getBalance(stationId.value),
  ]);
  Object.assign(realtime, rt);
  Object.assign(balance, bal);
}

async function onClimate() {
  const data = await climateCompensate(stationId.value, tw.value);
  climate.value = data as Record<string, any>;
  ElMessage.success(`已计算供水设定 ${climate.value.TgSet} ℃`);
}

onMounted(async () => {
  const list = await getStations("ansai");
  stations.value = (list as any).stations || [];
  const kpi = await getEnergy("2026-08-31", "ansai");
  Object.assign(energy, kpi);
  await loadStation();
});
</script>

<style scoped>
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.page-head h1 {
  margin: 0;
  font-size: 20px;
}
.block {
  margin-bottom: 16px;
}
.gauges {
  display: flex;
  justify-content: space-around;
  margin-bottom: 12px;
}
.station-plot {
  display: block;
  width: 100%;
  height: 160px;
  margin-top: 8px;
  border-radius: 8px;
}
</style>
