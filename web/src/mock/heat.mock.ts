/** Heat module mock fixtures — shapes match /api/heat/* data envelopes. */

export const stations = [
  {
    stationId: 1,
    name: "安塞中心站",
    region: "ansai",
    sourceId: 1,
    area: 12.5,
    designTg: 75,
    designTh: 50,
    address: "安塞区中心换热站",
    lng: 109.3205,
    lat: 36.8652,
    status: 1,
    supplyTemp: 72.5,
    returnTemp: 48.3,
    pressure: 0.58,
  },
  {
    stationId: 2,
    name: "城北站",
    region: "ansai",
    sourceId: 1,
    area: 11.8,
    designTg: 73,
    designTh: 48,
    address: "安塞区城北换热站",
    lng: 109.3252,
    lat: 36.8621,
    status: 1,
    supplyTemp: 71.2,
    returnTemp: 47.8,
    pressure: 0.55,
  },
  {
    stationId: 3,
    name: "城南站",
    region: "ansai",
    sourceId: 2,
    area: 13.2,
    designTg: 72,
    designTh: 47,
    address: "安塞区城南换热站",
    lng: 109.3183,
    lat: 36.8681,
    status: 1,
    supplyTemp: 70.8,
    returnTemp: 46.9,
    pressure: 0.61,
  },
];

export const realtime = {
  stationId: 1,
  stationName: "安塞中心站",
  supplyTemp: 72.5,
  returnTemp: 48.3,
  tempDiff: 24.2,
  pressure: 0.58,
  flowRate: 135.2,
  heatEnergy: 3.25,
  corrosionRate: 0.018,
  wallThickness: 8.5,
  roomTemp: 20.5,
  outdoorTemp: -3.2,
  velocity: 1.2,
  healthScore: 87,
  frostRisk: "low",
  userAbnormals: [] as Array<{ userId: number; status: string }>,
  eventTime: "2026-08-31 14:30:00",
};

export const balance = {
  stationId: 1,
  branches: [
    {
      branchId: "1",
      branchName: "北区支路",
      actualFlow: 45.2,
      designFlow: 48.0,
      beta: 0.942,
      unbalanced: false,
      suggestOpen: 5.8,
    },
    {
      branchId: "2",
      branchName: "南区支路",
      actualFlow: 30.1,
      designFlow: 40.0,
      beta: 0.753,
      unbalanced: true,
      suggestOpen: 24.7,
    },
    {
      branchId: "3",
      branchName: "东区支路",
      actualFlow: 52.0,
      designFlow: 50.0,
      beta: 1.04,
      unbalanced: false,
      suggestOpen: -4.0,
    },
  ],
  unbalancedCount: 1,
};

export const energy = {
  date: "2026-08-31",
  totalHeatEnergy: 1250.5,
  totalHeatLoss: 150.3,
  heatLossRate: 12.0,
  unitEnergy: 0.42,
  avgRoomTemp: 21.5,
  energySavingRate: 8.3,
  carbonReduction: 2.1,
};

export const climateResult = {
  stationId: 1,
  tw: -5.0,
  TgSet: 66.6,
  thSet: 41.6,
  actionId: 1001,
  status: 0,
};

export const hours = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, "0")}:00`);
export const supplyTempTrend = hours.map((_, i) => +(70 + Math.sin(i / 3.5) * 3.2).toFixed(1));
export const returnTempTrend = hours.map((_, i) => +(47 + Math.sin(i / 3.5 + 0.4) * 2.1).toFixed(1));
