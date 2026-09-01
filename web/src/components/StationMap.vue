<template>
  <div class="station-map" ref="container"></div>
</template>

<script setup lang="ts">
/**
 * StationMap — GIS point display for heating stations.
 *
 * Props:
 *   stations: Array<{ stationId: number; name: string; lng: number; lat: number; status: string }>
 *
 * This is a placeholder stub. Dev-1 will integrate a real map SDK
 * (e.g. Leaflet / AMap) in the Dashboard page.
 */
defineProps<{
  stations?: Array<{
    stationId: number;
    name: string;
    lng: number;
    lat: number;
    status: string;
  }>;
}>();
</script>

<style scoped>
.station-map {
  width: 100%;
  height: 400px;
  background: #f0f2f5;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
}
</style>
