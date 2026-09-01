/** Heat module mock fixtures (Dev-1 will expand) */

export const stations = [
  { stationId: 1, name: "安塞中心站", region: "ansai", designTg: 75, designTh: 50, status: 1 },
  { stationId: 2, name: "城北站", region: "ansai", designTg: 73, designTh: 48, status: 1 },
  { stationId: 3, name: "城南站", region: "ansai", designTg: 72, designTh: 47, status: 1 },
];

export const realtime = {
  supplyTemp: 72.5,
  returnTemp: 48.3,
  pressure: 0.58,
  flow: 135.2,
  heat: 98.6,
  corrosionRate: 0.018,
  roomTemp: 20.5,
  outdoorTemp: -3.2,
};

export const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`);
export const supplyTempTrend = hours.map(() => +(68 + Math.random() * 8).toFixed(1));
export const returnTempTrend = hours.map(() => +(45 + Math.random() * 6).toFixed(1));
