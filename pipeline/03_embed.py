# for each movie create a textual represenetation that combines title, genre, keyword and production company
#build a dictionary that maps movie id to its textual representation
import pandas as pd
import numpy as np
import json
import hashlib
from pathlib import Path
from joblib import dump, load
from scipy.sparse import save_npz
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer


movie_text_dict = {}
def dictionary_builder(df, dict): #in the dictionary, the key is the movie id and the value is the textual representation of the movie
    for index, row in df.iterrows():
        movie_id = row['id']
        title = row['title']
        genre = row['genres']
        keyword = row['keywords']
        production_company = row['production_companies']
        #combine the textual representation
        textual_representation = f"{title} {genre} {keyword} {production_company}"
        dict[movie_id] = textual_representation
    return dict
path = Path(__file__).resolve().parent / "data" / "df_modified_02.csv"
df_modified_02 = pd.read_csv(path)
dictionary_builder(df_modified_02, movie_text_dict)


#print the first 5 items of the dictionary
print("First 5 items of the movie text dictionary:")
for i, (key, value) in enumerate(movie_text_dict.items()):
    if i >= 5:
        break
    print(f"Movie ID: {key}, Textual Representation: {value}")

embedding_models = {"paraphrase-multilingual-MiniLM-L12-v2": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "paraphrase-multilingual-mpnet-base-v2": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    "intfloat/multilingual-e5-small": "intfloat/multilingual-e5-small",
    "intfloat/multilingual-e5-base": "intfloat/multilingual-e5-base",
    "BAAI/bge-m3": "BAAI/bge-m3"}

movie_ids = list(movie_text_dict.keys())#align the movie ids with the textual representations
movie_texts = list(movie_text_dict.values())
template_name = "title_genres_keywords_production_companies"
data_dir = Path(__file__).resolve().parent / "data" #create a directory to store the embeddings and other outputs
output_dir = data_dir / template_name / "overview"
output_dir.mkdir(parents=True, exist_ok=True)  
cache_path = output_dir / "embedding_cache.json" #load the cache if it exists, otherwise create an empty cache
try:
    cache = json.loads(cache_path.read_text(encoding="utf-8"))
except (FileNotFoundError, json.JSONDecodeError):
    cache = {}


def fingerprint(value):
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest() #the fingerprint is a SHA-256 hash of the serialized value, which is used to determine if the data has changed and if the cached version can be used.


def is_cached(filename, signature):
    return (output_dir / filename).is_file() and cache.get(filename) == signature #check if the file exists and if the signature matches the cached signature
#signature is a hash of the data, so if the data changes, the signature will change and the cached version will not be used.
#this function saves the data to a temporary file and then renames it to the final filename, which ensures that the file is not corrupted if the process is interrupted. It also updates the cache with the new signature.
def save_cached(filename, signature, writer):
    output_path = output_dir / filename
    temporary_path = output_path.with_name(output_path.stem + ".tmp" + output_path.suffix)
    writer(temporary_path)
    temporary_path.replace(output_path)
    cache[filename] = signature
    temporary_cache_path = cache_path.with_suffix(".tmp.json")
    temporary_cache_path.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")
    temporary_cache_path.replace(cache_path)


movie_ids_array = np.asarray(movie_ids, dtype=np.int64)
movie_ids_signature = fingerprint(movie_ids_array.tolist())
corpus_signature = fingerprint({
    "template": template_name,
    "movie_ids": movie_ids_array.tolist(),
    "movie_texts": movie_texts,
})
if not is_cached("movie_ids.npy", movie_ids_signature):
    save_cached("movie_ids.npy", movie_ids_signature,
                lambda destination: np.save(destination, movie_ids_array))

query_dfs = []
for language in ["en", "it"]:
    with (data_dir / f"queries_{language}.json").open(encoding="utf-8") as source:
        queries = json.load(source)
    query_df = pd.DataFrame([
        {
            "query_id": query_id,
            "query": definition["text"],
            "language": language,
        }
        for query_id, definition in queries.items()
    ])
    query_dfs.append(query_df)
    query_ids = query_df["query_id"].to_numpy(dtype=str)
    query_ids_signature = fingerprint(query_ids.tolist())
    query_ids_filename = f"query_ids_{language}.npy"
    if not is_cached(query_ids_filename, query_ids_signature):
        save_cached(query_ids_filename, query_ids_signature,
                    lambda destination: np.save(destination, query_ids))

