# utils/dbn_forward.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, List, Optional, Union
import numpy as np

def _normalize(vec: np.ndarray) -> np.ndarray:
    s = float(np.sum(vec))
    return vec / s if s > 0 else np.ones_like(vec) / len(vec)

def _one_hot_likelihood(states: List[str], observed: Optional[str]) -> np.ndarray:
    if observed is None or observed not in states:
        return np.ones(len(states), dtype=float)
    like = np.zeros(len(states), dtype=float)
    like[states.index(observed)] = 1.0
    return like

def _soft_likelihood(prob_by_state: Optional[Dict[str, float]], states: List[str]) -> np.ndarray:
    if not prob_by_state:
        return np.ones(len(states), dtype=float)
    return _normalize(np.array([float(prob_by_state.get(s, 0.0)) for s in states], dtype=float))

def forward_step(alpha_prev: np.ndarray, T: np.ndarray, emission_like: np.ndarray) -> np.ndarray:
    # alpha_t ∝ diag(emission) · (Tᵀ · alpha_{t-1})
    pred = T.T @ alpha_prev
    alpha_t = emission_like * pred
    return _normalize(alpha_t)

Emission = Optional[Union[Dict[str, float], str]]

def run_chain(
    stages: List[str],
    states: List[str],
    T: np.ndarray,
    alpha0: Optional[Dict[str, float]],
    emissions_by_stage: Dict[str, Emission]
) -> Dict[str, Dict[str, float]]:
    """
    emissions_by_stage[t] ∈ {None, 'High'/'Medium'/'Low', {'Low':p1,'Medium':p2,'High':p3}}
    """
    if alpha0:
        a = _normalize(np.array([alpha0.get(s, 0.0) for s in states], dtype=float))
    else:
        a = np.ones(len(states), dtype=float) / len(states)

    out: Dict[str, Dict[str, float]] = {}
    for i, t in enumerate(stages):
        e = emissions_by_stage.get(t, None)
        if isinstance(e, dict):
            like = _soft_likelihood(e, states)
        else:
            like = _one_hot_likelihood(states, e)

        if i == 0:
            a = _normalize(like * a)
        else:
            a = forward_step(a, T, like)

        out[t] = {s: float(a[j]) for j, s in enumerate(states)}
    return out



def rule_resilience_emission_gb(
        cap_marginals: Dict[str, Dict[str, float]],  # {'AbsorptionCapacity':{'Bad':..., 'Good':...}, ...}
        states: List[str],  # 应该为 ['Bad', 'Good']
        weights: Dict[str, float],  # {'AbsorptionCapacity':0.34, ...}
        temperature: float = 1.0
) -> Dict[str, float]:
    """
    将多个能力节点的 Good/Bad 边缘概率通过加权平均映射为 Resilience 的 soft 似然。
    """
    # 计算每个能力节点为 "Good" 的期望概率
    prob_good_sum = 0.0
    total_weight = 0.0
    for cap_name, weight in weights.items():
        dist = cap_marginals.get(cap_name, {})
        prob_good = dist.get("Good", 0.0)
        prob_good_sum += prob_good * weight
        total_weight += weight

    # 计算加权平均的 "Good" 概率
    if total_weight == 0:
        avg_prob_good = 0.5
    else:
        avg_prob_good = prob_good_sum / total_weight

    # 使用 softmax 思想（带温度参数）生成似然
    # raw score: 一个代表 Bad，一个代表 Good
    # 这里简单地将 avg_prob_good 作为 Good 的分数
    raw_scores = np.array([1.0 - avg_prob_good, avg_prob_good], dtype=float) * temperature

    # 防止数值溢出
    exp_scores = np.exp(raw_scores - np.max(raw_scores))
    softmax_probs = exp_scores / np.sum(exp_scores)

    return {states[0]: float(softmax_probs[0]), states[1]: float(softmax_probs[1])}
