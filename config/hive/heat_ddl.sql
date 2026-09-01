-- =============================================================================
-- 暖脉 AI 智慧供热平台 — Hive 数仓分层 DDL
-- 数仓: ODS(贴源) → DWD(明细) → DWS(汇总) → ADS(应用)
-- 执行: hive -f config/hive/heat_ddl.sql
-- 注意: 本文件为供热专用 DDL，原有的 hive_ddl.sql 保留为工业模板
-- =============================================================================

-- =============================================================================
-- 创建数据库
-- =============================================================================
CREATE DATABASE IF NOT EXISTS ods COMMENT 'ODS 贴源层';
CREATE DATABASE IF NOT EXISTS dwd COMMENT 'DWD 明细层';
CREATE DATABASE IF NOT EXISTS dws COMMENT 'DWS 汇总层';
CREATE DATABASE IF NOT EXISTS ads COMMENT 'ADS 应用层';


-- =============================================================================
-- ODS 层 — 原始数据贴源
-- =============================================================================

-- 供热传感器原始 JSON（Kafka → Logstash → 本表 / Kafka → Spark → 本表）
CREATE TABLE IF NOT EXISTS ods.heat_sensor_raw (
  raw_json    STRING COMMENT '完整 JSON 记录'
) COMMENT '供热传感器原始数据'
PARTITIONED BY (dt STRING COMMENT '日期分区 yyyy-MM-dd')
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/ods.db/heat_sensor_raw';


-- =============================================================================
-- DWD 层 — 清洗展开明细
-- =============================================================================

-- 供热传感器明细（从 raw_json 展开字段）
CREATE TABLE IF NOT EXISTS dwd.heat_sensor_detail (
  sensor_id       STRING    COMMENT '传感器ID',
  station_id      STRING    COMMENT '换热站ID',
  station_name    STRING    COMMENT '换热站名称',
  pipe_id         STRING    COMMENT '管段ID',
  device_type     STRING    COMMENT '设备类型: heat_source|station|pipe|user',
  event_time      STRING    COMMENT '采集时间',
  hour            INT       COMMENT '小时(0-23)',

  -- 温度
  supply_temp     DOUBLE    COMMENT '供水温度 ℃',
  return_temp     DOUBLE    COMMENT '回水温度 ℃',
  room_temp       DOUBLE    COMMENT '室温 ℃',
  outdoor_temp    DOUBLE    COMMENT '室外温度 ℃',

  -- 压力
  pressure        DOUBLE    COMMENT '管网压力 MPa',

  -- 流量
  flow_rate       DOUBLE    COMMENT '流量 m³/h',

  -- 热量
  heat_energy     DOUBLE    COMMENT '热量 GJ',

  -- 腐蚀
  corrosion_rate  DOUBLE    COMMENT '腐蚀速率 mm/年',
  wall_thickness  DOUBLE    COMMENT '当前壁厚 mm',

  -- 水力
  velocity        DOUBLE    COMMENT '流速 m/s',

  -- 健康与告警
  health_score    INT       COMMENT '健康评分(0-100)',
  alarm_code      INT       COMMENT '告警码(0=正常)',
  alarm_desc      STRING    COMMENT '告警描述',
  is_abnormal     INT       COMMENT '是否异常(0/1)'
) COMMENT '供热传感器明细'
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');


-- =============================================================================
-- DWS 层 — 业务汇总
-- =============================================================================

-- 换热站级日汇总（平衡度、热损耗、能耗）
CREATE TABLE IF NOT EXISTS dws.heat_station_summary (
  station_id          STRING    COMMENT '换热站ID',
  station_name        STRING    COMMENT '站名',
  total_records       BIGINT    COMMENT '当日采集记录数',

  -- 温度统计
  avg_supply_temp     DOUBLE    COMMENT '平均供水温度 ℃',
  avg_return_temp     DOUBLE    COMMENT '平均回水温度 ℃',
  avg_room_temp       DOUBLE    COMMENT '平均室温 ℃',
  max_supply_temp     DOUBLE    COMMENT '最高供水温度 ℃',
  min_supply_temp     DOUBLE    COMMENT '最低供水温度 ℃',

  -- 压力流量
  avg_pressure        DOUBLE    COMMENT '平均压力 MPa',
  avg_flow_rate       DOUBLE    COMMENT '平均流量 m³/h',

  -- 水力平衡
  avg_beta            DOUBLE    COMMENT '平均平衡度',
  unbalanced_count    INT       COMMENT '失衡支路数',
  imbalance_ratio     DOUBLE    COMMENT '失衡率(%)',

  -- 热损耗
  total_heat_loss     DOUBLE    COMMENT '总热损耗 W',
  avg_heat_loss_rate  DOUBLE    COMMENT '平均热损耗率(%)',

  -- 能耗
  total_heat_energy   DOUBLE    COMMENT '总供热量 GJ',
  unit_energy         DOUBLE    COMMENT '单位面积能耗 GJ/㎡',

  -- 运行
  online_hours        DOUBLE    COMMENT '在线时长(h)',
  alarm_count         INT       COMMENT '告警次数',
  avg_health_score    DOUBLE    COMMENT '平均健康评分'
) COMMENT '换热站日汇总'
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');


