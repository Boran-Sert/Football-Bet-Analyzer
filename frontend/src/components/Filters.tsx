"use client";

import { useState, useEffect } from "react";

interface FiltersProps {
  onLeagueChange: (val: string) => void;
}

const LEAGUE_NAME_TR: Record<string, string> = {
  "soccer_epl": "İngiltere Premier Lig",
  "soccer_efl_champ": "İngiltere Championship",
  "soccer_spain_la_liga": "İspanya La Liga",
  "soccer_spain_segunda_division": "İspanya La Liga 2",
  "soccer_germany_bundesliga": "Almanya Bundesliga",
  "soccer_germany_bundesliga2": "Almanya 2. Bundesliga",
  "soccer_italy_serie_a": "İtalya Serie A",
  "soccer_italy_serie_b": "İtalya Serie B",
  "soccer_france_ligue_one": "Fransa Ligue 1",
  "soccer_france_ligue_two": "Fransa Ligue 2",
  "soccer_turkey_super_league": "Türkiye Süper Lig",
  "soccer_netherlands_eredivisie": "Hollanda Eredivisie",
  "soccer_belgium_first_div": "Belçika Pro League",
};

export default function Filters({ onLeagueChange }: FiltersProps) {
  const [leagues, setLeagues] = useState<string[]>([]);

  useEffect(() => {
    const fetchLeagues = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/v1/football/matches/leagues");
        if (res.ok) {
          const data = await res.json();
          // Sadece tanımlı olduğumuz ve veri çektiğimiz ligleri göster
          const filtered = data.filter((l: string) => LEAGUE_NAME_TR[l]);
          setLeagues(filtered);
        }
      } catch (err) {
        console.error("Leagues fetch error", err);
      }
    };
    fetchLeagues();
  }, []);

  return (
    <div className="flex items-center w-full">
      <div className="relative group w-full">
        <select
          id="league-select"
          onChange={(e) => onLeagueChange(e.target.value)}
          className="bg-transparent border border-white/10 text-white py-2 px-4 rounded-xl focus:outline-none focus:border-primary/50 transition-all w-full appearance-none cursor-pointer pr-10 text-[10px] font-black uppercase tracking-widest"
        >
          <option value="" className="bg-[#050505]">Tüm Ligler</option>
          {leagues.map((league) => (
            <option key={league} value={league} className="bg-[#050505]">
              {LEAGUE_NAME_TR[league]}
            </option>
          ))}
        </select>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500">
           <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
        </div>
      </div>
    </div>
  );
}
