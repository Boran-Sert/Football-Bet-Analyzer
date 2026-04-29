import { SimilarMatchResult } from "@/types";

interface SimilarMatchesTableProps {
  results: SimilarMatchResult[];
}

export default function SimilarMatchesTable({ results }: SimilarMatchesTableProps) {
  if (!results || results.length === 0) {
    return null;
  }

  return (
    <div className="w-full mt-4">
      <div className="w-full bg-[#166534] px-4 py-2 text-xs font-bold text-green-100 rounded-t-lg border-b-0 border border-slate-700">
        En yakın {results.length} benzer iş eşleşmesi
      </div>
      <div className="w-full overflow-x-auto border border-slate-800 bg-[#0a0f18] rounded-b-lg">
        <table className="w-full text-left text-[10px] md:text-xs whitespace-nowrap">
          <thead className="bg-[#111827] text-slate-400 border-b border-slate-800">
            <tr>
              <th className="px-3 py-2 font-medium">Tarih</th>
              <th className="px-3 py-2 font-medium">Ev Sahibi</th>
              <th className="px-3 py-2 font-medium">Deplasman</th>
              <th className="px-3 py-2 font-medium text-center">Ev Sahibi Gol</th>
              <th className="px-3 py-2 font-medium text-center">Deplasman Gol</th>
              <th className="px-3 py-2 font-medium text-center">Ev Sahibi Sarı Kart</th>
              <th className="px-3 py-2 font-medium text-center">Deplasman Sarı Kart</th>
              <th className="px-3 py-2 font-medium text-center">Ev Sahibi Kırmızı Kart</th>
              <th className="px-3 py-2 font-medium text-center">Deplasman Kırmızı Kart</th>
              <th className="px-3 py-2 font-medium text-center">Ev Sahibi Korner</th>
              <th className="px-3 py-2 font-medium text-center">Deplasman Korner</th>
              <th className="px-3 py-2 font-medium text-right">MS 1</th>
              <th className="px-3 py-2 font-medium text-right">MS 0</th>
              <th className="px-3 py-2 font-medium text-right">MS 2</th>
              <th className="px-3 py-2 font-medium text-right">2.5 Alt</th>
              <th className="px-3 py-2 font-medium text-right">2.5 Üst</th>
              <th className="px-3 py-2 font-medium text-center">Toplam Korner</th>
              <th className="px-3 py-2 font-medium text-center">Toplam Sarı Kart</th>
              <th className="px-3 py-2 font-medium text-center">Toplam Kırmızı Kart</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {results.map((item) => {
              const match = item.match;
              const h2h = match.odds.h2h;
              const totals = match.odds.totals;
              const m = match.metrics;
              
              const hg = m.home_goals ?? 0;
              const ag = m.away_goals ?? 0;
              
              const homeWon = hg > ag;
              const awayWon = ag > hg;
              const draw = hg === ag;

              // Cell Backgrounds
              const homeBg = homeWon ? 'bg-green-900/40 text-green-300' : (awayWon ? 'bg-red-900/40 text-red-300' : 'bg-yellow-900/40 text-yellow-300');
              const awayBg = awayWon ? 'bg-green-900/40 text-green-300' : (homeWon ? 'bg-red-900/40 text-red-300' : 'bg-yellow-900/40 text-yellow-300');

              const dateStr = match.commence_time.split("T")[0];

              return (
                <tr key={match.external_id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-3 py-2 text-slate-400">{dateStr}</td>
                  <td className={`px-3 py-2 font-bold ${homeBg}`}>{match.home_team}</td>
                  <td className={`px-3 py-2 font-bold ${awayBg}`}>{match.away_team}</td>
                  
                  <td className="px-3 py-2 text-center text-slate-300">{hg}</td>
                  <td className="px-3 py-2 text-center text-slate-300">{ag}</td>
                  
                  <td className="px-3 py-2 text-center text-slate-400">{m.home_yellow ?? '-'}</td>
                  <td className="px-3 py-2 text-center text-slate-400">{m.away_yellow ?? '-'}</td>
                  
                  <td className="px-3 py-2 text-center text-slate-400">{m.home_red ?? '-'}</td>
                  <td className="px-3 py-2 text-center text-slate-400">{m.away_red ?? '-'}</td>
                  
                  <td className="px-3 py-2 text-center text-slate-400">{m.home_corners ?? '-'}</td>
                  <td className="px-3 py-2 text-center text-slate-400">{m.away_corners ?? '-'}</td>
                  
                  <td className="px-3 py-2 text-right font-medium text-slate-300">{h2h?.home ? h2h.home.toFixed(2) : '-'}</td>
                  <td className="px-3 py-2 text-right font-medium text-slate-300">{h2h?.draw ? h2h.draw.toFixed(2) : '-'}</td>
                  <td className="px-3 py-2 text-right font-medium text-slate-300">{h2h?.away ? h2h.away.toFixed(2) : '-'}</td>
                  
                  <td className="px-3 py-2 text-right font-medium text-slate-300">{totals?.under_2_5 ? totals.under_2_5.toFixed(2) : '-'}</td>
                  <td className="px-3 py-2 text-right font-medium text-slate-300">{totals?.over_2_5 ? totals.over_2_5.toFixed(2) : '-'}</td>
                  
                  <td className="px-3 py-2 text-center font-bold text-slate-300">{m.total_corners ?? '-'}</td>
                  <td className="px-3 py-2 text-center font-bold text-slate-300">{m.total_yellow ?? '-'}</td>
                  <td className="px-3 py-2 text-center font-bold text-slate-300">{m.total_red ?? '-'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
