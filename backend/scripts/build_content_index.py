"""
Revised Phase 10 CLI wrapper: rebuilds the extractive-search index from real
PUBLISHED content. The logic lives in app/ai/indexer.py so publishing a
release can run it too. Idempotent.

Usage:  cd backend && python3 -m scripts.build_content_index
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.indexer import rebuild_chunks
from app.database import SessionLocal


def run():
    db = SessionLocal()
    try:
        total = rebuild_chunks(db)
        db.commit()
        print(f"Built {total} content chunks.")
        return total
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
