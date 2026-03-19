#!/usr/bin/env python3
"""Generate comprehensive transliteration tables using xAI Grok Batch API.

Uses Grok to generate {Indic script word} → {English word} mappings for all 22
scheduled Indian languages. Each language gets 5 domain-focused batch requests
targeting 500+ entries each, for ~2500 entries per language.

Workflow:
    1. submit  — Send batch requests to Grok API (110 requests: 22 langs × 5 domains)
    2. status  — Check batch progress
    3. process — Download results, validate, merge per-language JSON files

Usage:
    python scripts/generate_transliterations_batch.py submit --api-key $XAI_API_KEY
    python scripts/generate_transliterations_batch.py status --api-key $XAI_API_KEY
    python scripts/generate_transliterations_batch.py process --api-key $XAI_API_KEY
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import requests as http_requests

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), "w", buffering=1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "grok-4-1-fast-non-reasoning"
BASE_URL = "https://api.x.ai/v1"
ADD_CHUNK_SIZE = 5  # requests per REST add call

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JOB_DIR = PROJECT_ROOT / "data" / "translit_batch_jobs"
OUTPUT_DIR = PROJECT_ROOT / "data" / "generated_transliterations"

# ---------------------------------------------------------------------------
# Language definitions
# ---------------------------------------------------------------------------
LANGUAGES = [
    # (lang_code, lang_name, script_name, script_notes)
    ("hi", "Hindi", "Devanagari",
     "Devanagari is an abugida. Aspirated consonants use ह-ligatures. Nukta (़) marks borrowed sounds like फ़ (fa), ज़ (za). Chandrabindu (ँ) and anusvara (ं) for nasals."),
    ("mr", "Marathi", "Devanagari",
     "Marathi Devanagari uses ॲ for English 'a' as in 'app'. Some words differ from Hindi spelling, e.g., ॅ vowel sign."),
    ("ne", "Nepali", "Devanagari",
     "Nepali Devanagari is very similar to Hindi. Some loanwords may have slightly different spellings reflecting Nepali pronunciation."),
    ("sa", "Sanskrit", "Devanagari",
     "Modern Sanskrit borrows English loanwords using standard Devanagari transliteration conventions similar to Hindi."),
    ("kok", "Konkani", "Devanagari",
     "Konkani uses Devanagari with spellings often close to Marathi or Hindi. Some words reflect Konkani phonology."),
    ("doi", "Dogri", "Devanagari",
     "Dogri uses Devanagari. Loanword spellings are generally similar to Hindi with occasional dialectal differences."),
    ("mai", "Maithili", "Devanagari",
     "Maithili uses Devanagari. Loanword spellings are generally similar to Hindi with occasional dialectal differences."),
    ("brx", "Bodo", "Devanagari",
     "Bodo uses Devanagari. Being a Tibeto-Burman language, some borrowed phonemes may be rendered differently than Hindi."),
    ("bn", "Bengali", "Bengali",
     "Bengali script uses conjunct consonants for clusters. No inherent distinction between 'v' and 'b'. Uses য় for 'y', ং for nasal."),
    ("as", "Assamese", "Bengali/Assamese",
     "Assamese uses a variant of Bengali script. Key difference: ৱ (wa) instead of Bengali ব for 'w/v'. র has a unique form."),
    ("gu", "Gujarati", "Gujarati",
     "Gujarati script lacks the top horizontal line of Devanagari. Otherwise similar character set. ક for 'k', ગ for 'g', etc."),
    ("pa", "Punjabi", "Gurmukhi",
     "Gurmukhi is used for Punjabi. Has its own character forms. Uses adhak (ੱ) for gemination. ਖ਼ for borrowed sounds."),
    ("or", "Odia", "Odia",
     "Odia script has distinctive rounded letterforms. Uses unique conjunct consonant formation rules. ସ for 's', କ for 'k'."),
    ("ta", "Tamil", "Tamil",
     "Tamil script LACKS aspirated consonants entirely. English 'p/b' both map to ப, 'd/t' to ட (retroflex) or த (dental). Use ஃ before ப for 'f' sound. 'z' uses ஜ. No native character for 'sh' — uses ஷ (Grantha)."),
    ("te", "Telugu", "Telugu",
     "Telugu script is an abugida with distinctive circular letterforms. Has full set of aspirated/unaspirated consonants. Zero-width joiner (ZWJ) sometimes used."),
    ("kn", "Kannada", "Kannada",
     "Kannada script is closely related to Telugu. Has all aspirated consonants. ಕ for 'k', ಗ for 'g', ಪ for 'p', ಬ for 'b'."),
    ("ml", "Malayalam", "Malayalam",
     "Malayalam has extensive conjunct consonants. Uses റ (chillu-ra) for English 'r' in many positions. ഫ for 'f', ബ for 'b'."),
    ("ur", "Urdu", "Perso-Arabic (Nastaliq)",
     "Urdu uses Perso-Arabic script (Nastaliq style). Right-to-left. Short vowels usually OMITTED. پ for 'p', ٹ for retroflex 't', چ for 'ch', ژ for 'zh'. English 'o' may use او or و."),
    ("ks", "Kashmiri", "Perso-Arabic",
     "Kashmiri uses a Perso-Arabic variant with additional diacritics for Kashmiri vowels. Some characters shared with Urdu."),
    ("sd", "Sindhi", "Perso-Arabic (Sindhi variant)",
     "Sindhi Perso-Arabic has additional characters: ٻ (implosive b), ڊ (implosive d), ٽ, ڪ. Different from Urdu script."),
    ("mni", "Manipuri", "Meetei Mayek",
     "Meetei Mayek is a unique abugida for Manipuri. Characters: ꯀ (ka), ꯁ (sa), ꯂ (la), ꯃ (ma), ꯄ (pa), ꯅ (na). Has its own vowel signs."),
    ("sat", "Santali", "Ol Chiki",
     "Ol Chiki is an ALPHABETIC script (not abugida) created for Santali. Each vowel and consonant has its own character. ᱚ=a, ᱛ=t, ᱜ=g, ᱝ=ng, ᱞ=l, ᱟ=aa, ᱠ=k, ᱡ=j, ᱢ=m, ᱣ=w, ᱤ=i, ᱥ=s, ᱦ=h, ᱧ=ny, ᱨ=r, ᱩ=u, ᱪ=ch, ᱫ=d, ᱬ=nn, ᱭ=y, ᱮ=e, ᱯ=p, ᱰ=dd, ᱱ=n, ᱲ=rr, ᱳ=o, ᱴ=tt, ᱵ=b, ᱶ=nasal, ᱷ=aspiration (h)."),
]

# Domain batches
DOMAIN_BATCHES = [
    ("A", "Technology, Office/Work, Communication, Social Media, E-commerce",
     """Include: app, software, hardware, wifi, bluetooth, screenshot, download, upload, install,
