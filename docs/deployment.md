# 暖脉 AI 智慧供热平台 — 部署文档

> 版本：v2026.08.31-部署
> 适用环境：开发环境（Docker Compose 本地部署）

---

## 1. 前置条件

| 依赖 | 最低版本 | 说明 |
|---|---|---|
| Docker | 24.0+ | 容器运行时 |
| Docker Compose | v2.20+ | 编排工具（支持 `docker compose` 子命令） |
| Python | 3.10+ | 后端服务运行 |
| pip | 22.0+ | Python 包管理 |
| Node.js | 18+ | 前端构建（仅前端开发） |
| Git | 2.30+ | 拉取代码 |

**硬件建议（开发环境）**：
- CPU：4 核+
- 内存：16 GB+（Docker 集群约需 8 GB）
- 磁盘：50 GB+（含镜像、模型、日志）

---

## 2. 项目拉取与配置

```bash
# 1. 克隆代码
git clone <repo-url> && cd YY

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入实际的 MySQL/Redis/Kafka 密码等（开发环境大部分用默认值即可）

# 3. 安装 Python 依赖
pip install -r requirements.txt  # 或手动安装
pip install fastapi uvicorn pymysql redis kafka-python scikit-learn joblib pandas numpy pyspark
```

---

## 3. Docker 集群启动

> 💡 **VM 部署用户**：如果您在 VMware 虚拟机上部署（8GB 内存），请改用 [虚拟机部署文档](部署文档-虚拟机部署.md)，其中使用优化版 `docker-compose-vm.yml`（含 MySQL/Redis，JVM 堆已压缩）。
>
> 以下为 **开发机**（16GB+ 内存）本地部署流程，使用原始 `docker-compose.yml`（不含 MySQL/Redis，需外部 MySQL）。

### 3.1 启动全部服务

```bash
# 方式一：使用脚本（推荐）
bash scripts/start_cluster.sh

# 方式二：手动启动
cd docker
docker compose up -d
```

**启动的服务（12 个容器）：**

| 服务 | 端口 | 用途 |
|---|---|---|
| zookeeper | 2181 | Kafka 依赖 |
| kafka | 9092(外部)/9093(内部) | 消息总线 |
| hadoop-namenode | 9870, 8020 | HDFS |
| hadoop-datanode | 9864 | HDFS 数据节点 |
| hive-metastore-postgresql | 5432 | Hive 元数据库 |
| hive-metastore | 9083 | Hive 元数据服务 |
| hive-server | 10000, 10002 | Hive SQL 执行 |
| elasticsearch | 9200, 9300 | 时序检索 |
| logstash | 5044, 5000 | Kafka→ES 数据管道 |
| kibana | 5601 | ES 可视化 |
| spark-master | 8080, 7077 | Spark 调度 |
| spark-worker | — | Spark 执行节点 |

### 3.2 等待启动完成

启动后需等待约 60 秒，各服务才能完全就绪。验证方式：

```bash
# 检查容器状态
docker compose ps

# 验证关键服务
curl http://localhost:9870           # HDFS Web UI
curl http://localhost:9200/_cat/health  # ES 集群状态（应返回 green）
docker exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092  # Kafka
curl http://localhost:8080           # Spark Master
```

---

## 4. 数据初始化

### 4.1 创建 Hive 数仓表

```bash
# 执行供热 DDL（ODS/DWD/DWS/ADS）
docker exec -i hive-server hive -f /dev/stdin < config/hive/heat_ddl.sql

# 或通过 Docker volume 挂载后执行
docker cp config/hive/heat_ddl.sql hive-server:/tmp/heat_ddl.sql
docker exec hive-server hive -f /tmp/heat_ddl.sql
```

### 4.2 初始化 MySQL 业务表

```bash
# 方式一：在 MySQL 容器中执行（需先启动 MySQL）
# 注意：当前 docker-compose.yml 未包含 MySQL 容器，需额外配置或使用外部 MySQL
mysql -u warmvein -p warmvein < config/mysql/heat_init.sql

# 方式二：如果使用外部 MySQL
mysql -h localhost -u warmvein -p warmvein < config/mysql/heat_init.sql
```

### 4.3 生成供热模拟数据

```bash
# 生成 1 万条供热传感器日志
python src/python/heat_generate_logs.py --count 10000 --output data/logs

# 生成 10 万条（用于压测）
python src/python/heat_generate_logs.py --count 100000 --output data/logs
```

### 4.4 加载数据到 Hive

```bash
# 将日志文件加载到 ODS 层
DATE=$(date +%Y-%m-%d)
bash scripts/load_data_to_hive.sh $DATE

# 执行 ETL 全链路（ODS → DWD → DWS → ADS）
bash scripts/etl_daily.sh $DATE
```

---

## 5. 后端服务启动

