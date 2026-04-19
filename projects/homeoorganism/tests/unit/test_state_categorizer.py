from homeoorganism.analytics.state_categorizer import classify_state
from homeoorganism.domain.types import BodyState


def test_classify_critical_low_energy():
    assert classify_state(BodyState(14, 70, False, True)) == "critical"


def test_classify_energy_dominant():
    assert classify_state(BodyState(40, 65, False, True)) == "energy_dominant"


def test_classify_neutral_edge():
    assert classify_state(BodyState(60, 60, False, True)) == "neutral"
