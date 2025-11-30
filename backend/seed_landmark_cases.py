#!/usr/bin/env python3
"""
Seed database with specific landmark Supreme Court cases.
Uses direct cluster IDs from CourtListener for reliable ingestion.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.db import SessionLocal, init_db
from services.courtlistener_service import courtlistener_service
import requests
from app.core.config import settings

# Landmark Supreme Court cases with their CourtListener cluster IDs
# These are well-known historical cases
LANDMARK_CASES = [
    {"id": 107252, "name": "Miranda v. Arizona (1966)"},
    {"id": 108781, "name": "Roe v. Wade (1973)"},
    {"id": 99441, "name": "Brown v. Board of Education (1954)"},
    {"id": 99039, "name": "Gideon v. Wainwright (1963)"},
    {"id": 99211, "name": "Mapp v. Ohio (1961)"},
    {"id": 107730, "name": "Terry v. Ohio (1968)"},
    {"id": 90575, "name": "Marbury v. Madison (1803)"},
    {"id": 145947, "name": "Citizens United v. FEC (2010)"},
    {"id": 111719, "name": "Chevron U.S.A. v. NRDC (1984)"},
    {"id": 118252, "name": "United States v. Lopez (1995)"},
    {"id": 100342, "name": "Griswold v. Connecticut (1965)"},
    {"id": 108483, "name": "Furman v. Georgia (1972)"},
    {"id": 99112, "name": "Engel v. Vitale (1962)"},
    {"id": 108530, "name": "Roe v. Wade (1973)"},  # Alternative ID
    {"id": 112155, "name": "New York Times Co. v. Sullivan (1964)"},
    {"id": 625847, "name": "Sackett v. Environmental Protection Agency"}
]


def fetch_opinion_from_cluster(cluster_id: int):
    """Fetch the first opinion from a cluster"""
    headers = {"Authorization": f"Token {settings.COURTLISTENER_API_KEY}"}

    # Get cluster
    cluster_url = f"https://www.courtlistener.com/api/rest/v4/clusters/{cluster_id}/"
    print(f"  Fetching cluster {cluster_id}...")

    try:
        response = requests.get(cluster_url, headers=headers, timeout=30)
        response.raise_for_status()
        cluster_data = response.json()

        # Get first opinion from sub_opinions
        sub_opinions = cluster_data.get("sub_opinions", [])
        if not sub_opinions:
            print(f"  ✗ No opinions found in cluster {cluster_id}")
            return None

        # Extract opinion ID from URL
        opinion_url = sub_opinions[0]
        opinion_id = int(opinion_url.rstrip('/').split('/')[-1])

        # Fetch the opinion
        print(f"  Fetching opinion {opinion_id}...")
        opinion_response = requests.get(opinion_url, headers=headers, timeout=30)
        opinion_response.raise_for_status()

        return opinion_response.json()

    except Exception as e:
        print(f"  ✗ Error fetching cluster {cluster_id}: {e}")
        return None


def main():
    print("="*60)
    print("SEEDING LANDMARK SUPREME COURT CASES")
    print("="*60)

    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    print("✓ Database initialized")

    db = SessionLocal()
    ingested_cases = []

    try:
        print(f"\n2. Fetching {len(LANDMARK_CASES)} landmark cases...")

        for case_info in LANDMARK_CASES:
            cluster_id = case_info["id"]
            case_name = case_info["name"]

            print(f"\n{case_name}")

            # Fetch opinion data
            opinion_data = fetch_opinion_from_cluster(cluster_id)

            if opinion_data:
                # Ingest the case
                case = courtlistener_service.ingest_case(opinion_data, db)
                if case:
                    ingested_cases.append(case)
                    print(f"  ✓ Successfully ingested: {case.citation}")

            # Small delay to be nice to API
            import time
            time.sleep(0.3)

        print(f"\n{'='*60}")
        print("SEEDING COMPLETE")
        print("="*60)
        print(f"\nSuccessfully ingested {len(ingested_cases)} cases:")
        for case in ingested_cases:
            print(f"  • {case.citation} - {case.case_name}")

    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
