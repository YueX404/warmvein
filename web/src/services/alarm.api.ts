import axios from "axios";
import http from "./api";

export interface AlarmItem {
  alarmId: number;
  stationId: number;
  level: number;
  levelName?: string;
  type: string;
  rootCause?: string;
  title?: string;
  status: number;
  statusName?: string;
  createdAt: string;
}

export const getAlarms = (level?: number, status?: number) => {
  const params: Record<string, number> = {};
  if (typeof level === "number") params.level = level;
  if (typeof status === "number") params.status = status;
  return http.get<AlarmItem[]>("/alarm/list", { params });
};

export const ackAlarm = (alarmId: number, operator: string) =>
  http.post<{ ok: boolean; alarmId: number }>("/alarm/ack", { alarmId, operator });

export function isAlarmBackendUnreachable(err: unknown): boolean {
  if (!axios.isAxiosError(err)) return false;
  return !err.response || err.response.status >= 500;
}
