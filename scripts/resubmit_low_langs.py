#!/usr/bin/env python3
"""Targeted resubmission for 5 under-performing languages.

Improved prompts with:
- max_tokens=65536 (doubled from 32768)
- Smaller, more focused domain splits (10 batches of 200 instead of 5 batches of 500)
- For mni (Manipuri): explicit Meetei Mayek character examples in prompt
- For mai (Maithili): explicit instruction to NOT duplicate Hindi entries
- For sd (Sindhi): explicit Sindhi-specific character examples

Usage:
    python scripts/resubmit_low_langs.py submit --api-key $XAI_API_KEY
    python scripts/resubmit_low_langs.py status --api-key $XAI_API_KEY
    python scripts/resubmit_low_langs.py process --api-key $XAI_API_KEY
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_transliterations_batch import (
    BASE_URL, api_create_batch, api_add_requests, api_get_batch,
    api_get_results, parse_json_response, OUTPUT_DIR,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JOB_DIR = PROJECT_ROOT / "data" / "translit_batch_jobs_v2"
DEFAULT_MODEL = "grok-4-1-fast-non-reasoning"

# ---------------------------------------------------------------------------
# Language-specific configs for the 5 under-performers
# ---------------------------------------------------------------------------

LANGUAGES = {
    "te": {
        "lang_name": "Telugu",
        "script_name": "Telugu",
        "script_notes": """Telugu script is an abugida with distinctive rounded letterforms.
Key characters: క(ka) ఖ(kha) గ(ga) ఘ(gha) చ(cha) జ(ja) ట(Ta) డ(Da) త(ta) ద(da) న(na) ప(pa) బ(ba) మ(ma) య(ya) ర(ra) ల(la) వ(va) శ(sha) ష(Sha) స(sa) హ(ha)
Vowel signs: ా(aa) ి(i) ీ(ii) ు(u) ూ(uu) ె(e) ే(ee) ొ(o) ో(oo) ై(ai) ౌ(au)
Virama/halant: ్ (suppresses inherent vowel)
Example mappings: కంప్యూటర్→computer, డౌన్లోడ్→download, స్క్రీన్షాట్→screenshot""",
    },
    "ne": {
        "lang_name": "Nepali",
        "script_name": "Devanagari",
        "script_notes": """Nepali uses Devanagari script, very similar to Hindi but with some pronunciation differences.
IMPORTANT: Nepali ASR may spell loanwords slightly differently from Hindi. For example:
- Hindi: कंप्यूटर vs Nepali: कम्प्युटर
- Hindi: इंटरनेट vs Nepali: इन्टरनेट
Use the Nepali pronunciation/spelling conventions, not Hindi ones.
Include words specific to Nepal context: trekking, Himalaya-related tourism, etc.""",
    },
    "mai": {
        "lang_name": "Maithili",
        "script_name": "Devanagari",
        "script_notes": """Maithili uses Devanagari script. While similar to Hindi, Maithili has distinct pronunciation patterns.
CRITICAL: Many Maithili loanword spellings are IDENTICAL to Hindi (e.g., कंप्यूटर, डाउनलोड).
Focus on words where Maithili spelling DIFFERS from Hindi, and on domain-specific terms not commonly covered.
Maithili-specific patterns: Sometimes uses छ where Hindi uses है, different verb endings.
Include education terms (tuition, hostel, exam), agriculture terms, and technology terms.""",
    },
    "sd": {
        "lang_name": "Sindhi",
        "script_name": "Sindhi Perso-Arabic",
        "script_notes": """Sindhi uses a modified Perso-Arabic script with ADDITIONAL characters not in Urdu:
