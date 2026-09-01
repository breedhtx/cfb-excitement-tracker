import streamlit as st
import requests

st.set_page_config(page_title="CFB Excitement Radar", page_icon="🏈", layout="wide")

st.title("🏈 College Football Excitement Radar")
st.caption("Live games ranked by drama, score closeness, and upset potential.")

# Manual refresh button
if st.button("🔄 Refresh Scores"):
    st.rerun()

def get_live_cfb_games():
    url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get('events', [])
    except Exception as e:
        st.error(f"Error fetching live data: {e}")
    return []

def calculate_excitement(game):
    competition = game['competitions'][0]
    status = competition['status']
    state = status['type']['state']
    
    # 0 = Pre-game, 1 = In-progress, 2 = Final
    if state == 'pre':
        return 0, "Scheduled", "Upcoming"
    if state == 'post':
        return 5, "Final", "Game finished"
    
    period = status.get('period', 1)
    clock = status.get('displayClock', '0:00')
    competitors = competition['competitors']
    
    team1, team2 = competitors[0], competitors[1]
    name1, name2 = team1['team']['shortDisplayName'], team2['team']['shortDisplayName']
    score1, score2 = int(team1.get('score', 0)), int(team2.get('score', 0))
    rank1 = team1.get('curatedRank', {}).get('current', 99)
    rank2 = team2.get('curatedRank', {}).get('current', 99)
    
    diff = abs(score1 - score2)
    score = 0
    reasons = []

    # Score Closeness
    if diff == 0:
        score += 35
        reasons.append("Tied game")
    elif diff <= 3:
        score += 30
        reasons.append(f"Field goal game (±{diff})")
    elif diff <= 8:
        score += 20
        reasons.append(f"One-possession game (±{diff})")
    elif diff <= 14:
        score += 10
        reasons.append(f"Two-possession game (±{diff})")

    # Time factor
    if period > 4:
        score += 45
        reasons.append("🚨 OVERTIME")
    elif period == 4:
        score += 30
        reasons.append("4th Quarter Crunch")
    elif period == 3:
        score += 15

    # Upset factor
    is_upset = False
    if rank1 <= 25 and rank2 > 25 and score2 >= score1:
        is_upset = True
        reasons.append(f"Upset Alert: {name2} leads #{rank1} {name1}")
    elif rank2 <= 25 and rank1 > 25 and score1 >= score2:
        is_upset = True
        reasons.append(f"Upset Alert: {name1} leads #{rank2} {name2}")
    elif rank1 <= 25 and rank2 <= 25:
        score += 10
        reasons.append("Top 25 Matchup")
        
    if is_upset and period >= 3:
        score += 25

    total = min(100, score)
    status_label = f"Q{period} {clock}"
    return total, status_label, ", ".join(reasons) if reasons else "Normal play"

# Fetch & display
events = get_live_cfb_games()

if not events:
    st.info("No college football games currently found on ESPN's scoreboard.")
else:
    processed_games = []
    for event in events:
        comp = event['competitions'][0]
        home = comp['competitors'][0]
        away = comp['competitors'][1]
        
        home_rank = f"#{home.get('curatedRank', {}).get('current')} " if home.get('curatedRank', {}).get('current', 99) <= 25 else ""
        away_rank = f"#{away.get('curatedRank', {}).get('current')} " if away.get('curatedRank', {}).get('current', 99) <= 25 else ""
        
        home_str = f"{home_rank}{home['team']['shortDisplayName']}"
        away_str = f"{away_rank}{away['team']['shortDisplayName']}"
        
        broadcasts = comp.get('broadcasts', [{}])
        tv_name = broadcasts[0].get('names', ['N/A'])[0] if broadcasts else 'N/A'
        
        excitement, clock_status, note = calculate_excitement(event)
        
        processed_games.append({
            "away": away_str,
            "away_score": away.get('score', '0'),
            "home": home_str,
            "home_score": home.get('score', '0'),
            "score": excitement,
            "clock": clock_status,
            "tv": tv_name,
            "note": note
        })

    # Sort: highest excitement first
    processed_games.sort(key=lambda x: x['score'], reverse=True)

    for g in processed_games:
        # Visual color tag based on excitement score
        if g['score'] >= 65:
            badge = "🔥 **MUST WATCH**"
        elif g['score'] >= 40:
            badge = "👀 **WATCHABLE**"
        elif g['clock'] == "Upcoming":
            badge = "⏳ **UPCOMING**"
        elif g['clock'] == "Final":
            badge = "🏁 **FINAL**"
        else:
            badge = "💤 **LOW DRAMA**"

        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.subheader(f"{g['away']} {g['away_score']}  @  {g['home']} {g['home_score']}")
                st.caption(f"Status: **{g['clock']}** | Channel: **{g['tv']}**")
                if g['note'] not in ["Upcoming", "Game finished", "Normal play"]:
                    st.write(f"⚡ *{g['note']}*")
            with col2:
                st.metric("Excitement Index", f"{g['score']}/100")
            with col3:
                st.write(badge)
