import streamlit as st
import requests

st.set_page_config(page_title="CFB Radar & Social Pulse", page_icon="🏈", layout="wide")

# Conference mappings for ESPN
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
    status_filter = st.radio("Game Status", ["All Games", "Live Only (On TV)", "Final Only (Completed)"])
    top25_only = st.checkbox("Ranked Teams Only (Top 25)", value=False)
    
    st.divider()
    if st.button("🔄 Refresh Data Now"):
        st.rerun()
    st.caption("Auto-refreshes when filters change. Completed games include final-minute recaps and Bluesky fan reactions.")

# --- API DATA FETCHERS ---
@st.cache_data(ttl=30)
def fetch_games(group_id):
    """Fetches live college football games from ESPN."""
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?groups={group_id}&limit=100"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json().get('events', [])
    except Exception as e:
        st.error(f"Error fetching live scoreboard: {e}")
    return []

@st.cache_data(ttl=300)
def fetch_game_recap(game_id):
    """Fetches written editorial recaps and key 4th quarter scoring drives from ESPN."""
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event={game_id}"
    try:
        res = requests.get(url, timeout=8)
        if res.status_code == 200:
            data = res.json()
            
            headline = ""
            story = ""
            article = data.get('article', {})
            if article:
                headline = article.get('headline', '')
                story = article.get('description', '')

            scoring_plays = data.get('scoringPlays', [])
            clutch_plays = []
            for play in scoring_plays:
                period = play.get('period', {}).get('number', 0)
                if period >= 4:
                    clock = play.get('clock', {}).get('displayValue', '')
                    text = play.get('text', '')
                    away_score = play.get('awayScore', 0)
                    home_score = play.get('homeScore', 0)
                    clutch_plays.append(f"**Q{period} ({clock})**: {text} *(Score: {away_score}-{home_score})*")

            return {
                "headline": headline,
                "story": story,
                "clutch_plays": clutch_plays[-3:]
            }
    except Exception:
        pass
    return None

@st.cache_data(ttl=45)
def get_bluesky_buzz(team1_name, team2_name, limit=4):
    """Searches Bluesky for public posts mentioning both teams. Requires no login."""
    query = f"{team1_name} {team2_name}"
    url = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
    params = {
        "q": query,
        "limit": limit
    }
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            posts = res.json().get('posts', [])
            extracted = []
            for p in posts:
                author = p.get('author', {}).get('displayName') or p.get('author', {}).get('handle', 'User')
                text = p.get('record', {}).get('text', '')
                extracted.append({"author": author, "text": text})
            return extracted
    except Exception:
        pass
    return []

def parse_game(game):
    comp = game['competitions'][0]
    status = comp['status']
    state = status['type']['state']
    
    period = status.get('period', 1)
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
    
    diff = abs(home_score - away_score)
    score = 0
    reasons = []
    
    if state == 'in':
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
            
        if period > 4:
            score += 45
            reasons.append("🚨 OVERTIME")
        elif period == 4:
            score += 30
            reasons.append("4th Quarter")
        elif period == 3:
            score += 15
            
        if home_rank <= 25 and away_rank > 25 and away_score >= home_score:
            score += 25
            reasons.append(f"Upset: {away_name} over #{home_rank}")
        elif away_rank <= 25 and home_rank > 25 and home_score >= away_score:
            score += 25
            reasons.append(f"Upset: {home_name} over #{away_rank}")
            
    elif state == 'post':
        score = 5
        if diff <= 3:
            reasons.append("Down-to-the-wire finish")
        elif diff <= 8:
            reasons.append("One-possession game")
        if (home_rank <= 25 and away_rank > 25 and away_score > home_score) or \
           (away_rank <= 25 and home_rank > 25 and home_score > away_score):
            reasons.append("UPSET COMPLETE")
            
    return {
        "id": game['id'],
        "state": state,
        "away_raw": away_name,
        "home_raw": home_name,
        "away_str": f"{f'#{away_rank} ' if away_rank <= 25 else ''}{away_name}",
        "home_str": f"{f'#{home_rank} ' if home_rank <= 25 else ''}{home_name}",
        "away_score": away_score,
        "home_score": home_score,
        "home_rank": home_rank,
        "away_rank": away_rank,
        "diff": diff,
        "status_detail": detail,
        "tv": tv_name,
        "score": min(100, score),
        "note": ", ".join(reasons) if reasons else ""
    }

