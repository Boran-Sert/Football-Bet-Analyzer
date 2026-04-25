"""Canli Iddaa Oran Benzerlik Analizi – Streamlit Uygulamasi.

Bu dosya sadece sayfa akisini yonetir.
Veri isleme  → data_processor.py
Veri cekme   → data_fetcher.py
UI stilleri  → ui_helpers.py
Benzerlik    → analyzer.py
Ayarlar      → config.py
"""

import streamlit as st
import pandas as pd

from config import SUPPORTED_LEAGUES, INFO_COLUMNS, get_seasons, get_current_season
from data_processor import (
    fetch_and_process,
    get_season_data,
    get_upcoming_fixtures,
    get_league_standings,
    get_standings_cache_key,
)
from data_fetcher import get_api_usage
from analyzer import get_similar_matches_for_upcoming
from ui_helpers import (
    inject_css,
    highlight_winner,
    highlight_standings,
    render_match_stats,
)


# ═══════════════════════════════════════════════
#  SAYFA KURULUMU
# ═══════════════════════════════════════════════


def setup_page():
    """Sayfa ayarlari ve baslik."""
    st.set_page_config(
        page_title="Canli Oran Analiz Sistemi",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_css()
    st.title("Canli Iddaa Oran Benzerlik Analizi")
    st.markdown(
        "**Sistem Ozeti:** Yaklasan maclarin canli oranlarini gecmis sezonlarla "
        "karsilastirarak, benzer oran profillerinin nasil sonuclandigini gosterir. "
        "Analiz icin tablodan bir mac secin."
    )


# ═══════════════════════════════════════════════
#  ANALIZ SEKMESI
# ═══════════════════════════════════════════════


def render_analysis_tab(upcoming: pd.DataFrame, hist: pd.DataFrame, league: str):
    """Canli oran analizi sekmesini render et.

    Returns:
        Secilen mac (pd.Series) veya None.
    """
    # Veri yoksa uyari goster
    if hist.empty and upcoming.empty:
        st.error(
            f"{league} icin veri ulasilamadi. Internet ve API limitlerini kontrol edin."
        )
        return None

    if upcoming.empty:
        st.warning(f"{league} icin yaklasan mac bulunamadi.")
        st.dataframe(hist, width="stretch", hide_index=True)
        return None

    if hist.empty:
        st.warning(f"{league} gecmis verileri yuklenemedi.")
        st.dataframe(upcoming, width="stretch", hide_index=True)
        return None

    # Mac secim tablosu
    st.caption("Analiz baslatmak icin tablodan macin uzerine tiklayin.")
    event = st.dataframe(
        upcoming,
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    st.divider()
    st.subheader("Gecmis Sezon Karsilastirmasi")

    # Secim kontrolu
    if not event.selection.rows:
        st.info("Yukaridaki tablodan bir mac secin.")
        return None

    match = upcoming.iloc[event.selection.rows[0]]
    st.info(f"**{match['Ev Sahibi']}** vs **{match['Deplasman']}**  ({match['Tarih']})")

    # Secili macin oranlari
    odds = {
        k: v
        for k, v in match.items()
        if k not in ("Tarih", "Ev Sahibi", "Deplasman") and pd.notna(v)
    }
    if odds:
        cols = st.columns(len(odds))
        for col, (label, val) in zip(cols, odds.items()):
            col.metric(label, val)

    # Benzerlik analizi
    top_n = st.slider("Benzer mac sayisi", 3, 15, 5)

    if st.button("Benzerleri Bul"):
        with st.spinner("Gecmis veriler taranarak oranlar karsilastiriliyor..."):
            results = get_similar_matches_for_upcoming(match, hist, top_n=top_n)

        if results.empty:
            st.warning("Bu oran profiline yeterli gecmis veri bulunamadi.")
            return match

        st.success(f"En yakin {len(results)} gecmis mac:")

        # Sonuc tablosu (benzerlik skoru haric)
        display = [c for c in results.columns if c != "Benzerlik_Skoru"]
        odds_cols = [c for c in display if c not in INFO_COLUMNS]

        styled = (
            results[display]
            .style.apply(highlight_winner, axis=1)
            .format(precision=2, subset=odds_cols)
        )
        st.dataframe(styled, width="stretch", hide_index=True)

        # Istatistik ozeti
        render_match_stats(results)

    return match


# ═══════════════════════════════════════════════
#  PUAN DURUMU SEKMESI
# ═══════════════════════════════════════════════


def render_standings_tab(league: str, season: str, selected_match):
    """Puan durumu sekmesini render et."""
    current = get_current_season()
    cache_key = get_standings_cache_key()

    # 1) Guncel sezon (her zaman en ustte)
    st.subheader(f"{league} Güncel Puan Durumu ({current})")
    st.info("ℹ️ Not: Puan durumu günde iki kez (06:00 ve 18:00) yenilenir.")
    _show_standings(league, current, cache_key, selected_match)

    # 2) Secili gecmis sezon (guncel degilse goster)
    if season != current:
        st.divider()
        st.subheader(f"{league} Geçmiş Sezon Puan Durumu ({season})")
        _show_standings(league, season, cache_key, selected_match)


def _show_standings(league: str, season: str, cache_key: str, selected_match):
    """Tek bir sezonun puan durumu tablosunu goster."""
    df = get_league_standings(league, season, cache_key)

    if df.empty:
        st.warning("Bu lig ve sezon icin puan durumu hesaplanamadi.")
        return

    # Secili mac varsa takimlari vurgula
    if selected_match is not None:
        styled = highlight_standings(
            df,
            selected_match["Ev Sahibi"],
            selected_match["Deplasman"],
        )
        st.dataframe(styled, width="stretch")
    else:
        st.dataframe(df, width="stretch")


# ═══════════════════════════════════════════════
#  ANA FONKSIYON
# ═══════════════════════════════════════════════


def main():
    setup_page()

    # Baslik ve lig secimi
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Yaklasan Maclar ve Guncel Oranlar")
    with col2:
        league = st.selectbox(
            "Lig Seciniz:",
            list(SUPPORTED_LEAGUES.keys()),
            label_visibility="collapsed",
        )

    # Sidebar ayarlari
    st.sidebar.header("Ayarlar")
    st.sidebar.markdown(f"**Aktif Lig:** {league}")
    st.sidebar.markdown("Kiyaslama yapilacak gecmis sezonu secin.")

    seasons = get_seasons()
    season = st.sidebar.selectbox("Gecmis Sezon:", seasons, index=1)

    # API kota bilgisi
    usage = get_api_usage()
    if usage:
        remaining = int(usage["remaining"])
        used = int(usage["used"]) if usage["used"] != "?" else 0
        total = remaining + used
        pct = remaining / total if total > 0 else 0
        st.sidebar.markdown("---")
        st.sidebar.markdown("**🔑 API Kota Durumu**")
        st.sidebar.progress(pct, text=f"{remaining} / {total} istek kaldi")
        if remaining < 50:
            st.sidebar.warning("⚠️ API kotaniz azaliyor!")

    st.sidebar.divider()
    st.sidebar.markdown(
        "Iddaa oranlari yabanci sitelerden alinarak karsilastirilmistir. "
        "Ufak virgulsul farklar olabilir."
    )

    # Veri yukle
    if st.sidebar.button("Verileri Guncelle"):
        get_season_data.clear()
        get_upcoming_fixtures.clear()
        hist = fetch_and_process(league, season, force=True)
        st.sidebar.success("Guncellendi." if not hist.empty else "Veri cekilemedi.")
    else:
        hist = get_season_data(league, season)

    upcoming = get_upcoming_fixtures(league)

    # Sekmeler
    tab1, tab2 = st.tabs(["📊 Canlı Oran Analizi", "🏆 Puan Durumu"])

    with tab1:
        selected_match = render_analysis_tab(upcoming, hist, league)

    with tab2:
        render_standings_tab(league, season, selected_match)


if __name__ == "__main__":
    main()
