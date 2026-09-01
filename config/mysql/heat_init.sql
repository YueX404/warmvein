-- =============================================================================
-- 暖脉 AI 智慧供热平台 — MySQL 主数据与业务表初始化
-- 数据库: warmvein | 字符集: utf8mb4 | 引擎: InnoDB
-- 执行: mysql -u root -p < config/mysql/heat_init.sql
-- =============================================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS warmvein
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE warmvein;

-- =============================================================================
-- 主数据表 (Master Data)
-- =============================================================================

-- 热源
CREATE TABLE IF NOT EXISTS md_heat_source (
  source_id     BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '热源ID',
  name          VARCHAR(64)  NOT NULL COMMENT '热源名称',
  type          VARCHAR(16)  NOT NULL COMMENT '类型: boiler(锅炉) | heat_pump(热泵) | waste(余热)',
  capacity      DECIMAL(12,2) COMMENT '供热能力 MW',
  address       VARCHAR(128) COMMENT '地址',
  lng           DECIMAL(10,7) COMMENT '经度',
  lat           DECIMAL(10,7) COMMENT '纬度',
  status        TINYINT      NOT NULL DEFAULT 1 COMMENT '0=停用 1=运行',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_type (type),
  INDEX idx_status (status)
) ENGINE=InnoDB COMMENT='热源主数据';

-- 换热站
CREATE TABLE IF NOT EXISTS md_station (
  station_id    BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '换热站ID',
  name          VARCHAR(64)  NOT NULL COMMENT '站名',
  source_id     BIGINT       COMMENT '所属热源ID',
  area          DECIMAL(10,2) COMMENT '供热面积 万㎡',
  design_flow   DECIMAL(10,2) COMMENT '设计流量 m³/h',
  design_tg     DECIMAL(6,2)  COMMENT '设计供水温度 ℃',
  design_th     DECIMAL(6,2)  COMMENT '设计回水温度 ℃',
  address       VARCHAR(128) COMMENT '地址',
  lng           DECIMAL(10,7) COMMENT '经度',
  lat           DECIMAL(10,7) COMMENT '纬度',
  status        TINYINT      NOT NULL DEFAULT 1 COMMENT '0=停用 1=运行 2=检修',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_source (source_id),
  INDEX idx_status (status)
) ENGINE=InnoDB COMMENT='换热站主数据';

-- 管网
CREATE TABLE IF NOT EXISTS md_pipe (
  pipe_id       BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '管段ID',
  name          VARCHAR(64)  COMMENT '管段名称',
  station_id    BIGINT       COMMENT '所属换热站',
  pipe_type     VARCHAR(16)  NOT NULL COMMENT 'primary(一次网) | secondary(二次网) | branch(支干) | user(支线)',
  material      VARCHAR(16)  COMMENT '材质: steel | pe | pp',
  diameter      DECIMAL(8,2)  COMMENT '管径 mm',
  length_m      DECIMAL(10,2) COMMENT '长度 m',
  install_year  INT           COMMENT '安装年份',
  insulation    VARCHAR(16)  COMMENT '保温等级: good | medium | poor | none',
  design_flow   DECIMAL(10,2) COMMENT '设计流量 m³/h',
  k_value       DECIMAL(8,4)  COMMENT '传热系数 W/(m²·℃)',
  min_wall      DECIMAL(6,2)  COMMENT '最小允许壁厚 mm',
  lng_start     DECIMAL(10,7) COMMENT '起点经度',
  lat_start     DECIMAL(10,7) COMMENT '起点纬度',
  lng_end       DECIMAL(10,7) COMMENT '终点经度',
  lat_end       DECIMAL(10,7) COMMENT '终点纬度',
  status        TINYINT      NOT NULL DEFAULT 1 COMMENT '0=停用 1=运行 2=检修',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_station (station_id),
  INDEX idx_type (pipe_type),
  INDEX idx_status (status)
) ENGINE=InnoDB COMMENT='管段主数据';

