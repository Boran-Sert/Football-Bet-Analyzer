"""UI yardimci fonksiyonlari: CSS, stil, vurgulama."""

import unicodedata

import pandas as pd
import streamlit as st


# ═══════════════════════════════════════════════
#  RESPONSIVE CSS
# ═══════════════════════════════════════════════


def inject_css():
    """Mobil, tablet, masaustu icin responsive CSS."""
    st.markdown(
        """
    <style>
        /* Base */
        html, body, [class*="css"] { font-size: 16px !important; }

        /* Phone */
        @media (max-width: 768px) {
            html, body, [class*="css"] { font-size: 14px !important; }
            h1 { font-size: 1.45rem !important; }
            h2, h3 { font-size: 1.15rem !important; }
            .block-container { padding: 0.8rem 0.6rem !important; }
            section[data-testid="stSidebar"] {
                min-width: 240px !important; max-width: 280px !important;
            }
            .stDataFrame { overflow-x: auto !important; -webkit-overflow-scrolling: touch; }
        }

        /* Tablet */
        @media (min-width: 769px) and (max-width: 1024px) {
            h1 { font-size: 1.9rem !important; }
            h2, h3 { font-size: 1.4rem !important; }
            .block-container { padding: 1.2rem 1.5rem !important; }
        }

        /* Desktop */
        @media (min-width: 1025px) {
            h1 { font-size: 2.3rem !important; }
            h2, h3 { font-size: 1.6rem !important; }
        }

        /* Dokunmatik butonlar */
        .stButton>button {
            font-size: 15px !important; padding: 12px 24px;
            font-weight: 600; min-height: 48px;
            border-radius: 8px; width: 100%;
            transition: transform 0.12s ease;
        }
        .stButton>button:active { transform: scale(0.97); }
        .stSelectbox > div > div, .stSlider > div { min-height: 44px !important; }
        .stAlert { font-size: 14px !important; }
    </style>
    """,
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════
#  TAKIM ISMI ESLELEME
# ═══════════════════════════════════════════════


from config import TEAM_ALIASES


def slugify(text: str) -> str:
    """Turkce karakterleri normalize et, sadece alfanumerik birak."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    # Turkce karakter donusumu
    tr_map = {"ı": "i", "ö": "o", "ü": "u", "ş": "s", "ğ": "g", "ç": "c"}
    for old, new in tr_map.items():
        text = text.replace(old, new)
    # Unicode aksanlari kaldir
    text = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )
    return "".join(c for c in text if c.isalnum())


def _apply_alias(name: str) -> str:
    """Isim manuel eslesme tablosunda varsa kisa versiyonunu dondur."""
    if not isinstance(name, str):
        return name
    low_name = name.lower().strip()
    return TEAM_ALIASES.get(low_name, name)


def match_team(name1: str, name2: str) -> bool:
    """Iki takim isminin eslip eslemedigini kontrol et (fuzzy ve alias destegi ile)."""
    # 1. Adim: Alias (kisa isim) uygula (Wolverhampton Wanderers -> Wolves)
    n1_alias = _apply_alias(name1)
    n2_alias = _apply_alias(name2)

    # 2. Adim: Slugify ve fuzzy check
    s1, s2 = slugify(n1_alias), slugify(n2_alias)
    if not s1 or not s2:
        return False
    return s1 in s2 or s2 in s1


# ═══════════════════════════════════════════════
#  TABLO STILLERI
# ═══════════════════════════════════════════════

# Stil sabitleri
_WIN_STYLE = (
    "background-color: rgba(39, 174, 96, 0.2); color: #2ecc71; font-weight: bold;"
)
_LOSE_STYLE = "background-color: rgba(192, 57, 43, 0.2); color: #e74c3c;"
_DRAW_STYLE = "color: #f1c40f;"
_HIGHLIGHT_STYLE = (
    "background-color: rgba(241, 196, 15, 0.4); font-weight: bold; color: white"
)


def highlight_winner(row: pd.Series) -> list[str]:
    """Kazanan takimi yesil, kaybedeni kirmizi, beraberligi sari yap."""
    styles = [""] * len(row)
    try:
        hg = pd.to_numeric(row.get("Ev Sahibi Gol", float("nan")), errors="coerce")
        ag = pd.to_numeric(row.get("Deplasman Gol", float("nan")), errors="coerce")

        if "Ev Sahibi" in row.index and "Deplasman" in row.index:
            hi = row.index.get_loc("Ev Sahibi")
            ai = row.index.get_loc("Deplasman")

            if pd.notna(hg) and pd.notna(ag):
                if hg > ag:
                    styles[hi] = _WIN_STYLE
                    styles[ai] = _LOSE_STYLE
                elif ag > hg:
                    styles[hi] = _LOSE_STYLE
                    styles[ai] = _WIN_STYLE
                else:
                    styles[hi] = _DRAW_STYLE
                    styles[ai] = _DRAW_STYLE
    except Exception:
        pass
    return styles


def highlight_standings(df: pd.DataFrame, home: str, away: str) -> pd.DataFrame:
    """Puan durumu tablosunda secili takimlari vurgula."""

    def _apply(row):
        if match_team(row["Takım"], home) or match_team(row["Takım"], away):
            return [_HIGHLIGHT_STYLE] * len(row)
        return [""] * len(row)

    return df.style.apply(_apply, axis=1)


# ═══════════════════════════════════════════════
#  ISTATISTIK OZETI
# ═══════════════════════════════════════════════


def render_match_stats(results: pd.DataFrame):
    """Benzerlik sonuclarinin istatistik ozetini goster."""
    if "Ev Sahibi Gol" not in results.columns or "Deplasman Gol" not in results.columns:
        return

    home_g = pd.to_numeric(results["Ev Sahibi Gol"], errors="coerce")
    away_g = pd.to_numeric(results["Deplasman Gol"], errors="coerce")
    total = len(results)

    home_wins = (home_g > away_g).sum()
    draws = (home_g == away_g).sum()
    away_wins = (home_g < away_g).sum()
    avg_total = (home_g + away_g).mean()

    st.markdown("---")
    st.subheader("Istatistik Ozeti")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ev Sahibi Galibiyet", f"{home_wins}/{total}")
    c2.metric("Beraberlik", f"{draws}/{total}")
    c3.metric("Deplasman Galibiyet", f"{away_wins}/{total}")
    c4.metric("Ort. Toplam Gol", f"{avg_total:.1f}" if pd.notna(avg_total) else "-")
