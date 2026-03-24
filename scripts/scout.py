#!/usr/bin/env python3
"""
CrabEgg Content Scout — Discovers and analyzes viral content.
Scrapes TikTok + Instagram via Apify, analyzes with Claude Haiku,
saves to viral library with dedup.
"""

import json
import os
import sys
import time
import requests
from datetime import datetime, timezone

# --- Config Loading ---

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_config(workspace):
    api_config = load_json(os.path.join(workspace, 'data', 'api-config.json'))
    sources = load_json(os.path.join(workspace, 'data', 'scraping-sources.json'))
    brand = load_json(os.path.join(workspace, 'data', 'brand-profile.json'))

    library_path = os.path.join(workspace, 'data', 'viral-library.json')
    if os.path.exists(library_path):
        library = load_json(library_path)
    else:
        library = {"posts": [], "last_updated": None}

    return api_config, sources, brand, library

# --- Apify Scraping ---

ACTOR_MAP = {
    ("tiktok", "account"): "clockworks/tiktok-profile-scraper",
    ("tiktok", "keyword"): "clockworks/tiktok-scraper",
    ("tiktok", "hashtag"): "clockworks/tiktok-hashtag-scraper",
    ("instagram", "account"): "apify/instagram-profile-scraper",
    ("instagram", "hashtag"): "apify/instagram-hashtag-scraper",
}

def build_apify_input(source):
    platform = source["platform"]
    source_type = source["type"]

    if platform == "tiktok" and source_type == "account":
        return {"profiles": [source["handle"]], "resultsPerPage": 30, "shouldDownloadVideos": False}
    elif platform == "tiktok" and source_type == "keyword":
        return {"searchQueries": [source["query"]], "resultsPerPage": 30, "searchSection": "video", "shouldDownloadVideos": False}
    elif platform == "tiktok" and source_type == "hashtag":
        return {"hashtags": [source["tag"].lstrip("#")], "resultsPerPage": 50, "shouldDownloadVideos": False}
    elif platform == "instagram" and source_type == "account":
        return {"usernames": [source["handle"].lstrip("@")], "resultsLimit": 30}
    elif platform == "instagram" and source_type == "hashtag":
        return {"hashtags": [source["tag"].lstrip("#")], "resultsLimit": 50}
    else:
        raise ValueError(f"Unknown source type: {platform}/{source_type}")

def run_apify_actor(api_key, actor_id, input_data):
    """Start an Apify actor run and wait for results."""
    print(f"  Starting Apify actor: {actor_id}")

    # Start the run
    resp = requests.post(
        f"https://api.apify.com/v2/acts/{actor_id}/runs",
        headers={"Authorization": f"Bearer {api_key}"},
        json=input_data,
        timeout=30
    )
    resp.raise_for_status()
    run_id = resp.json()["data"]["id"]
    print(f"  Run started: {run_id}")

    # Poll for completion
    for attempt in range(90):  # max 15 minutes
        time.sleep(10)
        status_resp = requests.get(
            f"https://api.apify.com/v2/actor-runs/{run_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15
        )
        status = status_resp.json()["data"]["status"]

        if status == "SUCCEEDED":
            print(f"  Run completed successfully")
            break
        elif status in ("FAILED", "TIMED-OUT", "ABORTED"):
            print(f"  Run failed with status: {status}")
            return []
        # else RUNNING — keep polling
    else:
        print(f"  Run timed out after 15 minutes")
        return []

    # Get results
    results_resp = requests.get(
        f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30
    )
    return results_resp.json()

# --- Post Normalization ---

def normalize_tiktok_post(raw, source):
    return {
        "external_id": str(raw.get("id", "")),
        "platform": "tiktok",
        "url": raw.get("webVideoUrl", ""),
        "caption": raw.get("text", ""),
        "creator_handle": raw.get("authorMeta", {}).get("name", ""),
        "creator_name": raw.get("authorMeta", {}).get("nickName", ""),
        "views": raw.get("playCount", 0),
        "likes": raw.get("diggCount", 0),
        "comments": raw.get("commentCount", 0),
        "shares": raw.get("shareCount", 0),
        "duration_seconds": raw.get("videoMeta", {}).get("duration", 0),
        "posted_at": raw.get("createTimeISO", ""),
        "thumbnail_url": raw.get("covers", {}).get("default", ""),
        "content_type": "video",
        "source_type": source["type"],
        "source_query": source.get("handle") or source.get("query") or source.get("tag", ""),
        "scraped_at": datetime.now(timezone.utc).isoformat()
    }

