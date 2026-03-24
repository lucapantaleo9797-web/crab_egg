#!/usr/bin/env python3
"""
CrabEgg Hatch — The main orchestrator.
Runs the full hatching ceremony: interview → config → scout → write → produce.
Can also run individual stages post-hatch.
"""

import json
import os
import sys
import shutil
from datetime import datetime, timezone

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

# --- Workspace Setup ---

def create_workspace(base_path):
    """Create the full CrabEgg workspace directory structure."""
    dirs = [
        'data',
        'output/scripts',
        'output/audio',
        'output/video',
        'output/thumbnails',
        'logs'
    ]
    for d in dirs:
        os.makedirs(os.path.join(base_path, d), exist_ok=True)

    # Initialize empty data files
    empty_files = {
        'data/viral-library.json': {"posts": [], "last_updated": None},
        'data/content-pipeline.json': {"entries": []},
        'data/performance-log.json': [],
        'data/spotify-cache.json': {"brand_audio_profile": None, "podcast_shows": [], "content_ideas_from_podcasts": [], "recommended_tracks": [], "last_refreshed": None},
        'logs/scrape-log.json': [],
        'logs/production-log.json': [],
        'logs/evolution-log.json': [],
        'logs/error-log.json': []
    }

    for path, default in empty_files.items():
        full_path = os.path.join(base_path, path)
        if not os.path.exists(full_path):
            save_json(full_path, default)

    return base_path

