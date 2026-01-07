import pandas as pd
import numpy as np
from nba_api.stats.endpoints import leaguedashplayerstats, leaguedashteamstats
import io
import re
import difflib
import unicodedata

# --- Configuration ---
SEASON_ID = '2025-26'
MIN_GAMES = 16
LEAGUE_AVG_TS = 0.58
LEAGUE_AVG_3P = 0.36  # 36% league avg

# --- Minutes filter ---
MIN_MINUTES_ELITE = 28.0
MIN_MINUTES_ROTATION = 20.0

# --- Manual Dictionary ---
NICKNAME_MAP = {
    "Jimmy Butler": "Jimmy Butler III",
    "Jayson Tatum": "Jayson Tatum",
    "Damian Lillard": "Damian Lillard",
    "Tyrese Haliburton": "Tyrese Haliburton",
    "Kyrie Irving": "Kyrie Irving",
    "Dejounte Murray": "Dejounte Murray",
    "Fred VanVleet": "Fred VanVleet",
    "Terry Rozier": "Terry Rozier III",
    "Trey Murphy III": "Trey Murphy III",
    "Scoot Henderson": "Scoot Henderson",
    "Alperen ?engn": "Alperen Sengun",
    "Cameron Thomas": "Cam Thomas",
    "Nicolas Claxton": "Nic Claxton",
    "Gregory Jackson": "GG Jackson",
    "Kenneth Lofton": "Kenny Lofton Jr.",
    "Robert Williams": "Robert Williams III",
    "Grant Williams": "Grant Williams",
    "Max Strus": "Max Strus",
    "Kelly Oubre Jr.": "Kelly Oubre Jr.",
    "Gary Trent Jr.": "Gary Trent Jr.",
    "Kevin Porter Jr.": "Kevin Porter Jr.",
    "Xavier Tillman Sr.": "Xavier Tillman"
}

