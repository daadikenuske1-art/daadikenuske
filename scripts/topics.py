"""
Topic rotation for DaadiKeNuske.

We rotate across broad remedy categories by day-of-year so content stays varied,
then ask Gemini to pick one *specific, unique* topic within that category that
has not been used in the last ROTATION_WINDOW days (tracked in state/history.json).
"""

import datetime
import json
import os

STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "state", "history.json")
ROTATION_WINDOW_DAYS = 90  # don't repeat a topic within this many days

CATEGORIES = [
    "Skin care home remedies (haldi, besan, aloe vera, chandan, multani mitti — for glow, tanning, dark spots, pimples)",
    "Hair care home remedies (hair growth, dandruff, hair fall, premature greying, oiling rituals)",
    "Pregnancy & women's nutrition (what to eat during pregnancy, post-delivery care, iron/calcium rich home foods)",
    "Mind & body relaxation (stress relief, better sleep, calming herbal drinks, breathing/rest rituals from Indian households)",
    "Digestion & gut health home remedies (bloating, acidity, constipation, appetite — kitchen spice remedies)",
    "Kids' health home remedies (cold/cough in children, immunity boosting foods, safe home remedies for common childhood issues)",
    "Weight & metabolism home remedies (natural fat-burning drinks, metabolism boosting kitchen ingredients)",
    "Seasonal & immunity remedies (monsoon/winter/summer specific kadha, immunity boosters, seasonal skin/hair care)",
    "Joint pain & body ache home remedies (oil massages, kitchen ingredient poultices, mobility)",
    "Beauty rituals (natural lip care, under-eye dark circles, sunburn relief, nail & hand care)",
]


def _load_history():
    if not os.path.exists(STATE_PATH):
        return []
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_history(history):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_todays_category():
    day_of_year = datetime.date.today().timetuple().tm_yday
    return CATEGORIES[day_of_year % len(CATEGORIES)]


def get_recent_topics(days=ROTATION_WINDOW_DAYS):
    history = _load_history()
    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    recent = []
    for entry in history:
        try:
            d = datetime.date.fromisoformat(entry["date"])
        except (KeyError, ValueError):
            continue
        if d >= cutoff:
            recent.append(entry["topic"])
    return recent


def record_topic(topic):
    history = _load_history()
    history.append({"date": datetime.date.today().isoformat(), "topic": topic})
    # keep file from growing forever
    cutoff = datetime.date.today() - datetime.timedelta(days=ROTATION_WINDOW_DAYS * 2)
    history = [
        e for e in history
        if "date" in e and datetime.date.fromisoformat(e["date"]) >= cutoff
    ]
    _save_history(history)
PASTE_TEST_123
