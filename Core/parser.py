import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime


class InstagramParser:
    def __init__(self, config, base_folder):
        self.config          = config
        self.base_folder     = Path(base_folder)
        self.device_owner_id = None

    # ─────────────────────────────────────────────────────────────────────────
    #  Timestamp convert
    # ─────────────────────────────────────────────────────────────────────────
    def _parse_timestamp(self, ts):
        if not ts:
            return 'N/A', 0
        try:
            ts = float(ts)
            if ts > 999_999_999_999_999:    # microseconds
                ts = ts / 1_000_000.0
            elif ts > 9_999_999_999:         # milliseconds
                ts = ts / 1000.0
            dt = datetime.fromtimestamp(ts)
            return dt.strftime('%Y-%m-%d %H:%M:%S'), int(ts)
        except Exception:
            return str(ts), 0

    # ─────────────────────────────────────────────────────────────────────────
    #  Fix mojibake encoding (Instagram JSON mein UTF-8 encoding issue)
    #  e.g.  \u00f0\u009f\u0091\u008d  →  👍
    # ─────────────────────────────────────────────────────────────────────────
    def _fix_encoding(self, text):
        if not text:
            return text
        try:
            return text.encode('latin-1').decode('utf-8')
        except Exception:
            return text

    # ─────────────────────────────────────────────────────────────────────────
    #  JSON export parse karo (Instagram official data)
    #  Folder structure:
    #    messages/inbox/username_threadid/message_1.json
    # ─────────────────────────────────────────────────────────────────────────
    def _parse_json_export(self):
        all_messages = []

        # message_1.json, message_2.json etc. dhundho recursively
        json_files = list(self.base_folder.rglob("message_*.json"))

        if not json_files:
            return []

        print(f"[+] {len(json_files)} JSON conversation file(s) found")

        for jf in json_files:
            try:
                with open(jf, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Participants
                participants = data.get('participants', [])
                participant_names = [p.get('name', '') for p in participants]
                title = data.get('title', jf.parent.name)

                print(f"[+] Parsing: {title}  ({len(data.get('messages', []))} messages)")

                messages = data.get('messages', [])

                for msg in messages:
                    sender   = self._fix_encoding(msg.get('sender_name', 'Unknown'))
                    ts_ms    = msg.get('timestamp_ms', 0)
                    content  = self._fix_encoding(msg.get('content', ''))
                    readable_time, ts_unix = self._parse_timestamp(ts_ms)

                    # Share/attachment check
                    share = msg.get('share', {})
                    if share:
                        share_link = share.get('link', '')
                        share_text = self._fix_encoding(share.get('share_text', ''))
                        if not content or 'sent an attachment' in content:
                            content = f"[SHARED LINK] {share_link}"
                        if share_text:
                            content += f" | {share_text[:100]}"

                    # Photos
                    photos = msg.get('photos', [])
                    if photos:
                        content = f"[PHOTO] {len(photos)} photo(s) shared"

                    # Videos
                    videos = msg.get('videos', [])
                    if videos:
                        content = f"[VIDEO] {len(videos)} video(s) shared"

                    # Audio
                    audio = msg.get('audio_files', [])
                    if audio:
                        content = f"[AUDIO] voice message"

                    # Reactions
                    reactions = msg.get('reactions', [])
                    reaction_str = ''
                    if reactions:
                        for r in reactions:
                            actor  = self._fix_encoding(r.get('actor', ''))
                            react  = self._fix_encoding(r.get('reaction', ''))
                            reaction_str += f"{actor} reacted {react} | "

                    final_text = content.strip() if content else ''
                    if reaction_str:
                        final_text += f" [REACTIONS: {reaction_str.rstrip('| ')}]"

                    # Unsent message check
                    is_unsent = msg.get('is_unsent', False)
                    status = 'UNSENT/DELETED' if is_unsent else ('ACTIVE' if final_text else 'DELETED')

                    all_messages.append({
                        'source':         'instagram_json',
                        'sender':         sender,
                        'sender_id':      sender,
                        'recipient_ids':  ', '.join([p for p in participant_names if p != sender]),
                        'text':           final_text,
                        'thread_id':      title,
                        'item_type':      'text',
                        'readable_time':  readable_time,
                        'timestamp_unix': ts_unix,
                        'status':         status,
                        'is_reaction':    False,
                        'conversation':   title,
                    })

            except Exception as e:
                print(f"[-] Error parsing {jf.name}: {e}")
                continue

        # Chronological order (oldest first)
        all_messages.sort(key=lambda x: x['timestamp_unix'])

        print(f"\n[+] JSON export parse complete:")
        print(f"    Total messages : {len(all_messages)}")

        # Per sender count
        from collections import Counter
        sender_counts = Counter(m['sender'] for m in all_messages)
        for sender, count in sender_counts.most_common():
            print(f"    {sender:<30} : {count} messages")

        return all_messages

    # ─────────────────────────────────────────────────────────────────────────
    #  direct.db parse (original method)
    # ─────────────────────────────────────────────────────────────────────────
    def _get_device_owner(self, conn):
        try:
            row = conn.execute(
                "SELECT user_id FROM db_created_config LIMIT 1"
            ).fetchone()
            if row:
                oid = str(row[0])
                print(f"[+] Device owner ID: {oid}")
                return oid
        except Exception:
            pass
        return None

    def _parse_message_blob(self, raw_blob):
        result = {
            'sender_id': None, 'is_sent_by_viewer': None,
            'text': None, 'item_type': None,
            'timestamp_micro': None, 'reaction': None,
            'item_id': None, 'is_reaction': False,
        }
        if not raw_blob:
            return result
        try:
            if isinstance(raw_blob, bytes):
                raw_str = raw_blob.decode('utf-8', errors='ignore')
            else:
                raw_str = str(raw_blob)
            if not raw_str.strip().startswith('{'):
                raw_str = '{' + raw_str
            data = json.loads(raw_str)
            result['sender_id']         = str(data.get('user_id', '')) or None
            result['is_sent_by_viewer'] = data.get('is_sent_by_viewer', None)
            result['text']              = data.get('text', None)
            result['item_type']         = data.get('item_type', None)
            result['item_id']           = data.get('item_id', None)
            ts_micro = data.get('timestamp_in_micro', data.get('timestamp', None))
            if ts_micro:
                result['timestamp_micro'] = ts_micro
            action_log = data.get('action_log', {})
            if action_log:
                result['is_reaction'] = action_log.get('is_reaction_log', False)
                desc = action_log.get('description', '')
                if desc:
                    result['reaction'] = desc
        except Exception:
            try:
                import re
                text_match = re.search(r'"text"\s*:\s*"([^"]+)"', str(raw_blob))
                if text_match:
                    result['text'] = text_match.group(1)
                uid_match = re.search(r'"user_id"\s*:\s*"(\d+)"', str(raw_blob))
                if uid_match:
                    result['sender_id'] = uid_match.group(1)
                viewer_match = re.search(r'"is_sent_by_viewer"\s*:\s*(true|false)', str(raw_blob))
                if viewer_match:
                    result['is_sent_by_viewer'] = viewer_match.group(1) == 'true'
            except Exception:
                pass
        return result

    def _resolve_sender(self, blob_data, row_user_id, owner_id):
        if blob_data['is_sent_by_viewer'] is not None:
            if blob_data['is_sent_by_viewer']:
                return "YOU (Device Owner)"
            else:
                sid = blob_data['sender_id'] or ''
                return f"THEM ({sid})" if sid else "THEM (Other Person)"
        if blob_data['sender_id'] and owner_id:
            if blob_data['sender_id'] == owner_id:
                return "YOU (Device Owner)"
            else:
                return f"THEM ({blob_data['sender_id']})"
        row_uid = str(row_user_id) if row_user_id else ''
        if owner_id and row_uid == owner_id:
            return "YOU (Device Owner)"
        elif row_uid:
            return f"THEM ({row_uid})"
        return "Unknown"

    def _parse_direct_db(self):
        all_messages = []
        db_path = self.base_folder / "direct.db"
        if not db_path.exists():
            found = list(self.base_folder.rglob("direct.db"))
            if found:
                db_path = found[0]
            else:
                return []

        print(f"[+] direct.db: {db_path} ({db_path.stat().st_size:,} bytes)")
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
        except Exception:
            try:
                conn = sqlite3.connect(str(db_path))
                conn.row_factory = sqlite3.Row
            except Exception as e:
                print(f"[-] Connect error: {e}")
                return []

        self.device_owner_id = self._get_device_owner(conn)
        try:
            rows = conn.execute("SELECT * FROM messages ORDER BY timestamp ASC").fetchall()
        except Exception as e:
            print(f"[-] Fetch error: {e}")
            conn.close()
            return []
        conn.close()

        for row in rows:
            r = dict(row)
            blob = self._parse_message_blob(r.get('message'))
            ts_source = blob['timestamp_micro'] or r.get('timestamp')
            readable_time, ts_unix = self._parse_timestamp(ts_source)
            text = ''
            if blob['text']:
                text = str(blob['text']).strip()
            elif r.get('text'):
                text = str(r.get('text')).strip()
            if blob['is_reaction'] and blob['reaction']:
                text = f"[REACTION] {blob['reaction']}"
            elif not text and blob['reaction']:
                text = f"[ACTION] {blob['reaction']}"
            msg_type = blob['item_type'] or str(r.get('message_type', 'text') or 'text')
            if not text and msg_type and msg_type != 'text':
                text = f"[{msg_type.upper()}]"
            sender = self._resolve_sender(blob, r.get('user_id'), self.device_owner_id)
            all_messages.append({
                'source':         'instagram_db',
                'sender':         sender,
                'sender_id':      str(r.get('user_id', '')),
                'recipient_ids':  str(r.get('recipient_ids', '')),
                'text':           text,
                'thread_id':      str(r.get('thread_id', 'N/A')),
                'item_type':      msg_type,
                'readable_time':  readable_time,
                'timestamp_unix': ts_unix,
                'status':         'DELETED' if not text.strip() else 'ACTIVE',
                'is_reaction':    blob['is_reaction'],
            })
        return all_messages

    # ─────────────────────────────────────────────────────────────────────────
    #  MAIN — automatically detect karo JSON hai ya DB
    # ─────────────────────────────────────────────────────────────────────────
    def parse_direct_messages(self):

        # ── Check 1: JSON export files hain? ────────────────────────────────
        json_files = list(self.base_folder.rglob("message_*.json"))
        if json_files:
            print(f"[+] Instagram JSON export detected — using JSON parser")
            messages = self._parse_json_export()
            if messages:
                return messages

        # ── Check 2: direct.db hai? ──────────────────────────────────────────
        db_files = list(self.base_folder.rglob("direct.db"))
        if db_files:
            print(f"[+] direct.db detected — using DB parser")
            messages = self._parse_direct_db()
            if messages:
                return messages

        print("[-] Koi bhi data source nahi mila!")
        print(f"    Folder check karo: {self.base_folder}")
        print("    JSON files (message_1.json) ya direct.db hona chahiye")
        return []