update, restart, reset, login, logout, password, server, database, cloud, backup, website,
browser, notification, setting, streaming, podcast, startup, crypto, blockchain,
meeting, deadline, budget, salary, manager, invoice, audit, presentation, spreadsheet,
email, message, forward, reply, comment, like, share, post, follow, subscribe, trending,
viral, influencer, content, algorithm, feed, story, reel,
order, delivery, tracking, refund, discount, coupon, cart, checkout, payment, COD, UPI,
review, rating, seller, buyer, marketplace, wishlist, prime, express"""),

    ("B", "Medicine/Health, Sports/Fitness, Food/Cooking, Fashion/Beauty",
     """Include: doctor, hospital, medicine, prescription, tablet, capsule, dose, injection,
vaccine, surgery, X-ray, MRI, ECG, blood, pressure, diabetes, patient, ward, emergency,
ambulance, clinic, pharmacy, insurance, claim, diagnosis, report, therapy, checkup,
match, cricket, football, batting, bowling, goal, score, team, coach, player, referee,
tournament, league, champion, medal, fitness, gym, workout, treadmill, protein, calorie,
diet, yoga, exercise, jogging, marathon, sprint,
recipe, microwave, oven, fridge, blender, grill, toast, bake, menu, chef, restaurant,
ingredient, sauce, cream, butter, cheese, pizza, burger, sandwich, salad, juice, smoothie,
fashion, dress, brand, designer, collection, trend, style, boutique, fabric, cotton,
silk, makeup, cosmetic, lipstick, foundation, salon, spa, manicure, pedicure"""),

    ("C", "Education, Finance/Banking, Legal, Real Estate, Automotive",
     """Include: school, college, university, exam, result, assignment, submit, grade, marks,
