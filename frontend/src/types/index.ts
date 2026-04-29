export interface H2HOdds {
  home: number;
  draw: number;
  away: number;
}

export interface TotalsOdds {
  over_1_5?: number | null;
  under_1_5?: number | null;
  over_2_5?: number | null;
  under_2_5?: number | null;
  over_3_5?: number | null;
  under_3_5?: number | null;
}

export interface BTTSOdds {
  yes?: number | null;
  no?: number | null;
}

export interface MatchOdds {
  h2h?: H2HOdds | null;
  totals?: TotalsOdds | null;
  btts?: BTTSOdds | null;
}

export interface MatchMetrics {
  home_goals?: number | null;
  away_goals?: number | null;
  total_goals?: number | null;
  
  home_ht_goals?: number | null;
  away_ht_goals?: number | null;

  home_corners?: number | null;
  away_corners?: number | null;
  total_corners?: number | null;
  
  home_yellow?: number | null;
  away_yellow?: number | null;
  total_yellow?: number | null;
  
  home_red?: number | null;
  away_red?: number | null;
  total_red?: number | null;
}

export interface MatchResponse {
  external_id: string;
  sport: string;
  league_key: string;
  league_title: string;
  home_team: string;
  away_team: string;
  commence_time: string; // ISO date string
  status: 'upcoming' | 'live' | 'completed';
  odds: MatchOdds;
  metrics: MatchMetrics;
}

export interface SimilarMatchResult {
  match: MatchResponse;
  distance: number;
  similarity_percentage: number;
}