query_signatures = {
    query_df.iloc[0]["language"]: fingerprint({
        "query_ids": query_df["query_id"].tolist(),
        "query_texts": query_df["query"].tolist(),
    })
    for query_df in query_dfs
}

tfidf_signature = fingerprint({"corpus": corpus_signature, "settings": "tfidf_defaults_v1"})
tfidf_tasks = [("tfidf_vectors.npz", movie_texts, tfidf_signature)]

#tfidf vectorization for queries
for query_df in query_dfs:
    language = query_df.iloc[0]['language']
    query_texts = query_df['query'].tolist()
    signature = fingerprint({"tfidf": tfidf_signature, "queries": query_signatures[language]})
    tfidf_tasks.append((f"query_tfidf_vectors_{language}.npz", query_texts, signature))

pending_tfidf_tasks = [task for task in tfidf_tasks if not is_cached(task[0], task[2])]
if pending_tfidf_tasks:
    if is_cached("tfidf_vectorizer.joblib", tfidf_signature):
        tfidf_vectorizer = load(output_dir / "tfidf_vectorizer.joblib")
    else:
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_vectorizer.fit(movie_texts)
        save_cached("tfidf_vectorizer.joblib", tfidf_signature,
                    lambda destination: dump(tfidf_vectorizer, destination))
    for filename, texts, signature in pending_tfidf_tasks:
        tfidf_vectors = tfidf_vectorizer.transform(texts)
        save_cached(filename, signature,
                    lambda destination: save_npz(destination, tfidf_vectors))
        del tfidf_vectors
else:
    print("Using cached TF-IDF vectors.")

#encode using the embedding models
for model_name, model_path in embedding_models.items():
    safe_model_name = model_name.replace("/", "_") 
    is_e5 = model_name.startswith("intfloat/multilingual-e5")
    model_settings = {"model": model_path, "normalize_embeddings": True, "e5_prefixes": is_e5}
    movie_signature = fingerprint({"corpus": corpus_signature, **model_settings})
    movie_filename = f"embeddings_{safe_model_name}.npy"
    query_tasks = []
    for query_df in query_dfs:
        language = query_df.iloc[0]['language']
        signature = fingerprint({"queries": query_signatures[language], **model_settings})
        filename = f"query_embeddings_{safe_model_name}_{language}.npy"
        if not is_cached(filename, signature):
            query_tasks.append((filename, query_df['query'].tolist(), signature))
    if is_cached(movie_filename, movie_signature) and not query_tasks:
        print(f"Using cached embeddings for {model_name}.")
        continue

    model = SentenceTransformer(model_path) #use sentence-transformers to encode the movie texts and queries into embeddings
    if not is_cached(movie_filename, movie_signature):
        print(f"Encoding using {model_name}...")
        model_texts = movie_texts
        if is_e5:
            model_texts = ["passage: " + text for text in movie_texts]
        embeddings = model.encode(
            model_texts,
            show_progress_bar=True,
            normalize_embeddings=True,
        )
        #save the embeddings to a NumPy file; rows match movie_ids.npy
        save_cached(movie_filename, movie_signature,
                    lambda destination: np.save(destination, embeddings))
        del embeddings

    #dense model embeddings for queries propend "query:" for multilingual-e5 models
    for filename, query_texts, signature in query_tasks:
        print(f"Encoding queries using {model_name}...")
        model_query_texts = query_texts
        if is_e5:
            model_query_texts = ["query: " + text for text in query_texts]
        query_embeddings = model.encode(
            model_query_texts,
            show_progress_bar=True,
            normalize_embeddings=True,
        )
        save_cached(filename, signature,
                    lambda destination: np.save(destination, query_embeddings))
        del query_embeddings
    del model
