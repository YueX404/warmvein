import axios from "axios";
import http from "./api";

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

export type PatrolRule = {
  stationId: number;
  patrolType: string;
  assignee: string;
  planDate: string;
  planName?: string;
};

export type PatrolGenerateResult = {
  patrolId: number;
};

export const createWorkOrder = (alarmId: number, assignee: string) =>
  http.post("/workorder/create", { alarmId, assignee }) as Promise<{ orderId: number }>;

export const getWorkOrder = (orderId: number) =>
  http.get(`/workorder/${orderId}`) as Promise<WorkOrderRow>;

export const generatePatrolPlan = (rule: PatrolRule) =>
  http.post("/patrol/plan/generate", rule) as Promise<PatrolGenerateResult>;

export function isWorkorderBackendUnreachable(err: unknown): boolean {
  if (!axios.isAxiosError(err)) return false;
  return !err.response || err.response.status >= 500;
}
