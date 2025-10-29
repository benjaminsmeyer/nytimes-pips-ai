import os
import json
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
start_date = datetime(2025, 8, 18)
end_date = datetime.today()
base_url = "https://www.nytimes.com/svc/pips/v1"
output_root = "boards"
# ----------------------

# Create folders
for folder in ["easy", "medium", "hard", "raw"]:
    os.makedirs(f"{output_root}/{folder}", exist_ok=True)

current = start_date
while current <= end_date:
    date_str = current.strftime("%Y-%m-%d")
    url = f"{base_url}/{date_str}.json"
    raw_path = f"{output_root}/raw/{date_str}.json"

    if os.path.exists(raw_path):
        print(f"{date_str}: Already exists, skipping.")
    else:
        print(f"Fetching {url} ...")
        r = requests.get(url)
        if r.status_code == 200 and r.text.strip():
            with open(raw_path, "w") as f:
                f.write(r.text)
            print(f"Saved raw file → {raw_path}")

            try:
                data = r.json()
                for level in ["easy", "medium", "hard"]:
                    if level in data:
                        out_path = f"{output_root}/{level}/{date_str}.json"
                        with open(out_path, "w") as out_file:
                            json.dump(data[level], out_file, indent=4)
                        print(f"  → Saved {level} puzzle at {out_path}")
            except Exception as e:
                print(f"Error parsing {date_str}: {e}")
        else:
            print(f"Failed to fetch {date_str}")
    
    current += timedelta(days=1)

print("Done fetching and splitting all puzzles.")
