"""
Generate movie recommendation model using Deep Learning (Sentence Transformers).

Uses the pre-trained 'all-MiniLM-L6-v2' sentence transformer to create 384-dimensional
semantic embeddings for each movie's tag text. Cosine similarity is then computed
on these dense embeddings for far better recommendations than bag-of-words.

Model: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
Dataset: https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset
"""
import os
import ast
import pickle
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'model')

# ─── Load datasets ───
MOVIES_CSV = os.path.join(DATA_DIR, 'movies_metadata.csv')
CREDITS_CSV = os.path.join(DATA_DIR, 'credits.csv')
KEYWORDS_CSV = os.path.join(DATA_DIR, 'keywords.csv')

for f in [MOVIES_CSV, CREDITS_CSV, KEYWORDS_CSV]:
    if not os.path.exists(f):
        print(f"Missing: {f}")
        print("Download 'The Movies Dataset' from Kaggle:")
        print("  https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset")
        exit(1)

print("=" * 60)
print("  Deep Learning Movie Recommender — Model Generation")
print("  Using: all-MiniLM-L6-v2 Sentence Transformer")
print("=" * 60)

print("\n[1/6] Loading CSV files...")
meta = pd.read_csv(MOVIES_CSV, low_memory=False)
credits = pd.read_csv(CREDITS_CSV)
keywords = pd.read_csv(KEYWORDS_CSV)

# ─── Clean IDs ───
meta = meta[meta['id'].apply(lambda x: str(x).isdigit())]
meta['id'] = meta['id'].astype(int)
credits['id'] = credits['id'].astype(int)
keywords['id'] = keywords['id'].astype(int)

# ─── Quality filter ───
meta['vote_count'] = pd.to_numeric(meta['vote_count'], errors='coerce').fillna(0)
meta = meta[meta['vote_count'] >= 25]
meta = meta[meta['adult'] != 'True']
meta = meta[meta['status'] == 'Released']
print(f"    Movies after quality filter: {len(meta)}")

# ─── Merge ───
print("\n[2/6] Merging datasets...")
movies = meta.merge(credits, on='id')
movies = movies.merge(keywords, on='id')
movies = movies[['id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew', 'vote_count', 'vote_average', 'popularity']]
movies.dropna(subset=['title', 'overview'], inplace=True)
movies = movies.reset_index(drop=True)
print(f"    Merged dataset: {len(movies)} movies")

# ─── Helper functions ───
def safe_parse(text):
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return []

def extract_names(text):
    return [item['name'] for item in safe_parse(text)]

def extract_top3_cast(text):
    parsed = safe_parse(text)
    return [item['name'] for item in parsed[:3]]

def extract_director(text):
    return [item['name'] for item in safe_parse(text) if item.get('job') == 'Director']

# ─── Process features ───
print("\n[3/6] Processing features...")
movies['genres'] = movies['genres'].apply(extract_names)
movies['keywords'] = movies['keywords'].apply(extract_names)
movies['cast'] = movies['cast'].apply(extract_top3_cast)
movies['crew'] = movies['crew'].apply(extract_director)

# Build rich text descriptions for the sentence transformer
# We create natural-language-like descriptions for better semantic understanding
def build_description(row):
    """Build natural language description for better semantic embeddings."""
    parts = []

    # Overview is the main content
    if isinstance(row['overview'], str) and row['overview'].strip():
        parts.append(row['overview'])

    # Genres as natural text
    if row['genres']:
        parts.append(f"Genres: {', '.join(row['genres'])}.")

    # Keywords
    if row['keywords']:
        parts.append(f"Themes: {', '.join(row['keywords'][:8])}.")

    # Cast
    if row['cast']:
        parts.append(f"Starring: {', '.join(row['cast'])}.")

    # Director
    if row['crew']:
        parts.append(f"Directed by {', '.join(row['crew'])}.")

    return " ".join(parts)

movies['description'] = movies.apply(build_description, axis=1)

# Build final dataframe
new = movies[['id', 'title', 'description']].copy()
new.columns = ['movie_id', 'title', 'tags']
new = new.drop_duplicates(subset='title', keep='first').reset_index(drop=True)
print(f"    Final dataset: {len(new)} unique movies")

# ─── Deep Learning: Sentence Transformer Embeddings ───
print("\n[4/6] Loading sentence transformer model (all-MiniLM-L6-v2)...")
model = SentenceTransformer('all-MiniLM-L6-v2')

print("\n[5/6] Generating semantic embeddings for all movies...")
print(f"    This will encode {len(new)} movie descriptions into 384-dim vectors...")

descriptions = new['tags'].tolist()
embeddings = model.encode(
    descriptions,
    show_progress_bar=True,
    batch_size=128,
    normalize_embeddings=True,  # Pre-normalize for faster cosine similarity
)

print(f"    Embeddings shape: {embeddings.shape}")

print("\n    Computing cosine similarity matrix...")
similarity = cosine_similarity(embeddings)
print(f"    Similarity matrix shape: {similarity.shape}")

# ─── Save model ───
print(f"\n[6/6] Saving model files to {MODEL_DIR}...")
os.makedirs(MODEL_DIR, exist_ok=True)

movie_list_path = os.path.join(MODEL_DIR, 'movie_list.pkl')
similarity_path = os.path.join(MODEL_DIR, 'similarity.pkl')

pickle.dump(new, open(movie_list_path, 'wb'))
pickle.dump(similarity, open(similarity_path, 'wb'))

print(f"\n{'=' * 60}")
print(f"  ✅ Model generation complete!")
print(f"{'=' * 60}")
print(f"  📁 {movie_list_path} ({os.path.getsize(movie_list_path) / 1024 / 1024:.1f} MB)")
print(f"  📁 {similarity_path} ({os.path.getsize(similarity_path) / 1024 / 1024:.1f} MB)")
print(f"  🎬 Total movies: {len(new)}")
print(f"  🧠 Embedding model: all-MiniLM-L6-v2 (384 dimensions)")
print(f"  📐 Method: Sentence Transformer + Cosine Similarity")
