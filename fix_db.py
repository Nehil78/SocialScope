import sqlite3
from pathlib import Path

print("🔧 Direct.db ko clean kar raha hoon...")

source_db = Path(r"D:\Minor\IMP\SocialScope-Forensic-Toolkit\data\sample_databases\direct.db")
clean_db  = Path(r"D:\Minor\IMP\SocialScope-Forensic-Toolkit\data\sample_databases\clean_direct.db")

if not source_db.exists():
    print("❌ direct.db file nahi mili")
    exit()

# Purani clean file delete kar
if clean_db.exists():
    clean_db.unlink()

# Nayi clean database bana
conn = sqlite3.connect(str(clean_db))
cursor = conn.cursor()

# Messages table create kar (tere latest Instagram ke hisaab se)
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    _id INTEGER PRIMARY KEY,
    user_id TEXT,
    thread_id TEXT,
    timestamp INTEGER,
    message_type TEXT,
    text TEXT
)
""")

# Purani file se data nikaal aur nayi file mein daal
old_conn = sqlite3.connect(str(source_db))
old_cursor = old_conn.cursor()

rows = old_cursor.execute("SELECT _id, user_id, thread_id, timestamp, message_type, text FROM messages").fetchall()

cursor.executemany("""
INSERT INTO messages (_id, user_id, thread_id, timestamp, message_type, text)
VALUES (?, ?, ?, ?, ?, ?)
""", rows)

conn.commit()
old_conn.close()
conn.close()

print(f"✅ Clean database ban gaya!")
print(f"   File: {clean_db}")
print(f"   Total rows copied: {len(rows)}")