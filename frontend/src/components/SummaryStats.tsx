import { SimilarMatchResult } from "@/types";

interface SummaryStatsProps {
  results: SimilarMatchResult[];
}

export default function SummaryStats({ results }: SummaryStatsProps) {
  if (!results || results.length === 0) {
    return null;
  }

  const totalMatches = results.length;
  let homeWins = 0;
  let draws = 0;
  let awayWins = 0;
  let totalGoalsSum = 0;

  results.forEach(item => {
    const m = item.match.metrics;
    const hg = m.home_goals ?? 0;
    const ag = m.away_goals ?? 0;

    if (hg > ag) homeWins++;
    else if (ag > hg) awayWins++;
    else draws++;

    totalGoalsSum += (m.total_goals ?? (hg + ag));
  });

  const avgGoals = (totalGoalsSum / totalMatches).toFixed(1);

  return (
    <div className="w-full mt-6 flex flex-col md:flex-row justify-between items-start md:items-center px-4">
      <div className="flex flex-col mb-4 md:mb-0">
        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Ev Sahibi Galibiyeti</span>
        <span className="text-3xl font-black text-slate-100">{homeWins}/{totalMatches}</span>
      </div>
      <div className="flex flex-col mb-4 md:mb-0">
        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Beraberlik</span>
        <span className="text-3xl font-black text-slate-100">{draws}/{totalMatches}</span>
      </div>
      <div className="flex flex-col mb-4 md:mb-0">
        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Deplasman Galibiyeti</span>
        <span className="text-3xl font-black text-slate-100">{awayWins}/{totalMatches}</span>
      </div>
      <div className="flex flex-col mb-4 md:mb-0">
        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Ort. Toplam Gol</span>
        <span className="text-3xl font-black text-slate-100">{avgGoals}</span>
      </div>
    </div>
  );
}
