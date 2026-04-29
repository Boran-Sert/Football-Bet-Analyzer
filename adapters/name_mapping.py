"""Takim ismi ve lig kodu eslestirme sozlukleri.

Farkli veri kaynaklarindaki (Odds API vs Football-data.co.uk CSV)
takim isimleri ve lig kodlari burada normalize edilir.
"""

# ═══════════════════════════════════════════════
#  CSV LIG KODU → ODDS API SPORT KEY
# ═══════════════════════════════════════════════

LEAGUE_CODE_TO_API_KEY: dict[str, str] = {
    # İngiltere
    "E0": "soccer_epl",
    "E1": "soccer_efl_champ",
    # İspanya
    "SP1": "soccer_spain_la_liga",
    "SP2": "soccer_spain_segunda_division",
    # Almanya
    "D1": "soccer_germany_bundesliga",
    "D2": "soccer_germany_bundesliga2",
    # İtalya
    "I1": "soccer_italy_serie_a",
    "I2": "soccer_italy_serie_b",
    # Fransa
    "F1": "soccer_france_ligue_one",
    "F2": "soccer_france_ligue_two",
    # Türkiye
    "T1": "soccer_turkey_super_league",
    # Portekiz
    "P1": "soccer_portugal_primeira_liga",
    # Hollanda
    "N1": "soccer_netherlands_eredivisie",
    # Belçika
    "B1": "soccer_belgium_first_div",
    # Yunanistan
    "G1": "soccer_greece_super_league",
    # İskoçya
    "SC0": "soccer_spl",
}

# Ters mapping: API key → CSV lig kodu
API_KEY_TO_LEAGUE_CODE: dict[str, str] = {v: k for k, v in LEAGUE_CODE_TO_API_KEY.items()}

# ═══════════════════════════════════════════════
#  LIG KODU → İNSAN-OKUNUR İSİM
# ═══════════════════════════════════════════════

LEAGUE_TITLES: dict[str, str] = {
    "soccer_epl": "Premier League",
    "soccer_efl_champ": "EFL Championship",
    "soccer_spain_la_liga": "La Liga",
    "soccer_spain_segunda_division": "La Liga 2",
    "soccer_germany_bundesliga": "Bundesliga",
    "soccer_germany_bundesliga2": "2. Bundesliga",
    "soccer_italy_serie_a": "Serie A",
    "soccer_italy_serie_b": "Serie B",
    "soccer_france_ligue_one": "Ligue 1",
    "soccer_france_ligue_two": "Ligue 2",
    "soccer_turkey_super_league": "Süper Lig",
    "soccer_portugal_primeira_liga": "Primeira Liga",
    "soccer_netherlands_eredivisie": "Eredivisie",
    "soccer_belgium_first_div": "Belgian Pro League",
    "soccer_greece_super_league": "Super League Greece",
    "soccer_spl": "Scottish Premiership",
}

# ═══════════════════════════════════════════════
#  TAKIM İSMİ NORMALİZASYONU
#  CSV isimleri → Standart isimler
# ═══════════════════════════════════════════════

TEAM_NAME_MAP: dict[str, str] = {
    # İngiltere
    "Man United": "Manchester United",
    "Man City": "Manchester City",
    "Nott'm Forest": "Nottingham Forest",
    "Nottingham": "Nottingham Forest",
    "Newcastle": "Newcastle United",
    "Wolves": "Wolverhampton Wanderers",
    "Wolverhampton": "Wolverhampton Wanderers",
    "Tottenham": "Tottenham Hotspur",
    "West Ham": "West Ham United",
    "Sheffield United": "Sheffield United",
    "Sheffield Utd": "Sheffield United",
    "Brighton": "Brighton and Hove Albion",
    "Leicester": "Leicester City",
    "Leeds": "Leeds United",
    "Ipswich": "Ipswich Town",
    "Luton": "Luton Town",

    # İspanya
    "Ath Madrid": "Atletico Madrid",
    "Atletico": "Atletico Madrid",
    "Ath Bilbao": "Athletic Bilbao",
    "Betis": "Real Betis",
    "Sociedad": "Real Sociedad",
    "La Coruna": "Deportivo La Coruna",
    "Celta": "Celta Vigo",
    "Vallecano": "Rayo Vallecano",

    # Almanya
    "Dortmund": "Borussia Dortmund",
    "M'gladbach": "Borussia Monchengladbach",
    "Monchengladbach": "Borussia Monchengladbach",
    "Bayern Munich": "Bayern Munich",
    "Bayern": "Bayern Munich",
    "Leverkusen": "Bayer Leverkusen",
    "Ein Frankfurt": "Eintracht Frankfurt",
    "Frankfurt": "Eintracht Frankfurt",

    # İtalya
    "Inter": "Inter Milan",
    "AC Milan": "AC Milan",
    "Milan": "AC Milan",

    # Fransa
    "Paris SG": "Paris Saint Germain",
    "PSG": "Paris Saint Germain",
    "St Etienne": "Saint Etienne",
    "Marseille": "Olympique Marseille",
    "Lyon": "Olympique Lyonnais",

    # Türkiye
    "Galatasaray": "Galatasaray",
    "Fenerbahce": "Fenerbahce",
    "Besiktas": "Besiktas",
    "Trabzonspor": "Trabzonspor",
    "Basaksehir": "Istanbul Basaksehir",
    "Istanbulspor": "Istanbulspor",
    "Antalyaspor": "Antalyaspor",
    "Konyaspor": "Konyaspor",
    "Sivasspor": "Sivasspor",
    "Kasimpasa": "Kasimpasa",
    "Rizespor": "Caykur Rizespor",
    "Caykur Rizespor": "Caykur Rizespor",
    "Hatayspor": "Hatayspor",
    "Kayserispor": "Kayserispor",
    "Samsunspor": "Samsunspor",
    "Gaziantep FK": "Gaziantep FK",
    "Gaziantep": "Gaziantep FK",
    "Pendikspor": "Pendikspor",
    "Adana Demirspor": "Adana Demirspor",
    "Alanyaspor": "Alanyaspor",
    "Bodrumspor": "Bodrumspor",
    "Eyupspor": "Eyupspor",
    "Goztepe": "Goztepe",
}


def normalize_team_name(raw_name: str) -> str:
    """Takim ismini standart formata donusturur.

    Eger mapping'te yoksa orijinal ismi strip edip dondurur.
    """
    name = raw_name.strip()
    return TEAM_NAME_MAP.get(name, name)