-- 传感器
CREATE TABLE IF NOT EXISTS md_sensor (
  sensor_id     BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '传感器ID',
  station_id    BIGINT       COMMENT '所属换热站',
  pipe_id       BIGINT       COMMENT '所属管段',
  sensor_type   VARCHAR(32)  NOT NULL COMMENT '类型: temp(温度) | pressure(压力) | flow(流量) | heat(热量) | corrosion(腐蚀) | room_temp(室温)',
  model         VARCHAR(32)  COMMENT '型号',
  install_date  DATE          COMMENT '安装日期',
  calibration_due DATE        COMMENT '下次校准日期',
  status        TINYINT      NOT NULL DEFAULT 1 COMMENT '0=停用 1=正常 2=异常 3=离线',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_station (station_id),
  INDEX idx_pipe (pipe_id),
  INDEX idx_type (sensor_type),
  INDEX idx_status (status)
) ENGINE=InnoDB COMMENT='传感器主数据';

-- 用户（供热用户/住户）
CREATE TABLE IF NOT EXISTS md_user (
  user_id       BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
  house_no      VARCHAR(32)  COMMENT '户号',
  address       VARCHAR(128) COMMENT '地址',
  phone         VARCHAR(20)  COMMENT '手机号(明文存储，查询脱敏)',
  station_id    BIGINT       COMMENT '所属换热站',
  area          DECIMAL(8,2)  COMMENT '建筑面积 ㎡',
  sms_subscribe TINYINT      NOT NULL DEFAULT 1 COMMENT '0=未订阅 1=已订阅短信',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_station (station_id),
  INDEX idx_phone (phone),
  INDEX idx_subscribe (sms_subscribe)
) ENGINE=InnoDB COMMENT='供热用户';

-- 组织架构
CREATE TABLE IF NOT EXISTS md_organization (
  org_id        BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '组织ID',
  name          VARCHAR(64)  NOT NULL COMMENT '组织名称',
  parent_id     BIGINT       COMMENT '上级组织ID',
  org_type      VARCHAR(16)  NOT NULL COMMENT 'company(公司) | dept(部门) | team(班组)',
  leader        VARCHAR(32)  COMMENT '负责人',
  phone         VARCHAR(20)  COMMENT '联系电话',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_parent (parent_id)
) ENGINE=InnoDB COMMENT='组织架构';


-- =============================================================================
-- 业务表 (Business)
-- =============================================================================

-- 预警记录
CREATE TABLE IF NOT EXISTS biz_alarm (
  alarm_id      BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '预警ID',
  station_id    BIGINT       NOT NULL COMMENT '关联换热站',
  pipe_id       BIGINT       COMMENT '关联管段(可选)',
  level         TINYINT      NOT NULL COMMENT '级别: 1=蓝(轻微) 2=黄(1-3月) 3=橙(1月内) 4=红(72h内)',
  type          VARCHAR(32)  NOT NULL COMMENT '类型: freeze(冻堵) | leak(泄漏) | corrosion(腐蚀) | pressure(压力) | balance(失衡) | theft(偷热) | other',
  root_cause    VARCHAR(32)  COMMENT '根因标签',
  title         VARCHAR(128) COMMENT '预警标题',
  description   TEXT          COMMENT '预警描述',
  status        TINYINT      NOT NULL DEFAULT 0 COMMENT '0=未确认 1=已确认 2=已处置 3=已关闭',
  operator      VARCHAR(32)  COMMENT '确认人',
  ack_at        DATETIME     COMMENT '确认时间',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_station (station_id),
  INDEX idx_level (level),
  INDEX idx_status (status),
  INDEX idx_created (created_at)
) ENGINE=InnoDB COMMENT='预警记录';

-- 预报记录
CREATE TABLE IF NOT EXISTS biz_forecast (
  forecast_id   BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '预报ID',
  station_id    BIGINT       COMMENT '关联换热站',
  pipe_id       BIGINT       COMMENT '关联管段',
  type          VARCHAR(32)  NOT NULL COMMENT '类型: freeze(冻堵) | lifetime(寿命) | fault(故障) | energy(能效)',
  title         VARCHAR(128) COMMENT '预报标题',
  risk_level    VARCHAR(16)  COMMENT '风险等级: high | medium | low',
  forecast_date DATE          COMMENT '预报目标日期',
  description   TEXT          COMMENT '预报内容',
  suggestion    TEXT          COMMENT '建议措施',
  status        TINYINT      NOT NULL DEFAULT 0 COMMENT '0=待查看 1=已查看 2=已处置',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_station (station_id),
  INDEX idx_type (type),
  INDEX idx_date (forecast_date)
) ENGINE=InnoDB COMMENT='预报记录';

