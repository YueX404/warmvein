import http from "./api";
import { useMock } from "./useMock";
import { recovery } from "../mock/twin.mock";

export interface RecoveryCurve {
  startTime: string;
  targetSupplyTemp: number;
  rampRate?: number;
  steps?: number;
}

export const simulateRecovery = (stationId: number, curve: RecoveryCurve) => {
  if (useMock) {
    const steps = curve.steps || 12;
    const timestamps = Array.from({ length: steps }, (_, i) => {
      const minutes = i * 30;
      const hour = 8 + Math.floor(minutes / 60);
      const minute = minutes % 60;
      return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
    });
    const target = curve.targetSupplyTemp;
    const roomTemp = timestamps.map((_, i) =>
      +(16 + ((18.2 - 16) * i) / Math.max(steps - 1, 1)).toFixed(1)
    );
    return Promise.resolve({
      ...recovery,
      stationId,
      hoursToReach: +(steps * 0.5).toFixed(1),
      tReach: `2026-08-31 ${timestamps[timestamps.length - 1]}:00`,
      converged: roomTemp[roomTemp.length - 1] >= 18,
      chart: {
        timestamps,
        supplyTemp: timestamps.map((_, i) =>
          +(20 + ((target - 20) * i) / Math.max(steps - 1, 1)).toFixed(1)
        ),
        returnTemp: timestamps.map((_, i) =>
          +(18 + ((target - 30 - 18) * i) / Math.max(steps - 1, 1)).toFixed(1)
        ),
        roomTemp,
      },
    });
  }
  return http.post("/twin/simulate/recovery", { stationId, curve });
};
