/** Alarm module mock fixtures aligned with GET /api/alarm/list */

export interface AlarmMock {
  alarmId: number;
  stationId: number;
  level: number;
  levelName: string;
  type: string;
  rootCause: string;
  title: string;
  status: number;
  statusName: string;
  createdAt: string;
}

export const alarms: AlarmMock[] = [
  {
    alarmId: 1,
    stationId: 1,
    level: 4,
    levelName: "红色",
    type: "freeze",
    rootCause: "供水温度过低",
    title: "安塞区第一换热站冻堵预警",
    status: 0,
    statusName: "未确认",
    createdAt: "2026-08-31 09:12:00",
  },
  {
    alarmId: 2,
    stationId: 2,
    level: 2,
    levelName: "黄色",
    type: "corrosion",
    rootCause: "管壁减薄",
    title: "安塞区第二换热站腐蚀预警",
    status: 1,
    statusName: "已确认",
    createdAt: "2026-08-31 08:30:00",
  },
  {
    alarmId: 3,
    stationId: 3,
    level: 3,
    levelName: "橙色",
    type: "leak",
    rootCause: "压力骤降",
    title: "安塞区第三换热站疑似泄漏",
    status: 0,
    statusName: "未确认",
    createdAt: "2026-08-31 10:05:00",
  },
  {
    alarmId: 4,
    stationId: 1,
    level: 1,
    levelName: "蓝色",
    type: "balance",
    rootCause: "流量偏差",
    title: "安塞区第一换热站水力失衡",
    status: 0,
    statusName: "未确认",
    createdAt: "2026-08-31 07:40:00",
  },
];

export const stations = [
  { stationId: 1, name: "安塞区第一换热站", lng: 109.323, lat: 36.864, status: "alarm" },
  { stationId: 2, name: "安塞区第二换热站", lng: 109.331, lat: 36.871, status: "normal" },
  { stationId: 3, name: "安塞区第三换热站", lng: 109.318, lat: 36.858, status: "alarm" },
];

export function filterAlarms(level?: number, status?: number): AlarmMock[] {
  return alarms.filter((item) => {
    if (level !== undefined && item.level !== level) return false;
    if (status !== undefined && item.status !== status) return false;
    return true;
  });
}
