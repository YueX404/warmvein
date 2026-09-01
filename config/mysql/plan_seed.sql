-- Demo seed for biz_plan. Manual only; do not merge into heat_init.sql.
-- Usage: mysql -u warmvein -p warmvein < config/mysql/plan_seed.sql
-- Idempotent: skip a plan_type that already has an enabled row.

INSERT INTO biz_plan (name, plan_type, alarm_level, trigger_condition, steps, resource_list, status)
SELECT '冻堵应急处置预案', 'freeze', 4,
  '供回水温差异常且室外低温',
  '[{"step":1,"action":"确认冻结管段与影响用户","role":"调度值班","resource":"SCADA"},{"step":2,"action":"热源提温并加大循环流量","role":"热源厂","resource":"循环泵"},{"step":3,"action":"现场保温解冻并回访测温","role":"抢修班","resource":"移动热源车"}]',
  '["热源厂","抢修班","移动热源车"]',
  1
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_plan WHERE plan_type = 'freeze' AND status = 1);

INSERT INTO biz_plan (name, plan_type, alarm_level, trigger_condition, steps, resource_list, status)
SELECT '爆管抢修预案', 'burst', 4,
  '管段压力骤降或流量突增',
  '[{"step":1,"action":"关闭上下游阀门隔离漏点","role":"管网班","resource":"阀门井"},{"step":2,"action":"排水降压并设置警戒","role":"抢修班","resource":"抽水泵"},{"step":3,"action":"换管焊接并试压恢复","role":"焊接班","resource":"备管/焊机"}]',
  '["管网班","抢修班","焊接班"]',
  1
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_plan WHERE plan_type = 'burst' AND status = 1);

INSERT INTO biz_plan (name, plan_type, alarm_level, trigger_condition, steps, resource_list, status)
SELECT '计划停暖通知预案', 'shutdown', 2,
  '计划检修或事故停运',
  '[{"step":1,"action":"核定停暖范围与时长","role":"调度值班","resource":"调度台"},{"step":2,"action":"通知受影响小区与单位","role":"客服","resource":"短信网关"},{"step":3,"action":"降负荷停运并监护回水","role":"热源厂","resource":"热源机组"}]',
  '["调度台","客服","热源厂"]',
  1
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_plan WHERE plan_type = 'shutdown' AND status = 1);

INSERT INTO biz_plan (name, plan_type, alarm_level, trigger_condition, steps, resource_list, status)
SELECT '第三方破坏应急预案', 'third_party', 2,
  '施工占压、盗水或外力破坏',
  '[{"step":1,"action":"现场取证并通知执法","role":"巡线员","resource":"执法联络"},{"step":2,"action":"隔离受损管段保障其余供暖","role":"管网班","resource":"阀门井"},{"step":3,"action":"修复后恢复并回访","role":"抢修班","resource":"抢修车"}]',
  '["巡线员","管网班","抢修班"]',
  1
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_plan WHERE plan_type = 'third_party' AND status = 1);
