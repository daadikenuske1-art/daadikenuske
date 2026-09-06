"""
Uses Gemini to:
1. Pick a specific, unique home-remedy topic within today's category.
2. Write a long-form Hindi narration script (~6-8 minutes when spoken).
3. Write a short-form Hindi narration script (<=30 seconds when spoken, punchy).
4. Write YouTube titles/descriptions/tags for both.
5. Write 2 detailed AI-image-generation prompts (concrete visual scenes that match
   the narration precisely) for each section of the long video, and 2 for the short video.

Outputs a single JSON blob consumed by the rest of the pipeline.
"""

import json
import os
import re

import google.generativeai as genai

from topics import get_todays_category, get_recent_topics, record_topic

GEMINI_MODEL = "gemini-3.6-flash"


def _configure():
    api_key = os.environ["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)


def _extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text.strip())
    text = re.sub(r"```$", "", text.strip())
    return json.loads(text.strip())


PROMPT_TEMPLATE = """You are the head writer for "DaadiKeNuske" (दादी के नुस्खे), a Hindi-language YouTube channel about
Indian grandmother-style home remedies: food habits, eating habits, skin and hair care,
pregnancy nutrition, mental relaxation, and everyday wellness — all natural, kitchen-ingredient
based remedies, explained simply and warmly like a daadi (grandmother) talking to her family.

Today's remedy category is: {category}

Do NOT reuse any of these topics already covered recently: {recent_topics}

Pick ONE specific, concrete, unique remedy topic within today's category (e.g. not just
"skin care" but "haldi (turmeric) face pack for glowing skin — how and when to apply").

Return ONLY valid JSON (no markdown fences) with this exact shape:

{{
  "topic": "short topic name",
  "long_video": {{
    "title": "catchy Hindi YouTube title, under 100 chars, include relevant keywords",
    "description": "2-3 paragraph Hindi YouTube description with natural keywords, plus a short disclaimer that this is traditional home remedy info and not a substitute for medical advice",
    "tags": ["hindi", "tag2", "..."],
    "script_sections": [
      {{
        "narration_hi": "Hindi narration text for this section, warm and conversational, like a daadi speaking",
        "visual_keywords": ["detailed image-generation prompt 1", "detailed image-generation prompt 2"]
      }}
    ]
  }},
  "short_video": {{
    "title": "catchy Hindi Shorts title, under 80 chars, must work with #Shorts",
    "description": "1 short Hindi paragraph + relevant hashtags including #Shorts",
    "tags": ["hindi", "shorts", "..."],
    "narration_hi": "single punchy Hindi narration script, MUST be speakable within 28-30 seconds (roughly 60-70 Hindi words), hook in first line",
    "visual_keywords": ["detailed image-generation prompt 1", "detailed image-generation prompt 2"]
  }}
}}

Rules:
- script_sections for the long video should have 6 to 9 sections, each 45-90 spoken seconds
  of Hindi narration (roughly 90-160 Hindi words per section), covering: hook/intro, what the
  remedy is, why/how it works (simple traditional explanation), step-by-step how to prepare
  and apply/use it, when/how often to use it, precautions, and a warm closing with a
  call-to-subscribe.
- All narration must be in Hindi (Devanagari script), natural spoken style, no English words
  except unavoidable product/ingredient names.
- visual_keywords must be in English, exactly 2 items per section (and exactly 2 for the
  short video). Each item is a full, self-contained AI-image-generation prompt describing one
  specific, realistic, concrete scene that directly matches what that section's narration is
  about — not a generic keyword. Be precise about the subject, setting, ingredients, and action
  shown (e.g. "a close-up of golden turmeric powder in a small brass bowl on a rustic wooden
  kitchen counter, soft warm morning light, no text or logos" rather than just "turmeric").
  The two prompts for a section should show two different, complementary moments of that
  section's content (e.g. the raw ingredient, then the remedy being prepared or applied).
  Never include any text, captions, watermarks, or logos in the described scene.
- Never give medical claims as guaranteed cures; frame everything as traditional/home-remedy
  knowledge passed down, and add a brief safety caveat (patch test, consult a doctor for
  serious/persistent issues, pregnancy-specific care under doctor's guidance).
- Output must be valid JSON only.
"""


def generate_content_plan():
    _configure()
    category = get_todays_category()
    recent_topics = get_recent_topics()
    recent_str = ", ".join(recent_topics) if recent_topics else "(none yet)"

    model = genai.GenerativeModel(GEMINI_MODEL)
    prompt = PROMPT_TEMPLATE.format(category=category, recent_topics=recent_str)
    response = model.generate_content(prompt)
    plan = _extract_json(response.text)

    record_topic(plan["topic"])
    return plan


if __name__ == "__main__":
    plan = generate_content_plan()
    out_path = os.path.join(os.path.dirname(__file__), "..", "state", "today_plan.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print(f"Generated plan for topic: {plan['topic']}")
    print(f"Saved to {out_path}")