# --- PROCESS DATA ---
group_id = CONFERENCE_MAP[selected_conf]
events = fetch_games(group_id)
parsed = [parse_game(e) for e in events]

if top25_only:
    parsed = [g for g in parsed if g['home_rank'] <= 25 or g['away_rank'] <= 25]

if status_filter == "Live Only (On TV)":
    parsed = [g for g in parsed if g['state'] == 'in']
elif status_filter == "Final Only (Completed)":
    parsed = [g for g in parsed if g['state'] == 'post']

parsed.sort(key=lambda x: (x['state'] == 'in', x['score'], -x['diff']), reverse=True)
live_games = [g for g in parsed if g['state'] == 'in']

# --- APP HEADER ---
st.title("🏈 College Football Live Command Center")
st.caption(f"Tracking **{selected_conf}** | {len(parsed)} games")

# --- QUAD-BOX MATRIX (LIVE WINDOW) ---
if status_filter != "Final Only (Completed)":
    st.header("📺 Optimal Quad-Box Matrix (Top 4 Live Screens)")
    if len(live_games) == 0:
        st.info("No games are currently live in this window. Check the scoreboard below.")
    else:
        quad_games = live_games[:4]
        cols = st.columns(min(len(quad_games), 4))
        for idx, g in enumerate(quad_games):
            with cols[idx]:
                with st.container(border=True):
                    st.markdown(f"#### 🖥️ Screen {idx+1}: **{g['tv']}**")
                    st.markdown(f"**{g['away_str']} {g['away_score']}** @ **{g['home_str']} {g['home_score']}**")
                    st.write(f"⏱️ `{g['status_detail']}`")
                    st.caption(f"⚡ **Index: {g['score']}/100** | {g['note']}")
    st.divider()

# --- SCOREBOARD & SOCIAL CONTEXT ---
st.header("📋 Scoreboard & Live Reactions")

if not parsed:
    st.warning("No games found matching your current filter.")
else:
    for g in parsed:
        border_box = True if g['state'] == 'in' else False
        with st.container(border=border_box):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.subheader(f"{g['away_str']} {g['away_score']}  @  {g['home_str']} {g['home_score']}")
                st.write(f"Status: **{g['status_detail']}** | Channel: **{g['tv']}**")
                if g['note']:
                    st.caption(f"⚡ *{g['note']}*")
            with c2:
                if g['state'] == 'in':
                    st.metric("Excitement", f"{g['score']}/100")
                elif g['state'] == 'post':
                    st.metric("Margin", f"{g['diff']} pts")
                else:
                    st.write("Upcoming")
            with c3:
                if g['state'] == 'in':
                    st.write("🔴 **ON TV NOW**")
                elif g['state'] == 'post':
                    st.write("🏁 **FINAL**")
                else:
                    st.write("⏳ **SCHEDULED**")

            # 1. BLUESKY FAN REACTIONS
            with st.expander("💬 What fans are saying on Bluesky"):
                with st.spinner("Checking Bluesky chatter..."):
                    social_posts = get_bluesky_buzz(g['away_raw'], g['home_raw'])
                if social_posts:
                    for post in social_posts:
                        st.markdown(f"**@{post['author']}**: {post['text']}")
                        st.divider()
                else:
                    st.caption("No recent Bluesky chatter found for this matchup yet.")

            # 2. FINAL GAME SUMMARY (For completed games)
            if g['state'] == 'post':
                with st.expander("📖 View Game Summary & Deciding Plays"):
                    with st.spinner("Loading recap..."):
                        recap = fetch_game_recap(g['id'])
                    
                    if recap:
                        if recap['headline']:
                            st.markdown(f"**{recap['headline']}**")
                        if recap['story']:
                            st.write(recap['story'])
                        
                        if recap['clutch_plays']:
                            st.markdown("##### ⏱️ Late-Game Deciding Plays:")
                            for play in recap['clutch_plays']:
                                st.write(f"- {play}")
                    else:
                        st.write("Detailed recap not yet published for this matchup.")
        
