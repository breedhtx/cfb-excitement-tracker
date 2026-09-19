import streamlit as st
import requests

st.set_page_config(page_title="College Football Heat Map", page_icon="🏈", layout="wide")

# Embedded Hot-Rod Flame & Sideways Football SVG Logo
LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <linearGradient id="skyBg" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0b0a10"/>
      <stop offset="50%" stop-color="#180c10"/>
      <stop offset="100%" stop-color="#2a0808"/>
    </linearGradient>
    <linearGradient id="redFlame" x1="0%" y1="100%" x2="0%" y2="0%">
      <stop offset="0%" stop-color="#b71c1c"/>
      <stop offset="60%" stop-color="#e64a19"/>
      <stop offset="100%" stop-color="#ff7043"/>
    </linearGradient>
    <linearGradient id="orangeFlame" x1="0%" y1="100%" x2="0%" y2="0%">
      <stop offset="0%" stop-color="#e65100"/>
      <stop offset="60%" stop-color="#ff9800"/>
      <stop offset="100%" stop-color="#ffb74d"/>
    </linearGradient>
    <linearGradient id="yellowFlame" x1="0%" y1="100%" x2="0%" y2="0%">
      <stop offset="0%" stop-color="#ffb300"/>
      <stop offset="70%" stop-color="#ffee58"/>
      <stop offset="100%" stop-color="#fffde7"/>
    </linearGradient>
    <linearGradient id="leather" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#93461e"/>
      <stop offset="100%" stop-color="#4e210a"/>
    </linearGradient>
    <clipPath id="ballClip">
      <path d="M 110 256 C 185 130, 327 130, 402 256 C 327 382, 185 382, 110 256 Z"/>
    </clipPath>
  </defs>

  <rect width="512" height="512" rx="110" fill="url(#skyBg)"/>
  <path d="M 0 512 L 0 320 C 20 280, 35 210, 45 130 C 55 220, 75 250, 95 190 C 115 130, 130 70, 145 20 C 160 90, 185 180, 205 130 C 225 80, 240 30, 256 0 C 272 30, 287 80, 307 130 C 327 180, 352 90, 367 20 C 382 70, 397 130, 417 190 C 437 250, 457 220, 467 130 C 477 210, 492 280, 512 320 L 512 512 Z" fill="url(#redFlame)"/>
  <path d="M 0 512 L 0 370 C 30 330, 50 260, 65 180 C 80 250, 105 260, 125 210 C 145 150, 160 100, 185 60 C 200 130, 225 180, 240 120 C 250 80, 256 50, 256 50 C 256 50, 262 80, 272 120 C 287 180, 312 130, 327 60 C 352 100, 367 150, 387 210 C 407 260, 432 250, 447 180 C 462 260, 482 330, 512 370 L 512 512 Z" fill="url(#orangeFlame)"/>
  <path d="M 0 512 L 0 420 C 40 380, 80 300, 105 230 C 125 300, 150 280, 175 200 C 195 140, 215 130, 230 100 C 245 150, 256 160, 256 160 C 256 160, 267 150, 282 100 C 297 130, 317 140, 337 200 C 362 280, 387 300, 407 230 C 432 300, 472 380, 512 420 L 512 512 Z" fill="url(#yellowFlame)"/>

  <circle cx="85" cy="80" r="4.5" fill="#fff59d"/>
  <circle cx="195" cy="35" r="3.5" fill="#ffe082"/>
  <circle cx="320" cy="30" r="4" fill="#fff59d"/>
  <circle cx="430" cy="75" r="3.5" fill="#ffe082"/>

  <path d="M 110 264 C 185 138, 327 138, 402 264 C 327 390, 185 390, 110 264 Z" fill="#000000" opacity="0.6"/>
  <path d="M 110 256 C 185 130, 327 130, 402 256 C 327 382, 185 382, 110 256 Z" fill="url(#leather)" stroke="#1a0803" stroke-width="3"/>

  <g clip-path="url(#ballClip)">
    <ellipse cx="145" cy="256" rx="14" ry="68" fill="none" stroke="#ffffff" stroke-width="15" opacity="0.95"/>
    <ellipse cx="367" cy="256" rx="14" ry="68" fill="none" stroke="#ffffff" stroke-width="15" opacity="0.95"/>
  </g>

  <line x1="115" y1="256" x2="397" y2="256" stroke="#1f0902" stroke-width="2.5"/>
  <g stroke="#ffffff" stroke-linecap="round">
    <line x1="205" y1="256" x2="307" y2="256" stroke-width="6.5"/>
    <line x1="217" y1="240" x2="217" y2="272" stroke-width="4.5"/>
    <line x1="235" y1="240" x2="235" y2="272" stroke-width="4.5"/>
    <line x1="256" y1="240" x2="256" y2="272" stroke-width="4.5"/>
    <line x1="277" y1="240" x2="277" y2="272" stroke-width="4.5"/>
    <line x1="295" y1="240" x2="295" y2="272" stroke-width="4.5"/>
  </g>
</svg>"""

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
        st.cache_data.clear()
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
    
    # Broadcast / TV channel
    broadcasts = comp.get('broadcasts', [{}])
    tv_name = broadcasts[0].get('names', ['TV N/A'])[0] if broadcasts else 'TV N/A'
    
    # Point Spread & Betting Line
    odds_list = comp.get('odds', [])
    line_display = "Line: N/A"
    if odds_list:
        odds = odds_list[0]
        details = odds.get('details')
        over_under = odds.get('overUnder')
        if details:
            line_display = f"Line: {details}"
            if over_under:
                line_display += f" (O/U {over_under})"
        elif over_under:
            line_display = f"O/U: {over_under}"
    
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
        
    # Drive Count Estimation
    current_drive_num = 0
    if situation:
        current_drive_num = situation.get('currentDrive', {}).get('driveNumber', 0)
        if not current_drive_num:
            current_drive_num = situation.get('lastPlay', {}).get('drive', {}).get('driveNumber', 0)

    past_early_game = (period >= 2) or (current_drive_num >= 6)

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
        
        # Upset in progress (only after Q1 or 3 drives)
        is_potential_upset = (home_rank <= 25 and away_rank > 25 and away_score >= home_score) or \
                             (away_rank <= 25 and home_rank > 25 and home_score >= away_score)
        
        if is_potential_upset and past_early_game:
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
        "line": line_display,
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

# App Header with Custom Flame Logo
header_col1, header_col2 = st.columns([0.15, 0.85])
with header_col1:
    st.image(LOGO_SVG, width=54)
with header_col2:
    st.markdown(
        f"<h2 style='margin:0; padding:0; font-size:1.75rem; font-weight:800;'>College Football Heat Map</h2>"
        f"<div style='font-size:0.85rem; color:#a0aec0;'>Tracking <strong>{selected_conf}</strong> • {len(parsed)} games tracked</div>",
        unsafe_allow_html=True
    )

st.write("")

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
            <div class="meta-line">📺 {g['tv']} &nbsp;|&nbsp; 🎲 {g['line']} &nbsp;|&nbsp; ⏱️ {status_badge} ({g['status']}) &nbsp;|&nbsp; Heat Index: <strong>{g['index']}/100</strong></div>
            {context_html}
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
      
