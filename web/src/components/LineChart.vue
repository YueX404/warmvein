<template>
  <div class="line-chart" ref="chartRef"></div>
</template>

<script setup lang="ts">
/**
 * LineChart — ECharts line chart wrapper.
 *
 * Props:
 *   xData:  array of x-axis labels
 *   series: array of { name, data }
 *   title:  optional chart title
 */
import { ref, onMounted, watch, onBeforeUnmount } from "vue";
import * as echarts from "echarts";

const props = defineProps<{
  xData: (string | number)[];
  series: Array<{ name: string; data: (string | number)[] }>;
  title?: string;
}>();

const chartRef = ref<HTMLDivElement>();
let chart: echarts.ECharts | null = null;

function renderChart() {
  if (!chartRef.value) return;
  if (!chart) {
    chart = echarts.init(chartRef.value);
  }
  chart.setOption({
    title: props.title ? { text: props.title, left: "center" } : undefined,
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: props.xData },
    yAxis: { type: "value" },
    series: props.series.map((s) => ({
      name: s.name,
      type: "line",
      data: s.data,
      smooth: true,
    })),
  });
}

onMounted(renderChart);
watch(() => [props.xData, props.series], renderChart, { deep: true });
onBeforeUnmount(() => chart?.dispose());
</script>

<style scoped>
.line-chart {
  width: 100%;
  height: 300px;
}
</style>
