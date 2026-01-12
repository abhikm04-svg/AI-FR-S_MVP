import os
import pymongo
from supabase import create_client, Client
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = "financial_advisor_db"

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") # Service role key

def migrate():
    if not MONGO_URI or not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: Missing credentials. Ensure MONGO_URI, SUPABASE_URL, and SUPABASE_KEY are set.")
        return

    # Initialize Clients
    mongo_client = pymongo.MongoClient(MONGO_URI)
    mongo_db = mongo_client[MONGO_DB_NAME]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 1. Migrate mf_schemes
    print("📥 Migrating mf_schemes...")
    schemes = list(mongo_db["mf_schemes"].find({}))
    if schemes:
        formatted_schemes = []
        for s in schemes:
            formatted_schemes.append({
                "scheme_code": s["scheme_code"],
                "scheme_name": s["scheme_name"],
                "last_updated": s.get("last_updated").isoformat() if s.get("last_updated") else None
            })
        
        # Batch upsert to Supabase
        for i in range(0, len(formatted_schemes), 100):
            batch = formatted_schemes[i:i+100]
            supabase.table("mf_schemes").upsert(batch).execute()
        print(f"✅ Migrated {len(formatted_schemes)} schemes.")

    # 2. Migrate mf_nav_history
    print("📥 Migrating mf_nav_history...")
    nav_history = list(mongo_db["mf_nav_history"].find({}))
    if nav_history:
        formatted_nav = []
        for n in nav_history:
            formatted_nav.append({
                "scheme_code": n["scheme_code"],
                "scheme_name": n.get("scheme_name"),
                "history": n["history"],
                "last_updated": n.get("fetched_at").isoformat() if n.get("fetched_at") else (n.get("last_updated").isoformat() if n.get("last_updated") else None)
            })
        
        for i in tqdm(range(0, len(formatted_nav), 50)):
            batch = formatted_nav[i:i+50]
            supabase.table("mf_nav_history").upsert(batch).execute()
        print(f"✅ Migrated {len(formatted_nav)} NAV history records.")

if __name__ == "__main__":
    migrate()
