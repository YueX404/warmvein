-- ==============================================================================
-- 智能制造工业设备监控数仓建表语句
-- 分层：ODS（原始数据） → DWD（明细数据） → DWS（聚合数据） → ADS（应用数据）
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS ods;
CREATE DATABASE IF NOT EXISTS dwd;
CREATE DATABASE IF NOT EXISTS dws;
CREATE DATABASE IF NOT EXISTS ads;

-- ==============================================================================
-- ODS层：原始设备传感器数据
-- ==============================================================================
USE ods;

-- 设备传感器原始数据表（存储从Kafka采集的完整JSON记录）
-- 使用单列raw_json存储完整JSON字符串，避免依赖第三方JsonSerDe
-- 查询时使用 get_json_object(raw_json, '$.field') 提取字段
CREATE EXTERNAL TABLE IF NOT EXISTS ods.device_sensor_raw (
    raw_json STRING COMMENT '原始JSON记录字符串'
)
PARTITIONED BY (dt STRING COMMENT '日期分区 yyyy-MM-dd')
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/ods.db/device_sensor_raw';

-- 设备告警原始数据表（同样使用单列raw_json存储）
CREATE EXTERNAL TABLE IF NOT EXISTS ods.device_alarm_raw (
    raw_json STRING COMMENT '原始告警JSON记录字符串'
)
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/ods.db/device_alarm_raw';

-- ==============================================================================
-- DWD层：清洗后的设备明细数据
-- ==============================================================================
USE dwd;

-- 设备传感器明细宽表（展开params为独立字段，便于SQL查询）
CREATE TABLE IF NOT EXISTS dwd.device_sensor_detail (
    device_id STRING COMMENT '设备编号',
    device_type STRING COMMENT '设备类型',
    workshop STRING COMMENT '所属车间',
    event_time STRING COMMENT '事件时间',
    hour INT COMMENT '小时(0-23)',
    status_code INT COMMENT '设备状态编码',
    status_name STRING COMMENT '状态名称',
    spindle_speed DOUBLE COMMENT '主轴转速(rpm)',
    feed_rate DOUBLE COMMENT '进给速度(mm/min)',
    spindle_load DOUBLE COMMENT '主轴负载率(%)',
    spindle_temp DOUBLE COMMENT '主轴轴承温度(℃)',
    hydraulic_pressure DOUBLE COMMENT '液压系统压力(MPa)',
    coolant_temp DOUBLE COMMENT '冷却系统温度(℃)',
    vibration DOUBLE COMMENT '振动烈度(mm/s)',
    joint_current DOUBLE COMMENT '关节电机电流(A)',
    joint_torque DOUBLE COMMENT '关节力矩(N·m)',
    servo_temp DOUBLE COMMENT '伺服电机温度(℃)',
    reducer_temp DOUBLE COMMENT '减速器壳体温度(℃)',
    joint_vibration DOUBLE COMMENT '关节振动值(mm/s)',
    cycle_count INT COMMENT '循环计数',
    injection_pressure DOUBLE COMMENT '注射压力(MPa)',
    holding_pressure DOUBLE COMMENT '保压压力(MPa)',
    system_oil_pressure DOUBLE COMMENT '系统油压(MPa)',
    barrel_temp DOUBLE COMMENT '料筒温度(℃)',
    mold_temp DOUBLE COMMENT '模具温度(℃)',
    hydraulic_oil_temp DOUBLE COMMENT '液压油温度(℃)',
    cycle_time DOUBLE COMMENT '成型周期(s)',
    discharge_pressure DOUBLE COMMENT '排气压力(MPa)',
    discharge_temp DOUBLE COMMENT '排气温度(℃)',
    lubricant_temp DOUBLE COMMENT '润滑油温度(℃)',
    motor_current DOUBLE COMMENT '主机电机电流(A)',
    power DOUBLE COMMENT '设备总功率(kW)',
    alarm_code INT COMMENT '告警代码',
    alarm_desc STRING COMMENT '告警描述',
    health_score INT COMMENT '健康度评分',
    is_abnormal INT COMMENT '是否异常(0正常/1异常)'
)
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- ==============================================================================
-- DWS层：设备KPI聚合数据
-- ==============================================================================
USE dws;

