/** SMS module mock fixtures aligned with biz_sms_template seed. */

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
  errorMsg: string;
  content: string;
  createdAt: string;
};

export const templates: SmsTemplate[] = [
  {
    templateCode: "ALARM_BLUE",
    content: "【暖脉供热】{stationName}水力失衡预警(蓝色)，请关注。详情见平台。",
    scene: "alarm_blue",
    status: 1,
  },
  {
    templateCode: "ALARM_YELLOW",
    content: "【暖脉供热】{stationName}设备异常预警(黄色)，建议尽快排查。详情见平台。",
    scene: "alarm_yellow",
    status: 1,
  },
  {
    templateCode: "ALARM_ORANGE",
    content: "【暖脉供热】{stationName}严重预警(橙色)，请立即处理！详情见平台。",
    scene: "alarm_orange",
    status: 1,
  },
  {
    templateCode: "ALARM_RED",
    content: "【暖脉供热】{stationName}紧急预警(红色)，需立即到场！联系人:{leaderPhone}",
    scene: "alarm_red",
    status: 1,
  },
  {
    templateCode: "SHUTDOWN",
    content:
      "【暖脉供热】尊敬的用户，{area}将于{startTime}至{endTime}进行管道检修，届时暂停供暖，请提前做好保暖准备。",
    scene: "shutdown",
    status: 1,
  },
  {
    templateCode: "FROST",
    content: "【暖脉供热】寒潮预警，{stationName}已启动防冻模式，供水温度已提升至{tgSet}℃。",
    scene: "frost",
    status: 1,
  },
  {
    templateCode: "PUBLIC",
    content: "【暖脉供热】{message}",
    scene: "public",
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
    errorMsg: "",
    content: "【暖脉供热】一号站紧急预警，需立即到场！联系人:138****0000",
    createdAt: "2026-09-01 09:12:00",
  },
  {
    id: 2,
    batchId: "b1770000001",
    phoneMasked: "139****5678",
    templateCode: "ALARM_RED",
    status: 3,
    receipt: "",
    errorMsg: "Timeout",
    content: "【暖脉供热】一号站紧急预警，需立即到场！联系人:138****0000",
    createdAt: "2026-09-01 09:12:01",
  },
  {
    id: 3,
    batchId: "b1770000002",
    phoneMasked: "137****0000",
    templateCode: "FROST",
    status: 4,
    receipt: "",
    errorMsg: "rate limited",
    content: "【暖脉供热】寒潮预警，一号站已启动防冻模式，供水温度已提升至55℃。",
    createdAt: "2026-09-01 08:40:00",
  },
];

export function filterLogs(batchId?: string): SmsLogMock[] {
  if (!batchId) return logs;
  return logs.filter((row) => row.batchId === batchId);
}
