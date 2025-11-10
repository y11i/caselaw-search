#!/usr/bin/env python3
"""
Database seeding script for Legal AI MVP.
Fetches landmark Supreme Court cases from CourtListener and stores them with embeddings.

Usage:
    python seed_database.py --count 20
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.db import SessionLocal, init_db
from services.courtlistener_service import courtlistener_service


def seed_database(count: int = 20):
    """
    Seed the database with landmark cases.

    Args:
        count: Number of cases to ingest
    """
    print("=" * 60)
    print("LEGAL AI DATABASE SEEDING")
    print("=" * 60)

    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    print("✓ Database initialized")

    # Create database session
    db = SessionLocal()

    try:
        print(f"\n2. Fetching {count} landmark Supreme Court cases from CourtListener...")
        print("   This may take a few minutes...")

        ingested_cases = courtlistener_service.ingest_landmark_cases(db, count=count)

        print(f"\n✓ Successfully ingested {len(ingested_cases)} cases")
        print("\nIngested cases:")
        for i, case in enumerate(ingested_cases, 1):
            print(f"   {i}. {case.citation} - {case.case_name}")

        print("\n" + "=" * 60)
        print("SEEDING COMPLETE")
        print("=" * 60)
        print(f"\nTotal cases in database: {len(ingested_cases)}")
        print("\nYou can now:")
        print("  1. Start the backend: uvicorn app.main:app --reload")
        print("  2. Test queries at: http://localhost:8000/docs")
        print("  3. Example query: 'What are Miranda rights?'")

    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Seed the database with landmark legal cases"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Number of cases to ingest (default: 20)"
    )

    args = parser.parse_args()

    sys.exit(seed_database(args.count))


if __name__ == "__main__":
    main()