scholarship, tuition, fees, hostel, campus, lecture, professor, syllabus, semester,
library, certificate, degree, diploma, graduation, admission, enrollment,
bank, account, balance, transfer, deposit, withdrawal, loan, EMI, interest, credit,
debit, card, ATM, UPI, NEFT, RTGS, statement, cheque, investment, mutual fund, stock,
share, dividend, portfolio, tax, GST, income, return, filing,
lawyer, case, court, judge, bail, petition, hearing, verdict, appeal, legal, witness,
evidence, contract, agreement, notary, affidavit, FIR, complaint,
property, flat, apartment, plot, builder, broker, registration, stamp duty, mortgage,
rent, lease, tenant, landlord, maintenance, construction, interior, architect,
car, bike, scooter, engine, brake, clutch, gear, tire, tyre, puncture, mileage,
fuel, petrol, diesel, service, insurance, parking, license, highway, traffic"""),

    ("D", "Agriculture, Travel/Tourism, Entertainment/Music, Science, Environment, Military/Government",
     """Include: fertilizer, pesticide, tractor, harvest, crop, seed, irrigation, organic, farm,
soil, compost, greenhouse, agriculture, subsidy, market, yield, season, monsoon,
flight, airport, passport, visa, hotel, booking, resort, tourist, guide, trek, trekking,
cruise, trip, itinerary, luggage, boarding, terminal, transit, layover, ticket,
movie, cinema, theatre, trailer, release, director, actor, producer, shooting, scene,
song, music, album, concert, guitar, piano, drum, DJ, track, playlist, volume, speaker,
bass, remix, lyrics, karaoke, microphone, studio, record, channel, live, stream,
experiment, laboratory, research, sample, test, hypothesis, data, analysis, formula,
molecule, atom, electron, neutron, gene, DNA, protein, cell, microscope, telescope,
climate, pollution, recycle, solar, panel, carbon, emission, waste, plastic, ban,
ozone, global warming, biodegradable, ecosystem, conservation, renewable, sustainable,
army, navy, air force, defense, missile, radar, satellite, border, patrol, security"""),

    ("E", "Variant Spellings, Short Words, Compound Words, Modern Slang",
     """This batch focuses on COMPLETENESS:
1. SHORT WORDS (2-4 letters) commonly used in code-mixing: on, off, ok, yes, no, hi, bye,
   app, bug, fix, run, set, get, put, add, cut, pin, van, fan, map, cap, tab, tag, bat, bet,
   bit, bot, box, bus, cab, cam, cup, dip, dot, gap, gun, hat, hit, hop, hub, jam, jog, kit,
   lab, lid, lip, log, lot, mad, mix, mob, mop, mud, net, nod, nut, pad, pan, pat, pen, pet,
   pig, pit, pop, pot, pub, pun, rag, ram, rap, rat, rib, rim, rod, rot, row, rub, rug, sad,
   sap, sir, sit, six, sob, sum, sun, tap, tax, ten, tin, tip, top, tub, tug, van, vet, vow,
   wag, web, wig, win, wit, zip, zoo

2. COMPOUND/MODERN WORDS: smartphone, smartwatch, powerbank, screenshot, screenshot, livestream,
   YouTube, WhatsApp, Instagram, Facebook, Twitter, Snapchat, TikTok, Netflix, Amazon, Flipkart,
   Google, Uber, Ola, Swiggy, Zomato, Paytm, PhonePe, WiFi, Bluetooth, hotspot, broadband,
   startup, lockdown, shutdown, upgrade, downgrade, feedback, deadline, timeline, workflow,
   database, frontend, backend, fullstack, middleware, microservice, DevOps, API, URL, QR code