-- 工单
CREATE TABLE IF NOT EXISTS biz_work_order (
  order_id      BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '工单ID',
  alarm_id      BIGINT       COMMENT '触发预警ID',
  title         VARCHAR(128) COMMENT '工单标题',
  description   TEXT          COMMENT '工单描述',
  order_type    VARCHAR(16)  NOT NULL COMMENT 'repair(维修) | patrol(巡检) | emergency(应急)',
  priority      TINYINT      NOT NULL DEFAULT 2 COMMENT '优先级: 1=高 2=中 3=低',
  assignee      VARCHAR(32)  COMMENT '负责人',
  station_id    BIGINT       COMMENT '关联换热站',
  status        TINYINT      NOT NULL DEFAULT 0 COMMENT '0=待派 1=已派 2=处置中 3=待核验 4=已销号',
  due_at        DATETIME     COMMENT '截止时间',
  closed_at     DATETIME     COMMENT '关闭时间',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_alarm (alarm_id),
  INDEX idx_assignee (assignee),
  INDEX idx_status (status),
  INDEX idx_created (created_at)
) ENGINE=InnoDB COMMENT='工单';

-- 工单操作轨迹
CREATE TABLE IF NOT EXISTS biz_work_order_trace (
  trace_id      BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '轨迹ID',
  order_id      BIGINT       NOT NULL COMMENT '工单ID',
  action        VARCHAR(32)  NOT NULL COMMENT '操作: create | assign | accept | process | review | close | escalate',
  operator      VARCHAR(32)  NOT NULL COMMENT '操作人',
  remark        TEXT          COMMENT '备注',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_order (order_id)
) ENGINE=InnoDB COMMENT='工单操作轨迹';

-- 巡检计划
CREATE TABLE IF NOT EXISTS biz_patrol (
  patrol_id     BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '巡检ID',
  station_id    BIGINT       COMMENT '关联换热站',
  plan_name     VARCHAR(64)  COMMENT '计划名称',
  patrol_type   VARCHAR(16)  NOT NULL COMMENT 'daily(日常) | special(专项) | emergency(应急)',
  assignee      VARCHAR(32)  COMMENT '巡检人',
  plan_date     DATE          COMMENT '计划日期',
  status        TINYINT      NOT NULL DEFAULT 0 COMMENT '0=待执行 1=执行中 2=已完成 3=已取消',
  route_points  TEXT          COMMENT '巡检路线点位(JSON)',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_station (station_id),
  INDEX idx_date (plan_date),
  INDEX idx_status (status)
) ENGINE=InnoDB COMMENT='巡检计划';

-- 预案
CREATE TABLE IF NOT EXISTS biz_plan (
  plan_id       BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '预案ID',
  name          VARCHAR(64)  NOT NULL COMMENT '预案名称',
  plan_type     VARCHAR(32)  NOT NULL COMMENT 'freeze(冻堵) | burst(爆管) | shutdown(停暖) | third_party(第三方破坏)',
  alarm_level   TINYINT      COMMENT '匹配预警级别',
  trigger_condition TEXT     COMMENT '触发条件描述',
  steps         TEXT          COMMENT '处置步骤(JSON: [{step, action, role, resource}])',
  resource_list TEXT          COMMENT '所需资源(JSON)',
  status        TINYINT      NOT NULL DEFAULT 1 COMMENT '0=停用 1=启用',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_type (plan_type),
  INDEX idx_level (alarm_level)
) ENGINE=InnoDB COMMENT='应急预案';

-- 预案执行记录
CREATE TABLE IF NOT EXISTS biz_plan_execution (
  exec_id       BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '执行ID',
  plan_id       BIGINT       NOT NULL COMMENT '预案ID',
  alarm_id      BIGINT       COMMENT '触发预警ID',
  operator      VARCHAR(32)  COMMENT '启动人',
  status        TINYINT      NOT NULL DEFAULT 0 COMMENT '0=启动中 1=执行中 2=已完成 3=已终止',
  started_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '启动时间',
  finished_at   DATETIME     COMMENT '完成时间',
  remark        TEXT          COMMENT '执行备注',
  INDEX idx_plan (plan_id),
  INDEX idx_alarm (alarm_id)
) ENGINE=InnoDB COMMENT='预案执行记录';

