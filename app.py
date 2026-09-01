import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="CFB Excitement Radar & Quad-Box", page_icon="🏈", layout="wide")

# ESPN Conference / Group ID mapping
CONFERENCE_MAP = {
    "All FBS": 80,
    "SEC": 8,
    "Big Ten": 4,
    "Big 12": 9,
    "ACC": 1,
    "Pac-12": 15,
    "American (AAC)": 151,
    "Mountain West": 17,
    "Sun Belt": 37,
    "Conference USA": 12,
    "MAC": 15
}

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.title("🏈 Radar Controls")
    selected_conf = st.selectbox("Filter by Conference", list(CONFERENCE_MAP.keys()))
    top25_only = st.checkbox("Ranked Teams Only (Top 25)", value=False)
    live_only = st.checkbox("Live Games Only (Currently on TV)", value=False)
    
    st.divider()
    if st.button("🔄 Refresh Data Now"):
        st.rerun()
    st.caption("Auto-refreshes when filters change. ESPN scoreboard data updates in real-time.")

# --- API DATA FETCHER ---
@st.cache_data(ttl=30)
def fetch_games(group_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?groups={group_id}&limit=100"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json().get('events', [])
    except Exception as e:
        st.error(f"Error connecting to ESPN: {e}")
    return []

def parse_game(game):
    comp = game['competitions'][0]
    status = comp['status']
    state = status['type']['state'] # 'pre', 'in', 'post'
    
    period = status.get('period', 1)
    clock = status.get('displayClock', '0:00')
    detail = status['type'].get('detail', '')
    
    competitors = comp['competitors']
    home = competitors[0]
    away = competitors[1]
    
    home_name = home['team']['shortDisplayName']
    away_name = away['team']['shortDisplayName']
    home_score = int(home.get('score', 0))
    away_score = int(away.get('score', 0))
    
    home_rank = home.get('curatedRank', {}).get('current', 99)
    away_rank = away.get('curatedRank', {}).get('current', 99)
    
    broadcasts = comp.get('broadcasts', [{}])
    tv_name = broadcasts[0].get('names', ['TV N/A'])[0] if broadcasts else 'TV N/A'
    
    # Calculate Excitement Score (0 - 100)
    score = 0
    reasons = []
    
    if state == 'in':
        diff = abs(home_score - away_score)
        
        # Closeness
        if diff == 0:
            score += 35
            reasons.append("Tied")
        elif diff <= 3:
            score += 30
            reasons.append(f"±{diff} pts")
        elif diff <= 8:
            score += 20
            reasons.append(f"±{diff} pts")
        elif diff <= 14:
            score += 10
            reasons.append(f"±{diff} pts")
            
        # Quarter Leverage
        if period > 4:
            score += 45
            reasons.append("🚨 OVERTIME")
        elif period == 4:
            score += 30
            reasons.append("4th Quarter")
        elif period == 3:
            score += 15
            
        # Upset Alert
        if home_rank <= 25 and away_rank > 25 and away_score >= home_score:
            score += 25
            reasons.append(f"Upset: {away_name} over #{home_rank}")
        elif away_rank <= 25 and home_rank > 25 and home_score >= away_score:
            score += 25
            reasons.append(f"Upset: {home_name} over #{away_rank}")
        elif home_rank <= 25 and away_rank <= 25:
            score += 10
            reasons.append("Top 25 Matchup")
            
    elif state == 'post':
        score = 5
        reasons.append("Final")
    else:
        score = 0
        reasons.append("Upcoming")
        
    total_score = min(100, score)
    
    return {
        "id": game['id'],
        "state": state,
        "away_str": f"{f'#{away_rank} ' if away_rank <= 25 else ''}{away_name}",
        "home_str": f"{f'#{home_rank} ' if home_rank <= 25 else ''}{home_name}",
        "away_score": away_score,
        "home_score": home_score,
        "home_rank": home_rank,
        "away_rank": away_rank,
        "status_detail": detail,
        "tv": tv_name,
        "score": total_score,
        "note": ", ".join(reasons) if reasons else ""
    }

# --- LOAD DATA ---
group_id = CONFERENCE_MAP[selected_conf]
events = fetch_games(group_id)
parsed = [parse_game(e) for e in events]

# --- FILTERING ---
if top25_only:
    parsed = [g for g in parsed if g['home_rank'] <= 25 or g['away_rank'] <= 25]

if live_only:
    parsed = [g for g in parsed if g['state'] == 'in']

# Sort by Excitement Score descending
parsed.sort(key=lambda x: x['score'], reverse=True)
live_games = [g for g in parsed if g['state'] == 'in']

# --- APP HEADER ---
st.title("🏈 College Football Live Command Center")
st.caption(f"Showing **{selected_conf}** | {len(parsed)} games tracked")

# --- OPTIMAL 4-SCREEN SPLIT SCREEN SECTION ---
st.header("📺 Optimal Quad-Box Matrix (Top 4 Screens)")
st.caption("The 4 most exciting live games in this viewing window and what channels to tune into:")

if len(live_games) == 0:
    st.info("No games are currently live in this window. Upcoming games will appear below.")
else:
    quad_games = live_games[:4]
    
    # 2x2 Grid for Split Screen
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    grid_cols = [row1_col1, row1_col2, row2_col1, row2_col2]
    
    for idx, g in enumerate(quad_games):
        with grid_cols[idx]:
            with st.container(border=True):
                st.markdown(f"#### 🖥️ Screen {idx+1}: **{g['tv']}**")
                st.markdown(f"**{g['away_str']} {g['away_score']}** @ **{g['home_str']} {g['home_score']}**")
                st.write(f"⏱️ `{g['status_detail']}` | ⚡ **Index: {g['score']}/100**")
                if g['note']:
                    st.caption(f"*{g['note']}*")

st.divider()

# --- FULL SCOREBOARD ---
st.header("📋 All Tracked Games")

if not parsed:
    st.warning("No games match the selected filters.")
else:
    for g in parsed:
        if g['state'] == 'in':
            badge = "🔴 **ON TV NOW**"
            border_color = True
        elif g['state'] == 'post':
            badge = "🏁 **FINAL**"
            border_color = False
        else:
            badge = "⏳ **UPCOMING**"
            border_color = False

        with st.container(border=border_color):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.subheader(f"{g['away_str']} {g['away_score']} @ {g['home_str']} {g['home_score']}")
                st.write(f"📺 Channel: **{g['tv']}** | Status: **{g['status_detail']}**")
                if g['note']:
                    st.caption(f"⚡ {g['note']}")
            with c2:
                st.metric("Excitement", f"{g['score']}/100")
            with c3:
                st.write(badge)
