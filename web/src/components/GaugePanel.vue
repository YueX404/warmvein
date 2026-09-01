<template>
  <div class="gauge-panel" ref="chartRef"></div>
</template>

<script setup lang="ts">
/**
 * GaugePanel — ECharts gauge (speedometer-style) for a single metric.
 *
 * Props:
 *   value:   current value
 *   max:     maximum value (default 100)
 *   title:   gauge title
 *   unit:    unit label
 */
import { ref, onMounted, watch, onBeforeUnmount } from "vue";
import * as echarts from "echarts";

const props = withDefaults(
  defineProps<{
    value: number;
    max?: number;
    title?: string;
    unit?: string;
  }>(),
  { max: 100, title: "", unit: "" }
);

const chartRef = ref<HTMLDivElement>();
let chart: echarts.ECharts | null = null;

function renderChart() {
  if (!chartRef.value) return;
  if (!chart) {
    chart = echarts.init(chartRef.value);
  }
  chart.setOption({
    series: [
      {
        type: "gauge",
        min: 0,
        max: props.max,
        title: { show: !!props.title, text: props.title, offsetCenter: [0, "70%"] },
        detail: {
          formatter: `{value}${props.unit}`,
          fontSize: 18,
          offsetCenter: [0, "45%"],
        },
        data: [{ value: props.value }],
      },
    ],
  });
}

onMounted(renderChart);
watch(() => props.value, renderChart);
onBeforeUnmount(() => chart?.dispose());
</script>

<style scoped>
.gauge-panel {
  width: 200px;
  height: 200px;
}
</style>