-- 设备状态统计汇总表
CREATE TABLE IF NOT EXISTS dws.device_status_summary (
    device_id STRING COMMENT '设备编号',
    device_type STRING COMMENT '设备类型',
    workshop STRING COMMENT '所属车间',
    total_records BIGINT COMMENT '总记录数',
    run_count BIGINT COMMENT '运行状态次数',
    idle_count BIGINT COMMENT '待机状态次数',
    warning_count BIGINT COMMENT '预警状态次数',
    fault_count BIGINT COMMENT '故障状态次数',
    offline_count BIGINT COMMENT '关机状态次数',
    run_rate DECIMAL(10,4) COMMENT '运行率',
    avg_health_score DECIMAL(10,2) COMMENT '平均健康度',
    min_health_score INT COMMENT '最低健康度',
    alarm_count BIGINT COMMENT '告警次数'
)
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- 设备KPI指标汇总表（OEE/MTBF/MTTR等）
CREATE TABLE IF NOT EXISTS dws.device_kpi_summary (
    device_id STRING COMMENT '设备编号',
    device_type STRING COMMENT '设备类型',
    workshop STRING COMMENT '所属车间',
    run_time_min DECIMAL(10,2) COMMENT '运行时长(分钟)',
    planned_time_min DECIMAL(10,2) COMMENT '计划生产时长(分钟)',
    fault_time_min DECIMAL(10,2) COMMENT '故障时长(分钟)',
    fault_count INT COMMENT '故障次数',
    oee DECIMAL(10,4) COMMENT '设备综合效率',
    availability DECIMAL(10,4) COMMENT '时间稼动率',
    performance DECIMAL(10,4) COMMENT '性能稼动率',
    quality_rate DECIMAL(10,4) COMMENT '良品率',
    mtbf DECIMAL(10,2) COMMENT '平均无故障时间(小时)',
    mttr DECIMAL(10,2) COMMENT '平均修复时间(小时)',
    utilization_rate DECIMAL(10,4) COMMENT '设备稼动率'
)
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- 车间环境监测汇总表
CREATE TABLE IF NOT EXISTS dws.workshop_env_summary (
    workshop STRING COMMENT '车间名称',
    avg_temp DECIMAL(10,2) COMMENT '平均温度(℃)',
    avg_humidity DECIMAL(10,2) COMMENT '平均湿度(%RH)',
    avg_pressure DECIMAL(10,2) COMMENT '平均气压(kPa)',
    avg_noise DECIMAL(10,2) COMMENT '平均噪声(dB)',
    max_temp DECIMAL(10,2) COMMENT '最高温度(℃)',
    min_temp DECIMAL(10,2) COMMENT '最低温度(℃)'
)
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- ==============================================================================
-- ADS层：大屏应用层数据
-- ==============================================================================
USE ads;

-- 设备实时状态总览表（大屏顶部展示）
CREATE TABLE IF NOT EXISTS ads.device_overview (
    total_devices INT COMMENT '设备总数',
    online_devices INT COMMENT '在线设备数',
    running_devices INT COMMENT '运行中设备数',
    warning_devices INT COMMENT '预警设备数',
    fault_devices INT COMMENT '故障设备数',
    offline_devices INT COMMENT '离线设备数',
    online_rate DECIMAL(10,4) COMMENT '在线率',
    avg_health_score DECIMAL(10,2) COMMENT '全厂平均健康度',
    total_alarms INT COMMENT '当日告警总数',
    unhandled_alarms INT COMMENT '未处理告警数',
    factory_oee DECIMAL(10,4) COMMENT '全厂OEE',
    total_output INT COMMENT '当日总产量'
)
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- 告警类型统计表（大屏底部展示）
CREATE TABLE IF NOT EXISTS ads.alarm_type_stats (
    alarm_code INT COMMENT '告警代码',
    alarm_desc STRING COMMENT '告警描述',
    alarm_count BIGINT COMMENT '告警次数',
    device_type STRING COMMENT '设备类型',
    severity STRING COMMENT '告警等级(高/中/低)'
)
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- 设备健康度排名表
CREATE TABLE IF NOT EXISTS ads.device_health_ranking (
    device_id STRING COMMENT '设备编号',
    device_type STRING COMMENT '设备类型',
    workshop STRING COMMENT '所属车间',
    health_score INT COMMENT '健康度评分',
    run_rate DECIMAL(10,4) COMMENT '运行率',
    alarm_count INT COMMENT '告警次数',
    rul_prediction INT COMMENT '剩余使用寿命预测(%)',
    ranking INT COMMENT '健康度排名'
)
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');