def normalize_instagram_post(raw, source):
    views = raw.get("videoViewCount", 0) or raw.get("likesCount", 0)
    posted_at = raw.get("timestamp", "")
    if isinstance(posted_at, (int, float)):
        posted_at = datetime.fromtimestamp(posted_at, tz=timezone.utc).isoformat()

    return {
        "external_id": str(raw.get("id", "")),
        "platform": "instagram",
        "url": raw.get("url", ""),
        "caption": raw.get("caption", ""),
        "creator_handle": raw.get("ownerUsername", ""),
        "creator_name": raw.get("ownerFullName", ""),
        "views": views,
        "likes": raw.get("likesCount", 0),
        "comments": raw.get("commentsCount", 0),
        "shares": 0,
        "duration_seconds": raw.get("videoDuration", 0),
        "posted_at": posted_at,
        "thumbnail_url": raw.get("displayUrl", ""),
        "content_type": raw.get("type", "Video").lower(),
        "source_type": source["type"],
        "source_query": source.get("handle") or source.get("query") or source.get("tag", ""),
        "scraped_at": datetime.now(timezone.utc).isoformat()
    }

def normalize_post(raw, source):
    if source["platform"] == "tiktok":
        return normalize_tiktok_post(raw, source)
    else:
        return normalize_instagram_post(raw, source)

# --- Dedup ---

def is_duplicate(post, library):
    existing_urls = {p["url"] for p in library["posts"]}
    return post["url"] in existing_urls

# --- Content Analysis (Claude Haiku) ---

def analyze_post(post, brand, api_key):
    """Call Claude Haiku to analyze a viral post."""

    prompt = f"""Analyze this viral {post['platform']} post:

CREATOR: {post['creator_handle']} ({post['creator_name']})
CAPTION: {post['caption'][:500]}
VIEWS: {post['views']:,}
LIKES: {post['likes']:,}
COMMENTS: {post['comments']:,}
SHARES: {post['shares']:,}
DURATION: {post['duration_seconds']}s
POSTED: {post['posted_at']}
URL: {post['url']}

The brand context:
NICHE: {', '.join(brand.get('niche_keywords', []))}
PRODUCT: {brand['name']} — {brand.get('pitch', '')}
AUDIENCE: {json.dumps(brand.get('audience', {}))}

Analyze this post and return JSON with these exact fields:

{{
  "title": "A short descriptive title for this viral post (max 10 words)",
  "hook": "The exact hook/opening line or concept that grabs attention",
  "hook_type": "One of: question, bold-claim, story-open, shock-value, relatable, how-to, myth-bust, before-after, list, trend-ride",
  "theme": "The core theme/topic",
  "why_viral": "2-3 sentences explaining specifically why this post performed well.",
  "adaptation_idea": "A specific, concrete idea for how {brand['name']} could adapt this concept. 2-3 sentences.",
  "viral_score": 8,
  "content_format": "One of: talking-head, montage, tutorial, reaction, story, duet, trend, review, transformation",
  "estimated_production": "One of: low, medium, high",
  "best_for": "One of: awareness, education, conversion, engagement"
}}

The viral_score should be 1-10. Respond ONLY with valid JSON."""

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=30
    )
    resp.raise_for_status()

    text = resp.json()["content"][0]["text"]
    # Clean potential markdown wrapping
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]

    analysis = json.loads(text)
    return analysis

# --- Creator Auto-Discovery ---

