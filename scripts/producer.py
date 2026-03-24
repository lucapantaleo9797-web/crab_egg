#!/usr/bin/env python3
"""
CrabEgg Video Producer — Generates all video assets from approved scripts.
ElevenLabs (audio) → Creatify (talking head) → Higgsfield (B-Roll)
"""

import json
import os
import sys
import time
import base64
import requests
from datetime import datetime, timezone

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def update_pipeline_status(workspace, vid_id, new_status):
    pipeline_path = os.path.join(workspace, 'data', 'content-pipeline.json')
    pipeline = load_json(pipeline_path)
    for entry in pipeline["entries"]:
        if entry["id"] == vid_id:
            entry["status"] = new_status
            entry["updated_at"] = datetime.now(timezone.utc).isoformat()
            break
    save_json(pipeline_path, pipeline)

# --- Step 1: ElevenLabs TTS ---

def generate_audio(voiceover, voice_id, api_key, output_dir, vid_id):
    """Generate speech audio with word-level timestamps."""
    print("  Step 1: Generating voiceover audio (ElevenLabs)...")

    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps",
        headers={
            "xi-api-key": api_key,
            "content-type": "application/json"
        },
        json={
            "text": voiceover.replace("[PAUSE]", "..."),
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.5,
                "use_speaker_boost": True
            },
            "output_format": "mp3_44100_128"
        },
        timeout=60
    )
    resp.raise_for_status()
    result = resp.json()

    # Save audio
    audio_path = os.path.join(output_dir, 'audio', f'{vid_id}.mp3')
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    audio_bytes = base64.b64decode(result["audio_base64"])
    with open(audio_path, 'wb') as f:
        f.write(audio_bytes)

    # Save timing
    timing_path = os.path.join(output_dir, 'audio', f'{vid_id}_timing.json')
    save_json(timing_path, result.get("alignment", {}))

    print(f"    Audio saved: {audio_path}")
    print(f"    Timing saved: {timing_path}")

    return audio_path, timing_path

# --- Step 2: Creatify Talking Head ---

def generate_talking_head(audio_path, avatar_url, creatify_id, creatify_key, output_dir, vid_id, voiceover):
    """Generate lip-synced talking head video with Creatify Aurora."""
    print("  Step 2: Generating talking head video (Creatify Aurora)...")

    # Upload audio and start render
    resp = requests.post(
        "https://api.creatify.ai/api/lipsyncs/",
        headers={
            "X-API-ID": creatify_id,
            "X-API-KEY": creatify_key,
            "content-type": "application/json"
        },
        json={
            "text": voiceover.replace("[PAUSE]", "..."),
            "creator": avatar_url,
            "aspect_ratio": "9:16"
        },
        timeout=30
    )
    resp.raise_for_status()
    render_id = resp.json()["id"]
    print(f"    Render started: {render_id}")

    # Poll for completion
    for attempt in range(60):  # max 30 minutes
        time.sleep(30)
        status_resp = requests.get(
            f"https://api.creatify.ai/api/lipsyncs/{render_id}/",
            headers={
                "X-API-ID": creatify_id,
                "X-API-KEY": creatify_key
            },
            timeout=15
        )
        result = status_resp.json()
        status = result.get("status", "unknown")

        if status == "done":
            video_url = result["output"]
            # Download video
            video_path = os.path.join(output_dir, 'video', f'{vid_id}_talking_head.mp4')
            os.makedirs(os.path.dirname(video_path), exist_ok=True)
            video_resp = requests.get(video_url, timeout=120)
            with open(video_path, 'wb') as f:
                f.write(video_resp.content)
            print(f"    Talking head saved: {video_path}")
            return video_path

        elif status == "failed":
            print(f"    Render failed!")
            return None

        print(f"    Polling... ({status})")

    print("    Render timed out after 30 minutes")
    return None

# --- Step 3: Higgsfield B-Roll ---

