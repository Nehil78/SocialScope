import sqlite3
import re
from pathlib import Path
from datetime import datetime


# ──────────────────────────────────────────────────────────────────────────────
#  SQLite internal strings jo KABHI real messages nahi hote — inhe filter karo
# ──────────────────────────────────────────────────────────────────────────────
SQLITE_NOISE_PREFIXES = (
    'CREATE ', 'INSERT ', 'SELECT ', 'UPDATE ', 'DELETE ', 'DROP ',
    'ALTER ', 'INDEX ', 'TABLE ', 'TRIGGER ', 'VIEW ', 'PRAGMA ',
    'SQLite ', 'sqlite_', 'autoindex', 'tabledb_', 'indexsqlite',
    'tablemutation', 'tablesession', 'tablethreads', 'tableandroid',
    'android_metadata', 'sqlite_sequence', 'db_created_', 'inbox_has_',
    'cursor_thread', 'cursor_timestamp', 'filter_sort_cursor',
    'SET_OR_UNRECOGNIZED', 'interop_user_type', 'is_eligible_for_rp',
    'outgoing_request', 'friendship_status', 'full_name',
    'inbox_prev_key', 'memris_seq', 'seq_id',
)

SQLITE_NOISE_SUBSTRINGS = (
    'INTEGER', 'NOT NULL', 'PRIMARY KEY', 'UNIQUE', 'DEFAULT',
    'REFERENCES', 'ON DELETE', 'ON UPDATE', 'AUTOINCREMENT',
    'table_info', 'column_info', 'db_created_config',
    'is_pinned INTEGER', 'is_unread_badging',
    '"version":', '"universe":', '"inbox_has_older"',
    'db_created_time', 'igd_stacks', 'rp_safety_noti',
    'ed_inbox_for_direct', 'is_verified', 'profile_',
    'friendship_status', 'blocking":false', 'following":',
    'fbid":"', 'interop_user',
)

# Minimum required: string mein kam se kam ek space ya common word hona chahiye
# Aur minimum length 15 — database schema tokens usually 10-14 char ke hote hain
MIN_MSG_LENGTH = 15

# Agar string mein sirf yeh characters hain toh yeh hex/binary garbage hai
HEX_ONLY = re.compile(r'^[0-9a-fA-F\-_\.:/]+$')

# JSON-heavy strings (schema metadata) — curly braces ratio check
def _is_json_schema(text: str) -> bool:
    """Agar string mostly JSON keys/schema hai toh True."""
    if text.count('"') > 6 and ':' in text and ('{' in text or '}' in text):
        return True
    return False

def _is_real_message(text: str) -> bool:
    """
    Yeh function decide karta hai ki binary scan se mila string
    actually ek real (deleted) message jaisa lagta hai ya nahi.

    Real messages mein:
      - Spaces hote hain (words hote hain)
      - Normal punctuation hoti hai
      - SQLite schema keywords NAHI hote
      - JSON structure NAHI hota (ya bahut kam)
    """
    t = text.strip()

    # Too short
    if len(t) < MIN_MSG_LENGTH:
        return False

    # Pure hex / technical identifiers
    if HEX_ONLY.match(t):
        return False

    # SQLite noise prefix check
    t_upper = t.upper()
    t_lower = t.lower()
    for prefix in SQLITE_NOISE_PREFIXES:
        if t.startswith(prefix) or t_lower.startswith(prefix.lower()):
            return False

    # SQLite noise substring check
    for substr in SQLITE_NOISE_SUBSTRINGS:
        if substr in t or substr.lower() in t_lower:
            return False

    # JSON schema-like string
    if _is_json_schema(t):
        return False

    # Must have at least one space (real messages have words)
    if ' ' not in t:
        return False

    # Must have some alphabetic content (not just numbers/symbols)
    alpha_count = sum(1 for c in t if c.isalpha())
    if alpha_count < 5:
        return False

    # Ratio check: too many special chars = schema/binary
    special = sum(1 for c in t if not c.isalnum() and c not in ' .,!?-\'\"')
    if len(t) > 0 and special / len(t) > 0.35:
        return False

    return True


