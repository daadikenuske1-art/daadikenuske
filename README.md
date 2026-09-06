# DaadiKeNuske — Automated Daily Home Remedy Channel

Automated pipeline that every day:
1. Picks a fresh, non-repeating home-remedy topic (skin, hair, pregnancy nutrition, mind/body relaxation, digestion, kids' health, weight, seasonal, joint care, beauty — rotates daily) and writes a full Hindi script using **Gemini**.
2. Converts the script to natural Hindi speech (free, no API key — `edge-tts`).
3. Fetches matching stock footage/photos from **Pexels** (free API).
4. Assembles a **long-form video** (6–9 sections, ~6–10 min, landscape, captioned) and a **Shorts video** (≤30s, vertical, captioned) with **ffmpeg**.
5. Uploads both to your YouTube channel automatically.
6. Runs every day on a schedule via **GitHub Actions** (free, unlimited minutes on a public repo) — no server, no laptop needed.

Everything is copy-paste — you don't need to write or run code except the two one-time commands marked below.

---

## Channel
- Name: **DaadiKeNuske**
- URL: https://www.youtube.com/channel/UCJCaQl_Y6poK6_5xdIUp5rQ

---

## One-time setup (do these in order)

### 1. Create the dedicated Gmail account
Create a brand-new Gmail account dedicated to this channel (e.g. `daadikenuske@gmail.com`). Use it to own the YouTube channel, the GCP project, and all API keys below. Keep its password saved somewhere safe — I never see or handle it.

### 2. Create a Google Cloud project + enable APIs
1. Go to https://console.cloud.google.com/ (signed in as the new Gmail account).
2. Create a new project, e.g. name it `daadikenuske`.
3. In **APIs & Services → Library**, enable:
   - **YouTube Data API v3**
   - **Generative Language API** (this is what Gemini uses)
4. Go to **APIs & Services → Credentials → Create Credentials → API key**. This is your `GEMINI_API_KEY`. (You can also get a Gemini key faster at https://aistudio.google.com/apikey — same account.)

### 3. Create a YouTube OAuth client (so uploads can happen with no browser, every day, automatically)
1. In the same GCP project: **APIs & Services → OAuth consent screen**.
   - User type: External. Fill in app name (`DaadiKeNuske`), your email. Add scope `.../auth/youtube.upload`. Add your new Gmail as a **test user**.
2. **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
   - Application type: **Desktop app**. Name it anything.
   - Save the **Client ID** and **Client Secret** shown — these are `YT_CLIENT_ID` and `YT_CLIENT_SECRET`.

### 4. Get your one-time YouTube refresh token
This is the only step that needs a terminal, and only ever runs **once** (not in GitHub Actions):

```bash
pip install google-auth-oauthlib
python scripts/get_refresh_token.py YOUR_CLIENT_ID YOUR_CLIENT_SECRET
```

A browser window opens — log in with the Gmail account that manages the DaadiKeNuske channel and approve access. The terminal will print:

```
YT_REFRESH_TOKEN=1//0g......
```

Copy that value — this is `YT_REFRESH_TOKEN`.

### 5. Get a free Pexels API key
1. Go to https://www.pexels.com/api/ and sign up (can use the same Gmail).
2. Copy your API key — this is `PEXELS_API_KEY`.

### 6. Create the public GitHub repo
1. Create a **public** GitHub org/account called `daadikenuske` (public repos get free, effectively unlimited GitHub Actions minutes — this is why we're using public, and your API keys stay safe as GitHub *Secrets*, never in the code).
2. Create a repo named `daadikenuske` under it.
3. Push this project's code to that repo (I can do this step with you once the repo exists — just share the repo URL).

### 7. Add your secrets to GitHub
In the repo: **Settings → Secrets and variables → Actions → New repository secret**. Add each of these (name must match exactly):

| Secret name | Value |
|---|---|
| `GEMINI_API_KEY` | from step 2 |
| `PEXELS_API_KEY` | from step 5 |
| `YT_CLIENT_ID` | from step 3 |
| `YT_CLIENT_SECRET` | from step 3 |
| `YT_REFRESH_TOKEN` | from step 4 |

These never appear in the code or logs — GitHub keeps them encrypted and only injects them at run time.

### 8. Test it
In the repo: **Actions tab → Daily DaadiKeNuske Upload → Run workflow**. Tick "Dry run" the first time (`skip_upload: true`) to confirm the video assembles correctly without publishing, then run again with dry run off to do a real end-to-end test upload.

After that, it runs automatically every day at 9:00 AM IST — one long video, one Short.

---

## Project structure

```
scripts/
  topics.py            # daily category rotation + duplicate-avoidance history
  generate_script.py   # Gemini: topic + long script + short script + metadata
  tts.py                # edge-tts Hindi narration audio
  fetch_visuals.py      # Pexels stock video/photo fetching
  ffmpeg_utils.py        # shared ffmpeg/ffprobe helpers (captions, scaling, concat)
  assemble_long.py       # builds the long-form landscape video
  assemble_short.py      # builds the <=30s vertical Shorts video
  upload_youtube.py      # headless YouTube upload via refresh token
  get_refresh_token.py   # ONE-TIME manual script (not run in CI)
  main.py                 # runs the full pipeline end to end
.github/workflows/
  daily-upload.yml        # the daily scheduled GitHub Action
state/
  history.json             # tracks used topics (committed back by the workflow)
  (audio/, visuals/, output/ are generated at runtime, gitignored)
```

## Costs
Everything here is free-tier: GitHub Actions (public repo), edge-tts, Pexels API, and Gemini's free tier (`gemini-2.0-flash`). If Gemini free-tier limits become an issue as the channel grows, the only paid piece would be Gemini usage — I can add a cost estimate once we see real daily usage.

## Safety / content notes
- All remedies are framed as traditional home-remedy knowledge, not medical claims — each video description includes a "not a substitute for medical advice" note, and pregnancy-related content is framed with a "consult your doctor" caveat, per the script generation prompt.
- Video category is set to "Howto & Style".