Sindhi-specific: ٻ(implosive b) ڀ(bh) ٽ(retroflex t) ٿ(th) ڄ(implosive j) ڃ(ny) ڇ(chh) ڊ(retroflex d) ڌ(dh) ڍ(ddh) ڏ(implosive d) ڙ(retroflex r) ڪ(k) ڳ(g) ڱ(ng) ڻ(retroflex n) ھ(h/aspiration)
Standard Arabic letters also used: ا ب ت ث ج ح خ د ذ ر ز س ش ص ض ط ظ ع غ ف ق ل م ن ه و ي
Short vowels are usually WRITTEN in Sindhi (unlike Urdu where they're often omitted).
Example: ڪمپيوٽر→computer, ڊائونلوڊ→download, اسڪرين→screen
IMPORTANT: Use Sindhi letter forms (ڪ not ک, ٽ not ٹ, ڊ not ڈ) for the correct Sindhi rendering.""",
    },
    "mni": {
        "lang_name": "Manipuri",
        "script_name": "Meetei Mayek",
        "script_notes": """Meetei Mayek is a unique alphabetic script (NOT an abugida) used for Manipuri/Meitei language.
Unlike most Indian scripts, each character represents a single sound.

CONSONANTS:
ꯀ=k, ꯁ=s, ꯂ=l, ꯃ=m, ꯄ=p, ꯅ=n, ꯆ=ch, ꯇ=t, ꯈ=kh, ꯉ=ng, ꯊ=th, ꯋ=w, ꯌ=y, ꯍ=h, ꯎ=u(consonant), ꯏ=i(consonant)
VOWELS (standalone):
ꯑ=a
VOWEL SIGNS (attached to consonants):
ꯥ=aa, ꯤ=i, ꯦ=e, ꯧ=ei, ꯨ=u, ꯩ=ou, ꯣ=o
FINAL CONSONANTS (coda forms):
ꯛ=k, ꯜ=l, ꯝ=m, ꯞ=p, ꯟ=n, ꯠ=t, ꯡ=ng

CRITICAL EXAMPLES of how English words are written in Meetei Mayek:
ꯀꯝꯄꯤꯎꯇꯔ = computer (ka-m-pa-i-u-ta-ra)
ꯐꯣꯟ = phone (pha-o-n) — note: ꯐ is used for 'ph/f' sound
ꯏꯟꯇꯔꯅꯦꯠ = internet (i-n-ta-ra-ne-t)
ꯑꯦꯞ = app (a-e-p)
ꯗꯥꯎꯟꯂꯣꯗ = download (da-aa-u-n-la-o-da)
ꯃꯤꯇꯤꯡ = meeting (mi-ti-ng)
ꯁꯛꯔꯤꯟꯁꯣꯠ = screenshot (sa-k-ra-i-n-sa-o-t)
ꯋꯥꯏꯐꯥꯏ = wifi (wa-aa-i-pha-aa-i)
ꯕ꯭ꯂꯨꯇꯨꯊ = bluetooth (ba-lu-tu-tha)

Generate ONLY valid Meetei Mayek script. Each entry must use characters from the U+ABC0-U+ABFF range.
Do NOT use Devanagari or Bengali script — Manipuri ASR outputs Meetei Mayek.""",
    },
}

# Smaller, focused domain batches — 10 per language instead of 5
DOMAIN_BATCHES = [
    ("F", "Technology & Computers",
     "computer, laptop, desktop, monitor, keyboard, mouse, printer, scanner, USB, HDMI, "
     "software, hardware, app, browser, website, server, database, cloud, backup, wifi, "
     "bluetooth, hotspot, router, modem, bandwidth, download, upload, install, update, "
     "restart, reset, crash, bug, fix, patch, version, upgrade, system, network, firewall"),

    ("G", "Mobile & Social Media",
     "phone, mobile, smartphone, tablet, screen, battery, charger, SIM, data, signal, "
     "notification, setting, ringtone, wallpaper, screenshot, selfie, camera, photo, video, "
     "WhatsApp, Instagram, Facebook, YouTube, Twitter, TikTok, Snapchat, Google, "
     "post, share, like, comment, follow, subscribe, trending, viral, story, reel, meme"),

    ("H", "Office, Finance & Banking",
     "office, meeting, deadline, budget, salary, manager, boss, team, project, report, "
     "email, message, document, file, folder, print, scan, copy, presentation, schedule, "
     "bank, account, balance, transfer, deposit, loan, EMI, interest, credit, debit, card, "
     "ATM, UPI, payment, invoice, receipt, refund, discount, tax, GST, insurance, policy"),

    ("I", "Medicine, Health & Sports",
     "doctor, hospital, clinic, medicine, tablet, capsule, injection, vaccine, dose, "
     "surgery, X-ray, blood, pressure, diabetes, patient, emergency, ambulance, pharmacy, "
     "gym, workout, fitness, exercise, yoga, diet, protein, calorie, treadmill, "
     "cricket, football, match, score, team, coach, player, referee, tournament, medal"),

    ("J", "Education, Food, Fashion & Daily Life",
     "school, college, university, exam, result, assignment, tuition, fees, hostel, "
     "scholarship, campus, lecture, syllabus, library, certificate, degree, admission, "
     "recipe, microwave, oven, fridge, blender, menu, restaurant, pizza, burger, juice, "
     "fashion, dress, brand, designer, collection, trend, style, fabric, salon, makeup, "
     "car, bike, engine, brake, tire, petrol, diesel, parking, license, traffic, "
     "hotel, booking, flight, passport, visa, ticket, tourist, guide, trek"),

    ("K", "Short Words & Compound Modern Terms",
     """CRITICAL: Generate entries for SHORT English words (2-4 letters) commonly used in code-mixing:
on, off, ok, yes, no, hi, bye, app, bug, fix, run, set, get, put, add, cut, fan, map, tab,
tag, bat, bet, bit, box, bus, cab, cup, dot, gap, gun, hat, hit, hub, jam, kit, lab, lid,
log, lot, mix, mob, net, nod, nut, pad, pan, pat, pen, pet, pin, pit, pop, pot, pub, rag,
ram, rap, rat, rib, rim, rod, row, rub, rug, sir, sit, six, sum, sun, tap, ten, tin, tip,
top, tub, van, vet, web, wig, win, zip, zoo, ace, aim, air, arc, arm, art, ask, axe

Also generate COMPOUND/MODERN terms: smartphone, smartwatch, powerbank, livestream,
screenshot, YouTube, WhatsApp, Instagram, startup, lockdown, shutdown, upgrade, downgrade,
feedback, deadline, timeline, workflow, database, frontend, backend, fullstack, QR code"""),
]


def build_request(custom_id, lang_code, lang_info, batch_id, domains, examples, model):
    system = f"""You are an expert linguist specializing in {lang_info['script_name']} script for {lang_info['lang_name']} language.
You understand exactly how English loanwords appear in {lang_info['lang_name']} ASR (speech recognition) output.

RULES:
- Output ONLY a valid JSON object. No markdown, no code fences, no explanation.
- Each key: an English loanword as it appears in {lang_info['script_name']} script in ASR output.
- Each value: the correct English word (lowercase).
- Generate AT LEAST 200 unique entries for the specified domains.
- Keep entries concise — one word per entry where possible.
- Do NOT include native {lang_info['lang_name']} words — ONLY English loanwords written in {lang_info['script_name']}."""

    user = f"""Generate a JSON dictionary mapping English loanwords in {lang_info['script_name']} script
(for {lang_info['lang_name']} language, code: {lang_code}) to their English form.

DOMAINS: {domains}

Target words to include:
{examples}

{lang_info['script_notes']}

Output ONLY valid JSON. No markdown fences. No explanation.
Format: {{"{lang_info['script_name']}_word": "english_word", ...}}"""

    return {
        "batch_request_id": custom_id,
        "batch_request": {
            "chat_get_completion": {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": 65536,
                "temperature": 0.3,
            }
        }
    }


def cmd_submit(args):
    JOB_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = JOB_DIR / "manifest.json"

    if manifest_path.exists() and not args.force:
        print(f"ERROR: {manifest_path} exists. Use --force to overwrite.")
        sys.exit(1)

    all_requests = []
    request_map = {}

    for lang_code, lang_info in LANGUAGES.items():
        for batch_id, domains, examples in DOMAIN_BATCHES:
            cid = f"{lang_code}_{batch_id}"
            req = build_request(cid, lang_code, lang_info, batch_id, domains, examples, args.model)
            all_requests.append((cid, req))
            request_map[cid] = {
                "lang_code": lang_code,
                "lang_name": lang_info["lang_name"],
                "batch_id": batch_id,
                "domains": domains,
            }

    print(f"Prepared {len(all_requests)} requests ({len(LANGUAGES)} languages × {len(DOMAIN_BATCHES)} batches)")

    if args.dry_run:
        for cid, info in sorted(request_map.items()):
            print(f"  {cid}: {info['lang_name']} — {info['domains'][:60]}...")
        return

    with open(JOB_DIR / "request_map.json", "w") as f:
        json.dump(request_map, f, indent=2)

    batch_name = f"translit_v2_{time.strftime('%Y%m%d_%H%M%S')}"
    print(f"\nCreating batch: {batch_name}")
    batch_resp = api_create_batch(args.api_key, batch_name)
    batch_id = batch_resp["batch_id"]
    print(f"  Batch ID: {batch_id}")

    total_added = 0
    for i in range(0, len(all_requests), 5):
        chunk = all_requests[i:i+5]
        batch_reqs = [req for _, req in chunk]
        ok = api_add_requests(args.api_key, batch_id, batch_reqs)
        if ok:
            total_added += len(chunk)
        else:
            for cid, _ in chunk:
                print(f"  FAILED: {cid}")

    manifest = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": args.model,
        "batch_id": batch_id,
        "batch_name": batch_name,
        "total_requests": len(all_requests),
        "requests_added": total_added,
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n{total_added}/{len(all_requests)} requests submitted to {batch_id}")


def cmd_status(args):
    manifest_path = JOB_DIR / "manifest.json"
    if not manifest_path.exists():
        print("ERROR: No manifest. Run 'submit' first.")
        sys.exit(1)
    with open(manifest_path) as f:
        manifest = json.load(f)

    from generate_transliterations_batch import api_headers
    import requests
    batch_id = manifest["batch_id"]
    resp = requests.get(f"{BASE_URL}/batches/{batch_id}",
                        headers=api_headers(args.api_key), timeout=30)
    resp.raise_for_status()
    state = resp.json()["state"]

    print(f"Batch: {manifest.get('batch_name', batch_id)}")
    print(f"  Requests:  {state['num_requests']:>4}")
    print(f"  Succeeded: {state['num_success']:>4}")
    print(f"  Errored:   {state['num_error']:>4}")
    print(f"  Pending:   {state['num_pending']:>4}")
    if state["num_pending"] == 0:
        print("  STATUS: COMPLETE")


def cmd_process(args):
    manifest_path = JOB_DIR / "manifest.json"
    request_map_path = JOB_DIR / "request_map.json"

    if not manifest_path.exists():
        print("ERROR: No manifest. Run 'submit' first.")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)
    with open(request_map_path) as f:
        request_map = json.load(f)

    batch_id = manifest["batch_id"]
    batch = api_get_batch(args.api_key, batch_id)
    state = batch["state"]

    if state["num_pending"] > 0:
        print(f"ERROR: Still {state['num_pending']} pending.")
        sys.exit(1)

    print(f"Downloading from {batch_id}: {state['num_success']} succeeded, {state['num_error']} errored")

    all_results = {}
    failed = []
    pagination_token = None
    while True:
        page = api_get_results(args.api_key, batch_id, page_size=100,
                               pagination_token=pagination_token)
        for result in page.get("results", []):
            cid = result.get("batch_request_id", "")
            br = result.get("batch_result", {})
            resp = br.get("response", {})
            chat = resp.get("chat_get_completion", {})
            choices = chat.get("choices", [])
            if choices:
                text = (choices[0].get("message", {}).get("content", "") or "").strip()
                all_results[cid] = text
            else:
                error = br.get("error", {})
                err_msg = error.get("message", "") if isinstance(error, dict) else str(error)
                failed.append({"custom_id": cid, "error": err_msg})
        pagination_token = page.get("pagination_token")
        if pagination_token is None:
            break

    print(f"Downloaded: {len(all_results)} succeeded, {len(failed)} failed")

    # Save raw
    with open(JOB_DIR / "raw_results.json", "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Parse and merge into EXISTING per-language files
    lang_new_entries: dict[str, dict[str, str]] = {}
    parse_ok = 0
    parse_fail = 0

    for cid, raw_text in sorted(all_results.items()):
        info = request_map.get(cid, {})
        lang_code = info.get("lang_code", cid.split("_")[0])

        parsed = parse_json_response(raw_text)
        if parsed is None:
            print(f"  PARSE FAIL: {cid}")
            parse_fail += 1
            continue

        parse_ok += 1
        if lang_code not in lang_new_entries:
            lang_new_entries[lang_code] = {}

        for indic_word, eng_word in parsed.items():
            if not isinstance(eng_word, str) or not isinstance(indic_word, str):
                continue
            eng_clean = eng_word.lower().strip()
            indic_clean = indic_word.strip()
            if not indic_clean or not eng_clean:
                continue

            # Same quality filters as main script
            if all(c.isascii() for c in indic_clean):
                continue
            if not all(c.isascii() for c in eng_clean):
                continue
            eng_clean = re.sub(r"\d+$", "", eng_clean).strip()
            if not eng_clean:
                continue
            latin_chars = sum(1 for c in indic_clean if c.isascii() and c.isalpha())
            non_ascii_chars = sum(1 for c in indic_clean if not c.isascii())
            if latin_chars > 0 and non_ascii_chars > 0:
                continue
            if len(indic_clean) == 1:
                continue
            if len(eng_clean.split()) > 3:
                continue

            lang_new_entries[lang_code][indic_clean] = eng_clean

    print(f"\nParsed: {parse_ok} succeeded, {parse_fail} failed")

    # Merge with existing files
    for lang_code, new_entries in sorted(lang_new_entries.items()):
        existing_path = OUTPUT_DIR / f"{lang_code}_transliterations.json"
        existing = {}
        if existing_path.exists():
            with open(existing_path) as f:
                existing = json.load(f)

        before = len(existing)
        existing.update(new_entries)
        after = len(existing)
        added = after - before

        with open(existing_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

        print(f"  {lang_code}: {before} → {after} (+{added} new, {len(new_entries)} from v2)")

    print(f"\nMerged into {OUTPUT_DIR}")


def main():
    parser = argparse.ArgumentParser(description="Targeted resubmission for low-count languages")
    parser.add_argument("--api-key", default=os.environ.get("XAI_API_KEY"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    subparsers = parser.add_subparsers(dest="command", required=True)

    sub = subparsers.add_parser("submit")
    sub.add_argument("--dry-run", action="store_true")
    sub.add_argument("--force", action="store_true")

    subparsers.add_parser("status")
    subparsers.add_parser("process")

    args = parser.parse_args()
    if not args.api_key:
        print("ERROR: No API key. Use --api-key or set XAI_API_KEY.")
        sys.exit(1)

    {"submit": cmd_submit, "status": cmd_status, "process": cmd_process}[args.command](args)


if __name__ == "__main__":
    main()
