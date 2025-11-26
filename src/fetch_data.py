import requests
import os
from dotenv import load_dotenv
import pandas as pd
import time

# Load API key
load_dotenv()
API_KEY = os.getenv('RIOT_API_KEY')

# API Configuration
BASE_URL = "https://americas.api.riotgames.com"
REGION_URL = "https://na1.api.riotgames.com"

def get_challenger_players(queue='RANKED_SOLO_5x5', limit=50):
    """Get top challenger players as starting point"""
    url = f"{REGION_URL}/lol/league/v4/challengerleagues/by-queue/{queue}"
    headers = {"X-Riot-Token": API_KEY}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        players = data['entries'][:limit]
        return [{'puuid': p['puuid'],
                 'tier': 'CHALLENGER',
                 'rank': p['rank'],
                 'leaguePoints': p['leaguePoints'],
                 'wins': p['wins'],
                 'losses': p['losses']} for p in players]
    else:
        print(f"Error: {response.status_code}")
        return []

def get_summoner_puuid(summoner_id):
    """Get PUUID needed for match history"""
    url = f"{REGION_URL}/lol/summoner/v4/summoners/{summoner_id}"
    headers = {"X-Riot-Token": API_KEY}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['puuid']
    return None

def get_match_history(puuid, count=20):
    """Get recent match IDs for a player"""
    url = f"{BASE_URL}/lol/match/v5/matches/by-puuid/{puuid}/ids"
    headers = {"X-Riot-Token": API_KEY}
    params = {'count': count}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return []

def collect_player_match_data(players_df, matches_per_player=20):
    """Collect match history for all players"""
    all_matches = []

    for idx, row in players_df.iterrows():
        puuid = row['puuid']
        print(f"Processing player {idx+1}/{len(players_df)}...")

        # Get match IDs
        match_ids = get_match_history(puuid, count=matches_per_player)

        for match_id in match_ids:
            all_matches.append({
                'puuid': puuid,
                'matchId': match_id,
                'wins': row['wins'],
                'losses': row['losses'],
                'leaguePoints': row['leaguePoints']
            })

        time.sleep(1.2)  # Rate limit protection

    return pd.DataFrame(all_matches)

if __name__ == "__main__":
    print("Fetching Challenger players...")
    players = get_challenger_players(limit=10)

    print(f"Found {len(players)} players")
    print("\nSample players:")
    for p in players[:3]:
        print(f"- PUUID: {p['puuid'][:20]}...: {p['wins']}W / {p['losses']}L ({p['leaguePoints']} LP)")

    # Save to CSV
    df = pd.DataFrame(players)
    df.to_csv('data/raw/challenger_players.csv', index=False)
    print(f"\nSaved {len(players)} players to data/raw/challenger_players.csv")

    # Collect match history
    print("\n" + "="*50)
    print("Collecting match history...")
    print("="*50)

    matches_df = collect_player_match_data(df, matches_per_player=20)

    matches_df.to_csv('data/raw/player_matches.csv', index=False)
    print(f"\n✓ Saved {len(matches_df)} match records to data/raw/player_matches.csv")