import unittest

import chromadb
from chromadb.config import Settings

from backend.app.knowledge_vector_store import KnowledgeVectorStore


class StubQueryEncoder:
    def encode(self, texts, normalize_embeddings, show_progress_bar):
        self.normalize_embeddings = normalize_embeddings
        return [[1.0, 0.0, 0.0] for _ in texts]


class KnowledgeVectorStoreTests(unittest.TestCase):
    def test_indexes_vectors_and_filters_search_by_category_and_topic(self):
        chunks = [
            {
                "chunk_id": "KB-NET-001-chunk-001",
                "article_id": "KB-NET-001",
                "title": "VPN connection help",
                "category": "Network",
                "sub_category": "VPN",
                "source_file": "vpn.md",
                "text": "Check the approved VPN client.",
                "embedding": [1.0, 0.0, 0.0],
                "embedding_model": "test-model",
            },
            {
                "chunk_id": "KB-NET-002-chunk-001",
                "article_id": "KB-NET-002",
                "title": "Wi-Fi connection help",
                "category": "Network",
                "sub_category": "Wi-Fi",
                "source_file": "wifi.md",
                "text": "Check the corporate wireless network.",
                "embedding": [0.8, 0.2, 0.0],
                "embedding_model": "test-model",
            },
            {
                "chunk_id": "KB-MSG-001-chunk-001",
                "article_id": "KB-MSG-001",
                "title": "Outlook synchronization help",
                "category": "Email",
                "sub_category": "Outlook",
                "source_file": "outlook.md",
                "text": "Check email synchronization status.",
                "embedding": [0.0, 1.0, 0.0],
                "embedding_model": "test-model",
            },
        ]
        encoder = StubQueryEncoder()

        client = chromadb.EphemeralClient(
            settings=Settings(anonymized_telemetry=False)
        )
        store = KnowledgeVectorStore(
            collection_name="test_knowledge",
            query_encoder=encoder,
            client=client,
        )
        store.index_chunks(chunks)

        results = store.search(
            "VPN connection", category="Network", topic="VPN", limit=5
        )

        self.assertEqual(encoder.normalize_embeddings, True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["chunk_id"], "KB-NET-001-chunk-001")
        self.assertEqual(results[0]["title"], "VPN connection help")
        self.assertEqual(results[0]["category"], "Network")
        self.assertEqual(results[0]["sub_category"], "VPN")
        self.assertEqual(results[0]["source_file"], "vpn.md")
        self.assertEqual(results[0]["text"], "Check the approved VPN client.")

        network_results = store.search(
            "network issue", category="Network", limit=5
        )
        self.assertEqual(len(network_results), 2)
        self.assertEqual(network_results[0]["chunk_id"], "KB-NET-001-chunk-001")


if __name__ == "__main__":
    unittest.main()
