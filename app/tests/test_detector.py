"""
Tests para el detector de SQLi
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import detector

def test_detector_initialization():
    """Test que el detector se puede inicializar"""
    assert detector is not None

def test_detector_basic_functionality():
    """Test básico del detector"""
    # Este test necesitará ser implementado con datos reales
    # Por ahora verificamos que la función existe
    assert hasattr(detector, 'run_analysis') or hasattr(detector, 'analyze_code')
