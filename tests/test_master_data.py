"""Task 1: master-data service and heat station list API."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import app
from services import master_data

client = TestClient(app)

_STATION_ROW = {
    "station_id": 1,
    "name": "CNC-001",
    "region": "ansai",
    "source_id": 1,
    "area": 12.50,
    "design_flow": 140.00,
    "design_tg": 75.00,
    "design_th": 50.00,
    "address": "机加工一车间 / CNC加工中心",
    "lng": 109.3205,
    "lat": 36.8652,
    "status": 1,
}


def _session_returning(rows, first=None):
    session = MagicMock()
    result = MagicMock()
    result.mappings.return_value.all.return_value = rows
    result.mappings.return_value.first.return_value = first
    session.execute.return_value = result
    session.__enter__.return_value = session
    session.__exit__.return_value = False
    return session


@patch("services.master_data.SessionLocal")
def test_get_stations_returns_list(mock_session_local):
    mock_session_local.return_value = _session_returning([_STATION_ROW])
    rows = master_data.get_stations(region="ansai")
    assert isinstance(rows, list)
    assert rows[0]["stationId"] == 1
    assert rows[0]["name"] == "CNC-001"


@patch("services.master_data.SessionLocal")
def test_list_subscribed_phones_filters_unsub(mock_session_local):
    mock_session_local.return_value = _session_returning(
        [{"phone": "13800001001"}, {"phone": "13800001002"}]
    )
    phones = master_data.list_subscribed_phones(station_id=1)
    assert all(isinstance(p, str) for p in phones)
    assert phones == ["13800001001", "13800001002"]


@patch("services.master_data.SessionLocal")
def test_get_user_by_id_masks_phone(mock_session_local):
    mock_session_local.return_value = _session_returning(
        [],
        first={
            "user_id": 1,
            "house_no": "CNC-001-01",
            "address": "机加工一车间1号楼101",
            "phone": "13800001001",
            "station_id": 1,
            "area": 86.0,
            "sms_subscribe": 1,
        },
    )
    user = master_data.get_user_by_id(1)
    assert user["phone"] == "138****1001"
    assert user["userId"] == 1


def test_mask_phone_short_value():
    assert master_data.mask_phone("123") == "123"


@patch("services.master_data.get_stations", return_value=[{"stationId": 1, "name": "CNC-001"}])
def test_stations_api_envelope(_mock_get):
    res = client.get("/api/heat/stations", params={"region": "ansai"})
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert "stations" in body["data"]
    assert body["data"]["stations"][0]["stationId"] == 1


def test_stations_api_rejects_bad_region():
    res = client.get("/api/heat/stations", params={"region": "ansai;drop"})
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 40001
