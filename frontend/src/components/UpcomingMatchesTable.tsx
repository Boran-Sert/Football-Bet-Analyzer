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
    <div className="w-full overflow-x-auto">
      <table className="w-full text-left text-sm whitespace-nowrap">
        <thead className="bg-white/[0.03] text-slate-500 border-b border-white/5">
          <tr>
            <th className="px-6 py-4 w-10 text-center text-[10px] font-black uppercase tracking-widest">#</th>
            <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest">Tarih</th>
            <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest">Ev Sahibi</th>
            <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest">Deplasman</th>
            <th className="px-6 py-4 text-right text-[10px] font-black uppercase tracking-widest">MS 1</th>
            <th className="px-6 py-4 text-right text-[10px] font-black uppercase tracking-widest">MS 0</th>
            <th className="px-6 py-4 text-right text-[10px] font-black uppercase tracking-widest">MS 2</th>
            <th className="px-6 py-4 text-right text-[10px] font-black uppercase tracking-widest">2.5 Alt</th>
            <th className="px-6 py-4 text-right text-[10px] font-black uppercase tracking-widest">2.5 Üst</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
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
                className={`cursor-pointer transition-all duration-300 hover:bg-white/[0.04] relative ${isSelected ? 'bg-primary/20 ring-1 ring-primary z-10 shadow-[0_0_15px_rgba(16,185,129,0.3)]' : ''}`}
              >
                <td className="px-6 py-4 text-center">
                  <div className={`w-4 h-4 rounded-full border-2 transition-all ${isSelected ? 'bg-primary border-primary emerald-glow' : 'border-white/20'}`}></div>
                </td>
                <td className="px-6 py-4 text-slate-500 text-xs font-medium">{dateStr}</td>
                <td className="px-6 py-4 font-bold text-white text-sm">{match.home_team}</td>
                <td className="px-6 py-4 font-bold text-white text-sm">{match.away_team}</td>
                
                {/* MS 1-0-2 */}
                <td className="px-6 py-4 text-right font-black text-white">{h2h?.home ? h2h.home.toFixed(2) : '-'}</td>
                <td className="px-6 py-4 text-right font-black text-white">{h2h?.draw ? h2h.draw.toFixed(2) : '-'}</td>
                <td className="px-6 py-4 text-right font-black text-white">{h2h?.away ? h2h.away.toFixed(2) : '-'}</td>
                
                {/* Totals */}
                <td className="px-6 py-4 text-right font-black text-slate-400">{totals?.under_2_5 ? totals.under_2_5.toFixed(2) : '-'}</td>
                <td className="px-6 py-4 text-right font-black text-slate-400">{totals?.over_2_5 ? totals.over_2_5.toFixed(2) : '-'}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
