<template>
  <el-container class="app-shell">
    <el-header class="app-header" height="56px">
      <div class="brand">安塞供暖智慧运行平台</div>
      <el-menu
        :default-active="active"
        mode="horizontal"
        router
        background-color="#0f2744"
        text-color="#c5d4e8"
        active-text-color="#67e0e3"
      >
        <el-menu-item index="/heat">运行监测</el-menu-item>
        <el-menu-item index="/twin">停暖恢复</el-menu-item>
        <el-menu-item index="/public">公众服务</el-menu-item>
        <el-menu-item index="/alarm">预警</el-menu-item>
        <el-menu-item index="/workorder">工单</el-menu-item>
        <el-menu-item index="/plan">预案</el-menu-item>
        <el-menu-item index="/sms">短信</el-menu-item>
      </el-menu>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const active = computed(() => route.path);
</script>

<style>
html,
body,
#app {
  margin: 0;
  height: 100%;
  background: #f4f6f9;
}
</style>

<style scoped>
.app-shell {
  min-height: 100%;
}
.app-header {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #0f2744;
  padding: 0 16px;
}
.brand {
  color: #fff;
  font-weight: 600;
  white-space: nowrap;
  font-size: 15px;
}
.app-header :deep(.el-menu) {
  flex: 1;
  border-bottom: none;
}
.app-main {
  padding: 16px 20px 24px;
}
</style>
