import http from "./api";
import { useMock } from "./useMock";
import * as heatMock from "../mock/heat.mock";

export const getStations = (region?: string) => {
  if (useMock) {
    return Promise.resolve({ stations: heatMock.stations });
  }
  return http.get("/heat/stations", { params: { region } });
};

export const getRealtime = (id: number) => {
  if (useMock) {
    const station = heatMock.stations.find((s) => s.stationId === id) || heatMock.stations[0];
    return Promise.resolve({
      ...heatMock.realtime,
      stationId: station.stationId,
      stationName: station.name,
      supplyTemp: station.supplyTemp,
      returnTemp: station.returnTemp,
      pressure: station.pressure,
      tempDiff: +(station.supplyTemp - station.returnTemp).toFixed(1),
    });
  }
  return http.get(`/heat/station/${id}/realtime`);
};

export const getBalance = (stationId: number) => {
  if (useMock) {
    return Promise.resolve({ ...heatMock.balance, stationId });
  }
  return http.get("/heat/balance", { params: { stationId } });
};

export const getEnergy = (date: string, region?: string) => {
  if (useMock) {
    return Promise.resolve({ ...heatMock.energy, date });
  }
  return http.get("/heat/energy", { params: { date, region } });
};

export const climateCompensate = (stationId: number, tw: number) => {
  if (useMock) {
    const tgSet = +(66.6 + (tw + 5) * -0.8).toFixed(1);
    return Promise.resolve({
      ...heatMock.climateResult,
      stationId,
      tw,
      TgSet: tgSet,
      thSet: +(tgSet - 25).toFixed(1),
    });
  }
  return http.post("/console/climate-compensate", { stationId, tw });
};
