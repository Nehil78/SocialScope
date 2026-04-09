import pandas as pd
from pathlib import Path
from datetime import datetime

class MasterTimeline:
    def __init__(self, messages):
        self.messages = messages
        self.df = None

    def build_timeline(self):
        if not self.messages:
            print("No messages for timeline")
            return pd.DataFrame()

        data = []
        for msg in self.messages:
            ts_unix = msg.get('timestamp_unix', 0)
            readable_time = msg.get('readable_time', 'N/A')
            if ts_unix > 0 and readable_time == 'N/A':
                try:
                    readable_time = datetime.fromtimestamp(ts_unix).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    readable_time = 'Invalid Time'

            data.append({
                'Time': readable_time,
                'Sender': msg.get('sender', 'Unknown'),
                'Message': msg.get('text', '[No text]'),
                'Source': msg.get('source', 'Instagram'),
                'Thread ID': msg.get('thread_id', 'N/A')
            })

        self.df = pd.DataFrame(data)
        self.df['sort_time'] = pd.to_datetime(self.df['Time'], errors='coerce')
        self.df = self.df.sort_values(by='sort_time', ascending=False)
        self.df = self.df.drop(columns=['sort_time'])
        self.df = self.df.reset_index(drop=True)
        return self.df

    def preview_table(self, rows=10):
        if self.df is None or self.df.empty:
            print("Timeline empty")
            return

        print("\nMaster Timeline (Latest messages first):")
        print("=" * 120)
        print(self.df.head(rows).to_string(index=True))
        print("=" * 120)

    def save_to_csv(self, output_dir="./output/timelines"):
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        file_path = Path(output_dir) / f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.df.to_csv(file_path, index=False, encoding='utf-8')
        print(f"Timeline CSV saved: {file_path}")