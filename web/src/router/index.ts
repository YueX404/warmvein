import { createRouter, createWebHistory } from "vue-router";

const routes = [
  { path: "/", redirect: "/heat" },
  {
    path: "/heat",
    name: "HeatDashboard",
    component: () => import("@/pages/heat/Dashboard.vue"),
  },
  {
    path: "/twin",
    name: "TwinRecovery",
    component: () => import("@/pages/twin/Recovery.vue"),
  },
  {
    path: "/public",
    name: "PublicService",
    component: () => import("@/pages/public/Service.vue"),
  },
  {
    path: "/alarm",
    name: "AlarmMap",
    component: () => import("@/pages/alarm/AlarmMap.vue"),
  },
  {
    path: "/workorder",
    name: "WorkOrder",
    component: () => import("@/pages/workorder/WorkOrder.vue"),
  },
  {
    path: "/plan",
    name: "PlanManage",
    component: () => import("@/pages/plan/PlanManage.vue"),
  },
  {
    path: "/sms",
    name: "SmsTemplate",
    component: () => import("@/pages/sms/TemplateManage.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
