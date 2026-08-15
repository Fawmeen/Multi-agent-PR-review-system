# pyrefly: ignore [missing-import]
import pytest
from app.economics.tracker import EconomicsTracker, MODEL_PRICING

def test_calculate_cost():
    # Test GPT-4 calculation
    # prompt: 0.03 per 1k, completion: 0.06 per 1k
    # 1000 prompt = 0.03
    # 500 completion = 0.03
    # total = 0.06
    cost = EconomicsTracker.calculate_cost("gpt-4", 1000, 500)
    assert abs(cost - 0.06) < 1e-6
    
    # Test GPT-3.5-turbo calculation
    # prompt: 0.0015 per 1k, completion: 0.002 per 1k
    # 2000 prompt = 0.003
    # 1000 completion = 0.002
    # total = 0.005
    cost = EconomicsTracker.calculate_cost("gpt-3.5-turbo", 2000, 1000)
    assert abs(cost - 0.005) < 1e-6
    
    # Test fallback model
    # default prompt: 0.01 per 1k, completion: 0.02 per 1k
    # 1000 prompt = 0.01
    # 1000 completion = 0.02
    # total = 0.03
    cost = EconomicsTracker.calculate_cost("unknown-model", 1000, 1000)
    assert abs(cost - 0.03) < 1e-6

def test_case_insensitivity():
    cost1 = EconomicsTracker.calculate_cost("GPT-4", 1000, 500)
    cost2 = EconomicsTracker.calculate_cost("gpt-4", 1000, 500)
    assert cost1 == cost2
