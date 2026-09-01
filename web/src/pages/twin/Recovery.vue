<template>
  <div class="recovery">
    <div class="page-head">
      <h1>停暖恢复仿真</h1>
    </div>

    <el-row :gutter="16">
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>仿真参数</template>
          <el-form label-width="108px" @submit.prevent="onSimulate">
            <el-form-item label="换热站">
              <el-select v-model="form.stationId" style="width: 100%">
                <el-option
                  v-for="item in stations"
                  :key="item.stationId"
                  :label="item.name"
                  :value="item.stationId"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="开始时间">
              <el-input v-model="form.startTime" />
            </el-form-item>
            <el-form-item label="目标供水 ℃">
              <el-input-number v-model="form.targetSupplyTemp" :min="40" :max="90" />
            </el-form-item>
            <el-form-item label="升温速率">
              <el-input-number v-model="form.rampRate" :min="0.5" :max="8" :step="0.5" />
            </el-form-item>
            <el-form-item label="步数">
              <el-input-number v-model="form.steps" :min="6" :max="48" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" native-type="submit" :loading="loading">开始仿真</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>恢复曲线</template>
          <el-descriptions v-if="result" :column="3" size="small" border class="summary">
            <el-descriptions-item label="达标时刻">{{ result.tReach }}</el-descriptions-item>
            <el-descriptions-item label="耗时 h">{{ result.hoursToReach }}</el-descriptions-item>
            <el-descriptions-item label="收敛">
              <el-tag :type="result.converged ? 'success' : 'warning'" size="small">
                {{ result.converged ? "室温已达 18℃" : "未收敛" }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
          <LineChart
            v-if="chartX.length"
            title="供水 / 回水 / 室温"
            :x-data="chartX"
            :series="chartSeries"
          />
          <el-empty v-else description="点击开始仿真生成曲线" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import LineChart from "@/components/LineChart.vue";
import { getStations } from "@/services/heat.api";
import { simulateRecovery } from "@/services/twin.api";

const loading = ref(false);
const stations = ref<Array<{ stationId: number; name: string }>>([]);
const form = reactive({
  stationId: 1,
  startTime: "2026-08-31 08:00:00",
  targetSupplyTemp: 65,
  rampRate: 2,
  steps: 12,
});
const result = ref<Record<string, any> | null>(null);
const chartX = ref<(string | number)[]>([]);
const chartSeries = ref<Array<{ name: string; data: (string | number)[] }>>([]);

async function onSimulate() {
  loading.value = true;
  try {
    const data = (await simulateRecovery(form.stationId, {
      startTime: form.startTime,
      targetSupplyTemp: form.targetSupplyTemp,
      rampRate: form.rampRate,
      steps: form.steps,
    })) as Record<string, any>;
    result.value = data;
    chartX.value = data.chart?.timestamps || [];
    chartSeries.value = [
      { name: "供水", data: data.chart?.supplyTemp || [] },
      { name: "回水", data: data.chart?.returnTemp || [] },
      { name: "室温", data: data.chart?.roomTemp || [] },
    ];
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  const list = await getStations("ansai");
  stations.value = (list as any).stations || [];
});
</script>

<style scoped>
.page-head h1 {
  margin: 0 0 16px;
  font-size: 20px;
}
.summary {
  margin-bottom: 12px;
}
</style>
