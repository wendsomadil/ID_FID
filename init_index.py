# init_index.py
"""
Ce script initialise l'index FAISS en extrayant les données des fichiers sources
(PDF, Excel, Word) via `load_text_data()` et en générant les embeddings nécessaires.
Doit être exécuté avant de lancer l'application principale.
"""

import os
import faiss
from sentence_transformers import SentenceTransformer

from chatbot.utils import load_text_data
from chatbot.config import FAISS_INDEX_PATH

def create_faiss_index(embedding_dim: int) -> faiss.Index:
    """Initialise un index FAISS de type L2 avec la dimension donnée."""
    return faiss.IndexFlatL2(embedding_dim)

def index_documents_with_faiss(texts: dict[str, str],
                               encoder: SentenceTransformer,
                               index: faiss.Index) -> faiss.Index:
    """
    Génère des embeddings pour les textes et les ajoute à l'index FAISS.
    texts : dict où chaque valeur est un document texte à encoder.
    """
    documents = list(texts.values())
    # Encodage
    embeddings = encoder.encode(documents,
                                convert_to_numpy=True,
                                show_progress_bar=True)
    # Ajout à l'index
    index.add(embeddings)
    return index

if __name__ == "__main__":
    # 1) Charger tous les textes (PDF, Excel, Word)
    print("Chargement des documents source…")
    texts = load_text_data()
    if not texts:
        print("⚠️ Aucun document trouvé. Vérifiez vos répertoires source.")
        exit(1)
    print(f"➡️ {len(texts)} documents chargés.")

    # 2) Initialiser le modèle d'encodage
    print("Initialisation du modèle SentenceTransformer…")
    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    embedding_dim = encoder.get_sentence_embedding_dimension()
    print(f"Dimension des embeddings : {embedding_dim}")

    # 3) Créer ou recréer l'index FAISS
    print("Création de l'index FAISS…")
    faiss_index = create_faiss_index(embedding_dim)

    # 4) Indexer les documents
    print("Génération des embeddings et indexation…")
    faiss_index = index_documents_with_faiss(texts, encoder, faiss_index)
    print(f"✔️ {faiss_index.ntotal} vecteurs indexés.")

    # 5) Sauvegarder l'index à la racine du projet
    os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
    faiss.write_index(faiss_index, FAISS_INDEX_PATH)
    print(f"✅ Index FAISS sauvegardé dans : {FAISS_INDEX_PATH}")
