/** SMS module mock fixtures */

export type SmsTemplate = {
  templateCode: string;
  content: string;
  scene: string;
  status: number;
};

export type SmsLogMock = {
  id: number;
  batchId: string;
  phoneMasked: string;
  templateCode: string;
  status: number;
  receipt: string;
  createdAt: string;
};

export const templates: SmsTemplate[] = [
  {
    templateCode: "ALARM_RED",
    content: "【暖脉供热】{stationName}紧急预警，需立即到场！",
    scene: "alarm_red",
    status: 1,
  },
  {
    templateCode: "SHUTDOWN",
    content: "【暖脉供热】{area}将于{startTime}停暖检修。",
    scene: "shutdown",
    status: 1,
  },
  {
    templateCode: "FROST",
    content: "【暖脉供热】寒潮预警，已启动防冻模式。",
    scene: "frost",
    status: 1,
  },
];

export const logs: SmsLogMock[] = [
  {
    id: 1,
    batchId: "b1770000001",
    phoneMasked: "138****1234",
    templateCode: "ALARM_RED",
    status: 2,
    receipt: "mock-1",
    createdAt: "2026-09-01 09:12:00",
  },
  {
    id: 2,
    batchId: "b1770000001",
    phoneMasked: "139****5678",
    templateCode: "ALARM_RED",
    status: 3,
    receipt: "",
    createdAt: "2026-09-01 09:12:01",
  },
  {
    id: 3,
    batchId: "b1770000002",
    phoneMasked: "137****0000",
    templateCode: "FROST",
    status: 4,
    receipt: "",
    createdAt: "2026-09-01 08:40:00",
  },
];

export function filterLogs(batchId?: string): SmsLogMock[] {
  if (!batchId) return logs;
  return logs.filter((row) => row.batchId === batchId);
}
