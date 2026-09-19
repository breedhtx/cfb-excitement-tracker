import streamlit as st
import requests

st.set_page_config(page_title="College Football Heat Map", page_icon="🏈", layout="wide")

# Styling: high-density mobile scanning
st.markdown("""
<style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
    .heat-row {
        background-color: #171923;
        border-radius: 8px;
        padding: 9px 12px;
        margin-bottom: 8px;
        border-left: 6px solid #444;
    }
    .heat-urgent { border-left-color: #ff3333 !important; background-color: #241416 !important; }
    .heat-monitor { border-left-color: #ffaa00 !important; }
    .heat-routine { border-left-color: #4a5568 !important; }
    .team-line { font-size: 1.02rem; font-weight: 700; }
    .badge-urgent { color: #ff4d4d; font-weight: 800; font-size: 0.85rem; letter-spacing: 0.5px; }
    .badge-monitor { color: #ffbb33; font-weight: 700; font-size: 0.85rem; }
    .badge-routine { color: #a0aec0; font-weight: 600; font-size: 0.82rem; }
    .meta-line { font-size: 0.82rem; color: #a0aec0; margin-top: 2px; }
    .context-line { font-size: 0.84rem; color: #f6e05e; font-weight: 500; margin-top: 2px; }
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

# Major historic rivalries lookup
RIVALRIES = {
    frozenset(["Michigan", "Ohio State"]): "The Game",
    frozenset(["Alabama", "Auburn"]): "Iron Bowl",
    frozenset(["Texas", "Oklahoma"]): "Red River Rivalry",
    frozenset(["Army", "Navy"]): "Army-Navy Game",
    frozenset(["Florida", "Georgia"]): "World's Largest Outdoor Cocktail Party",
    frozenset(["USC", "UCLA"]): "Battle for the Victory Bell",
    frozenset(["USC", "Notre Dame"]): "Jeweled Shillelagh",
    frozenset(["Oregon", "Oregon State"]): "Civil War",
    frozenset(["Washington", "Washington State"]): "Apple Cup",
    frozenset(["Ole Miss", "Mississippi State"]): "Egg Bowl",
    frozenset(["Florida State", "Florida"]): "Sunshine Showdown",
    frozenset(["Florida State", "Miami"]): "Miami-FSU Rivalry",
    frozenset(["Georgia", "Georgia Tech"]): "Clean, Old-Fashioned Hate",
    frozenset(["Pittsburgh", "West Virginia"]): "Backyard Brawl",
    frozenset(["Louisville", "Kentucky"]): "Governor's Cup",
    frozenset(["Clemson", "South Carolina"]): "Palmetto Bowl",
    frozenset(["Iowa", "Iowa State"]): "Cy-Hawk Series",
    frozenset(["Iowa", "Wisconsin"]): "Heartland Trophy",
    frozenset(["Wisconsin", "Minnesota"]): "Paul Bunyan's Axe",
    frozenset(["Purdue", "Indiana"]): "Old Oaken Bucket",
    frozenset(["Illinois", "Northwestern"]): "Land of Lincoln Trophy",
    frozenset(["BYU", "Utah"]): "Holy War",
    frozenset(["Arizona", "Arizona State"]): "Territorial Cup",
    frozenset(["California", "Stanford"]): "The Big Game",
    frozenset(["Colorado", "Utah"]): "Rumble in the Rockies",
    frozenset(["Kansas", "Kansas State"]): "Sunflower Showdown",
    frozenset(["Oklahoma", "Oklahoma State"]): "Bedlam",
    frozenset(["LSU", "Ole Miss"]): "Magnolia Bowl",
    frozenset(["Texas A&M", "Texas"]): "Lone Star Showdown"
}

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.title("🏈 Heat Map Controls")
    selected_conf = st.selectbox("Conference", list(CONFERENCE_MAP.keys()))
    status_filter = st.radio("Status", ["All", "Live Only", "Finals Only"])
    top25_only = st.checkbox("Ranked Teams Only (Top 25)", value=False)
    
    st.divider()
    if st.button("🔄 Refresh Now"):
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
    
    situation = comp.get('situation', {})
    context_notes = []
    
    diff = abs(home_score - away_score)
    leader = home_name if home_score > away_score else away_name if away_score > home_score else None
    trailer = away_name if home_score > away_score else home_name if away_score > home_score else None

    # Check for historic rivalry
    pair = frozenset([home_name, away_name])
    rivalry_title = RIVALRIES.get(pair, None)
    if rivalry_title:
        context_notes.append(f"🏆 **{rivalry_title}**")
        
    # Situational context for live games
    if state == 'in':
        possession_id = situation.get('possession')
        is_redzone = situation.get('isRedZone', False)
        down_dist = situation.get('downDistanceText', '')
        last_play = situation.get('lastPlay', {}).get('text', '')
        
        poss_team = home_name if possession_id == home.get('id') else away_name if possession_id == away.get('id') else ""

        if is_redzone:
            context_notes.append(f"🔴 **{poss_team} in RED ZONE** ({down_dist})")
        elif poss_team and trailer and poss_team == trailer and diff <= 8 and period >= 3:
            context_notes.append(f"⚡ **{trailer} driving to tie/take lead** ({down_dist})")
        elif down_dist:
            context_notes.append(f"🏈 {poss_team} ball: {down_dist}")

        if last_play and ("TOUCHDOWN" in last_play or "INTERCEPTED" in last_play or "FUMBLE" in last_play or "field goal" in last_play.lower()):
            context_notes.append(f"⚠️ *Play: {last_play}*")

    elif state == 'post':
        if diff == 0:
            context_notes.append("Ended in Tie")
        elif diff <= 3:
            context_notes.append(f"🏁 {leader} won nail-biter (±{diff})")
        elif diff <= 8:
            context_notes.append(f"🏁 One-possession finish ({leader} by {diff})")

    # --- HEAT MAP INDEX CALCULATION (0 - 100) ---
    score = 0
    
    # 1. Team Rankings & Postseason / Championship Stakes
    if home_rank <= 25 and away_rank <= 25:
        score += 18  # Top 25 matchup
        if home_rank <= 10 and away_rank <= 10:
            score += 10 # Elite top-10 showdown
    elif home_rank <= 25 or away_rank <= 25:
        score += 8   # At least one ranked team
        
    # 2. Rivalry Boost
    if rivalry_title:
        score += 15

    # 3. Live Drama & Closeness Leverage
    if state == 'in':
        if diff == 0: score += 35
        elif diff <= 3: score += 30
        elif diff <= 8: score += 20
        elif diff <= 14: score += 10
        
        if period > 4: score += 40      # Overtime
        elif period == 4: score += 25   # 4th quarter
        elif period == 3: score += 12   # 2nd half
        
        if (home_rank <= 25 and away_rank > 25 and away_score >= home_score) or \
           (away_rank <= 25 and home_rank > 25 and home_score >= away_score):
            score += 25
            context_notes.insert(0, "🚨 **UPSET ALERT**")

    elif state == 'post':
        score = min(score, 30)

    total_index = min(100, score)

    # --- HEAT MAP LABEL TIERS ---
    if total_index >= 75:
        heat_tier = "urgent"
        label = "🚨 CHANGE THE CHANNEL NOW"
    elif total_index >= 40:
        heat_tier = "monitor"
        label = "👀 MONITORING"
    else:
        heat_tier = "routine"
        label = "🏈 IT'S FOOTBALL"

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
        "index": total_index,
        "heat_tier": heat_tier,
        "label": label,
        "context": " | ".join(context_notes)
    }

# --- RUN & RENDER ---
events = fetch_games(CONFERENCE_MAP[selected_conf])
parsed = [parse_game(e) for e in events]

if top25_only:
    parsed = [g for g in parsed if g['home_rank'] <= 25 or g['away_rank'] <= 25]

if status_filter == "Live Only":
    parsed = [g for g in parsed if g['state'] == 'in']
elif status_filter == "Finals Only":
    parsed = [g for g in parsed if g['state'] == 'post']

parsed.sort(key=lambda x: (x['state'] == 'in', x['index']), reverse=True)

st.title("🏈 College Football Heat Map")
st.caption(f"Tracking **{selected_conf}** • `{len(parsed)} games tracked`")

if not parsed:
    st.info("No games match your selected filters.")
else:
    for g in parsed:
        row_class = f"heat-{g['heat_tier']}"
        badge_class = f"badge-{g['heat_tier']}"
        
        status_badge = "<span style='color:#ff4b4b;font-weight:700;'>● LIVE</span>" if g['state'] == 'in' else g['status']
        context_html = f"<div class='context-line'>{g['context']}</div>" if g['context'] else ""

        html = f"""
        <div class="heat-row {row_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div class="team-line">{g['away_str']} &nbsp;{g['away_score'] if g['state'] != 'pre' else ''} &nbsp;@&nbsp; {g['home_str']} &nbsp;{g['home_score'] if g['state'] != 'pre' else ''}</div>
                <div class="{badge_class}">{g['label']}</div>
            </div>
            <div class="meta-line">📺 {g['tv']} &nbsp;|&nbsp; ⏱️ {status_badge} ({g['status']}) &nbsp;|&nbsp; Heat Index: <strong>{g['index']}/100</strong></div>
            {context_html}
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
        
