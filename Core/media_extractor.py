import hashlib
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

class MediaExtractor:
    def __init__(self, data_folder):
        self.data_folder = Path(data_folder)
        self.media_folder = Path("./output/media")
        self.media_folder.mkdir(parents=True, exist_ok=True)

    def calculate_sha256(self, file_path):
        """File ka SHA-256 hash nikaalta hai"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        return sha256.hexdigest()

    def extract_exif(self, image_path):
        """Image ka EXIF metadata (GPS, Camera, Date)"""
        try:
            img = Image.open(image_path)
            exif_data = {}
            exif = img._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == "GPSInfo":
                        gps = {}
                        for t in value:
                            gps_tag = GPSTAGS.get(t, t)
                            gps[gps_tag] = value[t]
                        exif_data["GPS"] = gps
                    else:
                        exif_data[tag] = value
            return exif_data
        except:
            return {}

    def extract_media_from_db(self, messages):
        """Messages se media files detect karta hai"""
        media_count = 0
        extracted = []

        for msg in messages:
            text = msg.get('text', '')
            if any(ext in text.lower() for ext in ['.jpg', '.jpeg', '.png', '.mp4', '.gif', '.webp']):
                media_count += 1
                extracted.append({
                    'message_time': msg.get('readable_time'),
                    'sender': msg.get('sender'),
                    'text': text[:150],
                    'hash': 'N/A (media not extracted yet)',
                    'exif': {}
                })

        print(f"[+] {media_count} media files detected in messages")
        return extracted