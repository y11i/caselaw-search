#!/usr/bin/env python3
"""
Reset the database - drops all tables and recreates them.
WARNING: This will delete all data!
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.db import reset_db
from services.vector_search_service import vector_search_service

if __name__ == "__main__":
    print("⚠️  WARNING: This will delete ALL data from:")
    print("  - PostgreSQL database (all cases)")
    print("  - Qdrant vector database (all embeddings)")
    print("  - Redis cache (all cached queries)")
    response = input("\nAre you sure you want to continue? (yes/no): ")

    if response.lower() == "yes":
        print("\n1. Resetting PostgreSQL database...")
        reset_db()
        print("✓ PostgreSQL reset complete")

        print("\n2. Recreating Qdrant collection...")
        try:
            # Delete and recreate the collection
            vector_search_service.client.delete_collection(
                collection_name=vector_search_service.collection_name
            )
            vector_search_service._ensure_collection_exists()
            print("✓ Qdrant collection reset complete")
        except Exception as e:
            print(f"Note: {e}")

        print("\n✓ All databases reset successfully")
        print("\nYou can now run: python seed_database.py --count 20")
    else:
        print("Cancelled.")
