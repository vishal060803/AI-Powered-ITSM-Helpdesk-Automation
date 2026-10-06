import argparse
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EMBEDDINGS_FILE = PROJECT_ROOT / "data" / "embeddings" / "knowledge_chunks.jsonl"
DEFAULT_PERSIST_DIRECTORY = PROJECT_ROOT / "data" / "vector_store" / "chroma"
DEFAULT_COLLECTION_NAME = "knowledge_chunks"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
REQUIRED_CHUNK_FIELDS = (
    "chunk_id",
    "article_id",
    "title",
    "category",
    "sub_category",
    "source_file",
    "text",
    "embedding",
)


def load_embedding_records(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as source_file:
        for line_number, line in enumerate(source_file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_number} of {path}."
                ) from error
            if not isinstance(record, dict):
                raise ValueError(f"Expected a JSON object on line {line_number} of {path}.")
            missing_fields = [
                field for field in REQUIRED_CHUNK_FIELDS if field not in record
            ]
            if missing_fields:
                missing = ", ".join(missing_fields)
                raise ValueError(
                    f"Missing chunk fields on line {line_number} of {path}: {missing}."
                )
            records.append(record)
    return records


def _to_chroma_metadata(record: dict[str, Any]) -> dict[str, str | int | float | bool]:
    metadata: dict[str, str | int | float | bool] = {}
    for key, value in record.items():
        if key in {"embedding", "text"} or value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            metadata[key] = value
        elif isinstance(value, list):
            metadata[key] = ", ".join(str(item) for item in value)
        else:
            metadata[key] = json.dumps(value, ensure_ascii=True, sort_keys=True)
    return metadata


class KnowledgeVectorStore:
    def __init__(
        self,
        persist_directory: Path | None = None,
        collection_name: str | None = None,
        embedding_model_name: str | None = None,
        query_encoder: Any | None = None,
        client: Any | None = None,
    ) -> None:
        import chromadb
        from chromadb.config import Settings

        configured_directory = persist_directory or Path(
            os.getenv("CHROMA_PERSIST_DIRECTORY", str(DEFAULT_PERSIST_DIRECTORY))
        )
        if not configured_directory.is_absolute():
            configured_directory = PROJECT_ROOT / configured_directory

        self.persist_directory = configured_directory
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name or os.getenv(
            "CHROMA_COLLECTION_NAME", DEFAULT_COLLECTION_NAME
        )
        self.embedding_model_name = embedding_model_name or os.getenv(
            "EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL
        )
        self._client = (
            client
            if client is not None
            else chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(anonymized_telemetry=False),
            )
        )
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=None,
        )
        self._query_encoder = query_encoder

    @property
    def count(self) -> int:
        return self._collection.count()

    def index_chunks(self, chunks: list[dict[str, Any]]) -> int:
        if not chunks:
            raise ValueError("No embedded knowledge chunks were provided.")

        ids = [str(chunk["chunk_id"]) for chunk in chunks]
        if len(set(ids)) != len(ids):
            raise ValueError("Knowledge chunks must have unique chunk_id values.")

        vectors = [chunk["embedding"] for chunk in chunks]
        dimensions = {len(vector) for vector in vectors}
        if len(dimensions) != 1 or 0 in dimensions:
            raise ValueError("All knowledge embeddings must have the same non-zero size.")

        existing_ids = set(self._collection.get(include=["metadatas"])["ids"])
        incoming_ids = set(ids)
        stale_ids = existing_ids - incoming_ids
        if stale_ids:
            self._collection.delete(ids=sorted(stale_ids))

        self._collection.upsert(
            ids=ids,
            embeddings=[[float(value) for value in vector] for vector in vectors],
            documents=[str(chunk["text"]) for chunk in chunks],
            metadatas=[_to_chroma_metadata(chunk) for chunk in chunks],
        )
        return self.count

    def search(
        self,
        query: str,
        category: str | None = None,
        topic: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        if not query.strip():
            raise ValueError("Search query must not be empty.")
        if limit < 1:
            raise ValueError("limit must be a positive integer.")
        if self.count == 0:
            return []

        query_encoder = self._query_encoder
        if query_encoder is None:
            from sentence_transformers import SentenceTransformer

            query_encoder = SentenceTransformer(self.embedding_model_name)
            self._query_encoder = query_encoder

        query_vector = query_encoder.encode(
            [query], normalize_embeddings=True, show_progress_bar=False
        )[0]
        if hasattr(query_vector, "tolist"):
            query_vector = query_vector.tolist()

        filters = []
        if category:
            filters.append({"category": {"$eq": category}})
        if topic:
            filters.append({"sub_category": {"$eq": topic}})
        where = None
        if len(filters) == 1:
            where = filters[0]
        elif filters:
            where = {"$and": filters}

        result = self._collection.query(
            query_embeddings=[[float(value) for value in query_vector]],
            n_results=min(limit, self.count),
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        matches = []
        for index, chunk_id in enumerate(result["ids"][0]):
            match = dict(result["metadatas"][0][index])
            match["chunk_id"] = chunk_id
            match["text"] = result["documents"][0][index]
            match["distance"] = float(result["distances"][0][index])
            matches.append(match)
        return matches


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Index or search the persisted IT knowledge vector store."
    )
    parser.add_argument("--embeddings", type=Path, default=DEFAULT_EMBEDDINGS_FILE)
    parser.add_argument("--persist-dir", type=Path, default=None)
    parser.add_argument("--collection", default=None)
    parser.add_argument("--query", help="Semantic search query; omit to index chunks.")
    parser.add_argument("--category", help="Exact article category filter.")
    parser.add_argument("--topic", help="Exact article sub-category filter.")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    store = KnowledgeVectorStore(
        persist_directory=args.persist_dir,
        collection_name=args.collection,
    )
    if args.query:
        print(
            json.dumps(
                store.search(
                    args.query,
                    category=args.category,
                    topic=args.topic,
                    limit=args.limit,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    chunks = load_embedding_records(args.embeddings)
    count = store.index_chunks(chunks)
    print(f"Indexed {len(chunks)} knowledge chunks. Collection now contains {count}.")


if __name__ == "__main__":
    main()
