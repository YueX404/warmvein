from algorithm.hydraulic_balance import compute_balance


def test_balanced_branch():
    r = compute_balance({"b1": 100.0}, {"b1": 100.0})
    assert r["b1"]["beta"] == 1.0
    assert r["b1"]["unbalanced"] is False


def test_unbalanced_low():
    r = compute_balance({"b1": 80.0}, {"b1": 100.0})
    assert r["b1"]["beta"] == 0.8
    assert r["b1"]["unbalanced"] is True


def test_zero_design_safe():
    r = compute_balance({"b1": 50.0}, {"b1": 0.0})
    assert r["b1"]["beta"] == 0.0
    assert r["b1"]["suggest_open"] is None


def test_unbalanced_high():
    r = compute_balance({"b1": 120.0}, {"b1": 100.0})
    assert r["b1"]["beta"] == 1.2
    assert r["b1"]["unbalanced"] is True


def test_zero_actual_suggests_full_open():
    r = compute_balance({"b1": 0.0}, {"b1": 100.0})
    assert r["b1"]["beta"] == 0.0
    assert r["b1"]["unbalanced"] is True
    assert r["b1"]["suggest_open"] == 100.0