3. VARIANT SPELLINGS: For the top 200 most common English loanwords, provide ALL alternative
   spellings that an ASR system might produce. Different ASR systems (Google, Whisper, etc.)
   may render the same word slightly differently."""),
]


# ---------------------------------------------------------------------------
# REST API helpers
# ---------------------------------------------------------------------------

def api_headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def api_create_batch(api_key: str, batch_name: str) -> dict:
    resp = http_requests.post(
        f"{BASE_URL}/batches",
        json={"name": batch_name},
        headers=api_headers(api_key),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def api_add_requests(api_key: str, batch_id: str, batch_requests: list, retries: int = 3) -> bool:
    for attempt in range(retries):
        try:
            resp = http_requests.post(
                f"{BASE_URL}/batches/{batch_id}/requests",
                json={"batch_requests": batch_requests},
                headers=api_headers(api_key),
                timeout=300,
            )
            if resp.status_code == 200:
                return True
            if attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            print(f"    ERROR: add requests failed: {resp.status_code} {resp.text[:200]}")
            return False
        except Exception as e:
            if attempt < retries - 1:
                print(f"    Retry {attempt+1}/{retries}: {type(e).__name__}: {str(e)[:100]}")
                time.sleep(5 * (attempt + 1))
            else:
                print(f"    ERROR: {type(e).__name__}: {str(e)[:150]}")
                return False
    return False


def api_get_batch(api_key: str, batch_id: str) -> dict:
    resp = http_requests.get(
        f"{BASE_URL}/batches/{batch_id}",
        headers=api_headers(api_key),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def api_get_results(api_key: str, batch_id: str, page_size: int = 100,
                    pagination_token: str = None, retries: int = 5) -> dict:
    params = {"page_size": page_size}
    if pagination_token:
        params["pagination_token"] = pagination_token
    for attempt in range(retries):
        try:
            resp = http_requests.get(
                f"{BASE_URL}/batches/{batch_id}/results",
                params=params,
                headers=api_headers(api_key),
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if attempt < retries - 1:
                wait = 5 * (attempt + 1)
                print(f"    Retry {attempt+1}/{retries}: {e} (waiting {wait}s)")
                time.sleep(wait)
            else:
                raise


# ---------------------------------------------------------------------------
# Load existing transliterations to avoid duplicates
# ---------------------------------------------------------------------------

def load_existing_transliterations() -> dict[str, dict[str, str]]:
    """Load current _KNOWN_TRANSLITERATIONS from dictionary_lookup.py.

    We parse the existing entries so Grok can skip them and focus on NEW words.
    Returns dict of lang_code -> {indic: english}.
    """
    lookup_path = PROJECT_ROOT / "codemix_restore" / "dictionary_lookup.py"
    if not lookup_path.exists():
        return {}

    # We'll extract a sample (first 50 entries per language) to include in prompts
    # Full extraction would require AST parsing; a simple JSON load of the data dir is easier
    # For now, return empty - the prompt will say "focus on NEW entries not in common lists"
    return {}


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert linguist specializing in Indian language scripts and code-mixed speech patterns.
You deeply understand how English loanwords are transliterated into Indic scripts by ASR
(Automatic Speech Recognition) systems like Google Speech-to-Text, Whisper, and IndicASR.

Your task is to generate accurate {script_name} → English mappings for code-mixed ASR output.
These mappings will be used in a production NLP system to restore English words that ASR
rendered in native script back to Latin script.

CRITICAL RULES:
- Output ONLY a valid JSON object. No markdown fences, no explanation, no comments.
- Each key must be a word in {script_name} script as it would appear in ASR output.
- Each value must be the correct English word (lowercase).
- Generate AT LEAST 500 unique entries.
- Include variant spellings where ASR systems might produce different forms.
- Do NOT include native words — ONLY English loanwords written in native script."""


def build_user_prompt(lang_code: str, lang_name: str, script_name: str,
                      script_notes: str, batch_id: str, domains: str,
                      domain_examples: str) -> str:
    return f"""Generate a comprehensive JSON dictionary mapping English loanwords as they appear in
{script_name} script (for {lang_name} language, ISO code: {lang_code}) to their correct English form.

Context: When {lang_name} speakers use English words in conversation, ASR systems write those
words in {script_name} script. Your job is to provide the EXACT forms that ASR produces.

FOCUS DOMAINS for this batch ({batch_id}): {domains}

Requirements:
1. Generate AT LEAST 500 entries for these domains
2. Write EXACTLY how a {lang_name} ASR system would render each English word in {script_name}
   script — the actual ASR output form, not a dictionary/literary transliteration
3. Include words of ALL lengths — from short (2-3 letter) to long compound words
4. Include variant spellings where different ASR systems might produce different forms
5. For compound words, include both split and joined forms if applicable

Specific words/terms to include:
{domain_examples}

Script-specific notes for {script_name}:
{script_notes}

Output ONLY a valid JSON object mapping {script_name} strings to lowercase English strings.
No markdown, no code fences, no explanation. Just the JSON object.
Example: {{"{script_name}_word1": "english1", "{script_name}_word2": "english2"}}"""


