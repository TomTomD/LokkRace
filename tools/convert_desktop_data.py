#!/usr/bin/env python3
"""Convert the desktop app's data/kanotister/*.json files into a single
web-app bundle (lokkrace-data.json).

Usage:
    python tools/convert_desktop_data.py <data_dir> [output.json]

<data_dir> is the folder that contains a "kanotister" subfolder (i.e. the
"data" folder the desktop app writes). Race .txt files are ignored — all the
history the web app needs lives in each participant's race_history.
"""
import glob
import json
import os
import sys

BUNDLE_VERSION = 1


def convert(data_dir):
    participants = []
    pattern = os.path.join(data_dir, "kanotister", "*.json")
    for path in sorted(glob.glob(pattern)):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        # Keep only the fields the bundle model owns; drop transient race state.
        participants.append({
            "name": data["name"],
            "best_time_seconds": data.get("best_time_seconds"),
            "number": data.get("number", 0),
            "race_history": data.get("race_history", []),
        })
    participants.sort(key=lambda p: p["name"].lower())
    return {"version": BUNDLE_VERSION, "participants": participants}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    data_dir = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "lokkrace-data.json"

    bundle = convert(data_dir)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)

    n = len(bundle["participants"])
    with_history = sum(1 for p in bundle["participants"] if p["race_history"])
    print(f"Wrote {out_path}")
    print(f"  {n} kanotister ({with_history} with race history)")


if __name__ == "__main__":
    main()
