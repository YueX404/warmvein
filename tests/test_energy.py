"""Task 8: energy KPI accounting and regional benchmark."""

from unittest.mock import patch

import pytest

from services.energy import benchmark, compute_kpi


@pytest.fixture(autouse=True)
def _offline_backends():
    import services.heat_run as heat_run_mod

    heat_run_mod._DB_DOWN = False
    with patch("services.energy.SessionLocal", side_effect=OSError("offline")):
        with patch("services.heat_run.SessionLocal", side_effect=OSError("offline")):
            with patch("services.heat_run.redis_client") as mock_redis:
                mock_redis.get.return_value = None
                yield
    heat_run_mod._DB_DOWN = False


def test_kpi_shape():
    k = compute_kpi("2026-08-31", "ansai")
    assert "heatLossKwh" in k and "unitHeatKwh" in k
    assert "sourcePowerKwh" in k
    assert k["heatLossKwh"] >= 0
    assert k["heatSupplyGj"] > 0


def test_benchmark_flags_gap():
    b = benchmark({"unitHeatKwh": 1.2}, baseline=1.0)
    assert b["gap"] == "high"
    assert b["diff"] == 0.2


def test_benchmark_mid_and_low():
    assert benchmark({"unitHeatKwh": 1.05}, baseline=1.0)["gap"] == "mid"
    assert benchmark({"unitHeatKwh": 0.9}, baseline=1.0)["gap"] == "low"
    assert benchmark({"unitHeatKwh": 1.0}, baseline=1.0)["gap"] == "low"