def build_batch_request(custom_id: str, lang_code: str, lang_name: str,
                        script_name: str, script_notes: str,
                        batch_id: str, domains: str, domain_examples: str,
                        model: str) -> dict:
    system = SYSTEM_PROMPT.replace("{script_name}", script_name)
    user = build_user_prompt(lang_code, lang_name, script_name, script_notes,
                             batch_id, domains, domain_examples)
    return {
        "batch_request_id": custom_id,
        "batch_request": {
            "chat_get_completion": {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": 32768,
                "temperature": 0.3,
            }
        }
    }


# ---------------------------------------------------------------------------
# SUBMIT
# ---------------------------------------------------------------------------

def cmd_submit(args):
    JOB_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = JOB_DIR / "manifest.json"

    if manifest_path.exists() and not args.force:
        print(f"ERROR: {manifest_path} exists. Use --force to overwrite.")
        sys.exit(1)

    print("[1/3] Preparing batch requests...")
    all_requests = []
    request_map = {}

    for lang_code, lang_name, script_name, script_notes in LANGUAGES:
        for batch_id, domains, domain_examples in DOMAIN_BATCHES:
            custom_id = f"{lang_code}_{batch_id}"
            req = build_batch_request(
                custom_id, lang_code, lang_name, script_name, script_notes,
                batch_id, domains, domain_examples, args.model,
            )
            all_requests.append((custom_id, req))
            request_map[custom_id] = {
                "lang_code": lang_code,
                "lang_name": lang_name,
                "script_name": script_name,
                "batch_id": batch_id,
                "domains": domains,
            }

    print(f"  {len(all_requests)} requests ({len(LANGUAGES)} languages × {len(DOMAIN_BATCHES)} batches)")

    if args.dry_run:
        print(f"\n=== DRY RUN ===")
        for cid, info in sorted(request_map.items()):
            print(f"  {cid}: {info['lang_name']} ({info['script_name']}) — {info['batch_id']}: {info['domains'][:60]}...")
        return

    # Save request map
    with open(JOB_DIR / "request_map.json", "w") as f:
        json.dump(request_map, f, indent=2)

    print(f"\n[2/3] Creating batch...")
    batch_name = f"transliterations_{time.strftime('%Y%m%d_%H%M%S')}"
    batch_resp = api_create_batch(args.api_key, batch_name)
    batch_id = batch_resp["batch_id"]
    print(f"  Batch ID: {batch_id}")

    print(f"\n[3/3] Adding requests...")
    total_added = 0
    for chunk_start in range(0, len(all_requests), ADD_CHUNK_SIZE):
        chunk = all_requests[chunk_start:chunk_start + ADD_CHUNK_SIZE]
        batch_reqs = [req for _, req in chunk]
        ok = api_add_requests(args.api_key, batch_id, batch_reqs)
        if ok:
            total_added += len(chunk)
        else:
            for cid, _ in chunk:
                print(f"  FAILED: {cid}")

        if (chunk_start // ADD_CHUNK_SIZE + 1) % 10 == 0:
            print(f"  {total_added}/{len(all_requests)} added")

    manifest = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": args.model,
        "batch_id": batch_id,
        "batch_name": batch_name,
        "total_requests": len(all_requests),
        "requests_added": total_added,
        "languages": len(LANGUAGES),
        "batches_per_language": len(DOMAIN_BATCHES),
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n{total_added}/{len(all_requests)} requests submitted to batch {batch_id}")
    print(f"Run 'status' to check progress.")


# ---------------------------------------------------------------------------
# STATUS
# ---------------------------------------------------------------------------

def cmd_status(args):
    manifest_path = JOB_DIR / "manifest.json"
    if not manifest_path.exists():
        print("ERROR: No manifest. Run 'submit' first.")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    batch_id = manifest["batch_id"]
    batch = api_get_batch(args.api_key, batch_id)
    state = batch["state"]

    print(f"Batch: {manifest.get('batch_name', batch_id)}")
    print(f"Model: {manifest['model']}")
    print(f"  Requests:  {state['num_requests']:>6}")
    print(f"  Succeeded: {state['num_success']:>6}")
    print(f"  Errored:   {state['num_error']:>6}")
    print(f"  Pending:   {state['num_pending']:>6}")

    if state["num_pending"] == 0:
        print("  STATUS: COMPLETE")
    else:
        pct = (state["num_success"] + state["num_error"]) / max(state["num_requests"], 1) * 100
        print(f"  Progress: {pct:.1f}%")


# ---------------------------------------------------------------------------
# PROCESS
# ---------------------------------------------------------------------------

def parse_json_response(text: str) -> dict | None:
    """Parse Grok's response into a JSON dict.

    Handles 5 failure modes:
    1. Clean JSON — direct parse
    2. Markdown-wrapped — strip ```json ... ``` fences
    3. Truncated JSON — trim to last complete "key": "value" pair, close with }
    4. Apostrophe in keys (Assamese) — fix broken quoting
    5. Orphan keys (key without value) — remove them
    """
    text = text.strip()

    # Step 1: Strip markdown code fences (greedy — handle truncated fences too)
    md_match = re.search(r"```(?:json)?\s*(\{.*)", text, re.DOTALL)
    if md_match:
        text = md_match.group(1)
        # Remove trailing ``` if present
        text = re.sub(r"\s*```\s*$", "", text)

    # Step 2: Find the JSON object start
    brace_start = text.find("{")
    if brace_start == -1:
        return None
    text = text[brace_start:]

    # Step 3: Fix apostrophe quoting issue (Assamese ভিডিঅ' etc.)
    # Pattern: a non-escaped apostrophe followed by ': "' breaks the JSON
    text = re.sub(r"'(\s*:\s*\")", r"'\1", text)
    # More specific: fix cases where closing " on key is missing before :
    # e.g., "ভিডিঅ': "video"  →  "ভিডিঅ'": "video"
    text = re.sub(r'(?<=\w)\'(\s*:\s*")', r"'\"\1", text)
    # Simpler fix: "word': " → "word'": "
    text = text.replace("': \"", "'\": \"")

    # Step 4: Try direct parse
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # Step 5: Remove orphan keys (key followed by , instead of : "value")
    # Pattern: "key",\n  "next_key" where there's no : between
    text_cleaned = re.sub(r'"[^"]*"\s*,\s*(?="[^"]*"\s*:)', "", text)
    try:
        obj = json.loads(text_cleaned)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        text = text_cleaned  # keep the cleanup for truncation step

    # Step 6: Handle truncated JSON — extract all complete "key": "value" pairs
    # and reconstruct a valid JSON object
    pairs = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', text)
    if pairs:
        result = {}
        for key, value in pairs:
            key = key.strip()
            value = value.strip()
            if key and value:
                result[key] = value
        if result:
            return result

    return None


def cmd_process(args):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = JOB_DIR / "manifest.json"
    request_map_path = JOB_DIR / "request_map.json"

    if not manifest_path.exists():
        print("ERROR: No manifest. Run 'submit' first.")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)
    with open(request_map_path) as f:
        request_map = json.load(f)

    # Collect all batch IDs (main + any resubmit batches)
    batch_ids = [("main", manifest["batch_id"])]
    for resub_name in sorted(JOB_DIR.glob("resubmit*.json")):
        with open(resub_name) as f:
            resub = json.load(f)
        label = resub_name.stem  # e.g. "resubmit_manifest" or "resubmit2_manifest"
        batch_ids.append((label, resub["batch_id"]))

    # Check all batches are complete
    for label, bid in batch_ids:
        batch = api_get_batch(args.api_key, bid)
        state = batch["state"]
        if state["num_pending"] > 0:
            print(f"ERROR: {label} batch {bid} still has {state['num_pending']} pending.")
            sys.exit(1)
        print(f"{label} batch {bid}: {state['num_success']} succeeded, {state['num_error']} errored")

    # Download results from all batches (resubmit results overwrite main)
    all_results: dict[str, str] = {}
    failed: list[dict] = []

    for label, bid in batch_ids:
        print(f"\nDownloading {label} results from {bid}...")
        pagination_token = None

        while True:
            page = api_get_results(args.api_key, bid, page_size=100,
                                   pagination_token=pagination_token)
            results = page.get("results", [])

            for result in results:
                cid = result.get("batch_request_id", "")
                br = result.get("batch_result", {})
                resp = br.get("response", {})
                chat = resp.get("chat_get_completion", {})
                choices = chat.get("choices", [])

                if choices:
                    text = (choices[0].get("message", {}).get("content", "") or "").strip()
                    all_results[cid] = text  # resubmit overwrites main
                else:
                    error = br.get("error", {})
                    err_msg = error.get("message", "") if isinstance(error, dict) else str(error)
                    if cid not in all_results:  # only record if not already succeeded
                        failed.append({"custom_id": cid, "error": err_msg})

            pagination_token = page.get("pagination_token")
            if pagination_token is None:
                break

    print(f"\nTotal downloaded: {len(all_results)} succeeded, {len(failed)} failed")

    # Save raw results
    with open(JOB_DIR / "raw_results.json", "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    if failed:
        with open(JOB_DIR / "failed_requests.json", "w") as f:
            json.dump(failed, f, indent=2)
        print(f"Failed requests saved to {JOB_DIR / 'failed_requests.json'}")

    # Process into per-language files
    lang_entries: dict[str, dict[str, str]] = {}
    parse_success = 0
    parse_fail = 0

    for cid, raw_text in sorted(all_results.items()):
        info = request_map.get(cid, {})
        lang_code = info.get("lang_code", cid.split("_")[0])

        parsed = parse_json_response(raw_text)
        if parsed is None:
            print(f"  PARSE FAIL: {cid} — could not extract JSON")
            parse_fail += 1
            continue

        parse_success += 1
        if lang_code not in lang_entries:
            lang_entries[lang_code] = {}

        # Merge entries with quality filtering
        for indic_word, eng_word in parsed.items():
            if not isinstance(eng_word, str) or not isinstance(indic_word, str):
                continue
            eng_clean = eng_word.lower().strip()
            indic_clean = indic_word.strip()
            if not indic_clean or not eng_clean:
                continue

            # Quality filter 1: Skip all-Latin identity entries (COD→cod, UPI→upi)
            if all(c.isascii() for c in indic_clean):
                continue

            # Quality filter 2: Skip entries where English value has non-ASCII
            if not all(c.isascii() for c in eng_clean):
                continue

            # Quality filter 3: Strip trailing digits from English (fertilizer1→fertilizer)
            eng_clean = re.sub(r"\d+$", "", eng_clean).strip()
            if not eng_clean:
                continue

            # Quality filter 4: Skip mixed-script keys (Indic + Latin chars mixed)
            latin_chars = sum(1 for c in indic_clean if c.isascii() and c.isalpha())
            non_ascii_chars = sum(1 for c in indic_clean if not c.isascii())
            if latin_chars > 0 and non_ascii_chars > 0:
                # Mixed script — skip (e.g., "बodysuit", "टrello")
                continue

            # Quality filter 5: Skip reversed entries (English key → Indic value)
            if all(c.isascii() or c.isspace() for c in indic_clean):
                continue

            # Quality filter 6: Skip single-char Indic keys (too many false positives)
            if len(indic_clean) == 1:
                continue

            # Quality filter 7: Skip if English value has > 3 words (phrase, not a word)
            if len(eng_clean.split()) > 3:
                continue

            lang_entries[lang_code][indic_clean] = eng_clean

    print(f"\nParsed: {parse_success} succeeded, {parse_fail} failed")

    # Save per-language files
    total_entries = 0
    for lang_code in sorted(lang_entries.keys()):
        entries = lang_entries[lang_code]
        total_entries += len(entries)
        output_path = OUTPUT_DIR / f"{lang_code}_transliterations.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        print(f"  {lang_code}: {len(entries):>5} entries -> {output_path.name}")

    print(f"\nTotal: {len(lang_entries)} languages, {total_entries:,} entries")
    print(f"Saved to {OUTPUT_DIR}")
    print(f"\nRun 'python scripts/merge_transliterations.py' to merge into codebase.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate transliteration tables via Grok Batch API"
    )
    parser.add_argument("--api-key", default=os.environ.get("XAI_API_KEY"),
                        help="xAI API key (or set XAI_API_KEY env var)")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Grok model (default: {DEFAULT_MODEL})")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sub = subparsers.add_parser("submit", help="Submit batch for transliteration generation")
    sub.add_argument("--dry-run", action="store_true", help="Show requests without submitting")
    sub.add_argument("--force", action="store_true", help="Overwrite existing manifest")

    subparsers.add_parser("status", help="Check batch status")
    subparsers.add_parser("process", help="Download results and produce per-language files")

    args = parser.parse_args()

    if not args.api_key and args.command != "process":
        print("ERROR: No API key. Use --api-key or set XAI_API_KEY env var.")
        sys.exit(1)

    if args.command == "submit":
        cmd_submit(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "process":
        cmd_process(args)


if __name__ == "__main__":
    main()
