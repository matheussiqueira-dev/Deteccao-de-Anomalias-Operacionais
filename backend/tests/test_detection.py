from app.ml_models.isolation_forest import IsolationForestDetector


def test_isolation_forest_scores_normalized():
    detector = IsolationForestDetector(min_samples=10, contamination=0.2)
    for i in range(9):
        assert detector.update_and_score("finance:daily_expense", float(i)) is None

    score = detector.update_and_score("finance:daily_expense", 9.0)
    assert score is not None
    assert 0.0 <= score <= 1.0

    score2 = detector.update_and_score("finance:daily_expense", 1000.0)
    assert score2 is not None
    assert 0.0 <= score2 <= 1.0
