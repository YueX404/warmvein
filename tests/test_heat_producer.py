from heat_kafka_producer import build_sensor_record, build_alarm_record


def test_sensor_record_shape():
    rec = build_sensor_record(station_id=1, supply_temp=75.0, return_temp=50.0,
                              pressure=0.6, flow=120.0, heat=80.0, corrosion=0.02,
                              room_temp=20.0, outdoor_temp=-5.0, ts="2026-08-31 10:00:00")
    assert rec["station_id"] == 1
    assert set(["supplyTemp", "returnTemp", "pressure", "flow", "heat",
                "corrosionRate", "roomTemp", "outdoorTemp"]) <= set(rec.keys())


def test_alarm_record_has_level_and_type():
    a = build_alarm_record(station_id=1, alarm_type="frost", level=3, ts="2026-08-31 10:00:00")
    assert a["level"] == 3 and a["alarmType"] == "frost"
