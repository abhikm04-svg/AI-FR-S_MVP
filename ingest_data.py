import os
import time
from supabase import create_client, Client
import pandas as pd
from mftool import Mftool
from datetime import datetime, timedelta
from tqdm import tqdm
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Load environment variables (Local testing uses .env, GitHub uses Secrets)
load_dotenv()

# --- CONFIGURATION ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") # Service role key
# Number of threads (Keep between 5-10 to avoid API rate limiting)
MAX_WORKERS = 10 

def get_db_connection():
    """Establishes connection to Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: SUPABASE_URL or SUPABASE_KEY environment variable not set.")
        return None
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Connected to Supabase")
        return supabase
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return None

def ingest_schemes(supabase, mf):
    """Fetches list of schemes and filters for Direct-Growth."""
    print("📥 Fetching Scheme Codes...")
    try:
        all_codes = mf.get_scheme_codes()
    except Exception as e:
        print(f"❌ Error fetching scheme codes: {e}")
        return
    
    filtered_schemes = []
    # Logic: Only Direct & Growth plans to optimize storage and relevance
    for code, name in all_codes.items():
        if "Direct" in name and "Growth" in name:
            filtered_schemes.append({
                "scheme_code": code,
                "scheme_name": name
            })
    
    print(f"🔍 Found {len(filtered_schemes)} 'Direct & Growth' schemes.")
    
    # Upsert in batches of 100
    for i in range(0, len(filtered_schemes), 100):
        batch = filtered_schemes[i:i+100]
        try:
            supabase.table("mf_schemes").upsert(batch).execute()
        except Exception as e:
            print(f"❌ Error during scheme upsert: {e}")
    
    print(f"💾 Scheme List Synced.")

def fetch_and_save_nav(scheme, supabase, mf):
    """Worker function: Fetches history for one scheme and saves to DB."""
    code = scheme['scheme_code']
    last_upd_str = scheme.get('last_updated')
    
    # Incremental Logic: Skip if updated in last 24 hours
    if last_upd_str:
        try:
            # Handle possible ISO formats or TIMESTAMPTZ from Supabase
            last_upd = datetime.fromisoformat(last_upd_str.replace('Z', '+00:00'))
            if datetime.now(last_upd.tzinfo) - last_upd < timedelta(hours=24):
                return
        except:
            pass

    try:
        # Fetch historical data via mftool
        data = mf.get_scheme_historical_nav(code)
        
        if data and 'data' in data:
            nav_data = data['data']
            
            # Upsert into NAV history table
            supabase.table("mf_nav_history").upsert({
                "scheme_code": code,
                "history": nav_data, 
                "scheme_name": scheme['scheme_name'],
                "last_updated": datetime.now().isoformat()
            }).execute()
            
            # Update the main scheme list with the new timestamp
            supabase.table("mf_schemes").update({
                "last_updated": datetime.now().isoformat()
            }).eq("scheme_code", code).execute()
    except Exception as e:
        # Silently pass or log minimal info to keep the thread pool running
        pass

def ingest_history_parallel(supabase, mf):
    """Processes all schemes using multithreading for speed."""
    try:
        response = supabase.table("mf_schemes").select("*").execute()
        schemes = response.data
    except Exception as e:
        print(f"❌ Error fetching schemes from Supabase: {e}")
        return
    
    print(f"🚀 Starting Parallel Ingestion with {MAX_WORKERS} threads for {len(schemes)} schemes...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # tqdm displays the progress bar
        list(tqdm(executor.map(lambda s: fetch_and_save_nav(s, supabase, mf), schemes), total=len(schemes)))

if __name__ == "__main__":
    # Initialize components
    mf = Mftool()
    supabase = get_db_connection()
    
    if supabase is not None:
        start_time = time.time()
        
        # 1. Sync the list of available Mutual Funds
        ingest_schemes(supabase, mf)
        
        # 2. Update NAV history using parallel processing
        ingest_history_parallel(supabase, mf)
        
        total_time = (time.time() - start_time) / 60
        print(f"\n🎉 Ingestion Complete! Total time: {total_time:.2f} minutes")