def discover_creators(new_posts, sources):
    """Find new creators from keyword/hashtag searches and add them as sources."""
    existing_handles = {
        s["handle"].lstrip("@").lower()
        for s in sources["sources"]
        if s["type"] == "account"
    }

    discovered = []
    for post in new_posts:
        if post["source_type"] in ("keyword", "hashtag") and post["views"] > 100000:
            handle = post["creator_handle"].lower()
            if handle and handle not in existing_handles:
                new_source = {
                    "type": "account",
                    "platform": post["platform"],
                    "handle": f"@{handle}",
                    "min_views": 50000,
                    "active": True,
                    "auto_discovered": True,
                    "discovered_from": post["url"],
                    "discovered_at": datetime.now(timezone.utc).isoformat()
                }
                sources["sources"].append(new_source)
                existing_handles.add(handle)
                discovered.append(new_source)
                print(f"  Auto-discovered creator: @{handle} ({post['platform']})")

    return discovered

# --- Main Scout Flow ---

def run_scout(workspace):
    print("\n  ,;;,")
    print(" ( o o)  CrabEgg Scout: Starting content discovery...")
    print("/'   '\\")
    print()

    api_config, sources, brand, library = load_config(workspace)
    apify_key = api_config.get("apify_api_key", "")
    anthropic_key = api_config.get("anthropic_api_key", "")

    if not apify_key:
        print("ERROR: No Apify API key found in api-config.json")
        return
    if not anthropic_key:
        print("ERROR: No Anthropic API key found in api-config.json")
        return

    active_sources = [s for s in sources["sources"] if s.get("active", True)]
    print(f"  Processing {len(active_sources)} active sources...")

    all_new_posts = []
    scrape_log = []

    for i, source in enumerate(active_sources):
        actor_key = (source["platform"], source["type"])
        actor_id = ACTOR_MAP.get(actor_key)

        if not actor_id:
            print(f"  Skipping unknown source type: {actor_key}")
            continue

        source_label = source.get("handle") or source.get("query") or source.get("tag", "unknown")
        print(f"\n  [{i+1}/{len(active_sources)}] Scraping {source['platform']}/{source['type']}: {source_label}")

        try:
            input_data = build_apify_input(source)
            raw_results = run_apify_actor(apify_key, actor_id, input_data)

            # Normalize
            posts = [normalize_post(r, source) for r in raw_results]

            # Filter by min_views
            min_views = source.get("min_views", 0)
            posts = [p for p in posts if p["views"] >= min_views]

            # Dedup
            new_posts = [p for p in posts if not is_duplicate(p, library)]

            print(f"  Found {len(raw_results)} posts → {len(posts)} above threshold → {len(new_posts)} new")

            # Analyze each new post
            for j, post in enumerate(new_posts):
                print(f"    Analyzing post {j+1}/{len(new_posts)}...")
                try:
                    analysis = analyze_post(post, brand, anthropic_key)
                    post["analysis"] = analysis
                    post["adapted"] = False
                    all_new_posts.append(post)
                except Exception as e:
                    print(f"    Analysis failed: {e}")

            scrape_log.append({
                "source": source_label,
                "platform": source["platform"],
                "type": source["type"],
                "total_found": len(raw_results),
                "above_threshold": len(posts),
                "new_posts": len(new_posts),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        except Exception as e:
            print(f"  Error scraping {source_label}: {e}")
            scrape_log.append({
                "source": source_label,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

    # Auto-discover creators
    print("\n  Checking for new creators to auto-discover...")
    discovered = discover_creators(all_new_posts, sources)
    if discovered:
        save_json(os.path.join(workspace, 'data', 'scraping-sources.json'), sources)
        print(f"  Added {len(discovered)} new creators to watch list")

    # Save to viral library
    library["posts"].extend(all_new_posts)
    library["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_json(os.path.join(workspace, 'data', 'viral-library.json'), library)

    # Save scrape log
    log_path = os.path.join(workspace, 'logs', 'scrape-log.json')
    existing_log = load_json(log_path) if os.path.exists(log_path) else []
    existing_log.extend(scrape_log)
    save_json(log_path, existing_log)

    # Summary
    print(f"\n  ,;;,")
    print(f" ( o o)  Scout complete!")
    print(f"/'   '\\")
    print(f"  {len(all_new_posts)} new viral posts added to library")
    print(f"  {len(discovered)} new creators auto-discovered")
    print(f"  Library now has {len(library['posts'])} total posts")
    print()

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    run_scout(workspace)
