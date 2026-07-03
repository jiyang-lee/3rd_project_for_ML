from __future__ import annotations

from heatgrid_ops.anomaly import decide_anomaly


def test_anomaly_requires_iforest_mahalanobis_and_criticality() -> None:
    detected = decide_anomaly(
        {
            "iforest_score_ratio": 0.91,
            "mahalanobis_score_ratio": 1.01,
            "anomaly_criticality": 6,
        }
    )
    missed = decide_anomaly(
        {
            "iforest_score_ratio": 0.91,
            "mahalanobis_score_ratio": 0.99,
            "anomaly_criticality": 6,
        }
    )
    assert detected.detected is True
    assert missed.detected is False
