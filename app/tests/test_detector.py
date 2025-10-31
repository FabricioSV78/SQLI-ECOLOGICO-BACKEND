from app.core import detector

def test_detector_runs():
    result = detector.run_analysis("fake_project")
    assert "predictions" in result
