#!/usr/bin/env python3
"""
CrabEgg Script Writer — Generates branded video scripts from viral posts.
Uses Claude Sonnet to create full scripts with B-Roll markers.
"""

import json
import os
import sys
import requests
from datetime import datetime, timezone

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

# --- Post Selection ---

def get_best_unadapted_post(library, top_n=5):
    """Get the highest-scored unadapted posts."""
    unadapted = [p for p in library["posts"] if not p.get("adapted", False) and "analysis" in p]

    # Sort by viral_score
    unadapted.sort(
        key=lambda p: p["analysis"].get("viral_score", 0),
        reverse=True
    )

    return unadapted[:top_n]

def display_candidates(candidates):
    """Display top candidates for user selection."""
    print("\n  Top viral posts ready for adaptation:\n")
    for i, post in enumerate(candidates):
        a = post["analysis"]
        print(f"  [{i+1}] {a.get('title', 'Untitled')}")
        print(f"      Score: {a.get('viral_score', '?')}/10 | {post['platform']} | {post['views']:,} views")
        print(f"      Hook: {a.get('hook', 'N/A')[:80]}...")
        print(f"      Theme: {a.get('theme', 'N/A')} | Format: {a.get('content_format', 'N/A')}")
        print(f"      Idea: {a.get('adaptation_idea', 'N/A')[:100]}...")
        print()

    return candidates

# --- Script Generation ---

def build_script_prompt(brand, post, spotify_data=None, revision_feedback=None, previous_script=None):
    """Assemble the full script generation prompt."""

    analysis = post["analysis"]
    th_pct = brand.get("content_split", {}).get("talking_head", 60)
    br_pct = brand.get("content_split", {}).get("broll", 40)

    prompt = f"""Write a short-form video script for {brand['name']}.

BRAND CONTEXT:
- Product: {brand['name']} — {brand.get('pitch', '')}
- Price: {brand.get('price', 'N/A')}
- Voice: {brand.get('voice', 'casual-fun')}
- Audience: {json.dumps(brand.get('audience', {}))}
- Language: {brand.get('language', 'English')}
- B-Roll Style: {brand.get('broll_style', 'cinematic')}
- Content Split: {th_pct}% talking head / {br_pct}% B-Roll

VIRAL INSPIRATION:
This script is adapted from a viral {post['platform']} post:
- Title: {analysis.get('title', '')}
- Hook: {analysis.get('hook', '')}
- Hook Type: {analysis.get('hook_type', '')}
- Theme: {analysis.get('theme', '')}
- Why it went viral: {analysis.get('why_viral', '')}
- Adaptation idea: {analysis.get('adaptation_idea', '')}
- Original format: {analysis.get('content_format', '')}
"""

    if spotify_data and spotify_data.get("brand_audio_profile"):
        profile = spotify_data["brand_audio_profile"]
        prompt += f"""
MUSIC/VIBE CONTEXT:
- Brand playlist vibe: {brand.get('music_genre', 'ambient')} (energy: {profile.get('energy', 0.5):.1f}, tempo: {profile.get('tempo', 120):.0f} BPM)
- Consider pacing the script to match this energy level
"""

    if revision_feedback:
        prompt += f"""
REVISION REQUEST:
The previous version was rejected with this feedback:
"{revision_feedback}"

Please address this feedback while keeping what worked.
Previous script for reference:
{json.dumps(previous_script, indent=2)}
"""

    prompt += f"""
Generate a complete video script as JSON with these fields:
{{
  "title": "Video title (catchy, max 60 chars)",
  "hook": "The exact opening line",
  "voiceover": "Full voiceover script with [PAUSE] markers. ~45 seconds when read aloud.",
  "estimated_length_seconds": 45,
  "broll_segments": [
    {{
      "segment_number": 1,
      "timestamp_start": 0.0,
      "timestamp_end": 3.0,
      "type": "talking-head",
      "voiceover_excerpt": "Words spoken during this segment",
      "visual_description": "What the viewer sees",
      "ai_prompt": "For ai-video/ai-still types: detailed generation prompt",
      "camera_direction": "Cinematic direction"
    }}
  ],
  "music_suggestion": "Background music mood and tempo",
  "hashtags": ["#relevant", "#hashtags"],
  "cta": "Call-to-action text",
  "caption": "Post caption with hashtags and CTA",
  "thumbnail_concept": "Thumbnail image description"
}}

RULES:
1. Hook MUST be adapted from the viral inspiration but original for {brand['name']}
2. Every segment needs a clear type: talking-head, ai-video, ai-still, or personal
3. Voiceover must sound natural, not scripted
4. Include at least one pattern interrupt
5. CTA must reference {brand['name']} and create urgency
6. Segments must cover full duration with no gaps
7. ai_prompt fields must be 50+ words for quality generation
8. Respect content split: ~{th_pct}% talking-head, ~{br_pct}% other types

Respond ONLY with valid JSON. No markdown wrapping."""

    return prompt

def generate_script(prompt, api_key):
    """Call Claude Sonnet to generate the script."""

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 4096,
            "system": "You are an expert short-form video scriptwriter. Respond ONLY in valid JSON.",
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=60
    )
    resp.raise_for_status()

    text = resp.json()["content"][0]["text"].strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]

    return json.loads(text)

# --- Script Validation ---

