"""
Tests para el modelo de Machine Learning
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import ml_model

def test_ml_model_exists():
    """Test que el módulo ML existe"""
    assert ml_model is not None

def test_ml_model_placeholder():
    """Test placeholder del modelo ML"""
    parsed = {"queries": []}
    result = ml_model.analyze_code(parsed)
    assert isinstance(result, dict)
