from pathlib import Path
import unittest

from backend.app.knowledge_pipeline import (
    chunk_articles,
    generate_embeddings,
    load_articles,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTICLES_DIRECTORY = PROJECT_ROOT / "data" / "knowledge_docs"


class KnowledgeLoadingTests(unittest.TestCase):
    def test_loads_article_frontmatter_and_body(self):
        articles = load_articles(ARTICLES_DIRECTORY)

        self.assertEqual(len(articles), 7)
        article = articles[0]
        self.assertTrue(article["article_id"].startswith("KB-"))
        self.assertTrue(article["title"])
        self.assertTrue(article["category"])
        self.assertTrue(article["source_file"].endswith(".md"))
        self.assertIn("## Steps", article["content"])


class KnowledgeChunkingTests(unittest.TestCase):
    def test_chunks_respect_size_and_preserve_article_metadata(self):
        article = load_articles(ARTICLES_DIRECTORY)[0]
        max_chars = 280

        chunks = chunk_articles([article], max_chars=max_chars)

        self.assertGreater(len(chunks), 1)
        self.assertEqual(len({chunk["chunk_id"] for chunk in chunks}), len(chunks))
        for chunk in chunks:
            self.assertLessEqual(len(chunk["text"]), max_chars)
            self.assertEqual(chunk["article_id"], article["article_id"])
            self.assertEqual(chunk["title"], article["title"])
            self.assertEqual(chunk["category"], article["category"])
            self.assertEqual(chunk["source_file"], article["source_file"])


class KnowledgeEmbeddingTests(unittest.TestCase):
    def test_attaches_normalized_model_vectors_to_chunks(self):
        class StubEncoder:
            def __init__(self):
                self.normalize_embeddings = None

            def encode(self, texts, normalize_embeddings, show_progress_bar):
                self.normalize_embeddings = normalize_embeddings
                return [[1.0, 0.0] for _ in texts]

        encoder = StubEncoder()
        chunks = chunk_articles(load_articles(ARTICLES_DIRECTORY)[:1], max_chars=500)

        embedded_chunks = generate_embeddings(
            chunks,
            model_name="test/embedding-model",
            encoder=encoder,
        )

        self.assertTrue(encoder.normalize_embeddings)
        self.assertEqual(len(embedded_chunks), len(chunks))
        self.assertEqual(embedded_chunks[0]["embedding"], [1.0, 0.0])
        self.assertEqual(
            embedded_chunks[0]["embedding_model"], "test/embedding-model"
        )
        self.assertEqual(
            embedded_chunks[0]["chunk_id"], chunks[0]["chunk_id"]
        )


if __name__ == "__main__":
    unittest.main()
