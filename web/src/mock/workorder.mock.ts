/** Work order / patrol mock fixtures aligned with Task 6/7 APIs */

export type WorkOrderTrace = {
  action: string;
  operator: string;
  time: string;
};

export type WorkOrderRow = {
  orderId: number;
  alarmId: number;
  assignee: string;
  status: number;
  statusName: string;
  createdAt: string;
  updatedAt: string;
  trace: WorkOrderTrace[];
};

export type PatrolPlan = {
  patrolId: number;
  stationId: number;
  patrolType: "daily" | "special" | "emergency";
  assignee: string;
  planDate: string;
  planName: string;
};

const STATUS_NAME: Record<number, string> = {
  0: "待派",
  1: "已派",
  2: "处置中",
  3: "待核验",
  4: "已销号",
};

export const orders: WorkOrderRow[] = [
  {
    orderId: 101,
    alarmId: 1,
    assignee: "张三",
    status: 2,
    statusName: "处置中",
    createdAt: "2026-08-31 09:20:00",
    updatedAt: "2026-08-31 11:05:00",
    trace: [
      { action: "create", operator: "系统", time: "2026-08-31 09:20:00" },
      { action: "dispatch", operator: "调度", time: "2026-08-31 09:28:00" },
      { action: "arrive", operator: "张三", time: "2026-08-31 11:05:00" },
    ],
  },
  {
    orderId: 102,
    alarmId: 3,
    assignee: "李四",
    status: 1,
    statusName: "已派",
    createdAt: "2026-08-31 10:10:00",
    updatedAt: "2026-08-31 10:16:00",
    trace: [
      { action: "create", operator: "系统", time: "2026-08-31 10:10:00" },
      { action: "dispatch", operator: "调度", time: "2026-08-31 10:16:00" },
    ],
  },
];

export const patrols: PatrolPlan[] = [
  {
    patrolId: 6001,
    stationId: 1,
    patrolType: "daily",
    assignee: "王五",
    planDate: "2026-09-01",
    planName: "1#换热站日常巡检",
  },
  {
    patrolId: 6002,
    stationId: 3,
    patrolType: "special",
    assignee: "李四",
    planDate: "2026-09-02",
    planName: "3#站压力表专项",
  },
];

export function findOrder(orderId: number): WorkOrderRow | undefined {
  return orders.find((item) => item.orderId === orderId);
}

export function mockCreateOrder(alarmId: number, assignee: string): WorkOrderRow {
  const now = "2026-09-01 12:00:00";
  const order: WorkOrderRow = {
    orderId: 200 + orders.length,
    alarmId,
    assignee,
    status: 0,
    statusName: STATUS_NAME[0],
    createdAt: now,
    updatedAt: now,
    trace: [{ action: "create", operator: "系统", time: now }],
  };
  orders.push(order);
  return order;
}

export function mockGeneratePatrol(rule: {
  stationId: number;
  patrolType: PatrolPlan["patrolType"];
  assignee: string;
  planDate: string;
  planName?: string;
}): PatrolPlan {
  const plan: PatrolPlan = {
    patrolId: 7000 + patrols.length,
    stationId: rule.stationId,
    patrolType: rule.patrolType,
    assignee: rule.assignee,
    planDate: rule.planDate,
    planName: rule.planName || "auto",
  };
  patrols.push(plan);
  return plan;
}
