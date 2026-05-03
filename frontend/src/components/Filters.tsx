"use client";

import { useState, useEffect } from "react";
import { API_URL } from "@/config/constants";

interface FiltersProps {
  onLeagueChange: (val: string) => void;
  onTimeRangeChange: (val: string) => void;
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

export default function Filters({ onLeagueChange, onTimeRangeChange }: FiltersProps) {
  const [leagues, setLeagues] = useState<string[]>([]);

  useEffect(() => {
    const fetchLeagues = async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/football/matches/leagues`, {
          credentials: "include"
        });
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
    <div className="flex flex-col md:flex-row items-center gap-4 w-full">
      {/* Lig Filtresi */}
      <div className="relative group flex-1">
        <select
          id="league-select"
          onChange={(e) => onLeagueChange(e.target.value)}
          className="bg-white/5 border border-white/10 text-white py-2.5 px-4 rounded-xl focus:outline-none focus:border-primary/50 transition-all w-full appearance-none cursor-pointer pr-10 text-[10px] font-black uppercase tracking-widest"
        >
          <option value="" className="bg-[#050505]">Tüm Ligler</option>
          {leagues.map((league) => (
            <option key={league} value={league} className="bg-[#050505]">
              {LEAGUE_NAME_TR[league] || league}
            </option>
          ))}
        </select>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500">
           <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
        </div>
      </div>

      {/* Saat Filtresi */}
      <div className="relative group w-48">
        <select
          id="time-range-select"
          onChange={(e) => onTimeRangeChange(e.target.value)}
          className="bg-white/5 border border-white/10 text-amber-500 py-2.5 px-4 rounded-xl focus:outline-none focus:border-amber-500/50 transition-all w-full appearance-none cursor-pointer pr-10 text-[10px] font-black uppercase tracking-widest"
        >
          <option value="all" className="bg-[#050505]">Tüm Saatler</option>
          <option value="15-18" className="bg-[#050505]">15:00 - 18:00</option>
          <option value="18-20" className="bg-[#050505]">18:00 - 20:00</option>
          <option value="20-00" className="bg-[#050505]">20:00 - 00:00</option>
        </select>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-amber-500/50">
           <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
        </div>
      </div>
    </div>
  );
}
