"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "../lib/api";

const LEAGUES = [
  "Türkiye Süper Lig",
  "İngiltere Premier Lig",
  "İspanya La Liga",
  "İtalya Serie A",
  "Almanya Bundesliga",
  "Fransa Ligue 1",
];

const SEASONS = [
  "2025-2026",
  "2024-2025",
  "2023-2024",
];

export default function HomePage() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [league, setLeague] = useState("");
  const [season, setSeason] = useState("2024-2025");
  const [matches, setMatches] = useState([]);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [topN, setTopN] = useState(5);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  /* Kullanici kontrolu */
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }
    api.getMe().then(setUser).catch(() => {
      localStorage.removeItem("token");
      router.push("/login");
    });
  }, [router]);

  /* Maclari cek */
  const fetchMatches = useCallback(async () => {
    setLoading(true);
    setSelectedMatch(null);
    setAnalysis(null);
    try {
      const data = await api.getMatches({
        league: league || undefined,
        season: season || undefined,
      });
      setMatches(data);
    } catch {
      setMatches([]);
    } finally {
      setLoading(false);
    }
  }, [league, season]);

  useEffect(() => {
    if (user) fetchMatches();
  }, [user, league, season, fetchMatches]);

  /* Analiz baslat */
  const handleAnalyze = async (match) => {
    setSelectedMatch(match.id);
    setAnalyzing(true);
    try {
      const data = await api.analyze(match.id, topN);
      setAnalysis(data);
    } catch {
      setAnalysis(null);
    } finally {
      setAnalyzing(false);
    }
  };

  /* Cikis */
  const logout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  if (!user) return <div className="spinner" />;

  return (
    <>
      {/* NAVBAR */}
      <nav className="navbar">
        <div className="container">
          <a className="navbar-brand" href="/">⚽ <span>Football</span>SaaS</a>
          <div className="navbar-user">
            <span>👤 {user.username}</span>
            <button className="btn btn-ghost btn-sm" onClick={logout}>Çıkış</button>
          </div>
        </div>
      </nav>

      <main className="container" style={{ paddingTop: 28, paddingBottom: 60 }}>
        {/* FILTRELER */}
        <div className="filters-bar">
          <div className="select-wrapper">
            <select className="select" value={league} onChange={(e) => setLeague(e.target.value)}>
              <option value="">Tüm Ligler</option>
              {LEAGUES.map((l) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>
          <div className="select-wrapper">
            <select className="select" value={season} onChange={(e) => setSeason(e.target.value)}>
              <option value="">Tüm Sezonlar</option>
              {SEASONS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className="select-wrapper" style={{ maxWidth: 160 }}>
            <select className="select" value={topN} onChange={(e) => setTopN(Number(e.target.value))}>
              {[3, 5, 10, 15, 20].map((n) => (
                <option key={n} value={n}>Top {n} benzer</option>
              ))}
            </select>
          </div>
        </div>

        {/* MACLAR */}
        <h2 className="section-title">
          📅 Maçlar
          {matches.length > 0 && <span style={{ color: "var(--text-muted)", fontWeight: 400, fontSize: "0.85rem" }}> ({matches.length} maç)</span>}
        </h2>
        {loading ? (
          <div className="spinner" />
        ) : matches.length === 0 ? (
          <div className="empty-state">
            <div className="icon">🏟️</div>
            <p>Seçili filtrelerle maç bulunamadı.</p>
          </div>
        ) : (
          <div className="match-grid">
            {matches.map((m) => {
              const hg = m.home_goals;
              const ag = m.away_goals;
              const isFinished = m.status === "finished" && hg !== null;

              return (
                <div
                  key={m.id}
                  className={`match-card ${selectedMatch === m.id ? "active" : ""}`}
                  onClick={() => handleAnalyze(m)}
                >
                  <div className="league-badge">{m.league}</div>
                  <div className="teams">
                    <span className={`team-name ${isFinished ? (hg > ag ? "winner" : hg < ag ? "loser" : "draw-team") : ""}`}>
                      {m.home_team}
                    </span>
                    {isFinished ? (
                      <span className="vs" style={{ fontWeight: 700, fontSize: "1rem", color: "var(--text-primary)" }}>
                        {hg} - {ag}
                      </span>
                    ) : (
                      <span className="vs">VS</span>
                    )}
                    <span className={`team-name ${isFinished ? (ag > hg ? "winner" : ag < hg ? "loser" : "draw-team") : ""}`} style={{ textAlign: "right" }}>
                      {m.away_team}
                    </span>
                  </div>
                  <div className="match-date">
                    {new Date(m.match_date).toLocaleDateString("tr-TR", {
                      day: "numeric", month: "long", year: "numeric",
                    })}
                  </div>
                  {m.odds_home && (
                    <div className="odds-row">
                      <div className="odds-badge">1<strong>{m.odds_home?.toFixed(2)}</strong></div>
                      <div className="odds-badge">X<strong>{m.odds_draw?.toFixed(2)}</strong></div>
                      <div className="odds-badge">2<strong>{m.odds_away?.toFixed(2)}</strong></div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ANALIZ SONUCLARI */}
        {analyzing && <div className="spinner" />}
        {analysis && !analyzing && (
          <div className="analysis-panel">
            <h2 className="section-title">📊 Benzerlik Analizi Sonuçları</h2>

            {/* Istatistik kartlari */}
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-value" style={{ color: "var(--green)" }}>{analysis.home_win_pct}%</div>
                <div className="stat-label">Ev Sahibi Kazanır</div>
              </div>
              <div className="stat-card">
                <div className="stat-value" style={{ color: "var(--yellow)" }}>{analysis.draw_pct}%</div>
                <div className="stat-label">Beraberlik</div>
              </div>
              <div className="stat-card">
                <div className="stat-value" style={{ color: "var(--red)" }}>{analysis.away_win_pct}%</div>
                <div className="stat-label">Deplasman Kazanır</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{analysis.avg_total_goals}</div>
                <div className="stat-label">Ort. Toplam Gol</div>
              </div>
            </div>

            {/* Benzer maclar tablosu */}
            <div className="card" style={{ padding: 0, overflow: "hidden" }}>
              <table className="similar-table">
                <thead>
                  <tr>
                    <th>Tarih</th>
                    <th>Ev Sahibi</th>
                    <th>Skor</th>
                    <th>Deplasman</th>
                    <th>MS 1</th>
                    <th>MS X</th>
                    <th>MS 2</th>
                  </tr>
                </thead>
                <tbody>
                  {analysis.similar_matches.map((sm) => {
                    const hg = sm.home_goals ?? 0;
                    const ag = sm.away_goals ?? 0;
                    const homeClass = hg > ag ? "winner" : hg < ag ? "loser" : "draw-team";
                    const awayClass = ag > hg ? "winner" : ag < hg ? "loser" : "draw-team";

                    return (
                      <tr key={sm.id}>
                        <td style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                          {new Date(sm.match_date).toLocaleDateString("tr-TR")}
                        </td>
                        <td><span className={homeClass}>{sm.home_team}</span></td>
                        <td style={{ fontWeight: 700, textAlign: "center" }}>{hg} - {ag}</td>
                        <td><span className={awayClass}>{sm.away_team}</span></td>
                        <td>{sm.odds_home?.toFixed(2) ?? "-"}</td>
                        <td>{sm.odds_draw?.toFixed(2) ?? "-"}</td>
                        <td>{sm.odds_away?.toFixed(2) ?? "-"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