def save_brand_profile(workspace, answers):
    """Convert interview answers to brand profile JSON."""
    profile = {
        "name": answers.get("product_name", ""),
        "product_type": answers.get("product_type", ""),
        "pitch": answers.get("pitch", ""),
        "price": answers.get("price", ""),
        "audience": answers.get("audience", {}),
        "voice": answers.get("voice", "casual-fun"),
        "language": answers.get("language", "English"),
        "niche_keywords": answers.get("niche_keywords", []),
        "content_split": {
            "talking_head": answers.get("talking_head_pct", 60),
            "broll": answers.get("broll_pct", 40)
        },
        "posting_frequency": answers.get("posting_frequency", 3),
        "avatar_url": answers.get("avatar_url", ""),
        "voice_id": answers.get("voice_id", ""),
        "broll_style": answers.get("broll_style", "cinematic"),
        "spotify_playlist": answers.get("spotify_playlist", ""),
        "podcast_keywords": answers.get("podcast_keywords", []),
        "music_genre": answers.get("music_genre", "ambient"),
        "shopify_store": answers.get("shopify_store", ""),
        "commission_rate": answers.get("commission_rate", 0),
        "payment_method": answers.get("payment_method", "stripe"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    save_json(os.path.join(workspace, 'data', 'brand-profile.json'), profile)
    return profile

def save_api_config(workspace, keys):
    """Save API configuration."""
    config = {
        "anthropic_api_key": keys.get("anthropic", ""),
        "apify_api_key": keys.get("apify", ""),
        "elevenlabs_api_key": keys.get("elevenlabs", ""),
        "creatify_api_id": keys.get("creatify_id", ""),
        "creatify_api_key": keys.get("creatify_key", ""),
        "higgsfield_api_key": keys.get("higgsfield", ""),
        "shopify_access_token": keys.get("shopify", ""),
        "shopify_store_url": keys.get("shopify_store_url", ""),
        "spotify_client_id": keys.get("spotify_client_id", ""),
        "spotify_client_secret": keys.get("spotify_client_secret", ""),
        "stripe_secret_key": keys.get("stripe", ""),
        "stripe_webhook_secret": keys.get("stripe_webhook", ""),
        "configured_at": datetime.now(timezone.utc).isoformat()
    }

    save_json(os.path.join(workspace, 'data', 'api-config.json'), config)
    return config

def save_scraping_sources(workspace, competitors, keywords, niche_keywords):
    """Build scraping sources from user input."""
    sources = {"sources": []}

    # Add competitor accounts
    for handle in competitors:
        handle = handle.strip()
        if not handle:
            continue
        platform = "instagram" if handle.startswith("@") and "tiktok" not in handle.lower() else "tiktok"
        sources["sources"].append({
            "type": "account",
            "platform": platform,
            "handle": handle if handle.startswith("@") else f"@{handle}",
            "min_views": 50000,
            "active": True,
            "auto_discovered": False
        })

    # Add keyword searches
    for kw in (keywords or niche_keywords):
        kw = kw.strip()
        if not kw:
            continue
        for platform in ["tiktok", "instagram"]:
            sources["sources"].append({
                "type": "keyword",
                "platform": platform,
                "query": kw,
                "min_views": 100000,
                "active": True
            })

    # Add hashtag searches from niche keywords
    for kw in niche_keywords:
        kw = kw.strip()
        if not kw:
            continue
        for platform in ["tiktok", "instagram"]:
            sources["sources"].append({
                "type": "hashtag",
                "platform": platform,
                "tag": f"#{kw.replace(' ', '')}",
                "min_views": 50000,
                "active": True
            })

    save_json(os.path.join(workspace, 'data', 'scraping-sources.json'), sources)
    return sources

# --- Status ---

def show_status(workspace):
    """Display full pipeline status."""
    print("\n  ,;;,")
    print(" ( o o)  CrabEgg Status Report")
    print("/'   '\\")
    print()

    # Brand
    brand_path = os.path.join(workspace, 'data', 'brand-profile.json')
    if os.path.exists(brand_path):
        brand = load_json(brand_path)
        print(f"  Brand: {brand.get('name', 'Not set')}")
        print(f"  Voice: {brand.get('voice', 'Not set')}")
        print(f"  Niche: {', '.join(brand.get('niche_keywords', []))}")
    else:
        print("  Brand: NOT CONFIGURED (run hatch first)")

    # Viral Library
    lib_path = os.path.join(workspace, 'data', 'viral-library.json')
    if os.path.exists(lib_path):
        lib = load_json(lib_path)
        posts = lib.get("posts", [])
        adapted = sum(1 for p in posts if p.get("adapted"))
        print(f"\n  Viral Library: {len(posts)} posts ({adapted} adapted, {len(posts)-adapted} available)")
        if lib.get("last_updated"):
            print(f"  Last scraped: {lib['last_updated']}")
    else:
        print("\n  Viral Library: EMPTY")

    # Content Pipeline
    pipe_path = os.path.join(workspace, 'data', 'content-pipeline.json')
    if os.path.exists(pipe_path):
        pipe = load_json(pipe_path)
        entries = pipe.get("entries", [])
        by_status = {}
        for e in entries:
            s = e.get("status", "unknown")
            by_status[s] = by_status.get(s, 0) + 1
        print(f"\n  Content Pipeline: {len(entries)} entries")
        for status, count in by_status.items():
            print(f"    {status}: {count}")
    else:
        print("\n  Content Pipeline: EMPTY")

    # Sources
    src_path = os.path.join(workspace, 'data', 'scraping-sources.json')
    if os.path.exists(src_path):
        sources = load_json(src_path)
        active = sum(1 for s in sources.get("sources", []) if s.get("active"))
        auto = sum(1 for s in sources.get("sources", []) if s.get("auto_discovered"))
        print(f"\n  Scraping Sources: {len(sources.get('sources', []))} total ({active} active, {auto} auto-discovered)")

    # Spotify
    spot_path = os.path.join(workspace, 'data', 'spotify-cache.json')
    if os.path.exists(spot_path):
        spot = load_json(spot_path)
        print(f"\n  Spotify: {len(spot.get('podcast_shows', []))} podcasts, {len(spot.get('recommended_tracks', []))} tracks")
        if spot.get("vibe"):
            print(f"  Vibe: {spot['vibe']}")

    # Performance
    perf_path = os.path.join(workspace, 'data', 'performance-log.json')
    if os.path.exists(perf_path):
        perf = load_json(perf_path)
        if perf:
            revenue = sum(e.get("revenue", 0) for e in perf)
            print(f"\n  Sales: {len(perf)} orders, ${revenue:.2f} total revenue")
        else:
            print(f"\n  Sales: No orders yet")

    # API Keys
    api_path = os.path.join(workspace, 'data', 'api-config.json')
    if os.path.exists(api_path):
        config = load_json(api_path)
        configured = []
        missing = []
        key_names = {
            "anthropic_api_key": "Anthropic",
            "apify_api_key": "Apify",
            "elevenlabs_api_key": "ElevenLabs",
            "creatify_api_key": "Creatify",
            "higgsfield_api_key": "Higgsfield",
            "shopify_access_token": "Shopify",
            "spotify_client_id": "Spotify",
            "stripe_secret_key": "Stripe"
        }
        for key, name in key_names.items():
            if config.get(key):
                configured.append(name)
            else:
                missing.append(name)
        print(f"\n  API Keys configured: {', '.join(configured) if configured else 'none'}")
        if missing:
            print(f"  API Keys missing: {', '.join(missing)}")

    print()

# --- Main ---

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hatch.py <workspace> [command]")
        print("Commands: setup, status, info")
        sys.exit(1)

    workspace = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else "setup"

    if command == "setup":
        create_workspace(workspace)
        print(f"  Workspace created at: {workspace}")
    elif command == "status":
        show_status(workspace)
    elif command == "info":
        show_status(workspace)
    else:
        print(f"Unknown command: {command}")
