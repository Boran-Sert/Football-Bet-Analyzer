import { MatchResponse } from "@/types";

interface UpcomingMatchesTableProps {
  matches: MatchResponse[];
  selectedMatchId: string | null;
  onSelectMatch: (match: MatchResponse) => void;
}

export default function UpcomingMatchesTable({ matches, selectedMatchId, onSelectMatch }: UpcomingMatchesTableProps) {
  if (!matches || matches.length === 0) {
    return (
      <div className="w-full text-center py-8 bg-[#0a0f18] rounded-xl border border-slate-800">
        <p className="text-slate-500 text-sm">Gösterilecek maç bulunamadı.</p>
      </div>
    );
  }

  return (
    <div className="w-full overflow-x-auto rounded-xl border border-slate-800 bg-[#0a0f18]">
      <table className="w-full text-left text-sm whitespace-nowrap">
        <thead className="bg-[#111827] text-slate-400 border-b border-slate-800">
          <tr>
            <th className="px-4 py-3 w-10 text-center">#</th>
            <th className="px-4 py-3">Tarih</th>
            <th className="px-4 py-3">Ev Sahibi</th>
            <th className="px-4 py-3">Deplasman</th>
            <th className="px-4 py-3 text-right">MS 1</th>
            <th className="px-4 py-3 text-right">MS 0</th>
            <th className="px-4 py-3 text-right">MS 2</th>
            <th className="px-4 py-3 text-right">2.5 Alt</th>
            <th className="px-4 py-3 text-right">2.5 Üst</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/50">
          {matches.map((match) => {
            const isSelected = selectedMatchId === match.external_id;
            const h2h = match.odds.h2h;
            const totals = match.odds.totals;
            const dateStr = new Date(match.commence_time).toLocaleString("tr-TR", {
              month: "2-digit",
              day: "2-digit",
              hour: "2-digit",
              minute: "2-digit",
            });

            return (
              <tr 
                key={match.external_id} 
                onClick={() => onSelectMatch(match)}
                className={`cursor-pointer transition-colors hover:bg-slate-800/50 ${isSelected ? 'bg-blue-900/20' : 'bg-[#0a0f18]'}`}
              >
                <td className="px-4 py-3 text-center">
                  <input 
                    type="checkbox" 
                    checked={isSelected}
                    onChange={() => onSelectMatch(match)}
                    className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-blue-500 focus:ring-blue-500 focus:ring-offset-slate-900 cursor-pointer"
                  />
                </td>
                <td className="px-4 py-3 text-slate-400 text-xs">{dateStr}</td>
                <td className="px-4 py-3 font-semibold text-slate-200">{match.home_team}</td>
                <td className="px-4 py-3 font-semibold text-slate-200">{match.away_team}</td>
                
                {/* MS 1-0-2 */}
                <td className="px-4 py-3 text-right font-medium text-slate-300">{h2h?.home ? h2h.home.toFixed(2) : '-'}</td>
                <td className="px-4 py-3 text-right font-medium text-slate-300">{h2h?.draw ? h2h.draw.toFixed(2) : '-'}</td>
                <td className="px-4 py-3 text-right font-medium text-slate-300">{h2h?.away ? h2h.away.toFixed(2) : '-'}</td>
                
                {/* Totals */}
                <td className="px-4 py-3 text-right font-medium text-slate-300">{totals?.under_2_5 ? totals.under_2_5.toFixed(2) : '-'}</td>
                <td className="px-4 py-3 text-right font-medium text-slate-300">{totals?.over_2_5 ? totals.over_2_5.toFixed(2) : '-'}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
