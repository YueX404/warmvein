# Changelog

本文件记录暖脉 AI 智慧供热平台的所有重要变更。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

---

## [Unreleased]

### 新增
- 安塞区城市安全生命线管网 AI 智慧平台项目启动
- 基于工业设备监控模板（FastAPI + Kafka + Spark + Hive + ES + sklearn + ECharts）构建脚手架
- 供热核心闭环设计（需求→设计→功能→任务拆分→实现计划）

---

## [0.1.0] - 2026-08-31

### 项目初始化

#### 代码骨架
- `src/python/main.py` — FastAPI 服务入口（7 模块路由挂载点）
- `src/python/config/settings.py` — 环境变量配置（待改造）
- `src/python/db.py` — MySQL 引擎 + Redis 客户端（待改造）
- `src/python/kafka_topics.py` — Topic 常量（待改造）
- `src/python/response.py` — 统一响应 `ok/fail`
- `src/python/generate_logs.py` — 模拟数据生成（工业模板）
- `src/python/kafka_producer.py` — Kafka 生产者（工业模板）
- `src/python/spark_analysis.py` — Spark 离线分析（工业模板）
- `src/python/train_sklearn_model.py` — ML 模型训练（工业模板）

#### Docker 集群
- `docker/docker-compose.yml` — 12 服务编排（ZK/Kafka/Hadoop/Hive/ES/Logstash/Kibana/Spark）
- `docker/lib/postgresql-42.7.4.jar` — PostgreSQL JDBC 驱动
- `docker/lib/guava-27.0-jre.jar` — Hadoop 依赖

#### 数据配置
- `config/hive/hive_ddl.sql` — 工业设备数仓 DDL（ODS/DWD/DWS/ADS 8 张表）
- `config/hive/hive-site.xml` — Hive 配置
- `config/logstash/kafka_to_es.conf` — Logstash Kafka→ES 管道

#### 运维脚本
- `scripts/start_cluster.sh` — 集群启动 + 健康检查
- `scripts/stop_cluster.sh` — 集群停止
- `scripts/start_project.sh` — 一键全流程启动
- `scripts/load_data_to_hive.sh` — JSON→Hive ODS 加载
- `scripts/etl_daily.sh` — ODS→DWD→DWS→ADS 全链路 ETL
- `scripts/diagnose_ports.sh` — 端口诊断
- `scripts/check_project.sh` — 环境检查
- `scripts/verify_project.sh` — 运行状态验证

#### 文档体系
- `README.md` — 项目简介、技术架构、快速开始、团队分工
- `docs/需求分析文档.md` — FR/NFR 需求条目、切片范围
- `docs/系统设计文档.md` — 分层架构、算法设计、安全等保三级
- `docs/功能开发文档.md` — API 清单、DDL、错误码、算法伪代码、SMS 服务实现
- `docs/开发任务拆分-角色A-平台与智能底座.md` — ~~旧方案~~角色 A 任务（后端/数据/算法，前后端拆分方案，已被 Dev-1/Dev-2 取代）
- `docs/开发任务拆分-角色B-前端与展现层.md` — ~~旧方案~~角色 B 任务（前端/展现层，前后端拆分方案，已被 Dev-1/Dev-2 取代）
- `docs/superpowers/plans/F0-shared-scaffold.md` — 共享脚手架实现计划
- `docs/superpowers/plans/Dev-1-运行流.md` — Dev-1 TDD 实现计划
- `docs/superpowers/plans/Dev-2-处置流.md` — Dev-2 TDD 实现计划

#### 新增文档（2026-08-31 补齐）
- `.env.example` — 环境变量配置模板
- `config/mysql/heat_init.sql` — MySQL 主数据/业务表建表脚本（16 张表）
- `config/hive/heat_ddl.sql` — 供热专用数仓 DDL（6 张表）
- `docs/deployment.md` — 部署文档（Docker 集群 + 服务启动 + 脚本说明）
- `docker/docker-compose-vm.yml` — 虚拟机优化版 Docker 编排（含 MySQL/Redis）
- `docs/部署文档-虚拟机部署.md` — VMware 虚拟机部署指南
- `CHANGELOG.md` — 版本变更记录
- `docs/api-guide.md` — API 接口文档（17 个端点）
- `docs/database-schema.md` — 数据字典（MySQL + Hive + Redis + ES）

---

## 版本规划

| 版本 | 里程碑 | 内容 |
|---|---|---|
| 0.2.0 | M1 | 数据接入改造 + 数仓/业务表 + 监测大屏 |
| 0.3.0 | M2 | 预警引擎 + 预报/寿命模型 + 短信服务 |
| 0.4.0 | M3 | 水力平衡/热损耗/气候补偿 + 工单闭环 |
| 1.0.0 | M4 | 数字孪生/热力仿真 + 预案 + 公众服务 + 等保合规 |
