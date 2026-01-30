import psycopg2
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# Credentials (from user history)
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "Xazrat_ali571",
    "host": "db.fqefyhkucykkmafxched.supabase.co",
    "port": "5432"
}

def check_calls():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. Check Total Count
        cur.execute("SELECT COUNT(*) FROM calls;")
        total_calls = cur.fetchone()[0]
        
        # 2. Get Last 5 Calls
        cur.execute("""
            SELECT id, phone_number, status, direction, created_at, binotel_uuid 
            FROM calls 
            ORDER BY created_at DESC 
            LIMIT 5;
        """)
        rows = cur.fetchall()
        
        print("\n=== SUPABASE CALLS REPORT ===")
        print(f"Total Calls in DB: {total_calls}")
        print("------------------------------------------------")
        if rows:
            for row in rows:
                print(f"ID: {row[0]}")
                print(f"Phone: {row[1]}")
                print(f"Status: {row[2]}")
                print(f"Direction: {row[3]}")
                print(f"Time: {row[4]}")
                print(f"Binotel UUID: {row[5]}")
                print("------------------------------------------------")
        else:
            print("No calls found yet.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    check_calls()
