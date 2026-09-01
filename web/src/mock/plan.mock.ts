/** Plan module mock fixtures */

export type PlanStep = {
  step: number;
  action: string;
  role: string;
  resource: string;
};

export const plans = [
  {
    planId: 1,
    name: "冻堵应急处置预案",
    planType: "freeze",
    alarmLevel: 4,
    status: 1,
    triggerCondition: "供回水温差异常且室外低温",
    steps: [
      { step: 1, action: "确认冻结管段与影响用户", role: "调度值班", resource: "SCADA" },
      { step: 2, action: "热源提温并加大循环流量", role: "热源厂", resource: "循环泵" },
      { step: 3, action: "现场保温解冻并回访测温", role: "抢修班", resource: "移动热源车" },
    ] as PlanStep[],
    resourceList: ["热源厂", "抢修班", "移动热源车"],
  },
  {
    planId: 2,
    name: "爆管抢修预案",
    planType: "burst",
    alarmLevel: 4,
    status: 1,
    triggerCondition: "管段压力骤降或流量突增",
    steps: [
      { step: 1, action: "关闭上下游阀门隔离漏点", role: "管网班", resource: "阀门井" },
      { step: 2, action: "排水降压并设置警戒", role: "抢修班", resource: "抽水泵" },
      { step: 3, action: "换管焊接并试压恢复", role: "焊接班", resource: "备管/焊机" },
    ] as PlanStep[],
    resourceList: ["管网班", "抢修班", "焊接班"],
  },
  {
    planId: 3,
    name: "计划停暖通知预案",
    planType: "shutdown",
    alarmLevel: 2,
    status: 1,
    triggerCondition: "计划检修或事故停运",
    steps: [
      { step: 1, action: "核定停暖范围与时长", role: "调度值班", resource: "调度台" },
      { step: 2, action: "通知受影响小区与单位", role: "客服", resource: "短信网关" },
      { step: 3, action: "降负荷停运并监护回水", role: "热源厂", resource: "热源机组" },
    ] as PlanStep[],
    resourceList: ["调度台", "客服", "热源厂"],
  },
  {
    planId: 4,
    name: "第三方破坏应急预案",
    planType: "third_party",
    alarmLevel: 2,
    status: 1,
    triggerCondition: "施工占压、盗水或外力破坏",
    steps: [
      { step: 1, action: "现场取证并通知执法", role: "巡线员", resource: "执法联络" },
      { step: 2, action: "隔离受损管段保障其余供暖", role: "管网班", resource: "阀门井" },
      { step: 3, action: "修复后恢复并回访", role: "抢修班", resource: "抢修车" },
    ] as PlanStep[],
    resourceList: ["巡线员", "管网班", "抢修班"],
  },
];
