<template>
  <div class="alarm-card" :class="`level-${level}`">
    <div class="alarm-header">
      <span class="alarm-level">{{ levelLabel }}</span>
      <span class="alarm-type">{{ alarmType }}</span>
    </div>
    <div class="alarm-body">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * AlarmCard — displays an alarm event with color-coded severity.
 *
 * Props:
 *   level:     1=blue 2=yellow 3=orange 4=red
 *   alarmType: alarm type label
 */
import { computed } from "vue";

const props = defineProps<{
  level: number;
  alarmType?: string;
}>();

const levelLabel = computed(() => {
  const map: Record<number, string> = {
    1: "蓝色",
    2: "黄色",
    3: "橙色",
    4: "红色",
  };
  return map[props.level] || "未知";
});
</script>

<style scoped>
.alarm-card {
  border-radius: 8px;
  padding: 12px 16px;
  border-left: 4px solid #ccc;
}
.level-1 { border-left-color: #409eff; background: #ecf5ff; }
.level-2 { border-left-color: #e6a23c; background: #fdf6ec; }
.level-3 { border-left-color: #f56c6c; background: #fef0f0; }
.level-4 { border-left-color: #c00; background: #fde2e2; }
.alarm-header { display: flex; gap: 8px; align-items: center; font-weight: 600; }
.alarm-level { font-size: 12px; }
.alarm-body { margin-top: 8px; font-size: 13px; color: #666; }
</style>
