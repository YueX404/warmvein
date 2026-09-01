import http from "./api";

export type PlanRow = {
  plan_id: number | null;
  name?: string;
  plan_type: string;
  alarm_level?: number | null;
  trigger_condition?: string;
  steps?: string;
  resource_list?: string;
  status?: number;
};

export type ActivateResult = {
  ok: boolean;
  execId: number;
};

export const matchPlan = (alarmType: string, level = 2) =>
  http.post("/plan/match", { alarmType, level }) as Promise<PlanRow>;

export const activatePlan = (planId: number, alarmId?: number, operator = "") =>
  http.post("/plan/activate", { planId, alarmId, operator }) as Promise<ActivateResult>;