def generate_broll_still(prompt, api_key, output_dir, vid_id, segment_num):
    """Generate AI still image with Higgsfield Nano Banana 2."""
    print(f"    Generating still for segment {segment_num} (Nano Banana 2)...")

    resp = requests.post(
        "https://api.higgsfield.ai/v1/generations",
        headers={
            "Authorization": f"Bearer {api_key}",
            "content-type": "application/json"
        },
        json={
            "model": "nano-banana-2",
            "prompt": prompt,
            "aspect_ratio": "9:16",
            "num_images": 1
        },
        timeout=30
    )
    resp.raise_for_status()
    gen_id = resp.json()["id"]

    # Poll
    for attempt in range(30):  # max 5 minutes
        time.sleep(10)
        status_resp = requests.get(
            f"https://api.higgsfield.ai/v1/generations/{gen_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15
        )
        result = status_resp.json()

        if result.get("status") == "completed":
            image_url = result["output_url"]
            image_path = os.path.join(output_dir, 'video', f'{vid_id}_broll_seg{segment_num}.png')
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            img_resp = requests.get(image_url, timeout=60)
            with open(image_path, 'wb') as f:
                f.write(img_resp.content)
            print(f"      Still saved: {image_path}")
            return image_path, image_url

        elif result.get("status") == "failed":
            print(f"      Still generation failed")
            return None, None

    print(f"      Still generation timed out")
    return None, None

def generate_broll_video(prompt, image_url, api_key, output_dir, vid_id, segment_num, duration=5):
    """Generate AI video clip with Higgsfield Kling 3.0."""
    print(f"    Generating video for segment {segment_num} (Kling 3.0)...")

    resp = requests.post(
        "https://api.higgsfield.ai/v1/generations",
        headers={
            "Authorization": f"Bearer {api_key}",
            "content-type": "application/json"
        },
        json={
            "model": "kling-3.0",
            "prompt": prompt,
            "image_url": image_url,
            "duration": duration,
            "aspect_ratio": "9:16"
        },
        timeout=30
    )
    resp.raise_for_status()
    gen_id = resp.json()["id"]

    # Poll
    for attempt in range(60):  # max 10 minutes
        time.sleep(10)
        status_resp = requests.get(
            f"https://api.higgsfield.ai/v1/generations/{gen_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15
        )
        result = status_resp.json()

        if result.get("status") == "completed":
            video_url = result["output_url"]
            video_path = os.path.join(output_dir, 'video', f'{vid_id}_broll_seg{segment_num}.mp4')
            vid_resp = requests.get(video_url, timeout=120)
            with open(video_path, 'wb') as f:
                f.write(vid_resp.content)
            print(f"      Video saved: {video_path}")
            return video_path

        elif result.get("status") == "failed":
            print(f"      Video generation failed")
            return None

    print(f"      Video generation timed out")
    return None

def process_broll_segments(segments, api_key, output_dir, vid_id):
    """Process all B-Roll segments."""
    print("  Step 3: Generating B-Roll assets (Higgsfield)...")
    results = []

    for seg in segments:
        seg_num = seg.get("segment_number", 0)
        seg_type = seg.get("type", "")

        if seg_type == "talking-head":
            print(f"    Segment {seg_num}: talking-head (covered by Creatify)")
            results.append({"segment": seg_num, "type": "talking-head", "status": "complete"})

        elif seg_type == "personal":
            print(f"    Segment {seg_num}: personal footage (flagged for user)")
            results.append({"segment": seg_num, "type": "personal", "status": "pending_user"})

        elif seg_type == "ai-still":
            image_path, _ = generate_broll_still(
                seg.get("ai_prompt", seg.get("visual_description", "")),
                api_key, output_dir, vid_id, seg_num
            )
            results.append({
                "segment": seg_num,
                "type": "ai-still",
                "status": "complete" if image_path else "failed",
                "asset_path": image_path
            })

        elif seg_type == "ai-video":
            # First generate the still frame
            duration = seg.get("timestamp_end", 0) - seg.get("timestamp_start", 0)
            image_path, image_url = generate_broll_still(
                seg.get("ai_prompt", seg.get("visual_description", "")),
                api_key, output_dir, vid_id, seg_num
            )
            if image_url:
                video_path = generate_broll_video(
                    seg.get("ai_prompt", ""),
                    image_url, api_key, output_dir, vid_id, seg_num,
                    duration=min(int(duration), 10)
                )
                results.append({
                    "segment": seg_num,
                    "type": "ai-video",
                    "status": "complete" if video_path else "failed",
                    "still_path": image_path,
                    "video_path": video_path
                })
            else:
                results.append({"segment": seg_num, "type": "ai-video", "status": "failed"})

    return results

