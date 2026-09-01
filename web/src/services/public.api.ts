import http from "./api";
import { useMock } from "./useMock";
import * as publicMock from "../mock/public.mock";

export const notifyStopHeating = (stationId: number, planTime: string) => {
  if (useMock) {
    return Promise.resolve({ ...publicMock.notifyResult, stationId, planTime });
  }
  return http.post("/public/notify/stop-heating", { stationId, planTime });
};

export const reportRepair = (userId: number, desc: string) => {
  if (useMock) {
    return Promise.resolve({
      ...publicMock.repairResult,
      order_id: publicMock.repairResult.order_id + (userId % 10),
    });
  }
  return http.post("/public/repair/report", { userId, desc });
};
