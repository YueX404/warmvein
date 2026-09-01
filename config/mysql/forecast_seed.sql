-- Demo seed for biz_forecast. Manual only; do not merge into heat_init.sql.
-- Usage: mysql -u warmvein -p warmvein < config/mysql/forecast_seed.sql
-- Idempotent: skip a type that already has a row.

INSERT INTO biz_forecast (station_id, pipe_id, type, title, risk_level, forecast_date, description, suggestion, status)
SELECT 1, 1, 'freeze', '未来3天冻堵风险', 'high', '2026-09-02',
  '预计9月2日最低气温-12℃，供水温度偏低，有冻堵风险',
  '建议提前提升供水温度至50℃以上，增加循环泵频率',
  0
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_forecast WHERE type = 'freeze');

INSERT INTO biz_forecast (station_id, pipe_id, type, title, risk_level, forecast_date, description, suggestion, status)
SELECT 2, 2, 'lifetime', '管段剩余寿命偏低', 'medium', '2026-09-15',
  '壁厚接近下限，按当前腐蚀速率剩余寿命不足两年',
  '安排壁厚复测，必要时列入换管计划',
  0
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_forecast WHERE type = 'lifetime');

INSERT INTO biz_forecast (station_id, pipe_id, type, title, risk_level, forecast_date, description, suggestion, status)
SELECT 3, 3, 'fault', '换热站运行异常趋势', 'medium', '2026-09-03',
  '供回水温差与流量偏离历史基线，存在故障前兆',
  '核对传感器与阀门开度，必要时派单巡检',
  0
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_forecast WHERE type = 'fault');

INSERT INTO biz_forecast (station_id, pipe_id, type, title, risk_level, forecast_date, description, suggestion, status)
SELECT 4, 4, 'energy', '能效下降预报', 'low', '2026-09-10',
  '单位面积热耗连续偏高，气候补偿可能未跟上',
  '复核气候补偿曲线并检查水力平衡',
  0
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_forecast WHERE type = 'energy');
