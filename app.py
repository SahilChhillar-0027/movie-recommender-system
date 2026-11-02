import pickle
import streamlit as st
import requests
import json
import os
import hashlib
from datetime import datetime
from thefuzz import fuzz, process

# ─── Page Config ───
st.set_page_config(
    page_title="CineMatch — Premium Movie Vault",
    page_icon="🎞️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TMDB_API_KEY = "8265bd1679663a7ea12ac168da84d2e8"
USER_DATA_DIR = os.path.join(os.path.dirname(__file__), 'user_data')
os.makedirs(USER_DATA_DIR, exist_ok=True)

# ─── Mood → Genre Mapping ───
MOOD_MAP = {
    "😄 Happy": {"genres": ["Comedy", "Family", "Animation", "Music"], "label": "Happy", "color": "#F59E0B"},
    "😢 Sad": {"genres": ["Drama", "Romance"], "label": "Sad", "color": "#3B82F6"},
    "😱 Thrilled": {"genres": ["Action", "Thriller", "Adventure"], "label": "Thrilled", "color": "#EF4444"},
    "🤔 Curious": {"genres": ["Mystery", "Science Fiction", "Documentary"], "label": "Curious", "color": "#8B5CF6"},
    "😍 Romantic": {"genres": ["Romance", "Drama", "Comedy"], "label": "Romantic", "color": "#EC4899"},
    "👻 Scared": {"genres": ["Horror", "Thriller", "Mystery"], "label": "Scared", "color": "#1F2937"},
    "🌌 Adventurous": {"genres": ["Adventure", "Fantasy", "Science Fiction"], "label": "Adventurous", "color": "#10B981"},
    "😎 Chill": {"genres": ["Comedy", "Animation", "Family", "Music"], "label": "Chill", "color": "#06B6D4"},
}

# ─── CSS — Load Stylesheet ───
css_file = os.path.join(os.path.dirname(__file__), 'skeu_style.css')
if os.path.exists(css_file):
    with open(css_file) as _css:
        st.markdown(f'<style>{_css.read()}</style>', unsafe_allow_html=True)


# ─── Load Data ───
@st.cache_resource
def load_data():
    movies = pickle.load(open('model/movie_list.pkl', 'rb'))
    similarity = pickle.load(open('model/similarity.pkl', 'rb'))
    return movies, similarity

movies, similarity = load_data()
movie_list = sorted(movies['title'].values.tolist())


# ─── Auth Functions ───
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def load_user(username):
    path = os.path.join(USER_DATA_DIR, f'{username}.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def save_user(username, data):
    path = os.path.join(USER_DATA_DIR, f'{username}.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def create_user(username, password):
    return {
        'name': username,
        'password': hash_pw(password),
        'history': [],
        'favorites': [],
        'mood_history': [],
        'created': datetime.now().isoformat()
    }


# ─── TMDB API ───
@st.cache_data(ttl=3600)
def fetch_trending():
    try:
        data = requests.get(f"https://api.themoviedb.org/3/trending/movie/day?api_key={TMDB_API_KEY}", timeout=8).json()
        return [{'title': m.get('title',''), 'poster': f"https://image.tmdb.org/t/p/w342{m['poster_path']}" if m.get('poster_path') else None,
                 'rating': m.get('vote_average',0), 'year': m.get('release_date','')[:4] if m.get('release_date') else ''} for m in data.get('results',[])[:10]]
    except Exception: return []

@st.cache_data(ttl=3600)
def fetch_movie_details(movie_id):
    try:
        data = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US&append_to_response=videos,credits", timeout=8).json()
        trailer_key = None
        for v in data.get('videos',{}).get('results',[]):
            if v.get('site')=='YouTube' and v.get('type')=='Trailer': trailer_key = v['key']; break
        if not trailer_key:
            for v in data.get('videos',{}).get('results',[]):
                if v.get('site')=='YouTube': trailer_key = v['key']; break
        cast = [{'name':c['name'],'character':c.get('character',''),'photo':f"https://image.tmdb.org/t/p/w185{c['profile_path']}" if c.get('profile_path') else None} for c in data.get('credits',{}).get('cast',[])[:5]]
        director = next((c['name'] for c in data.get('credits',{}).get('crew',[]) if c.get('job')=='Director'), '')
        return {'poster': f"https://image.tmdb.org/t/p/w500{data['poster_path']}" if data.get('poster_path') else None,
                'rating': data.get('vote_average',0), 'vote_count': data.get('vote_count',0),
                'year': data.get('release_date','')[:4] if data.get('release_date') else '',
                'genres': [g['name'] for g in data.get('genres',[])[:3]],
                'overview': data.get('overview',''), 'tagline': data.get('tagline',''),
                'runtime': data.get('runtime',0), 'budget': data.get('budget',0), 'revenue': data.get('revenue',0),
                'trailer_key': trailer_key, 'cast': cast, 'director': director}
    except Exception: return None


# ─── Helpers ───
def get_conf_color(s):
    if s >= 70: return "linear-gradient(90deg,#D4A843,#F5D98A)", "#D4A843"
    elif s >= 50: return "linear-gradient(90deg,#C0792A,#E8A94A)", "#C0792A"
    elif s >= 30: return "linear-gradient(90deg,#8B6914,#B8912E)", "#8B6914"
    return "linear-gradient(90deg,#8B3A3A,#C25555)", "#8B3A3A"

def fmt_money(a):
    if a>=1e9: return f"${a/1e9:.1f}B"
    elif a>=1e6: return f"${a/1e6:.0f}M"
    elif a>0: return f"${a:,.0f}"
    return "—"

def gen_explanation(src, title, det, score, source_type="content"):
    reasons = []
    sw, rw = set(src.lower().split()), set(title.lower().split())
    common = sw & rw - {'the','a','an','of','in','and','to','is'}
    if common: reasons.append(f"🎬 **Same franchise** — Part of the *{' '.join(w.title() for w in common)}* universe")
    if det and det.get('genres'): reasons.append(f"🎭 **Genre match** — {', '.join(det['genres'])}")
    if det and det.get('director'): reasons.append(f"🎥 **Director** — {det['director']}")
    if source_type == "mood": reasons.append("💫 **Mood-based** — Matches your current emotional preference")
    if source_type == "history": reasons.append("📜 **History-based** — Based on your past viewing patterns")
    if score >= 75: reasons.append("🔥 **Very high similarity** — Plot, themes & cast closely match")
    elif score >= 60: reasons.append("✨ **Strong thematic overlap** — Similar storyline elements")
    elif score >= 40: reasons.append("💡 **Shared themes** — Overlapping keywords & archetypes")
    else: reasons.append("🌱 **Discovery pick** — Subtle narrative similarities")
    return reasons


def get_content_recs(movie, n=5):
    """Content-based recommendations."""
    idx = movies[movies['title'] == movie].index[0]
    dists = sorted(list(enumerate(similarity[idx])), reverse=True, key=lambda x: x[1])
    results = []
    for i in dists[1:n+1]:
        mid, title, score = movies.iloc[i[0]].movie_id, movies.iloc[i[0]].title, round(i[1]*100)
        det = fetch_movie_details(mid)
        if det:
            det.update({'title': title, 'match': score, 'source': 'content',
                        'explanations': gen_explanation(movie, title, det, score, 'content')})
            results.append(det)
    return results


def get_history_recs(user_data, selected_movie, n=3):
    """History-based: recs from user's past searches (not the current one)."""
    history = [h for h in user_data.get('history', []) if h != selected_movie and h in movies['title'].values]
    if not history: return []
    # Use most recent movie from history
    last = history[-1]
    idx = movies[movies['title'] == last].index[0]
    dists = sorted(list(enumerate(similarity[idx])), reverse=True, key=lambda x: x[1])
    results = []
    for i in dists[1:n+1]:
        mid, title, score = movies.iloc[i[0]].movie_id, movies.iloc[i[0]].title, round(i[1]*100)
        if title == selected_movie: continue
        det = fetch_movie_details(mid)
        if det:
            det.update({'title': title, 'match': score, 'source': 'history',
                        'explanations': gen_explanation(last, title, det, score, 'history')})
            results.append(det)
    return results


def get_mood_recs(mood, selected_movie, n=3):
    """Mood/emotion-based: find movies matching mood genres."""
    mood_genres = set(MOOD_MAP.get(mood, {}).get('genres', []))
    if not mood_genres: return []
    results = []
    for _, row in movies.iterrows():
        if row['title'] == selected_movie: continue
        tag_text = row.get('tags', '')
        if not any(g.lower() in tag_text.lower() for g in mood_genres):
            continue
        det = fetch_movie_details(row['movie_id'])
        if det and set(det.get('genres', [])) & mood_genres:
            score = len(set(det.get('genres', [])) & mood_genres) * 25 + int(det.get('rating', 0) * 5)
            det.update({'title': row['title'], 'match': min(score, 95), 'source': 'mood',
                        'explanations': gen_explanation(selected_movie, row['title'], det, score, 'mood')})
            results.append(det)
        if len(results) >= n: break
    results.sort(key=lambda x: x['match'], reverse=True)
    return results[:n]


# ─── Session State Init ───
for key, val in [('logged_in', False), ('username', ''), ('user_data', {}), ('page', 'login')]:
    if key not in st.session_state:
        st.session_state[key] = val


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE: LOGIN / SIGNUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if not st.session_state.logged_in:
    col_a, col_b, col_c = st.columns([1, 1.5, 1])
    with col_b:
        st.markdown("""
        <div class="auth-container">
            <div class="auth-logo">
                <div class="icon">🎞️</div>
                <h1>CineMatch</h1>
                <p>Your Premium Movie Vault</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["🔐 Login", "🆕 Sign Up"])

        with tab_login:
            login_user = st.text_input("Username", placeholder="Enter your username", key="login_user")
            login_pass = st.text_input("Password", type="password", placeholder="Enter password", key="login_pass")
            if st.button("🔓 Login", key="login_btn"):
                if login_user and login_pass:
                    ud = load_user(login_user.strip())
                    if ud and ud.get('password') == hash_pw(login_pass):
                        st.session_state.logged_in = True
                        st.session_state.username = login_user.strip()
                        st.session_state.user_data = ud
                        st.session_state.page = 'home'
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("Please fill in both fields")

        with tab_signup:
            new_user = st.text_input("Choose username", placeholder="Enter a username", key="signup_user")
            new_pass = st.text_input("Choose password", type="password", placeholder="Min 4 characters", key="signup_pass")
            new_pass2 = st.text_input("Confirm password", type="password", placeholder="Re-enter password", key="signup_pass2")
            if st.button("✨ Create Account", key="signup_btn"):
                if new_user and new_pass:
                    if len(new_pass) < 4:
                        st.error("Password must be at least 4 characters")
                    elif new_pass != new_pass2:
                        st.error("Passwords don't match")
                    elif load_user(new_user.strip()):
                        st.error("Username already exists")
                    else:
                        ud = create_user(new_user.strip(), new_pass)
                        save_user(new_user.strip(), ud)
                        st.session_state.logged_in = True
                        st.session_state.username = new_user.strip()
                        st.session_state.user_data = ud
                        st.session_state.page = 'home'
                        st.success("✅ Account created!")
                        st.rerun()
                else:
                    st.warning("Please fill in all fields")



    st.stop()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGGED IN — MAIN APP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ud = st.session_state.user_data

# Sidebar — Vintage Control Panel
with st.sidebar:
    st.markdown(f"""<div style="text-align:center;padding:1rem 0 0.5rem">
        <div style="font-size:2.5rem;filter:drop-shadow(0 3px 8px rgba(212,168,67,0.4))">🎞️</div>
        <div style="font-family:'Cinzel',serif;font-size:1.3rem;font-weight:900;
            background:linear-gradient(135deg,#D4A843,#F5D98A);-webkit-background-clip:text;
            -webkit-text-fill-color:transparent;margin:0.3rem 0">CineMatch</div>
        <div style="font-size:0.65rem;color:#6B6580;text-transform:uppercase;letter-spacing:3px;font-weight:700">Premium Vault</div>
    </div>""", unsafe_allow_html=True)
    st.markdown(f"""<div style="background:linear-gradient(145deg,#222234,#1A1A2A);border-radius:14px;padding:1rem;margin:1rem 0;
        box-shadow:0 4px 16px rgba(0,0,0,0.4) inset,0 1px 0 rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.04)">
        <div style="font-size:0.65rem;color:#6B6580;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:0.5rem">👤 Curator</div>
        <div style="font-size:1.1rem;font-weight:800;color:#D4A843">{st.session_state.username}</div>
        <div style="display:flex;gap:1.5rem;margin-top:0.8rem">
            <div><span style="font-weight:900;color:#E8E0D0">{len(ud.get('history',[]))}</span><br><span style="font-size:0.6rem;color:#5A5470;text-transform:uppercase;letter-spacing:1px">Searches</span></div>
            <div><span style="font-weight:900;color:#E8E0D0">{len(ud.get('favorites',[]))}</span><br><span style="font-size:0.6rem;color:#5A5470;text-transform:uppercase;letter-spacing:1px">Favorites</span></div>
        </div>
    </div>""", unsafe_allow_html=True)

    if ud.get('history'):
        st.markdown("---")
        st.markdown("**📜 Recent Films**")
        for h in reversed(ud['history'][-5:]): st.caption(f"🎬 {h}")

    if ud.get('favorites'):
        st.markdown("---")
        st.markdown("**⭐ Favorites**")
        for f in ud['favorites'][-5:]: st.caption(f"❤️ {f}")



    if st.button("🚪 Logout"):
        for k in ['logged_in','username','user_data','page']:
            st.session_state[k] = False if k=='logged_in' else ('' if k in ['username'] else ({} if k=='user_data' else 'login'))
        st.rerun()


# Hero
st.markdown(f"""
<div class="hero">
    <div class="hero-icon">🎞️</div>
    <h1>CineMatch</h1>
    <p>Welcome back, <strong>{st.session_state.username}</strong>! Select a film & mood for curated recommendations</p>
</div>
""", unsafe_allow_html=True)

total = len(movies)
st.markdown(f"""
<div class="stats">
    <div class="stat"><div class="stat-val">{total:,}</div><div class="stat-lbl">Films</div></div>
    <div class="stat"><div class="stat-val">🧠</div><div class="stat-lbl">Hybrid AI</div></div>
    <div class="stat"><div class="stat-val">🎥</div><div class="stat-lbl">Trailers</div></div>
    <div class="stat"><div class="stat-val">💫</div><div class="stat-lbl">Mood Engine</div></div>
</div>
""", unsafe_allow_html=True)


# ── Trending ──
st.markdown('<div class="section-hdr">🎯 Now Showing — Trending</div>', unsafe_allow_html=True)
trending = fetch_trending()
if trending:
    tcols = st.columns(min(10, len(trending)), gap="small")
    for i, (tc, tm) in enumerate(zip(tcols, trending)):
        with tc:
            st.markdown(f"""<div class="trend-card anim" style="position:relative;animation-delay:{i*0.04}s">
                <div class="trend-rank">#{i+1}</div>
                <img src="{tm['poster'] or 'https://via.placeholder.com/342x513/1A1A2E/6C63FF?text=N/A'}" loading="lazy"/>
                <div class="trend-body"><div class="trend-title">{tm['title']}</div><div class="trend-meta">⭐ {tm['rating']:.1f} · {tm['year']}</div></div>
            </div>""", unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# ━━━ STEP 1: Select Movie ━━━
st.markdown('<div class="section-hdr">🔍 Step 1 — Select a Film</div>', unsafe_allow_html=True)

col_l, col_c, col_r = st.columns([1, 3, 1])
with col_c:
    search_query = st.text_input("Search (fuzzy enabled)", placeholder="Type a movie name...", key="search")
    if search_query:
        q = search_query.lower().strip()
        exact = [m for m in movie_list if m.lower()==q]
        starts = [m for m in movie_list if m.lower().startswith(q) and m.lower()!=q]
        contains = [m for m in movie_list if q in m.lower() and not m.lower().startswith(q)]
        subs = exact + starts + contains
        fuzzy_r = process.extract(q, movie_list, scorer=fuzz.token_set_ratio, limit=15)
        fuzzy_m = [r[0] for r in fuzzy_r if r[1]>=65 and r[0] not in subs]
        filtered = subs + fuzzy_m
        if filtered:
            lbl = f"🎯 {len(filtered)} movie(s) found"
            if not subs and fuzzy_m: lbl += " (fuzzy match)"
            selected_movie = st.selectbox(lbl, filtered, index=0)
        else:
            st.warning(f"❌ No matches for \"{search_query}\"")
            selected_movie = None
    else:
        selected_movie = st.selectbox("Browse catalog", movie_list, index=None, placeholder="Or browse all...")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# ━━━ STEP 2: Select Mood ━━━
st.markdown('<div class="section-hdr">💫 Step 2 — Set Your Mood</div>', unsafe_allow_html=True)

mood_cols = st.columns(4)
selected_mood = None
for i, (mood_key, mood_info) in enumerate(MOOD_MAP.items()):
    with mood_cols[i % 4]:
        emoji, label = mood_key.split(" ", 1)
        if st.button(f"{emoji}\n{label}", key=f"mood_{i}", width="stretch"):
            st.session_state['selected_mood'] = mood_key

selected_mood = st.session_state.get('selected_mood')
if selected_mood:
    st.success(f"Mood: **{selected_mood}** — Looking for {', '.join(MOOD_MAP[selected_mood]['genres'])} movies")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# ━━━ STEP 3: Get Hybrid Recommendations ━━━
st.markdown('<div class="section-hdr">🚀 Step 3 — Launch Recommendations</div>', unsafe_allow_html=True)

col_l2, col_c2, col_r2 = st.columns([1, 3, 1])
with col_c2:
    rec_btn = st.button("🎬 Analyze & Recommend", width="stretch")

if rec_btn and selected_movie:
    # Save to history
    if selected_movie not in ud.get('history', []):
        ud.setdefault('history', []).append(selected_movie)
    if selected_mood:
        ud.setdefault('mood_history', []).append({'mood': selected_mood, 'movie': selected_movie, 'time': datetime.now().isoformat()})
    save_user(st.session_state.username, ud)

    # Analysis steps visualization
    st.markdown("""
    <div class="step-container">
        <div class="step-pill step-done">✓ Movie Selected</div>
        <div class="step-pill step-done">✓ Mood Analyzed</div>
        <div class="step-pill step-active">⚡ Hybrid Model Running</div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("🧠 Running hybrid recommendation engine..."):
        # Fetch selected movie details
        sel_movie_id = movies[movies['title'] == selected_movie].iloc[0].movie_id
        sel_details = fetch_movie_details(sel_movie_id)

        # 1. Content-based (main)
        content_recs = get_content_recs(selected_movie, n=5)

        # 2. History-based
        history_recs = get_history_recs(ud, selected_movie, n=3)

        # 3. Mood-based
        mood_recs = get_mood_recs(selected_mood, selected_movie, n=3) if selected_mood else []

    # Update steps
    st.markdown("""
    <div class="step-container">
        <div class="step-pill step-done">✓ Movie Selected</div>
        <div class="step-pill step-done">✓ Mood Analyzed</div>
        <div class="step-pill step-done">✓ Hybrid Analysis Complete</div>
    </div>
    """, unsafe_allow_html=True)

    # ── SELECTED MOVIE DETAILS ──
    if sel_details:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="section-hdr">🎯 Your Selected Movie</div>', unsafe_allow_html=True)

        sel_l, sel_r = st.columns([1, 2.5])
        with sel_l:
            sel_poster = sel_details.get('poster') or "https://via.placeholder.com/500x750/1A1A2E/6C63FF?text=N/A"
            st.markdown(f"""
            <div class="movie-card anim" style="max-width:320px">
                <div class="poster-wrap">
                    <img src="{sel_poster}" loading="lazy"/>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with sel_r:
            st.markdown(f'<div class="details-title">{selected_movie}</div>', unsafe_allow_html=True)
            if sel_details.get('tagline'):
                st.markdown(f'<div class="details-tagline">"{sel_details["tagline"]}"</div>', unsafe_allow_html=True)
            if sel_details.get('overview'):
                st.markdown(f'<div class="details-overview">{sel_details["overview"]}</div>', unsafe_allow_html=True)

            sel_rt = f"{sel_details['runtime']}min" if sel_details.get('runtime') else "—"
            sel_meta = f'<div class="details-meta">'
            sel_meta += f'<div class="meta-item"><div class="meta-val">⭐ {sel_details["rating"]:.1f}</div><div class="meta-lbl">{sel_details.get("vote_count",0):,} votes</div></div>'
            sel_meta += f'<div class="meta-item"><div class="meta-val">🕐 {sel_rt}</div><div class="meta-lbl">Runtime</div></div>'
            sel_meta += f'<div class="meta-item"><div class="meta-val">📅 {sel_details.get("year","")}</div><div class="meta-lbl">Year</div></div>'
            if sel_details.get('budget'):
                sel_meta += f'<div class="meta-item"><div class="meta-val">💰 {fmt_money(sel_details["budget"])}</div><div class="meta-lbl">Budget</div></div>'
            if sel_details.get('revenue'):
                sel_meta += f'<div class="meta-item"><div class="meta-val">💵 {fmt_money(sel_details["revenue"])}</div><div class="meta-lbl">Revenue</div></div>'
            sel_meta += '</div>'
            st.markdown(sel_meta, unsafe_allow_html=True)

            if sel_details.get('genres'):
                st.markdown(" ".join([f'<span class="badge badge-genre" style="font-size:0.75rem;padding:0.2rem 0.6rem">{g}</span>' for g in sel_details['genres']]), unsafe_allow_html=True)
            if sel_details.get('director'):
                st.markdown(f"**🎬 Director:** {sel_details['director']}")

        # Cast for selected movie
        if sel_details.get('cast'):
            st.markdown("**🎭 Top Cast**")
            cast_cols = st.columns(min(5, len(sel_details['cast'])))
            for cc, actor in zip(cast_cols, sel_details['cast']):
                with cc:
                    if actor['photo']:
                        st.image(actor['photo'], width=80)
                    st.caption(f"**{actor['name']}**\n{actor['character']}")

        # Trailer for selected movie
        if sel_details.get('trailer_key'):
            st.markdown("**🎥 Watch Trailer**")
            st.video(f"https://www.youtube.com/watch?v={sel_details['trailer_key']}")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── CONTENT-BASED RESULTS ──
    st.markdown(f'<div class="section-hdr">🎬 Similar Movies <span style="font-size:0.7rem;color:#9CA3AF">(content similarity)</span></div>', unsafe_allow_html=True)

    cols = st.columns(5, gap="medium")
    for idx, (col, m) in enumerate(zip(cols, content_recs)):
        with col:
            poster_url = m['poster'] or "https://via.placeholder.com/500x750/1A1A2E/6C63FF?text=N/A"
            genre_badges = "".join([f'<span class="badge badge-genre">{g}</span>' for g in m.get('genres',[])])
            year_badge = f'<span class="badge badge-year">{m["year"]}</span>' if m.get('year') else ''
            grad, color = get_conf_color(m['match'])
            st.markdown(f"""
            <div class="movie-card anim" style="animation-delay:{idx*0.08}s">
                <div class="poster-wrap">
                    <img src="{poster_url}" loading="lazy"/>
                    <div class="poster-overlay"><span>{'🎥 Trailer' if m.get('trailer_key') else '📋 Details'}</span></div>
                </div>
                <div class="card-body">
                    <div class="card-title">{m['title']}</div>
                    <div class="badge-row"><span class="rating">⭐ {m['rating']:.1f}</span></div>
                    <div class="badge-row">{genre_badges} {year_badge}</div>
                    <div class="conf-wrap">
                        <div class="conf-bar-bg"><div class="conf-bar-fill" style="width:{m['match']}%;background:{grad}"></div></div>
                        <div class="conf-label"><span class="conf-text">Confidence</span><span class="conf-pct" style="color:{color}">{m['match']}%</span></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── HISTORY-BASED RESULTS ──
    if history_recs:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="section-hdr">📜 Based on Your History <span style="font-size:0.7rem;color:#9CA3AF">(user patterns)</span></div>', unsafe_allow_html=True)
        hcols = st.columns(min(3, len(history_recs)), gap="medium")
        for idx, (col, m) in enumerate(zip(hcols, history_recs)):
            with col:
                poster_url = m['poster'] or "https://via.placeholder.com/500x750/1A1A2E/6C63FF?text=N/A"
                grad, color = get_conf_color(m['match'])
                st.markdown(f"""
                <div class="movie-card anim" style="animation-delay:{idx*0.08}s">
                    <div class="poster-wrap"><img src="{poster_url}" loading="lazy"/></div>
                    <div class="card-body">
                        <div class="card-title">{m['title']}</div>
                        <div class="badge-row"><span class="rating">⭐ {m['rating']:.1f}</span> <span class="badge" style="background:rgba(212,168,67,0.12);color:#D4A843;border:1px solid rgba(212,168,67,0.25)">📜 History</span></div>
                        <div class="conf-wrap">
                            <div class="conf-bar-bg"><div class="conf-bar-fill" style="width:{m['match']}%;background:{grad}"></div></div>
                            <div class="conf-label"><span class="conf-text">Match</span><span class="conf-pct" style="color:{color}">{m['match']}%</span></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── MOOD-BASED RESULTS ──
    if mood_recs:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        mood_label = MOOD_MAP.get(selected_mood, {}).get('label', 'Mood')
        st.markdown(f'<div class="section-hdr">💫 {selected_mood} Picks <span style="font-size:0.7rem;color:#9CA3AF">(emotion match)</span></div>', unsafe_allow_html=True)
        mcols = st.columns(min(3, len(mood_recs)), gap="medium")
        for idx, (col, m) in enumerate(zip(mcols, mood_recs)):
            with col:
                poster_url = m['poster'] or "https://via.placeholder.com/500x750/1A1A2E/6C63FF?text=N/A"
                grad, color = get_conf_color(m['match'])
                st.markdown(f"""
                <div class="movie-card anim" style="animation-delay:{idx*0.08}s">
                    <div class="poster-wrap"><img src="{poster_url}" loading="lazy"/></div>
                    <div class="card-body">
                        <div class="card-title">{m['title']}</div>
                        <div class="badge-row"><span class="rating">⭐ {m['rating']:.1f}</span> <span class="badge" style="background:rgba(180,80,80,0.12);color:#C25555;border:1px solid rgba(180,80,80,0.25)">💫 Mood</span></div>
                        <div class="conf-wrap">
                            <div class="conf-bar-bg"><div class="conf-bar-fill" style="width:{m['match']}%;background:{grad}"></div></div>
                            <div class="conf-label"><span class="conf-text">Match</span><span class="conf-pct" style="color:{color}">{m['match']}%</span></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── DETAILED VIEWS ──
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-hdr">📋 Detailed Analysis</div>', unsafe_allow_html=True)

    all_recs = content_recs + history_recs + mood_recs
    # De-duplicate
    seen = set()
    unique_recs = []
    for r in all_recs:
        if r['title'] not in seen:
            seen.add(r['title'])
            unique_recs.append(r)

    for idx, m in enumerate(unique_recs[:6]):
        source_icon = {"content": "🎬", "history": "📜", "mood": "💫"}.get(m.get('source',''), '🎬')
        with st.expander(f"{m['title']} — {m['match']}% match", expanded=(idx==0), icon=source_icon):
            # Explanation
            explain_html = "".join([f'<div class="explain-reason">{r}</div>' for r in m.get('explanations',[])])
            st.markdown(f'<div class="explain-card"><div class="explain-title">📊 Why this was recommended</div>{explain_html}</div>', unsafe_allow_html=True)
            st.markdown("")

            dl, dr = st.columns([1, 2])
            with dl:
                if m['poster']: st.image(m['poster'], width="stretch")
            with dr:
                st.markdown(f'<div class="details-title">{m["title"]}</div>', unsafe_allow_html=True)
                if m.get('tagline'): st.markdown(f'<div class="details-tagline">"{m["tagline"]}"</div>', unsafe_allow_html=True)
                rt = f"{m['runtime']}min" if m.get('runtime') else "—"
                meta = f'<div class="details-meta"><div class="meta-item"><div class="meta-val">⭐ {m["rating"]:.1f}</div><div class="meta-lbl">{m.get("vote_count",0):,} votes</div></div><div class="meta-item"><div class="meta-val">🕐 {rt}</div><div class="meta-lbl">Runtime</div></div><div class="meta-item"><div class="meta-val">📅 {m.get("year","")}</div><div class="meta-lbl">Year</div></div>'
                if m.get('budget'): meta += f'<div class="meta-item"><div class="meta-val">💰 {fmt_money(m["budget"])}</div><div class="meta-lbl">Budget</div></div>'
                if m.get('revenue'): meta += f'<div class="meta-item"><div class="meta-val">💵 {fmt_money(m["revenue"])}</div><div class="meta-lbl">Revenue</div></div>'
                meta += '</div>'
                st.markdown(meta, unsafe_allow_html=True)

                grad, color = get_conf_color(m['match'])
                st.markdown(f'<div style="margin-bottom:0.5rem"><div style="display:flex;justify-content:space-between;margin-bottom:0.1rem"><span style="font-size:0.7rem;font-weight:600;color:#4B5563">Confidence</span><span style="font-size:0.9rem;font-weight:800;color:{color}">{m["match"]}%</span></div><div style="background:#F3F4F6;border-radius:10px;height:7px;overflow:hidden"><div style="background:{grad};width:{m["match"]}%;height:100%;border-radius:10px"></div></div></div>', unsafe_allow_html=True)

                if m.get('overview'): st.markdown(f'<div class="details-overview">{m["overview"]}</div>', unsafe_allow_html=True)
                if m.get('genres'): st.markdown(" ".join([f'<span class="badge badge-genre" style="font-size:0.65rem;padding:0.12rem 0.45rem">{g}</span>' for g in m['genres']]), unsafe_allow_html=True)
                if m.get('director'): st.markdown(f"**🎬 Director:** {m['director']}")

            if m.get('cast'):
                st.markdown("**🎭 Top Cast**")
                for cc, actor in zip(st.columns(min(5, len(m['cast']))), m['cast']):
                    with cc:
                        if actor['photo']: st.image(actor['photo'], width=70)
                        st.caption(f"**{actor['name']}**\n{actor['character']}")

            if m.get('trailer_key'):
                st.markdown("**🎥 Watch Trailer**")
                st.video(f"https://www.youtube.com/watch?v={m['trailer_key']}")

elif rec_btn and not selected_movie:
    st.warning("🎬 Please select a movie first!")


# Footer
st.markdown("""
<div class="footer">
    Crafted with 🎞️ passion · <strong>CineMatch</strong> Premium Vault · Hybrid AI Engine
    <br/>13,000+ titles · <a href="https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset">The Movies Dataset</a> · <a href="https://www.themoviedb.org/">TMDB</a>
</div>
""", unsafe_allow_html=True)