```bash
# 方式一：直接启动
uvicorn src.python.main:app --host 0.0.0.0 --port 8000 --reload

# 方式二：使用脚本（含数据生成+ETL+Kafka 生产）
bash scripts/start_project.sh
```

**启动后访问：**
- API 文档（Swagger）：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

---

## 6. 前端开发启动

```bash
cd web
npm install
npm run dev
# 默认访问 http://localhost:5173
```

---

## 7. Kafka 实时数据流启动

```bash
# 启动 Kafka 生产者（实时模拟供热数据）
python src/python/heat_kafka_producer.py --bootstrap localhost:9092 --duration 300

# 数据流向：Producer → heat-sensor-topic → Logstash → ES
#                           ↓
#                    Spark → Hive 数仓
```

---

## 8. 脚本说明

| 脚本 | 用途 | 用法 |
|---|---|---|
| `scripts/start_cluster.sh` | 启动 Docker 集群并验证 | `bash scripts/start_cluster.sh` |
| `scripts/stop_cluster.sh` | 停止 Docker 集群 | `bash scripts/stop_cluster.sh` |
| `scripts/start_project.sh` | 一键启动全流程（集群+FastAPI+数据+ETL+Kafka） | `bash scripts/start_project.sh` |
| `scripts/diagnose_ports.sh` | 诊断端口占用 | `bash scripts/diagnose_ports.sh` |
| `scripts/check_project.sh` | 检查项目依赖和环境 | `bash scripts/check_project.sh` |
| `scripts/verify_project.sh` | 验证项目运行状态 | `bash scripts/verify_project.sh` |
| `scripts/load_data_to_hive.sh` | 加载 JSON 日志到 Hive ODS 层 | `bash scripts/load_data_to_hive.sh [日期]` |
| `scripts/etl_daily.sh` | 执行 ODS→DWD→DWS→ADS 全链路 ETL | `bash scripts/etl_daily.sh [日期]` |

> 不带日期参数时，默认使用当天/昨天日期。

---

## 9. Spark 离线分析

```bash
# 通过 spark-submit 执行（使用已有的 Spark 集群）
spark-submit --master spark://spark-master:7077 src/python/heat_spark_analysis.py 2026-08-31

# 或通过 docker exec
docker exec spark-master spark-submit \
  --master local[*] \
  /opt/spark/work-dir/src/python/heat_spark_analysis.py 2026-08-31
```

---

## 10. ML 模型训练

```bash
# 训练异常检测、寿命预测、用热异常模型
python src/python/heat_train_model.py

# 模型文件输出到 models/ 目录
ls models/*.pkl
```

---

## 11. 服务停止

```bash
# 停止 Docker 集群
cd docker && docker compose down

# 停止 FastAPI 服务
pkill -f "uvicorn.*main:app"

# 停止所有并清理数据卷（慎用，会删除 ES/HDFS 数据）
cd docker && docker compose down -v
```

---

## 12. 常见问题

### Q1: Kafka 启动失败 / 连接拒绝
```bash
# 检查 ZooKeeper 是否就绪
docker exec zookeeper ruok
# 应返回 "imok"

# 检查 Kafka 日志
docker logs kafka --tail 50
```

### Q2: HiveServer2 连接超时
Hive 启动较慢，需等待 metastore 完全就绪（通常 2-3 分钟）：
```bash
# 检查 Hive metastore 状态
docker logs hive-metastore --tail 20
# 看到 "Starting HiveMetastore on port 9083" 表示就绪
```

### Q3: Elasticsearch 集群状态为 red
```bash
curl http://localhost:9200/_cat/health?v
# 如果是 single-node 模式，yellow 状态是正常的
```

### Q4: ML 模型未加载
FastAPI 启动时若 `models/` 目录下无 `.pkl` 文件，会使用 dummy 模型。运行训练脚本即可：
```bash
python src/python/heat_train_model.py
```

### Q5: 端口冲突
```bash
# 检查端口占用
bash scripts/diagnose_ports.sh

# 手动检查（Linux/Mac）
lsof -i :8000
# Windows
netstat -ano | findstr :8000
```

---

## 13. 服务访问地址汇总

| 服务 | 地址 | 说明 |
|---|---|---|
| FastAPI | http://localhost:8000 | 后端 API |
| Swagger 文档 | http://localhost:8000/docs | API 交互文档 |
| 前端大屏 | http://localhost:5173 | Vue3 开发服务器 |
| HDFS Web UI | http://localhost:9870 | HDFS 管理 |
| Spark Master | http://localhost:8080 | Spark 集群管理 |
| Kibana | http://localhost:5601 | ES 数据可视化 |
| Elasticsearch | http://localhost:9200 | ES REST API |
| Kafka | localhost:9092 | Kafka Broker |
| ZooKeeper | localhost:2181 | ZK 客户端 |
| HiveServer2 | localhost:10000 | Hive JDBC/Thrift |
