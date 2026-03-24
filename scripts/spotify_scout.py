#!/usr/bin/env python3
"""
CrabEgg Spotify Scout — Discovers niche podcasts and curates brand-aligned music.
Uses Spotify API for podcast discovery and audio feature analysis.
"""

import json
import os
import sys
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

# --- Authentication ---

def get_spotify_token(client_id, client_secret):
    auth_str = f"{client_id}:{client_secret}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()

    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={"grant_type": "client_credentials"},
        timeout=15
    )
    resp.raise_for_status()
    return resp.json()["access_token"]

# --- Podcast Discovery ---

def search_podcasts(token, keywords, limit=10):
    query = " ".join(keywords)
    resp = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": query, "type": "show", "market": "US", "limit": limit},
        timeout=15
    )
    resp.raise_for_status()
    shows = resp.json().get("shows", {}).get("items", [])
    return [{
        "id": s["id"],
        "name": s["name"],
        "publisher": s["publisher"],
        "description": s.get("description", "")[:200],
        "total_episodes": s["total_episodes"],
        "url": s["external_urls"]["spotify"]
    } for s in shows if s]

def get_recent_episodes(token, show_id, limit=5):
    resp = requests.get(
        f"https://api.spotify.com/v1/shows/{show_id}/episodes",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": limit, "market": "US"},
        timeout=15
    )
    resp.raise_for_status()
    episodes = resp.json().get("items", [])
    return [{
        "id": e["id"],
        "name": e["name"],
        "description": e.get("description", "")[:300],
        "duration_ms": e["duration_ms"],
        "release_date": e["release_date"],
        "url": e["external_urls"]["spotify"]
    } for e in episodes if e]

# --- Music Analysis ---

def analyze_playlist(token, playlist_id):
    """Analyze audio features of a brand playlist."""
    resp = requests.get(
        f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 50},
        timeout=15
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    track_ids = [t["track"]["id"] for t in items if t.get("track") and t["track"].get("id")]

    if not track_ids:
        return None

    # Get audio features in batches of 100
    features_resp = requests.get(
        "https://api.spotify.com/v1/audio-features",
        headers={"Authorization": f"Bearer {token}"},
        params={"ids": ",".join(track_ids[:100])},
        timeout=15
    )
    features_resp.raise_for_status()
    features = [f for f in features_resp.json().get("audio_features", []) if f]

    if not features:
        return None

    avg = {
        "energy": sum(f["energy"] for f in features) / len(features),
        "valence": sum(f["valence"] for f in features) / len(features),
        "tempo": sum(f["tempo"] for f in features) / len(features),
        "danceability": sum(f["danceability"] for f in features) / len(features),
        "acousticness": sum(f["acousticness"] for f in features) / len(features),
        "instrumentalness": sum(f["instrumentalness"] for f in features) / len(features)
    }
    return avg

def get_recommendations(token, genre, energy, tempo, limit=20):
    """Get music recommendations matching brand vibe."""
    resp = requests.get(
        "https://api.spotify.com/v1/recommendations",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "seed_genres": genre,
            "target_energy": energy,
            "target_tempo": tempo,
            "limit": limit
        },
        timeout=15
    )
    resp.raise_for_status()
    tracks = resp.json().get("tracks", [])
    return [{
        "id": t["id"],
        "name": t["name"],
        "artist": t["artists"][0]["name"] if t.get("artists") else "Unknown",
        "duration_ms": t["duration_ms"],
        "preview_url": t.get("preview_url"),
        "url": t["external_urls"]["spotify"]
    } for t in tracks]

# --- Vibe Mapping ---

def get_vibe_description(profile):
    """Map audio features to a vibe description for script generation."""
    energy = profile.get("energy", 0.5)
    valence = profile.get("valence", 0.5)

    if energy > 0.6 and valence > 0.6:
        return "upbeat-energetic"
    elif energy > 0.6 and valence <= 0.6:
        return "intense-dramatic"
    elif energy <= 0.6 and valence > 0.6:
        return "chill-warm"
    else:
        return "moody-reflective"

# --- Main Spotify Scout Flow ---

