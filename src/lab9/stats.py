"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import scipy.stats

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    if len(human) != len(judge):
        raise ValueError(f"length mismatch: human={len(human)} vs judge={len(judge)}")
    tp = fp = fn = tn = 0
    for h_raw, j_raw in zip(human, judge):
        h = str(h_raw).strip().upper() == POS
        j = str(j_raw).strip().upper() == POS
        if h and j:
            tp += 1
        elif not h and j:
            fp += 1
        elif h and not j:
            fn += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    cm = confusion(human, judge)
    p = cm["tp"] / (cm["tp"] + cm["fp"]) if (cm["tp"] + cm["fp"]) > 0 else 0.0
    r = cm["tp"] / (cm["tp"] + cm["fn"]) if (cm["tp"] + cm["fn"]) > 0 else 0.0
    return float(p), float(r)


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    cm = confusion(human, judge)
    n = cm["tp"] + cm["fp"] + cm["fn"] + cm["tn"]
    if n == 0:
        raise ValueError("cannot compute cohen_kappa on empty sequences")
    p_o = (cm["tp"] + cm["tn"]) / n
    p_h_pos = (cm["tp"] + cm["fn"]) / n
    p_j_pos = (cm["tp"] + cm["fp"]) / n
    p_h_neg = 1.0 - p_h_pos
    p_j_neg = 1.0 - p_j_pos
    p_e = p_h_pos * p_j_pos + p_h_neg * p_j_neg
    if abs(1.0 - p_e) < 1e-12:
        raise ValueError("cohen_kappa undefined when p_e == 1")
    return float((p_o - p_e) / (1.0 - p_e))


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    denom = sensitivity + specificity - 1.0
    if abs(denom) < 1e-12:
        val = float(observed_rate)
    else:
        val = (float(observed_rate) + float(specificity) - 1.0) / denom
    return max(0.0, min(1.0, val))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    if len(a) != len(b):
        raise ValueError(f"length mismatch: a={len(a)} vs b={len(b)}")
    if not a:
        return (0.0, 0.0, 0.0)
    arr_a = np.asarray(a, dtype=float)
    arr_b = np.asarray(b, dtype=float)
    if np.allclose(arr_a, arr_b, rtol=0.0, atol=1e-12):
        return (0.0, 0.0, 0.0)
    res = scipy.stats.bootstrap(
        (arr_a, arr_b),
        lambda x, y: np.mean(x) - np.mean(y),
        paired=True,
        method="percentile",
        n_resamples=n_resamples,
        rng=np.random.default_rng(rng),
        confidence_level=confidence,
    )
    diff = float(np.mean(arr_a) - np.mean(arr_b))
    lo = float(res.confidence_interval.low)
    hi = float(res.confidence_interval.high)
    return (diff, lo, hi)


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    if n <= 0 or k <= 0 or c < 0 or c > n or k > n:
        raise ValueError(f"invalid (n={n}, c={c}, k={k})")
    if n - c < k:
        return 1.0
    return float(1.0 - math.comb(n - c, k) / math.comb(n, k))


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    if n <= 0 or k <= 0 or c < 0 or c > n or k > n:
        raise ValueError(f"invalid (n={n}, c={c}, k={k})")
    if c < k:
        return 0.0
    return float(math.comb(c, k) / math.comb(n, k))
