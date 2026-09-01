<template>
  <div class="service">
    <div class="page-head">
      <h1>公众服务</h1>
    </div>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>停暖通知</template>
          <el-form label-width="88px" @submit.prevent="onNotify">
            <el-form-item label="换热站">
              <el-select v-model="notifyForm.stationId" style="width: 100%">
                <el-option
                  v-for="item in stations"
                  :key="item.stationId"
                  :label="item.name"
                  :value="item.stationId"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="计划时间">
              <el-input v-model="notifyForm.planTime" placeholder="yyyy-MM-dd HH:mm" />
            </el-form-item>
            <el-form-item>
              <el-button type="warning" native-type="submit" :loading="notifyLoading">
                发送停暖通知
              </el-button>
            </el-form-item>
          </el-form>
          <el-alert
            v-if="notifyMsg"
            :title="notifyMsg"
            type="success"
            show-icon
            :closable="false"
          />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>线上报修</template>
          <el-form label-width="88px" @submit.prevent="onRepair">
            <el-form-item label="用户 ID">
              <el-input-number v-model="repairForm.userId" :min="1" />
            </el-form-item>
            <el-form-item label="问题描述">
              <el-input
                v-model="repairForm.desc"
                type="textarea"
                :rows="3"
                maxlength="255"
                show-word-limit
                placeholder="请描述不热、漏水等故障"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" native-type="submit" :loading="repairLoading">提交报修</el-button>
            </el-form-item>
          </el-form>
          <el-alert
            v-if="repairMsg"
            :title="repairMsg"
            type="success"
            show-icon
            :closable="false"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="block">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>公告</template>
          <el-timeline>
            <el-timeline-item
              v-for="item in announcements"
              :key="item.id"
              :timestamp="item.publishedAt"
            >
              <strong>{{ item.title }}</strong>
              <p>{{ item.content }}</p>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>报修记录</template>
          <el-table :data="serviceRequests" size="small">
            <el-table-column prop="id" label="单号" width="70" />
            <el-table-column prop="type" label="类型" width="80" />
            <el-table-column prop="phone" label="手机" />
            <el-table-column prop="status" label="状态" width="90" />
            <el-table-column prop="createdAt" label="时间" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { announcements, serviceRequests } from "@/mock/public.mock";
import { getStations } from "@/services/heat.api";
import { notifyStopHeating, reportRepair } from "@/services/public.api";

const stations = ref<Array<{ stationId: number; name: string }>>([]);
const notifyLoading = ref(false);
const repairLoading = ref(false);
const notifyMsg = ref("");
const repairMsg = ref("");
const notifyForm = reactive({
  stationId: 1,
  planTime: "2026-09-01 08:00",
});
const repairForm = reactive({
  userId: 1,
  desc: "",
});

async function onNotify() {
  if (!notifyForm.planTime.trim()) {
    ElMessage.error("请填写计划时间");
    return;
  }
  notifyLoading.value = true;
  try {
    const data = (await notifyStopHeating(notifyForm.stationId, notifyForm.planTime)) as Record<string, any>;
    notifyMsg.value = data.sent
      ? `已向 ${data.count} 位订阅用户发送停暖通知`
      : "未发送（无订阅用户）";
  } finally {
    notifyLoading.value = false;
  }
}

async function onRepair() {
  const desc = repairForm.desc.trim();
  if (!repairForm.userId || !desc) {
    ElMessage.error("请填写用户 ID 和问题描述");
    return;
  }
  repairLoading.value = true;
  try {
    const data = (await reportRepair(repairForm.userId, desc)) as Record<string, any>;
    repairMsg.value = `报修已受理，单号 ${data.order_id}`;
    repairForm.desc = "";
  } finally {
    repairLoading.value = false;
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
.block {
  margin-top: 16px;
}
p {
  margin: 4px 0 0;
  color: #666;
}
</style>
