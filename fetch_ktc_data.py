import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime  # Import for date and time

# Base URL
base_url = "https://keeptradecut.com/dynasty-rankings"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# TEP Levels and constants
tep_levels = [1.1, 1.2, 1.3]  # TEP multipliers
MAXPLAYERVAL = 10000           # Maximum player value
rank_bonus_base = {1.1: 250, 1.2: 350, 1.3: 450}  # Rank bonuses for each TEP level
rank_bonus_factor = 0.2  # Fixed multiplier for rank adjustment

# Formats to include
formats = [1, 2]  # Format 1 and Format 2

# Get current date and time
current_datetime = datetime.now()
formatted_date = current_datetime.strftime("%Y-%m-%d")
formatted_time = current_datetime.strftime("%H:%M:%S")
day_of_week = current_datetime.strftime("%A")

# Data storage
all_players = []

# Loop through formats and pages
for format_type in formats:
    print(f"Fetching data for format {format_type}...")
    for page in range(0, 11):  # Adjust the range as needed
        print(f"Fetching page {page} for format {format_type}...")
        params = {
            "filters": "QB|WR|RB|TE|RDP",  # Positions
            "format": format_type,        # Current format
            "page": page
        }
        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            player_items = soup.find_all('div', class_='onePlayer')  # Each player's container

            for player in player_items:
                # Extract rank
                rank = int(player.find('div', class_='rank-number').find('p').text.strip()) if player.find('div', class_='rank-number') else "N/A"

                # Extract player name
                player_name = player.find('a').text.strip() if player.find('a') else "N/A"

                # Extract team
                team = player.find('span', class_='player-team').text.strip() if player.find('span', class_='player-team') else "N/A"

                # Extract position and clean it
                position_tag = player.find('div', class_='position-team').find('p', class_='position')
                position = re.sub(r'\d+', '', position_tag.text).strip() if position_tag else "N/A"  # Remove trailing digits

                # Extract age and clean it
                age_tag = player.find('div', class_='position-team').find_all('p', class_='position')
                age = age_tag[1].text.strip().replace(" y.o.", "") if len(age_tag) > 1 else "N/A"

                # Extract tier and clean it
                tier_tag = player.find('div', class_='player-info').find('p', class_='position')
                tier = tier_tag.text.replace("Tier ", "").strip() if tier_tag else "N/A"  # Remove "Tier" word

                # Extract trend and handle positive/negative
                trend_tag = player.find('div', class_='trend').find('p') if player.find('div', class_='trend') else None
                if trend_tag:
                    trend_value = trend_tag.text.strip()
                    if "trend-down" in trend_tag["class"]:
                        trend = f"-{trend_value}"  # Make it negative
                    else:
                        trend = trend_value  # Keep it positive
                else:
                    trend = "N/A"

                # Extract base value
                value = int(player.find('div', class_='value').find('p').text.strip()) if player.find('div', class_='value') else "N/A"

                # Append baseline value
                all_players.append({
                    "Date": formatted_date,
                    "Time": formatted_time,
                    "Day of Week": day_of_week,
                    "Format": format_type,
                    "Rank": rank,
                    "Name": player_name,
                    "Team": team,
                    "Position": position,  # Cleaned position (e.g., QB)
                    "Age": age,
                    "Tier": tier,  # Cleaned tier (e.g., 1)
                    "Trend": trend,  # Negative for "trend-down"
                    "Base Value": value,
                    "TEP Level": "Baseline",
                    "Adjusted Value": value  # Baseline value is the same as base value
                })

                # Calculate TEP values
                for tep_level in tep_levels:
                    if position == "TE":  # Only adjust for tight ends
                        adjusted_value = tep_level * value
                        rank_bonus = rank / 200 * rank_bonus_base[tep_level] + rank_bonus_factor * rank_bonus_base[tep_level]
                        adjusted_value += rank_bonus
                        adjusted_value = min(MAXPLAYERVAL - 1, round(adjusted_value))
                    else:
                        adjusted_value = value  # Keep base value for non-tight ends

                    # Append data for each TEP level
                    all_players.append({
                        "Date": formatted_date,
                        "Time": formatted_time,
                        "Day of Week": day_of_week,
                        "Format": format_type,
                        "Rank": rank,
                        "Name": player_name,
                        "Team": team,
                        "Position": position,  # Cleaned position (e.g., QB)
                        "Age": age,
                        "Tier": tier,  # Cleaned tier (e.g., 1)
                        "Trend": trend,  # Negative for "trend-down"
                        "Base Value": value,
                        "TEP Level": tep_level,
                        "Adjusted Value": adjusted_value
                    })
        else:
            print(f"Failed to fetch page {page} for format {format_type}, status code: {response.status_code}")
            break

# Convert to DataFrame
df = pd.DataFrame(all_players)

# Save to CSV
df.to_csv("dynasty_rankings_with_date_time.csv", index=False)

print("Scraping complete! Data saved to 'dynasty_rankings_with_date_time.csv'.")