# --- Main Producer Flow ---

def run_producer(workspace, vid_id=None):
    print("\n  ,;;,")
    print(" ( o o)  CrabEgg Producer: Building video assets...")
    print("/'   '\\")
    print()

    api_config = load_json(os.path.join(workspace, 'data', 'api-config.json'))
    brand = load_json(os.path.join(workspace, 'data', 'brand-profile.json'))
    pipeline = load_json(os.path.join(workspace, 'data', 'content-pipeline.json'))

    # Find approved script
    approved = [e for e in pipeline["entries"] if e["status"] == "approved"]
    if vid_id:
        approved = [e for e in approved if e["id"] == vid_id]

    if not approved:
        print("  No approved scripts found. Approve a script first!")
        return

    entry = approved[0]
    vid_id = entry["id"]
    script = entry["script"]
    output_dir = os.path.join(workspace, 'output')

    print(f"  Processing: {vid_id} — {script.get('title', 'Untitled')}")
    print(f"  Segments: {len(script.get('broll_segments', []))}")
    print()

    # Step 1: Audio
    el_key = api_config.get("elevenlabs_api_key", "")
    voice_id = brand.get("voice_id", "")
    if el_key and voice_id:
        try:
            audio_path, timing_path = generate_audio(
                script["voiceover"], voice_id, el_key, output_dir, vid_id
            )
            update_pipeline_status(workspace, vid_id, "audio_done")
        except Exception as e:
            print(f"    Audio generation failed: {e}")
            audio_path = None
    else:
        print("  Skipping audio: missing ElevenLabs key or voice_id")
        audio_path = None

    # Step 2: Talking Head
    creatify_id = api_config.get("creatify_api_id", "")
    creatify_key = api_config.get("creatify_api_key", "")
    avatar_url = brand.get("avatar_url", "")
    if creatify_id and creatify_key and avatar_url:
        try:
            talking_head_path = generate_talking_head(
                audio_path, avatar_url, creatify_id, creatify_key,
                output_dir, vid_id, script["voiceover"]
            )
            update_pipeline_status(workspace, vid_id, "avatar_done")
        except Exception as e:
            print(f"    Talking head generation failed: {e}")
    else:
        print("  Skipping talking head: missing Creatify credentials or avatar")

    # Step 3: B-Roll
    hf_key = api_config.get("higgsfield_api_key", "")
    if hf_key:
        try:
            broll_segments = [s for s in script.get("broll_segments", [])
                            if s.get("type") in ("ai-still", "ai-video")]
            if broll_segments:
                broll_results = process_broll_segments(
                    broll_segments, hf_key, output_dir, vid_id
                )
                update_pipeline_status(workspace, vid_id, "broll_done")

                # Log results
                log_path = os.path.join(workspace, 'logs', 'production-log.json')
                existing_log = load_json(log_path) if os.path.exists(log_path) else []
                existing_log.append({
                    "vid_id": vid_id,
                    "broll_results": broll_results,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                save_json(log_path, existing_log)
        except Exception as e:
            print(f"    B-Roll generation failed: {e}")
    else:
        print("  Skipping B-Roll: missing Higgsfield API key")

    # Final status
    update_pipeline_status(workspace, vid_id, "review")

    # Summary
    print(f"\n  ,;;,")
    print(f" ( o o)  Production complete for {vid_id}!")
    print(f"/'   '\\")
    print(f"  Status: REVIEW")
    print(f"  Audio: {'output/audio/' + vid_id + '.mp3' if audio_path else 'skipped'}")
    print(f"  Assets in: output/video/")
    print(f"\n  Review the output and approve for posting.")
    print()

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    vid = sys.argv[2] if len(sys.argv) > 2 else None
    run_producer(workspace, vid)
