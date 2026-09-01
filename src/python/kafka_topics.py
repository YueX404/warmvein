"""
Kafka topic constants shared across Dev-1 and Dev-2.

Contract: these names are the single source of truth.
"""

HEAT_SENSOR_TOPIC = "heat-sensor-topic"
HEAT_ALARM_TOPIC = "heat-alarm-topic"       # Dev-1 produces, Dev-2 consumes
HEAT_FORECAST_TOPIC = "heat-forecast-topic"
SMS_NOTIFY_TOPIC = "sms-notify-topic"       # Dev-2 produces, sms_consumer consumes
