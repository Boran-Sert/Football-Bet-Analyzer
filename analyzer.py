"""Euclidean-distance similarity engine.

Compares an upcoming match's odds vector against every historical match.
Only columns present in BOTH datasets are used for the distance calculation,
so it gracefully handles mismatched column sets (e.g. upcoming has no IY data
but historical does).
"""

import pandas as pd
import numpy as np
from config import ALL_ODDS_MARKETS


def calculate_similarity(
    target: pd.Series, history: pd.DataFrame, markets: list
) -> pd.DataFrame:
    """Compute Euclidean distance between *target* and every row in *history*.

    All values are coerced to float64 to prevent dtype errors from CSV string leaks.
    """
    valid = [
        c
        for c in markets
        if c in history.columns and c in target.index and not pd.isna(target[c])
    ]

    if not valid:
        return pd.DataFrame()

    hist_mat = (
        history[valid]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
        .values.astype(np.float64)
    )
    tgt_vec = (
        pd.to_numeric(target[valid], errors="coerce")
        .fillna(0)
        .values.astype(np.float64)
    )

    dists = np.linalg.norm(hist_mat - tgt_vec, axis=1)

    out = history.copy()
    out["Benzerlik_Skoru"] = dists
    return out.sort_values("Benzerlik_Skoru")


def get_similar_matches_for_upcoming(
    target_match: pd.Series,
    historical_df: pd.DataFrame,
    top_n: int = 5,
) -> pd.DataFrame:
    """Return top-N historically similar matches for an upcoming fixture."""
    result = calculate_similarity(target_match, historical_df, ALL_ODDS_MARKETS)
    if result.empty:
        return pd.DataFrame()
    return result.head(top_n)
