import json
import model_data as md
from app import build_assets

if __name__ == "__main__":
    assets = build_assets()
    payload = {
        "budget": md.B,
        "count": len(assets),
        "assets": assets,
    }
    with open("assets.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print("assets.json üretildi.")
