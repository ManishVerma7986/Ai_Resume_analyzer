import os
import csv
import re
from collections import defaultdict
from typing import Tuple, Dict, List


def load_skill_dictionary(path: str) -> List[dict]:
    skills = []
    if not os.path.exists(path):
        raise FileNotFoundError(f"Skill dictionary not found: {path}")

    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            # Expect columns: skill, category, aliases
            aliases = []
            if row.get('aliases'):
                aliases = [a.strip() for a in re.split(r"[;,]", row['aliases']) if a.strip()]
            skills.append({
                'skill': row.get('skill', '').strip(),
                'category': row.get('category', 'Other').strip(),
                'aliases': aliases,
            })
    return skills


def _make_pattern(token: str):
    # Escape token and allow word boundaries; account for tokens with dots/spaces
    tok = re.escape(token)
    # allow matches that are standalone or with separators
    return re.compile(rf"(?<!\w)({tok})(?!\w)", flags=re.IGNORECASE)


def extract_skills_from_text(text: str, skill_dict_path: str) -> Tuple[Dict[str, List[str]], List[str]]:
    """Return (skills_by_category, all_detected_skills_list)"""
    skills_list = load_skill_dictionary(skill_dict_path)
    found = defaultdict(list)
    detected = set()

    for entry in skills_list:
        name = entry['skill']
        category = entry['category']
        aliases = [name] + entry.get('aliases', [])
        for token in aliases:
            if not token:
                continue
            pattern = _make_pattern(token)
            if pattern.search(text):
                if name not in detected:
                    found[category].append(name)
                    detected.add(name)
                break

    # Sort lists
    for k in list(found.keys()):
        found[k] = sorted(found[k])

    return dict(found), sorted(detected)
