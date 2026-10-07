import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
REQUIRED_ARTICLE_FIELDS = ("article_id", "title", "category", "source_file")
_DEFAULT_MODEL_RUN_LOG = Path(__file__).resolve().parents[2] / "data" / "embeddings" / "model_run_settings.json"
_LIST_ITEM = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")
_HEADING = re.compile(r"^#{1,6}\s+")
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def get_model_execution_snapshot() -> dict[str, Any]:
    cpu_count = os.cpu_count() or 0
    total_memory_mb = 0
    available_memory_mb = 0
    disk_free_gb = 0.0

    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as meminfo:
            entries = {}
            for line in meminfo:
                key, _, value = line.partition(":")
                if not _:
                    continue
                entries[key.strip()] = int(value.strip().split()[0])
            total_memory_mb = int(entries.get("MemTotal", 0) / 1024)
            available_memory_mb = int(entries.get("MemAvailable", entries.get("MemFree", 0)) / 1024)
    except OSError:
        pass

    disk_free_gb = shutil.disk_usage(str(Path(__file__).resolve().parents[2])).free / (1024 ** 3)

    try:
        process_output = subprocess.check_output(
            ["ps", "-eo", "comm="],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        backend_process_count = sum(1 for name in process_output.splitlines() if name.strip() == "uvicorn")
    except (FileNotFoundError, subprocess.CalledProcessError):
        backend_process_count = 0

    reasons: list[str] = []
    if cpu_count and cpu_count < 2:
        reasons.append("CPU count is below the recommended minimum for embedding work.")
    if total_memory_mb and total_memory_mb < 4096:
        reasons.append("System memory is below 4 GB; model rebuilds may be unstable.")
    if available_memory_mb and available_memory_mb < 1024:
        reasons.append("Available RAM is below 1 GB; prefer reuse of existing embeddings.")
    if disk_free_gb < 5:
        reasons.append("Less than 5 GB of free disk space remains.")
    if backend_process_count > 1:
        reasons.append("Multiple active backend processes were detected; use one active backend before heavy model work.")

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_count": cpu_count,
        "memory_total_mb": total_memory_mb,
        "memory_available_mb": available_memory_mb,
        "disk_free_gb": round(disk_free_gb, 2),
        "backend_process_count": backend_process_count,
        "safe_to_run": not reasons,
        "reasons": reasons,
    }
    return snapshot


def save_model_execution_snapshot(snapshot: dict[str, Any], output_path: str | Path | None = None) -> Path:
    path = Path(output_path) if output_path is not None else _DEFAULT_MODEL_RUN_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def validate_model_execution(output_path: str | Path | None = None) -> tuple[bool, dict[str, Any]]:
    snapshot = get_model_execution_snapshot()
    path = save_model_execution_snapshot(snapshot, output_path)
    if snapshot["safe_to_run"]:
        return True, {**snapshot, "log_path": str(path)}

    return False, {**snapshot, "log_path": str(path)}


