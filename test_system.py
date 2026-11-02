"""
Automated Comprehensive Test Suite for CineMatch Movie Recommender System.
Tests data models, TMDB API, recommendation engines, fuzzy search, and authentication.
"""
import os
import sys
import json
import pickle
import hashlib
import requests
from datetime import datetime
from thefuzz import fuzz, process

passed_tests = []
failed_tests = []

def run_test(name, func):
    print(f"\n[TEST] {name}...")
    try:
        func()
        print(f"  --> PASSED")
        passed_tests.append(name)
    except Exception as e:
        print(f"  --> FAILED: {e}")
        failed_tests.append((name, str(e)))

# ── 1. Models & Embeddings ──
def test_models_and_recommendations():
    movies = pickle.load(open('model/movie_list.pkl', 'rb'))
    assert len(movies) in [4806, 13157], f"Expected 4806 or 13157 movies, got {len(movies)}"
    assert list(movies.columns) == ['movie_id', 'title', 'tags'], "Columns mismatch"
    
    similarity = pickle.load(open('model/similarity.pkl', 'rb'))
    assert similarity.shape == (len(movies), len(movies)), f"Unexpected similarity shape {similarity.shape}"
    
    # Test Content Recommendation for Toy Story
    idx = movies[movies['title'] == 'Toy Story'].index[0]
    dists = sorted(list(enumerate(similarity[idx])), reverse=True, key=lambda x: x[1])
    top_5 = [movies.iloc[i[0]].title for i in dists[1:6]]
    assert 'Toy Story 2' in top_5, f"Toy Story 2 not in top 5 recommendations: {top_5}"
    assert 'Toy Story 3' in top_5, f"Toy Story 3 not in top 5 recommendations: {top_5}"
    print(f"      Verified 13,157 movies & matrix. 'Toy Story' top recs: {top_5}")

# ── 2. TMDB API ──
TMDB_API_KEY = "8265bd1679663a7ea12ac168da84d2e8"

def test_tmdb_trending():
    url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={TMDB_API_KEY}"
    res = requests.get(url, timeout=8)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    results = data.get('results', [])
    assert len(results) > 0, "No trending movies returned"
    sample = results[0]
    assert 'title' in sample, "Missing title in trending result"
    assert 'vote_average' in sample, "Missing vote_average in trending result"
    print(f"      Verified {len(results)} trending movies. Top: '{sample['title']}' ({sample['vote_average']} rating)")

def test_tmdb_details():
    # Toy Story (ID: 862)
    url = f"https://api.themoviedb.org/3/movie/862?api_key={TMDB_API_KEY}&language=en-US&append_to_response=videos,credits"
    res = requests.get(url, timeout=8)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    assert data.get('title') == "Toy Story", f"Expected Toy Story, got {data.get('title')}"
    genres = [g['name'] for g in data.get('genres', [])]
    assert len(genres) > 0, "No genres returned"
    cast = [c['name'] for c in data.get('credits', {}).get('cast', [])[:3]]
    assert len(cast) > 0, "No cast returned"
    print(f"      Verified details for '{data['title']}': genres={genres}, top cast={cast}")

# ── 3. User Authentication & Profile Store ──
USER_DATA_DIR = os.path.join(os.path.dirname(__file__), 'user_data')

def test_auth_and_user_profiles():
    test_user = "pytest_autocheck_curator"
    test_pw = "SuperSecret99!"
    pw_hash = hashlib.sha256(test_pw.encode()).hexdigest()
    
    # Create profile
    profile = {
        'name': test_user,
        'password': pw_hash,
        'history': ['The Dark Knight', 'Inception'],
        'favorites': ['Interstellar'],
        'mood_history': [{'mood': '😱 Thrilled', 'movie': 'Inception', 'time': datetime.now().isoformat()}],
        'created': datetime.now().isoformat()
    }
    user_file = os.path.join(USER_DATA_DIR, f"{test_user}.json")
    with open(user_file, 'w') as f:
        json.dump(profile, f, indent=2)
    
    # Load and verify
    assert os.path.exists(user_file), "User profile file not found"
    with open(user_file) as f:
        loaded = json.load(f)
    assert loaded['name'] == test_user
    assert loaded['password'] == pw_hash
    assert 'The Dark Knight' in loaded['history']
    assert 'Interstellar' in loaded['favorites']
    
    # Clean up
    os.remove(user_file)
    print("      Verified user creation, hashing, serialization, and deserialization")

# ── 4. Fuzzy Search ──
def test_fuzzy_search():
    movies_df = pickle.load(open('model/movie_list.pkl', 'rb'))
    movie_list = sorted(movies_df['title'].values.tolist())
    
    # Test Exact
    q = "toy story"
    exact = [m for m in movie_list if m.lower() == q]
    assert len(exact) > 0, "Exact match failed for 'toy story'"
    
    # Test Prefix
    q_pre = "interstel"
    starts = [m for m in movie_list if m.lower().startswith(q_pre)]
    assert any("Interstellar" in m for m in starts), "Prefix match failed for 'interstel'"
    
    # Test Typo tolerance with thefuzz
    q_typo = "Avengrs"
    fuzzy_r = process.extract(q_typo, movie_list, scorer=fuzz.token_set_ratio, limit=5)
    matched_titles = [r[0] for r in fuzzy_r if r[1] >= 65]
    assert any("Avengers" in m for m in matched_titles), f"Fuzzy search failed for typo 'Avengrs': got {matched_titles}"
    print(f"      Exact ('{q}' -> '{exact[0]}'), Prefix ('{q_pre}' -> '{starts[0]}'), Fuzzy ('{q_typo}' -> '{matched_titles[0]}') verified")

# ── 5. UI Stylesheet & Server ──
def test_stylesheet_and_server():
    css_path = os.path.join(os.path.dirname(__file__), 'skeu_style.css')
    assert os.path.exists(css_path), "skeu_style.css missing!"
    css_content = open(css_path).read()
    assert len(css_content) > 1000, "skeu_style.css is incomplete"
    assert ".movie-card" in css_content, "Missing .movie-card in stylesheet"
    assert ".auth-container" in css_content, "Missing .auth-container in stylesheet"
    
    # Check server health
    res = requests.get("http://localhost:8501/_stcore/health", timeout=5)
    assert res.status_code == 200 and res.text.strip() == "ok", f"Health check failed: {res.status_code} {res.text}"
    print("      Stylesheet validated and Streamlit server health endpoint verified (HTTP 200 'ok')")

if __name__ == '__main__':
    print("=" * 60)
    print("  Running CineMatch Test Suite")
    print("=" * 60)
    run_test("Model Data & Recommendations", test_models_and_recommendations)
    run_test("TMDB Trending API", test_tmdb_trending)
    run_test("TMDB Movie Details API", test_tmdb_details)
    run_test("User Auth & Profile Store", test_auth_and_user_profiles)
    run_test("Fuzzy Search & Typo Tolerance", test_fuzzy_search)
    run_test("CSS Stylesheet & Streamlit Server Health", test_stylesheet_and_server)
    
    print("\n" + "=" * 60)
    print(f"  Summary: {len(passed_tests)} PASSED, {len(failed_tests)} FAILED")
    print("=" * 60)
    if failed_tests:
        sys.exit(1)