-- 管段级日汇总（腐蚀、壁厚、热损）
CREATE TABLE IF NOT EXISTS dws.heat_pipe_summary (
  pipe_id             STRING    COMMENT '管段ID',
  pipe_name           STRING    COMMENT '管段名称',
  station_id          STRING    COMMENT '所属换热站',
  pipe_type           STRING    COMMENT '管段类型',
  total_records       BIGINT    COMMENT '采集记录数',

  -- 腐蚀
  avg_corrosion_rate  DOUBLE    COMMENT '平均腐蚀速率 mm/年',
  max_corrosion_rate  DOUBLE    COMMENT '最大腐蚀速率 mm/年',
  avg_wall_thickness  DOUBLE    COMMENT '平均壁厚 mm',
  min_wall_thickness  DOUBLE    COMMENT '最小壁厚 mm',

  -- 热损耗
  avg_heat_loss       DOUBLE    COMMENT '平均热损耗 W',
  total_heat_loss     DOUBLE    COMMENT '总热损耗 W·h',

  -- 温度
  avg_supply_temp     DOUBLE    COMMENT '平均供水温度 ℃',
  avg_return_temp     DOUBLE    COMMENT '平均回水温度 ℃',

  -- 寿命
  remain_life_year    DOUBLE    COMMENT '预测剩余寿命(年)',

  -- 运行
  alarm_count         INT       COMMENT '告警次数',
  avg_health_score    DOUBLE    COMMENT '平均健康评分'
) COMMENT '管段日汇总'
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');


-- =============================================================================
-- ADS 层 — 应用大屏
-- =============================================================================

-- 供热总览（指挥大屏核心指标）
CREATE TABLE IF NOT EXISTS ads.heat_overview (
  total_stations      INT       COMMENT '换热站总数',
  online_stations     INT       COMMENT '在线站数',
  running_stations    INT       COMMENT '运行站数',
  fault_stations      INT       COMMENT '故障站数',
  offline_stations    INT       COMMENT '离线站数',
  online_rate         DOUBLE    COMMENT '在线率(%)',

  total_pipes         INT       COMMENT '管段总数',
  warning_pipes       INT       COMMENT '预警管段数',

  total_users         INT       COMMENT '用户总数',

  avg_supply_temp     DOUBLE    COMMENT '全网平均供水温度 ℃',
  avg_return_temp     DOUBLE    COMMENT '全网平均回水温度 ℃',
  avg_room_temp       DOUBLE    COMMENT '全网平均室温 ℃',
  avg_pressure        DOUBLE    COMMENT '全网平均压力 MPa',

  total_heat_energy   DOUBLE    COMMENT '总供热量 GJ',
  total_heat_loss     DOUBLE    COMMENT '总热损耗 GJ',
  heat_loss_rate      DOUBLE    COMMENT '热损耗率(%)',

  total_alarms        INT       COMMENT '今日告警总数',
  unhandled_alarms    INT       COMMENT '未处置告警数',
  alarm_blue          INT       COMMENT '蓝色预警数',
  alarm_yellow        INT       COMMENT '黄色预警数',
  alarm_orange        INT       COMMENT '橙色预警数',
  alarm_red           INT       COMMENT '红色预警数',

  avg_health_score    DOUBLE    COMMENT '全网平均健康评分'
) COMMENT '供热大屏总览'
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');


-- 告警统计
CREATE TABLE IF NOT EXISTS ads.heat_alarm_stats (
  alarm_type          STRING    COMMENT '告警类型',
  alarm_level         INT       COMMENT '告警级别 1-4',
  alarm_count         INT       COMMENT '告警次数',
  station_count       INT       COMMENT '涉及站数',
  avg_resolve_time    DOUBLE    COMMENT '平均处置时长(分钟)',
  top_station         STRING    COMMENT '告警最多的站'
) COMMENT '告警类型统计'
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');
