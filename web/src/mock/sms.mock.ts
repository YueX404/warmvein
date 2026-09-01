/** SMS module mock fixtures */

export const templates = [
  { templateCode: "ALARM_RED", content: "【暖脉供热】{stationName}紧急预警，需立即到场！", scene: "alarm_red", status: 1 },
  { templateCode: "SHUTDOWN", content: "【暖脉供热】{area}将于{startTime}停暖检修。", scene: "shutdown", status: 1 },
  { templateCode: "FROST", content: "【暖脉供热】寒潮预警，已启动防冻模式。", scene: "frost", status: 1 },
];
