/** Twin module mock fixtures — shape matches POST /api/twin/simulate/recovery data. */

const timestamps = Array.from({ length: 12 }, (_, i) => `${String(8 + Math.floor(i / 2)).padStart(2, "0")}:${i % 2 === 0 ? "00" : "30"}`);

export const recovery = {
  stationId: 1,
  tReach: "2026-08-31 14:30:00",
  hoursToReach: 6.5,
  converged: true,
  chart: {
    timestamps,
    supplyTemp: timestamps.map((_, i) => +(20 + i * 3.8).toFixed(1)),
    returnTemp: timestamps.map((_, i) => +(18 + i * 2.4).toFixed(1)),
    roomTemp: timestamps.map((_, i) => +(16 + i * 0.22).toFixed(1)),
  },
};