def run_spotify_scout(workspace):
    print("\n  ,;;,")
    print(" ( o o)  CrabEgg Spotify Scout: Discovering niche audio...")
    print("/'   '\\")
    print()

    api_config = load_json(os.path.join(workspace, 'data', 'api-config.json'))
    brand = load_json(os.path.join(workspace, 'data', 'brand-profile.json'))

    client_id = api_config.get("spotify_client_id", "")
    client_secret = api_config.get("spotify_client_secret", "")

    if not client_id or not client_secret:
        print("  No Spotify API credentials found. Skipping Spotify integration.")
        print("  Get credentials at: https://developer.spotify.com/dashboard")
        return

    # Authenticate
    print("  Authenticating with Spotify...")
    token = get_spotify_token(client_id, client_secret)

    spotify_cache = {
        "brand_audio_profile": None,
        "vibe": None,
        "podcast_shows": [],
        "content_ideas_from_podcasts": [],
        "recommended_tracks": [],
        "last_refreshed": datetime.now(timezone.utc).isoformat()
    }

    # Analyze brand playlist if provided
    playlist_url = brand.get("spotify_playlist", "")
    if playlist_url:
        playlist_id = playlist_url.split("/")[-1].split("?")[0]
        print(f"  Analyzing brand playlist: {playlist_id}")
        profile = analyze_playlist(token, playlist_id)
        if profile:
            spotify_cache["brand_audio_profile"] = profile
            spotify_cache["vibe"] = get_vibe_description(profile)
            print(f"    Energy: {profile['energy']:.2f} | Valence: {profile['valence']:.2f}")
            print(f"    Tempo: {profile['tempo']:.0f} BPM | Vibe: {spotify_cache['vibe']}")

    # Discover podcasts
    keywords = brand.get("niche_keywords", [])
    podcast_keywords = brand.get("podcast_keywords", keywords)
    if podcast_keywords:
        print(f"\n  Searching podcasts for: {', '.join(podcast_keywords)}")
        shows = search_podcasts(token, podcast_keywords)
        spotify_cache["podcast_shows"] = shows
        print(f"    Found {len(shows)} relevant shows")

        # Get recent episodes from top 3 shows
        all_episodes = []
        for show in shows[:3]:
            print(f"    Fetching episodes from: {show['name']}")
            episodes = get_recent_episodes(token, show["id"])
            all_episodes.extend(episodes)

        # Extract content ideas (titles/descriptions become content inspiration)
        content_ideas = []
        for ep in all_episodes[:10]:
            content_ideas.append({
                "source_show": next((s["name"] for s in shows if any(
                    e["id"] == ep["id"] for e in get_recent_episodes(token, s["id"])
                )), "Unknown"),
                "episode_title": ep["name"],
                "episode_description": ep["description"],
                "potential_angle": f"Adapt '{ep['name']}' into a short-form video about {brand['name']}",
                "url": ep["url"]
            })
        spotify_cache["content_ideas_from_podcasts"] = content_ideas

    # Get music recommendations
    genre = brand.get("music_genre", "ambient")
    energy = spotify_cache.get("brand_audio_profile", {}).get("energy", 0.5)
    tempo = spotify_cache.get("brand_audio_profile", {}).get("tempo", 120)
    print(f"\n  Finding background music ({genre}, energy={energy:.1f}, tempo={tempo:.0f})...")
    try:
        tracks = get_recommendations(token, genre, energy, tempo)
        spotify_cache["recommended_tracks"] = tracks
        print(f"    Found {len(tracks)} recommended tracks")
    except Exception as e:
        print(f"    Recommendation failed: {e}")

    # Save cache
    save_json(os.path.join(workspace, 'data', 'spotify-cache.json'), spotify_cache)

    # Summary
    print(f"\n  ,;;,")
    print(f" ( o o)  Spotify Scout complete!")
    print(f"/'   '\\")
    print(f"  Vibe: {spotify_cache.get('vibe', 'not analyzed')}")
    print(f"  Podcasts found: {len(spotify_cache['podcast_shows'])}")
    print(f"  Content ideas: {len(spotify_cache['content_ideas_from_podcasts'])}")
    print(f"  Music recommendations: {len(spotify_cache['recommended_tracks'])}")
    print()

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    run_spotify_scout(workspace)