# --- 1. Extraction ---
def get_raw_salaries(csv_path='/content/salarios_nba.csv'):
    print(f"1. Loading salaries...")
    try:
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        header_row = 0
        for i, line in enumerate(lines):
            if 'Player' in line and ('Salary' in line or 'Tm' in line):
                header_row = i
                break

        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            df = pd.read_csv(f, header=header_row)

        if 'Player' not in df.columns:
            cols = [c for c in df.columns if 'Player' in str(c)]
            if cols: df = df.rename(columns={cols[0]: 'Player'})
            else: df = df.rename(columns={df.columns[1]: 'Player'})

        salary_col = [c for c in df.columns if '2025' in str(c) or '2026' in str(c)]
        final_col = salary_col[0] if salary_col else df.columns[3]

        df = df[['Player', final_col]].copy()
        df.columns = ['Player', 'Salary']
        df = df[df['Player'] != 'Player']

        df['Salary'] = df['Salary'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
        df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce')
        df = df.dropna(subset=['Salary']).drop_duplicates(subset=['Player'])
        return df
    except Exception as e:
        print(f"Error CSV: {e}")
        return pd.DataFrame()

def get_all_player_stats():
    print(f"2. API NBA: Getting stats...")
    try:
        # 1. Advanced stats (PIE, TS%, USG%)
        advanced = leaguedashplayerstats.LeagueDashPlayerStats(
            season=SEASON_ID, measure_type_detailed_defense='Advanced'
        ).get_data_frames()[0]

        # 2. Base Stats (FG3A, FG3_PCT, GP, MIN)
        base = leaguedashplayerstats.LeagueDashPlayerStats(
            season=SEASON_ID, measure_type_detailed_defense='Base'
        ).get_data_frames()[0]

        # 3. Merge both tables using PLAYER_ID
        cols_to_use = base[['PLAYER_ID', 'FG3M', 'FG3A', 'FG3_PCT']]
        df_merged = pd.merge(advanced, cols_to_use, on='PLAYER_ID', how='left')

        return df_merged
    except Exception as e:
        print(f"Error API: {e}")
        return pd.DataFrame()

def get_team_stats():
    try:
        stats = leaguedashteamstats.LeagueDashTeamStats(season=SEASON_ID, measure_type_detailed_defense='Advanced')
        return stats.get_data_frames()[0][['TEAM_ID', 'TEAM_NAME', 'NET_RATING']]
    except: return pd.DataFrame()

# --- Fix names with special characters ---
def fix_broken_names(df_csv, df_api):
    print("\n🔧 Repairing names...")
    api_names = df_api['PLAYER_NAME'].unique().tolist()

    def find_match(dirty_name):
        if dirty_name in NICKNAME_MAP:
            target = NICKNAME_MAP[dirty_name]
            if target in api_names: return target
        if dirty_name in api_names: return dirty_name
        if '?' in dirty_name:
            pattern = '^' + dirty_name.replace('?', '.') + '$'
            for api_name in api_names:
                if len(api_name) == len(dirty_name):
                    match = re.match(pattern, api_name)
                    if match: return api_name
        matches = difflib.get_close_matches(dirty_name, api_names, n=1, cutoff=0.96)
        if matches: return matches[0]
        return None

    df_csv['MATCHED_NAME'] = df_csv['Player'].apply(find_match)
    return df_csv

# --- Visualisation ---
def format_euro_currency(val): return "{:,.0f}".format(val).replace(",", ".") if pd.notna(val) else "-"
def format_pct(val): return "{:.1f}%".format(val * 100).replace(".", ",") if pd.notna(val) else "-"
def format_dec(val): return "{:.1f}".format(val).replace(".", ",") if pd.notna(val) else "-"
def format_score(val): return "{:.1f}".format(val).replace(".", ",") if pd.notna(val) else "-"

def finalize_and_print(df, title):
    if df.empty:
        print(f"\n--- {title} ---\n(Any player matches the criteria)")
        return
    df_show = df.copy()
    if 'PLAYER_NAME' in df_show.columns:
        df_show['Player'] = df_show['PLAYER_NAME']
    df_show['Salary_Formatted'] = df_show['Salary'].apply(format_euro_currency)

    # Add 3P% column
    if 'FG3_PCT' in df_show.columns:
        df_show['3P%'] = df_show['FG3_PCT'].apply(format_pct)
        cols = ['Player', 'Salary_Formatted', 'USG_PCT', 'TS_PCT', '3P%', 'PIE', 'REL_NET_RATING', 'SCORE']
    else:
        cols = ['Player', 'Salary_Formatted', 'USG_PCT', 'TS_PCT', 'PIE', 'REL_NET_RATING', 'SCORE']

    for col in ['TS_PCT', 'USG_PCT', 'PIE']:
        df_show[col] = df_show[col].apply(format_pct)
    df_show['REL_NET_RATING'] = df_show['REL_NET_RATING'].apply(format_dec)
    df_show['SCORE'] = df_show['SCORE'].apply(format_score)

    print(f"\n--- {title} ---")
    print(df_show[cols].reset_index(drop=True).to_string(index=False))

# --- Main ---
def main():
    df_salaries = get_raw_salaries()
    df_players = get_all_player_stats()
    df_teams = get_team_stats()

    if df_salaries.empty or df_players.empty: return None, None, None, None, None, None

    df_salaries = fix_broken_names(df_salaries, df_players)
    df_merged = pd.merge(df_salaries, df_players, left_on='MATCHED_NAME', right_on='PLAYER_NAME', how='inner')

    df_teams = df_teams.rename(columns={'NET_RATING': 'TEAM_NET_RATING'})
    df_final = pd.merge(df_merged, df_teams[['TEAM_ID', 'TEAM_NET_RATING']], on='TEAM_ID', how='inner')

    df_final['REL_NET_RATING'] = df_final['NET_RATING'] - df_final['TEAM_NET_RATING']

    # --- Global filter ---
    df_final = df_final[df_final['GP'] >= MIN_GAMES]

    # 1. Calculate attempted 3P per game
    df_final['FG3A_PG'] = df_final['FG3A'] / df_final['GP']

    # 2. Updated formula
    df_final['SCORE'] = (
        (df_final['PIE'] * 100) +
        df_final['REL_NET_RATING'] +
        ((df_final['TS_PCT'] - LEAGUE_AVG_TS) * 100) +
        (df_final['USG_PCT'] * 20) +
        ((df_final['FG3_PCT'] - LEAGUE_AVG_3P) * df_final['FG3A_PG'] * 15) # Factor Francotirador
    )

    # 1. Toxic contracts
    df_blacklist = df_final[
        (df_final['Salary'] > 20000000) &
        (df_final['USG_PCT'] > 0.23) &
        (df_final['MIN'] >= MIN_MINUTES_ROTATION)
    ].sort_values('SCORE', ascending=True).head(5)

    # 2. Fading stars
    excluded_blacklist = df_blacklist['Player'].tolist()

    df_paper_stars = df_final[
        (df_final['Salary'] > 30000000) &
        (df_final['REL_NET_RATING'] < 0.0) &
        (df_final['MIN'] >= MIN_MINUTES_ROTATION) &
        (~df_final['Player'].isin(excluded_blacklist))
    ].sort_values('SCORE', ascending=True).head(5)

    # 3. Silent killers
    excluded_all_bad = pd.concat([df_blacklist['Player'], df_paper_stars['Player']])

    df_albatross = df_final[
        (df_final['Salary'] > 18000000) &
        (df_final['USG_PCT'] <= 0.23) &
        (df_final['REL_NET_RATING'] < 1.5) &
        (df_final['MIN'] >= MIN_MINUTES_ROTATION) &
        (~df_final['Player'].isin(excluded_all_bad))
    ].sort_values('SCORE', ascending=True).head(5)

    # 4. Elite
    df_elite = df_final[
        (df_final['Salary'] > 30000000) &
        (df_final['MIN'] >= MIN_MINUTES_ELITE)
    ].sort_values('SCORE', ascending=False).head(5)

    # 5. Bargains
    df_bargains = df_final[
        (df_final['Salary'] < 15000000) &
        (df_final['REL_NET_RATING'] > 2.0) &
        (df_final['MIN'] >= MIN_MINUTES_ROTATION)
    ].sort_values('SCORE', ascending=False).head(10)

    print("\n" + "="*60)
    print(f"      Salary audit")
    print("="*60)

    finalize_and_print(df_blacklist, "Table 1: Toxic Contracts")
    finalize_and_print(df_paper_stars, "Table 2: Fading stars")
    finalize_and_print(df_albatross, "Table 3: Silent Killers")
    finalize_and_print(df_elite, "Table 4: Elite")
    finalize_and_print(df_bargains, "Table 5: Bargains")

    return df_final, df_blacklist, df_paper_stars, df_albatross, df_elite, df_bargains

if __name__ == "__main__":
    df_final, df_blacklist, df_paper_stars, df_albatross, df_elite, df_bargains = main()
