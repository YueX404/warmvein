#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spark工业设备数据分析脚本

功能：
1. 数据清洗：从ODS层读取原始设备传感器数据，展开params为独立字段
2. 状态统计：计算各设备运行/待机/故障状态分布
3. KPI计算：OEE、MTBF、MTTR、稼动率等核心指标
4. 告警分析：告警类型统计、设备健康度排名

使用示例：
    spark-submit --master spark://spark-master:7077 spark_analysis.py

依赖：
    PySpark 3.0+
"""

import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *


def create_spark_session(app_name="DeviceMonitoringAnalysis"):
    """
    创建SparkSession实例

    Args:
        app_name (str): 应用名称

    Returns:
        SparkSession: 配置好的Spark会话
    """
    spark = SparkSession.builder \
        .appName(app_name) \
        .enableHiveSupport() \
        .config("spark.sql.hive.metastorePartitionPruningFallbackOnException", "true") \
        .config("spark.sql.hive.metastorePartitionPruningFastFallback", "true") \
        .config("spark.sql.hive.convertMetastoreParquet", "false") \
        .config("spark.sql.hive.convertMetastoreOrc", "false") \
        .getOrCreate()
    return spark


def clean_and_transform(spark, date="2024-01-01"):
    """
    数据清洗：从ODS层读取原始JSON数据，展开params为独立字段写入DWD层

    Args:
        spark (SparkSession): Spark会话
        date (str): 日期参数

    Returns:
        DataFrame: 清洗后的明细DataFrame
    """
    # 从ODS层读取原始JSON数据，使用get_json_object提取字段
    # ODS表为单列raw_json STRING，存储完整JSON字符串
    cleaned_df = spark.sql(f"""
        SELECT
            get_json_object(raw_json, '$.device_id') AS device_id,
            get_json_object(raw_json, '$.device_type') AS device_type,
            get_json_object(raw_json, '$.workshop') AS workshop,
            get_json_object(raw_json, '$.event_timestamp') AS event_time,
            hour(from_unixtime(CAST(get_json_object(raw_json, '$.ts') AS BIGINT) div 1000)) AS hour,
            CAST(get_json_object(raw_json, '$.status_code') AS INT) AS status_code,
            get_json_object(raw_json, '$.status_name') AS status_name,
            CAST(get_json_object(raw_json, '$.params.spindle_speed') AS DOUBLE) AS spindle_speed,
            CAST(get_json_object(raw_json, '$.params.feed_rate') AS DOUBLE) AS feed_rate,
            CAST(get_json_object(raw_json, '$.params.spindle_load') AS DOUBLE) AS spindle_load,
            CAST(get_json_object(raw_json, '$.params.spindle_temp') AS DOUBLE) AS spindle_temp,
            CAST(get_json_object(raw_json, '$.params.hydraulic_pressure') AS DOUBLE) AS hydraulic_pressure,
            CAST(get_json_object(raw_json, '$.params.coolant_temp') AS DOUBLE) AS coolant_temp,
            CAST(get_json_object(raw_json, '$.params.vibration') AS DOUBLE) AS vibration,
            CAST(get_json_object(raw_json, '$.params.joint_current') AS DOUBLE) AS joint_current,
            CAST(get_json_object(raw_json, '$.params.joint_torque') AS DOUBLE) AS joint_torque,
            CAST(get_json_object(raw_json, '$.params.servo_temp') AS DOUBLE) AS servo_temp,
            CAST(get_json_object(raw_json, '$.params.reducer_temp') AS DOUBLE) AS reducer_temp,
            CAST(get_json_object(raw_json, '$.params.joint_vibration') AS DOUBLE) AS joint_vibration,
            CAST(get_json_object(raw_json, '$.params.cycle_count') AS INT) AS cycle_count,
            CAST(get_json_object(raw_json, '$.params.injection_pressure') AS DOUBLE) AS injection_pressure,
            CAST(get_json_object(raw_json, '$.params.holding_pressure') AS DOUBLE) AS holding_pressure,
            CAST(get_json_object(raw_json, '$.params.system_oil_pressure') AS DOUBLE) AS system_oil_pressure,
            CAST(get_json_object(raw_json, '$.params.barrel_temp') AS DOUBLE) AS barrel_temp,
            CAST(get_json_object(raw_json, '$.params.mold_temp') AS DOUBLE) AS mold_temp,
            CAST(get_json_object(raw_json, '$.params.hydraulic_oil_temp') AS DOUBLE) AS hydraulic_oil_temp,
            CAST(get_json_object(raw_json, '$.params.cycle_time') AS DOUBLE) AS cycle_time,
            CAST(get_json_object(raw_json, '$.params.discharge_pressure') AS DOUBLE) AS discharge_pressure,
            CAST(get_json_object(raw_json, '$.params.discharge_temp') AS DOUBLE) AS discharge_temp,
            CAST(get_json_object(raw_json, '$.params.lubricant_temp') AS DOUBLE) AS lubricant_temp,
            CAST(get_json_object(raw_json, '$.params.motor_current') AS DOUBLE) AS motor_current,
            CAST(get_json_object(raw_json, '$.params.power') AS DOUBLE) AS power,
            CAST(get_json_object(raw_json, '$.alarm_code') AS INT) AS alarm_code,
            get_json_object(raw_json, '$.alarm_desc') AS alarm_desc,
            CAST(get_json_object(raw_json, '$.health_score') AS INT) AS health_score,
            CASE WHEN CAST(get_json_object(raw_json, '$.alarm_code') AS INT) != 0
                  OR CAST(get_json_object(raw_json, '$.status_code') AS INT) IN (4, 5)
                 THEN 1 ELSE 0 END AS is_abnormal,
            dt
        FROM ods.device_sensor_raw
        WHERE dt = '{date}'
    """)

    # 写入DWD层宽表
    cleaned_df.write.mode("overwrite").partitionBy("dt").saveAsTable("dwd.device_sensor_detail")
    print(f"DWD层明细数据已保存，日期: {date}")

    return cleaned_df


def build_device_status_summary(spark, date="2024-01-01"):
    """
    构建设备状态统计汇总表（DWS层）

    Args:
        spark (SparkSession): Spark会话
        date (str): 日期参数
    """
    spark.sql(f"""
        INSERT OVERWRITE TABLE dws.device_status_summary PARTITION (dt='{date}')
        SELECT
            device_id,
            device_type,
            workshop,
            COUNT(*) AS total_records,
            SUM(CASE WHEN status_code = 2 THEN 1 ELSE 0 END) AS run_count,
            SUM(CASE WHEN status_code IN (1, 6) THEN 1 ELSE 0 END) AS idle_count,
            SUM(CASE WHEN status_code = 3 THEN 1 ELSE 0 END) AS warning_count,
            SUM(CASE WHEN status_code IN (4, 5) THEN 1 ELSE 0 END) AS fault_count,
            SUM(CASE WHEN status_code = 0 THEN 1 ELSE 0 END) AS offline_count,
            CASE WHEN COUNT(*) > 0
                 THEN SUM(CASE WHEN status_code = 2 THEN 1 ELSE 0 END) / COUNT(*)
                 ELSE 0 END AS run_rate,
            ROUND(AVG(health_score), 2) AS avg_health_score,
            MIN(health_score) AS min_health_score,
            SUM(CASE WHEN alarm_code != 0 THEN 1 ELSE 0 END) AS alarm_count
        FROM dwd.device_sensor_detail
        WHERE dt = '{date}'
        GROUP BY device_id, device_type, workshop
    """)
    print("设备状态统计汇总表构建完成")


def build_device_kpi_summary(spark, date="2024-01-01"):
    """
    构建设备KPI指标汇总表：OEE、MTBF、MTTR等（DWS层）

    Args:
        spark (SparkSession): Spark会话
        date (str): 日期参数
    """
    # 假设每条记录代表5秒采样间隔
    # 运行时长 = run_count * 5 / 60 分钟
    # 故障时长 = fault_count * 5 / 60 分钟
    # 计划生产时长 = 白班12小时 = 720分钟
    spark.sql(f"""
        INSERT OVERWRITE TABLE dws.device_kpi_summary PARTITION (dt='{date}')
        SELECT
            s.device_id,
            s.device_type,
            s.workshop,
            ROUND(s.run_count * 5.0 / 60.0, 2) AS run_time_min,
            720.0 AS planned_time_min,
            ROUND(s.fault_count * 5.0 / 60.0, 2) AS fault_time_min,
            CAST(s.fault_count AS INT) AS fault_count,
            -- OEE = 时间稼动率 × 性能稼动率 × 良品率
            -- 时间稼动率 = 运行时间 / 计划时间
            -- 性能稼动率 = 运行率 * 0.9（模拟性能系数）
            -- 良品率 = 1 - 异常率
            ROUND(
                (s.run_count * 5.0 / 60.0 / 720.0) *
                (CASE WHEN s.total_records > 0 THEN s.run_count * 1.0 / s.total_records ELSE 0 END * 0.9) *
                (1 - CASE WHEN s.total_records > 0 THEN s.alarm_count * 1.0 / s.total_records ELSE 0 END),
                4
            ) AS oee,
            ROUND(s.run_count * 5.0 / 60.0 / 720.0, 4) AS availability,
            ROUND(CASE WHEN s.total_records > 0 THEN s.run_count * 1.0 / s.total_records ELSE 0 END * 0.9, 4) AS performance,
            ROUND(1 - CASE WHEN s.total_records > 0 THEN s.alarm_count * 1.0 / s.total_records ELSE 0 END, 4) AS quality_rate,
            -- MTBF = 总运行时间 / 故障次数（小时）
            ROUND(CASE WHEN s.fault_count > 0
                       THEN (s.run_count * 5.0 / 3600.0) / s.fault_count
                       ELSE (s.run_count * 5.0 / 3600.0) END, 2) AS mtbf,
            -- MTTR = 故障总时长 / 故障次数（小时）
            ROUND(CASE WHEN s.fault_count > 0
                       THEN (s.fault_count * 5.0 / 3600.0) / s.fault_count
                       ELSE 0 END, 2) AS mttr,
            ROUND(s.run_count * 5.0 / 60.0 / 720.0, 4) AS utilization_rate
        FROM dws.device_status_summary s
        WHERE s.dt = '{date}'
    """)
    print("设备KPI指标汇总表构建完成")


def build_alarm_analysis(spark, date="2024-01-01"):
    """
    构建告警分析数据（ADS层）

    Args:
        spark (SparkSession): Spark会话
        date (str): 日期参数
    """
    # 告警类型统计
    spark.sql(f"""
        INSERT OVERWRITE TABLE ads.alarm_type_stats PARTITION (dt='{date}')
        SELECT
            alarm_code,
            alarm_desc,
            COUNT(*) AS alarm_count,
            device_type,
            CASE
                WHEN alarm_code IN (1004, 2004, 3004, 4001, 4005) THEN '高'
                WHEN alarm_code IN (1001, 2001, 3001, 4002) THEN '中'
                ELSE '低'
            END AS severity
        FROM dwd.device_sensor_detail
        WHERE dt = '{date}' AND alarm_code != 0
        GROUP BY alarm_code, alarm_desc, device_type
        ORDER BY alarm_count DESC
    """)
    print("告警类型统计表构建完成")


def build_device_overview(spark, date="2024-01-01"):
    """
    构建设备实时状态总览（ADS层）

    Args:
        spark (SparkSession): Spark会话
        date (str): 日期参数
    """
    spark.sql(f"""
        INSERT OVERWRITE TABLE ads.device_overview PARTITION (dt='{date}')
        SELECT
            COUNT(DISTINCT device_id) AS total_devices,
            COUNT(DISTINCT CASE WHEN status_code != 0 THEN device_id END) AS online_devices,
            COUNT(DISTINCT CASE WHEN status_code = 2 THEN device_id END) AS running_devices,
            COUNT(DISTINCT CASE WHEN status_code = 3 THEN device_id END) AS warning_devices,
            COUNT(DISTINCT CASE WHEN status_code IN (4, 5) THEN device_id END) AS fault_devices,
            COUNT(DISTINCT CASE WHEN status_code = 0 THEN device_id END) AS offline_devices,
            ROUND(
                COUNT(DISTINCT CASE WHEN status_code != 0 THEN device_id END) /
                COUNT(DISTINCT device_id), 4
            ) AS online_rate,
            ROUND(AVG(health_score), 2) AS avg_health_score,
            SUM(CASE WHEN alarm_code != 0 THEN 1 ELSE 0 END) AS total_alarms,
            SUM(CASE WHEN alarm_code != 0 AND status_code IN (3, 4, 5) THEN 1 ELSE 0 END) AS unhandled_alarms,
            ROUND(AVG(CASE WHEN status_code = 2 THEN 1.0 ELSE 0 END) * 0.85, 4) AS factory_oee,
            SUM(CASE WHEN status_code = 2 THEN 1 ELSE 0 END) AS total_output
        FROM dwd.device_sensor_detail
        WHERE dt = '{date}'
    """)
    print("设备实时状态总览表构建完成")


def build_health_ranking(spark, date="2024-01-01"):
    """
    构建设备健康度排名表（ADS层）

    Args:
        spark (SparkSession): Spark会话
        date (str): 日期参数
    """
    spark.sql(f"""
        INSERT OVERWRITE TABLE ads.device_health_ranking PARTITION (dt='{date}')
        SELECT
            device_id,
            device_type,
            workshop,
            avg_health_score AS health_score,
            run_rate,
            alarm_count,
            -- RUL预测：基于健康度和告警次数估算剩余寿命
            CASE
                WHEN avg_health_score > 80 THEN 90
                WHEN avg_health_score > 60 THEN 70
                WHEN avg_health_score > 40 THEN 45
                ELSE 20
            END AS rul_prediction,
            ROW_NUMBER() OVER (ORDER BY avg_health_score DESC) AS ranking
        FROM (
            SELECT
                device_id,
                device_type,
                workshop,
                AVG(health_score) AS avg_health_score,
                CASE WHEN COUNT(*) > 0
                     THEN SUM(CASE WHEN status_code = 2 THEN 1 ELSE 0 END) / COUNT(*)
                     ELSE 0 END AS run_rate,
                SUM(CASE WHEN alarm_code != 0 THEN 1 ELSE 0 END) AS alarm_count
            FROM dwd.device_sensor_detail
            WHERE dt = '{date}'
            GROUP BY device_id, device_type, workshop
        ) t
    """)
    print("设备健康度排名表构建完成")


def main():
    """
    主函数：执行完整的设备监控分析流程
    """
    date = "2024-01-01"
    if len(sys.argv) > 1:
        date = sys.argv[1]

    print(f"处理日期: {date}")

    spark = create_spark_session()

    try:
        # 步骤1：数据清洗，ODS → DWD
        print("\n[步骤1] 数据清洗与转换...")
        clean_and_transform(spark, date)

        # 步骤2：设备状态统计，DWD → DWS
        print("\n[步骤2] 设备状态统计汇总...")
        build_device_status_summary(spark, date)

        # 步骤3：KPI指标计算，DWS → DWS
        print("\n[步骤3] 设备KPI指标计算(OEE/MTBF/MTTR)...")
        build_device_kpi_summary(spark, date)

        # 步骤4：告警分析，DWD → ADS
        print("\n[步骤4] 告警类型统计分析...")
        build_alarm_analysis(spark, date)

        # 步骤5：设备总览，DWD → ADS
        print("\n[步骤5] 设备实时状态总览...")
        build_device_overview(spark, date)

        # 步骤6：健康度排名，DWD → ADS
        print("\n[步骤6] 设备健康度排名...")
        build_health_ranking(spark, date)

        print("\n✓ 所有分析任务执行完成")

    finally:
        spark.stop()
        print("Spark会话已停止")


if __name__ == "__main__":
    main()
