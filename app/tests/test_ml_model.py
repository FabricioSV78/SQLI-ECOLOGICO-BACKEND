from app.core import ml_model

def test_ml_model_placeholder():
    parsed = {"queries": []}
    result = ml_model.analyze_code(parsed)
    assert isinstance(result, dict)