def load_articles(directory: Path) -> list[dict[str, Any]]:
    articles = []
    for path in sorted(directory.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            raise ValueError(f"Missing YAML frontmatter in {path.name}.")

        frontmatter, separator, body = text[4:].partition("\n---")
        if not separator:
            raise ValueError(f"Unterminated YAML frontmatter in {path.name}.")

        metadata = yaml.safe_load(frontmatter)
        if not isinstance(metadata, dict):
            raise ValueError(f"Invalid YAML frontmatter in {path.name}.")

        missing_fields = [
            field for field in REQUIRED_ARTICLE_FIELDS if not metadata.get(field)
        ]
        if missing_fields:
            missing = ", ".join(missing_fields)
            raise ValueError(f"Missing article metadata in {path.name}: {missing}.")

        article = dict(metadata)
        article["source_file"] = str(article["source_file"])
        article["content"] = body.removeprefix("\n").strip()
        articles.append(article)

    return articles


def _markdown_blocks(section: str) -> list[str]:
    blocks: list[str] = []
    current_lines: list[str] = []

    def flush_current() -> None:
        if current_lines:
            blocks.append("\n".join(current_lines).strip())
            current_lines.clear()

    for line in section.splitlines():
        if not line.strip():
            flush_current()
        elif _LIST_ITEM.match(line):
            flush_current()
            blocks.append(line.strip())
        else:
            current_lines.append(line.rstrip())

    flush_current()
    return blocks


def _split_long_block(block: str, max_chars: int) -> list[str]:
    if len(block) <= max_chars:
        return [block]

    parts: list[str] = []
    current = ""
    for sentence in _SENTENCE_BOUNDARY.split(block):
        if len(sentence) > max_chars:
            if current:
                parts.append(current)
                current = ""
            for word in sentence.split():
                candidate = f"{current} {word}".strip()
                if len(candidate) > max_chars and current:
                    parts.append(current)
                    current = word
                elif len(candidate) > max_chars:
                    for start in range(0, len(word), max_chars):
                        parts.append(word[start : start + max_chars])
                else:
                    current = candidate
            continue

        candidate = f"{current} {sentence}".strip()
        if len(candidate) > max_chars and current:
            parts.append(current)
            current = sentence
        else:
            current = candidate

    if current:
        parts.append(current)
    return parts


def _chunk_section(section: str, max_chars: int) -> list[str]:
    blocks = _markdown_blocks(section)
    heading = blocks[0] if blocks and _HEADING.match(blocks[0]) else ""
    body_blocks = blocks[1:] if heading else blocks
    body_limit = max_chars - len(heading) - (2 if heading else 0)
    if body_limit < 1:
        raise ValueError("max_chars is too small to retain the section heading.")

    rendered_chunks: list[str] = []
    current_blocks: list[str] = []

    def render(blocks_to_render: list[str]) -> str:
        body = "\n\n".join(blocks_to_render).strip()
        return f"{heading}\n\n{body}".strip() if heading and body else heading or body

    for block in body_blocks:
        for part in _split_long_block(block, body_limit):
            candidate = render([*current_blocks, part])
            if len(candidate) <= max_chars:
                current_blocks.append(part)
            else:
                if current_blocks:
                    rendered_chunks.append(render(current_blocks))
                current_blocks = [part]

    if current_blocks:
        rendered_chunks.append(render(current_blocks))
    elif not rendered_chunks and heading:
        rendered_chunks.append(heading)

    return rendered_chunks


def chunk_articles(
    articles: list[dict[str, Any]], max_chars: int = 1200
) -> list[dict[str, Any]]:
    if max_chars < 1:
        raise ValueError("max_chars must be a positive integer.")

    chunks: list[dict[str, Any]] = []
    for article in articles:
        article_chunk_index = 0
        sections = re.split(r"(?m)(?=^#{1,6}\s+)", article["content"])
        for section in sections:
            section = section.strip()
            if not section:
                continue

            heading = next(
                (line.strip() for line in section.splitlines() if _HEADING.match(line)),
                "",
            )
            for text in _chunk_section(section, max_chars):
                article_chunk_index += 1
                chunk = {
                    "chunk_id": (
                        f"{article['article_id']}-chunk-{article_chunk_index:03d}"
                    ),
                    "article_id": article["article_id"],
                    "title": article["title"],
                    "category": article["category"],
                    "sub_category": article.get("sub_category", ""),
                    "source_file": article["source_file"],
                    "tags": article.get("tags", []),
                    "content_status": article.get("content_status", ""),
                    "section": heading,
                    "text": text,
                }
                chunks.append(chunk)

    return chunks


def generate_embeddings(
    chunks: list[dict[str, Any]],
    model_name: str | None = None,
    encoder: Any | None = None,
) -> list[dict[str, Any]]:
    if not chunks:
        return []

    model_name = model_name or os.getenv(
        "EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL
    )
    if encoder is None:
        from sentence_transformers import SentenceTransformer

        encoder = SentenceTransformer(model_name)

    vectors = encoder.encode(
        [chunk["text"] for chunk in chunks],
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    if len(vectors) != len(chunks):
        raise ValueError("The embedding model returned a different number of vectors.")

    embedded_chunks = []
    for chunk, vector in zip(chunks, vectors):
        record = dict(chunk)
        record["embedding"] = vector.tolist() if hasattr(vector, "tolist") else list(vector)
        record["embedding_model"] = model_name
        embedded_chunks.append(record)

    return embedded_chunks


def save_embeddings(chunks: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        for chunk in chunks:
            output_file.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Chunk and embed IT knowledge articles.")
    parser.add_argument(
        "--articles",
        type=Path,
        default=project_root / "data" / "knowledge_docs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root / "data" / "embeddings" / "knowledge_chunks.jsonl",
    )
    parser.add_argument("--max-chars", type=int, default=1200)
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Ignore resource safety checks and rebuild the embedding artifact anyway.",
    )
    args = parser.parse_args()

    safe_to_run, snapshot = validate_model_execution(
        output_path=project_root / "data" / "embeddings" / "model_run_settings.json"
    )
    if not safe_to_run and args.output.exists() and not args.force_rebuild:
        print(
            "Low-resource execution detected. Reusing the persisted embedding artifact instead of rebuilding it.\n"
            f"Snapshot: {snapshot}"
        )
        return

    if not safe_to_run and not args.output.exists() and not args.force_rebuild:
        raise RuntimeError(
            "The environment is not safe for model work. "
            "Free memory, close extra workloads, or rerun with --force-rebuild if you understand the risk."
        )

    articles = load_articles(args.articles)
    chunks = chunk_articles(articles, max_chars=args.max_chars)
    model_name = os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
    embedded_chunks = generate_embeddings(chunks, model_name=model_name)
    save_embeddings(embedded_chunks, args.output)

    print(
        f"Processed {len(articles)} articles into {len(embedded_chunks)} chunks "
        f"with {model_name}. Output: {args.output}"
    )


if __name__ == "__main__":
    main()