def validate_script(script):
    """Validate the generated script structure."""
    errors = []

    required_fields = ["title", "hook", "voiceover", "broll_segments", "cta"]
    for field in required_fields:
        if field not in script:
            errors.append(f"Missing required field: {field}")

    segments = script.get("broll_segments", [])
    if not segments:
        errors.append("No B-Roll segments defined")

    valid_types = {"talking-head", "ai-video", "ai-still", "personal"}
    for seg in segments:
        if seg.get("type") not in valid_types:
            errors.append(f"Segment {seg.get('segment_number', '?')}: invalid type '{seg.get('type')}'")
        if seg.get("type") in ("ai-video", "ai-still") and len(seg.get("ai_prompt", "")) < 20:
            errors.append(f"Segment {seg.get('segment_number', '?')}: ai_prompt too short")

    # Check for timestamp gaps
    for i in range(len(segments) - 1):
        end = segments[i].get("timestamp_end", 0)
        start = segments[i + 1].get("timestamp_start", 0)
        if abs(end - start) > 0.5:
            errors.append(f"Gap between segment {i+1} and {i+2}: {end}s to {start}s")

    return errors

# --- Pipeline Management ---

def save_to_pipeline(workspace, script, post, status="draft"):
    """Save script to content pipeline."""
    pipeline_path = os.path.join(workspace, 'data', 'content-pipeline.json')

    if os.path.exists(pipeline_path):
        pipeline = load_json(pipeline_path)
    else:
        pipeline = {"entries": []}

    entry = {
        "id": f"vid_{len(pipeline['entries']) + 1:03d}",
        "script": script,
        "source_post_url": post["url"],
        "source_post_platform": post["platform"],
        "status": status,
        "revision_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    pipeline["entries"].append(entry)
    save_json(pipeline_path, pipeline)

    return entry["id"]

def mark_post_adapted(workspace, post_url):
    """Mark a viral post as adapted."""
    library_path = os.path.join(workspace, 'data', 'viral-library.json')
    library = load_json(library_path)

    for p in library["posts"]:
        if p["url"] == post_url:
            p["adapted"] = True
            p["adapted_at"] = datetime.now(timezone.utc).isoformat()
            break

    save_json(library_path, library)

# --- Main Writer Flow ---

def run_writer(workspace, post_index=None):
    print("\n  ,;;,")
    print(" ( o o)  CrabEgg Writer: Generating branded script...")
    print("/'   '\\")
    print()

    api_config = load_json(os.path.join(workspace, 'data', 'api-config.json'))
    brand = load_json(os.path.join(workspace, 'data', 'brand-profile.json'))
    library = load_json(os.path.join(workspace, 'data', 'viral-library.json'))

    anthropic_key = api_config.get("anthropic_api_key", "")
    if not anthropic_key:
        print("ERROR: No Anthropic API key found")
        return

    # Load Spotify data if available
    spotify_path = os.path.join(workspace, 'data', 'spotify-cache.json')
    spotify_data = load_json(spotify_path) if os.path.exists(spotify_path) else None

    # Get candidates
    candidates = get_best_unadapted_post(library)
    if not candidates:
        print("  No unadapted posts available. Run the scout first!")
        return

    display_candidates(candidates)

    # Select post
    if post_index is not None and 0 <= post_index < len(candidates):
        selected = candidates[post_index]
    else:
        selected = candidates[0]  # Auto-select top post

    print(f"  Selected: {selected['analysis'].get('title', 'Untitled')}")
    print(f"  Generating script with Claude Sonnet...\n")

    # Generate
    prompt = build_script_prompt(brand, selected, spotify_data)
    script = generate_script(prompt, anthropic_key)

    # Validate
    errors = validate_script(script)
    if errors:
        print("  Validation warnings:")
        for e in errors:
            print(f"    - {e}")
        print("  Attempting regeneration...")
        script = generate_script(prompt + "\n\nPrevious attempt had validation errors. Please fix: " + "; ".join(errors), anthropic_key)

    # Save
    vid_id = save_to_pipeline(workspace, script, selected, status="draft")

    # Also save the raw script for easy reading
    script_path = os.path.join(workspace, 'output', 'scripts', f'{vid_id}.json')
    save_json(script_path, script)

    # Display
    print(f"\n  === GENERATED SCRIPT: {script.get('title', 'Untitled')} ===\n")
    print(f"  Hook: {script.get('hook', 'N/A')}")
    print(f"  Length: ~{script.get('estimated_length_seconds', '?')}s")
    print(f"  CTA: {script.get('cta', 'N/A')}")
    print(f"\n  Voiceover:")
    print(f"  {script.get('voiceover', 'N/A')[:500]}...")
    print(f"\n  B-Roll segments: {len(script.get('broll_segments', []))}")
    for seg in script.get("broll_segments", []):
        print(f"    [{seg.get('timestamp_start', 0):.1f}s-{seg.get('timestamp_end', 0):.1f}s] {seg.get('type', '?')}: {seg.get('visual_description', 'N/A')[:60]}")

    print(f"\n  Saved as {vid_id} (status: draft)")
    print(f"  Script file: output/scripts/{vid_id}.json")
    print(f"\n  To approve: update status to 'approved' in content-pipeline.json")
    print(f"  To revise: re-run writer with feedback")

    return vid_id, script

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    post_idx = int(sys.argv[2]) - 1 if len(sys.argv) > 2 else None
    run_writer(workspace, post_idx)