class WALRecovery:
    def __init__(self, db_path):
        p = Path(db_path)
        if p.suffix == '.wal' or str(p).endswith('-wal'):
            self.db_path  = Path(str(db_path).replace('-wal', ''))
            self.wal_path = p
        else:
            self.db_path  = p
            self.wal_path = Path(str(p) + '-wal')

    # ─────────────────────────────────────────────────────────────────────────
    #  Method 1: ROWID Gap Analysis  (most reliable — actual deleted row proof)
    # ─────────────────────────────────────────────────────────────────────────
    def _recover_from_freelist(self):
        recovered = []
        if not self.db_path.exists():
            return recovered

        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row

            # Kaunsi tables hain check karo
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t['name'] for t in tables]

            msg_table = None
            for t in table_names:
                if 'message' in t.lower():
                    msg_table = t
                    break

            if not msg_table:
                conn.close()
                return recovered

            rows = conn.execute(
                f"SELECT rowid, * FROM {msg_table} ORDER BY rowid ASC"
            ).fetchall()
            conn.close()

            if not rows:
                return recovered

            # ROWID gaps = deleted rows ka proof
            rowids = [r['rowid'] for r in rows]
            for i in range(len(rowids) - 1):
                gap = rowids[i + 1] - rowids[i]
                if gap > 1:
                    for missing in range(rowids[i] + 1, rowids[i + 1]):
                        recovered.append({
                            'status':        'DELETED (ROWID Gap)',
                            'possible_text': (
                                f'[Deleted message — ROWID {missing} '
                                f'(gap between row {rowids[i]} and {rowids[i+1]})]'
                            ),
                            'readable_time': 'N/A',
                            'source':        'rowid_gap_analysis',
                            'rowid':         missing
                        })

        except Exception as e:
            print(f"[-] Freelist recovery error: {str(e)}")

        return recovered

    # ─────────────────────────────────────────────────────────────────────────
    #  Method 2: Binary scan — IMPROVED with smart filtering
    # ─────────────────────────────────────────────────────────────────────────
    def _recover_from_binary_scan(self):
        """
        Database file ko binary mein scan karta hai aur SIRF
        real message jaisi strings nikalata hai.

        Pehle wala version SQLite schema strings bhi nikaal raha tha
        jaise table names, column definitions, JSON metadata — yeh sab
        ab filter ho jaayenge.
        """
        recovered = []
        if not self.db_path.exists():
            return recovered

        try:
            with open(self.db_path, 'rb') as f:
                raw = f.read()

            # Readable strings dhundho — min 15 chars
            pattern = rb'[\x20-\x7E]{15,300}'
            matches = re.findall(pattern, raw)

            seen = set()
            for match in matches:
                try:
                    text = match.decode('utf-8', errors='ignore').strip()

                    # Dedup
                    if text in seen:
                        continue
                    seen.add(text)

                    # Smart filter — sirf real messages
                    if _is_real_message(text):
                        recovered.append({
                            'status':        'POSSIBLE DELETED (Binary Scan)',
                            'possible_text': text,
                            'readable_time': 'N/A',
                            'source':        'binary_scan',
                            'sender':        'Unknown'
                        })

                except Exception:
                    continue

        except Exception as e:
            print(f"[-] Binary scan error: {str(e)}")

        return recovered

    # ─────────────────────────────────────────────────────────────────────────
    #  Method 3: WAL File Scan
    # ─────────────────────────────────────────────────────────────────────────
    def _recover_from_wal(self):
        recovered = []

        if not self.wal_path.exists():
            return recovered

        if self.wal_path.stat().st_size < 1024:
            print(f"[!] WAL file bahut chhoti ({self.wal_path.stat().st_size} bytes) — skip")
            return recovered

        try:
            with open(self.wal_path, 'rb') as f:
                raw = f.read()

            pattern = rb'[\x20-\x7E]{15,300}'
            matches = re.findall(pattern, raw)

            seen = set()
            for match in matches:
                try:
                    text = match.decode('utf-8', errors='ignore').strip()
                    if text in seen:
                        continue
                    seen.add(text)

                    # Same smart filter apply karo
                    if _is_real_message(text):
                        recovered.append({
                            'status':        'POSSIBLE DELETED (WAL)',
                            'possible_text': text,
                            'readable_time': 'N/A',
                            'source':        'wal_scan',
                            'sender':        'Unknown'
                        })
                except Exception:
                    continue

            print(f"[+] WAL se {len(recovered)} filtered strings mili")

        except Exception as e:
            print(f"[-] WAL scan error: {str(e)}")

        return recovered

    # ─────────────────────────────────────────────────────────────────────────
    #  Main recover function
    # ─────────────────────────────────────────────────────────────────────────
    def recover_deleted(self):
        print("\n[*] Deleted message recovery shuru...")

        all_recovered = []

        # ── Method 1: ROWID Gap ──────────────────────────────────────────────
        print("[*] Method 1: ROWID gap analysis...")
        freelist = self._recover_from_freelist()
        if freelist:
            print(f"    ✓ {len(freelist)} deleted row gaps mile (real deletions!)")
            all_recovered.extend(freelist)
        else:
            print("    → Koi ROWID gap nahi mila")

        # ── Method 2: Binary Scan (filtered) ────────────────────────────────
        print("[*] Method 2: Binary scan (schema noise filtered)...")
        binary = self._recover_from_binary_scan()
        if binary:
            print(f"    ✓ {len(binary)} message-like strings mile (filtered)")
            all_recovered.extend(binary[:30])   # max 30 — quality > quantity
        else:
            print("    → Koi message-like strings nahi mile (database likely encrypted)")

        # ── Method 3: WAL Scan ───────────────────────────────────────────────
        print("[*] Method 3: WAL file scan...")
        wal = self._recover_from_wal()
        if wal:
            print(f"    ✓ {len(wal)} strings WAL se mili")
            all_recovered.extend(wal[:30])
        else:
            print("    → WAL file nahi mili (normal for Instagram)")

        print(f"\n[+] Total recovered: {len(all_recovered)} items")

        # ── Summary ─────────────────────────────────────────────────────────
        if all_recovered:
            rowid_gaps = sum(1 for x in all_recovered if x['source'] == 'rowid_gap_analysis')
            binary_str = sum(1 for x in all_recovered if x['source'] == 'binary_scan')
            wal_str    = sum(1 for x in all_recovered if x['source'] == 'wal_scan')
            print(f"    ROWID gaps   : {rowid_gaps}  (confirmed deletions)")
            print(f"    Binary scan  : {binary_str}  (possible deleted text)")
            print(f"    WAL scan     : {wal_str}  (possible deleted text)")
        else:
            print("    → Koi bhi deleted data nahi mila.")
            print("    ℹ  Possible reason: Instagram database encrypted hai")
            print("       (Modern Instagram apps use SQLCipher encryption)")

        return all_recovered
