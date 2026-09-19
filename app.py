import streamlit as st
import requests

st.set_page_config(page_title="CFB Scoreboard", page_icon="🏈", layout="wide")

# Custom CSS to shrink text and make rows compact for phone scanning
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .game-row {
        background-color: #1a1c24;
        border-radius: 8px;
        padding: 8px 12px;
        margin-bottom: 8px;
        border-left: 5px solid #444;
    }
    .game-live { border-left-color: #ff4b4b !important; }
    .game-final { border-left-color: #666 !important; }
    .game-upcoming { border-left-color: #2b5c8f !important; }
    .team-line { font-size: 1.05rem; font-weight: 700; }
    .meta-line { font-size: 0.82rem; color: #aaa; margin-top: 2px; }
    .context-line { font-size: 0.85rem; color: #ffca28; font-weight: 500; margin-top: 3px; }
</style>
""", unsafe_allow_html=True)

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
    st.title("🏈 Filters")
    selected_conf = st.selectbox("Conference", list(CONFERENCE_MAP.keys()))
    status_filter = st.radio("Status", ["All", "Live Only", "Finals Only"])
    top25_only = st.checkbox("Ranked Teams (Top 25)", value=False)
    
    st.divider()
    if st.button("🔄 Refresh"):
        st.rerun()

# --- FETCH DATA ---
@st.cache_data(ttl=25)
def fetch_games(group_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?groups={group_id}&limit=100"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json().get('events', [])
    except Exception:
        pass
    return []

def parse_game(game):
    comp = game['competitions'][0]
    status = comp['status']
    state = status['type']['state']
    detail = status['type'].get('detail', '')
    period = status.get('period', 1)
    
    home = comp['competitors'][0]
    away = comp['competitors'][1]
    
    home_name = home['team']['shortDisplayName']
    away_name = away['team']['shortDisplayName']
    home_score = int(home.get('score', 0))
    away_score = int(away.get('score', 0))
    home_rank = home.get('curatedRank', {}).get('current', 99)
    away_rank = away.get('curatedRank', {}).get('current', 99)
    
    broadcasts = comp.get('broadcasts', [{}])
    tv_name = broadcasts[0].get('names', ['TV N/A'])[0] if broadcasts else 'TV N/A'
    
    # Situational context (possession, down & distance, drive context)
    situation = comp.get('situation', {})
    context_notes = []
    
    diff = abs(home_score - away_score)
    leader = home_name if home_score > away_score else away_name if away_score > home_score else None
    trailer = away_name if home_score > away_score else home_name if away_score > home_score else None
    
    # 1. Drive & Score Context
    if state == 'in':
        possession_id = situation.get('possession')
        is_redzone = situation.get('isRedZone', False)
        down_dist = situation.get('downDistanceText', '')
        possession_text = situation.get('possessionText', '')
        last_play = situation.get('lastPlay', {}).get('text', '')
        
        # Determine who has the ball
        poss_team = home_name if possession_id == home.get('id') else away_name if possession_id == away.get('id') else ""

        if is_redzone:
            context_notes.append(f"🔴 **{poss_team} in RED ZONE** ({down_dist})")
        elif poss_team and trailer and poss_team == trailer and diff <= 8 and period >= 3:
            context_notes.append(f"⚡ **{trailer} driving to tie/take lead** ({down_dist})")
        elif down_dist:
            context_notes.append(f"🏈 {poss_team} ball: {down_dist}")

        # Notable play callout
        if last_play and ("TOUCHDOWN" in last_play or "INTERCEPTED" in last_play or "FUMBLE" in last_play or "field goal" in last_play.lower()):
            context_notes.append(f"⚠️ *Play: {last_play}*")

    elif state == 'post':
        if diff == 0:
            context_notes.append("Ended in Tie")
        elif diff <= 3:
            context_notes.append(f"🏁 {leader} won on a nail-biter (±{diff} pts)")
        elif diff <= 8:
            context_notes.append(f"🏁 One-possession finish ({leader} by {diff})")
        else:
            context_notes.append(f"🏁 {leader} won by {diff}")
            
    # Excitement Calculation
    score = 0
    if state == 'in':
        if diff == 0: score += 35
        elif diff <= 3: score += 30
        elif diff <= 8: score += 20
        if period > 4: score += 45
        elif period == 4: score += 30
        elif period == 3: score += 15
        if (home_rank <= 25 and away_rank > 25 and away_score >= home_score) or (away_rank <= 25 and home_rank > 25 and home_score >= away_score):
            score += 25
            context_notes.insert(0, "🚨 **UPSET IN PROGRESS**")
    elif state == 'post':
        score = 5

    away_str = f"#{away_rank} {away_name}" if away_rank <= 25 else away_name
    home_str = f"#{home_rank} {home_name}" if home_rank <= 25 else home_name

    return {
        "state": state,
        "away_str": away_str,
        "home_str": home_str,
        "away_score": away_score,
        "home_score": home_score,
        "home_rank": home_rank,
        "away_rank": away_rank,
        "status": detail,
        "tv": tv_name,
        "score": min(100, score),
        "context": " | ".join(context_notes)
    }

# --- EXECUTE ---
events = fetch_games(CONFERENCE_MAP[selected_conf])
parsed = [parse_game(e) for e in events]

if top25_only:
    parsed = [g for g in parsed if g['home_rank'] <= 25 or g['away_rank'] <= 25]

if status_filter == "Live Only":
    parsed = [g for g in parsed if g['state'] == 'in']
elif status_filter == "Finals Only":
    parsed = [g for g in parsed if g['state'] == 'post']

# Sort: Live games first by excitement, then upcoming/finals
parsed.sort(key=lambda x: (x['state'] == 'in', x['score']), reverse=True)

# Compact Header
st.markdown(f"**{selected_conf} Scores** &nbsp;•&nbsp; `{len(parsed)} games`", unsafe_allow_html=True)

if not parsed:
    st.info("No games match the current filter.")
else:
    for g in parsed:
        state_class = "game-live" if g['state'] == 'in' else "game-final" if g['state'] == 'post' else "game-upcoming"
        status_badge = f"<span style='color:#ff4b4b;font-weight:700;'>LIVE</span>" if g['state'] == 'in' else g['status']
        
        score_display = f"{g['away_score']} - {g['home_score']}" if g['state'] != 'pre' else "vs"
        
        context_html = f"<div class='context-line'>{g['context']}</div>" if g['context'] else ""

        html = f"""
        <div class="game-row {state_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div class="team-line">{g['away_str']} &nbsp;{g['away_score'] if g['state'] != 'pre' else ''} &nbsp;@&nbsp; {g['home_str']} &nbsp;{g['home_score'] if g['state'] != 'pre' else ''}</div>
                <div style="font-size: 0.85rem; font-weight: 600; text-align: right;">{status_badge}</div>
            </div>
            <div class="meta-line">📺 {g['tv']} &nbsp;|&nbsp; ⏱️ {g['status']} &nbsp;|&nbsp; Index: {g['score']}/100</div>
            {context_html}
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