-- 短信模板
CREATE TABLE IF NOT EXISTS biz_sms_template (
  template_code VARCHAR(32)  PRIMARY KEY COMMENT '模板编码',
  content       VARCHAR(256) NOT NULL COMMENT '模板内容(支持{var}占位)',
  scene         VARCHAR(32)  NOT NULL COMMENT '场景: alarm_blue | alarm_yellow | alarm_orange | alarm_red | shutdown | frost | public | custom',
  status        TINYINT      NOT NULL DEFAULT 1 COMMENT '0=停用 1=启用',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='短信模板';

-- 短信发送记录
CREATE TABLE IF NOT EXISTS biz_sms_log (
  id            BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
  batch_id      VARCHAR(32)  NOT NULL COMMENT '批次ID',
  phone_masked  VARCHAR(20)  NOT NULL COMMENT '手机号(脱敏)',
  template_code VARCHAR(32)  COMMENT '使用的模板编码',
  content       VARCHAR(256) COMMENT '实际发送内容',
  status        TINYINT      NOT NULL DEFAULT 0 COMMENT '0=待发送 1=发送中 2=成功 3=失败 4=限流跳过',
  receipt       VARCHAR(64)  COMMENT '网关回执ID',
  error_msg     VARCHAR(128) COMMENT '失败原因',
  retry_count   TINYINT      NOT NULL DEFAULT 0 COMMENT '重试次数',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_batch (batch_id),
  INDEX idx_status (status),
  INDEX idx_created (created_at)
) ENGINE=InnoDB COMMENT='短信发送记录';

-- 换热站控制指令
CREATE TABLE IF NOT EXISTS biz_console_action (
  action_id     BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '指令ID',
  station_id    BIGINT       NOT NULL COMMENT '目标换热站',
  action_type   VARCHAR(16)  NOT NULL COMMENT 'climate(气候补偿) | manual(手动调节)',
  tg_set        DECIMAL(6,2) COMMENT '供水温度设定 ℃',
  th_set        DECIMAL(6,2) COMMENT '回水温度设定 ℃',
  tw            DECIMAL(5,2) COMMENT '室外温度 ℃',
  pump_speed    DECIMAL(5,2) COMMENT '循环泵频率 Hz',
  valve_opening DECIMAL(5,2) COMMENT '阀门开度 %',
  status        TINYINT      NOT NULL DEFAULT 0 COMMENT '0=待下发 1=已下发 2=执行成功 3=执行失败',
  operator      VARCHAR(32)  COMMENT '操作人',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  executed_at   DATETIME     COMMENT '执行时间',
  INDEX idx_station (station_id),
  INDEX idx_status (status),
  INDEX idx_created (created_at)
) ENGINE=InnoDB COMMENT='换热站控制指令';


-- =============================================================================
-- 初始化数据
-- =============================================================================

-- 短信模板
INSERT INTO biz_sms_template (template_code, content, scene) VALUES
  ('ALARM_BLUE',  '【暖脉供热】{stationName}水力失衡预警(蓝色)，请关注。详情见平台。', 'alarm_blue'),
  ('ALARM_YELLOW','【暖脉供热】{stationName}设备异常预警(黄色)，建议尽快排查。详情见平台。', 'alarm_yellow'),
  ('ALARM_ORANGE','【暖脉供热】{stationName}严重预警(橙色)，请立即处理！详情见平台。', 'alarm_orange'),
  ('ALARM_RED',   '【暖脉供热】{stationName}紧急预警(红色)，需立即到场！联系人:{leaderPhone}', 'alarm_red'),
  ('SHUTDOWN',    '【暖脉供热】尊敬的用户，{area}将于{startTime}至{endTime}进行管道检修，届时暂停供暖，请提前做好保暖准备。', 'shutdown'),
  ('FROST',       '【暖脉供热】寒潮预警，{stationName}已启动防冻模式，供水温度已提升至{tgSet}℃。', 'frost'),
  ('PUBLIC',      '【暖脉供热】{message}', 'public');
