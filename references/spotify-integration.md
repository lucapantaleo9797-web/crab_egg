# Spotify Integration Reference

CrabEgg uses Spotify for two purposes:
1. **Podcast Discovery** — Find niche-relevant podcasts for content ideas
2. **Music Curation** — Build brand-aligned playlists for video background vibes

---

## Authentication

Spotify uses OAuth2 Client Credentials flow (no user login needed for search/read).

```python
import requests
import base64

def get_spotify_token(client_id, client_secret):
    auth_str = f"{client_id}:{client_secret}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={"grant_type": "client_credentials"}
    )
    return response.json()["access_token"]
```

Token expires after 3600 seconds. Cache it and refresh when expired.

---

## Podcast Discovery Flow

### Step 1: Search for Shows
```python
def search_podcasts(token, keywords, limit=10):
    query = " ".join(keywords)
    response = requests.get(
        f"https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": query, "type": "show", "market": "US", "limit": limit}
    )
    shows = response.json()["shows"]["items"]
    return [{
        "id": s["id"],
        "name": s["name"],
        "publisher": s["publisher"],
        "description": s["description"][:200],
        "total_episodes": s["total_episodes"],
        "url": s["external_urls"]["spotify"]
    } for s in shows]
```

### Step 2: Get Recent Episodes
```python
def get_recent_episodes(token, show_id, limit=5):
    response = requests.get(
        f"https://api.spotify.com/v1/shows/{show_id}/episodes",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": limit, "market": "US"}
    )
    episodes = response.json()["items"]
    return [{
        "id": e["id"],
        "name": e["name"],
        "description": e["description"][:300],
        "duration_ms": e["duration_ms"],
        "release_date": e["release_date"],
        "url": e["external_urls"]["spotify"]
    } for e in episodes]
```

### Step 3: Extract Content Ideas
Feed episode titles and descriptions to Claude Haiku:
```
Given these podcast episodes from the {{niche}} niche:
{{episode_list}}

Extract 5 content ideas that could be adapted into short-form video scripts.
For each idea, provide: topic, angle, why it would work as short-form content.
```

---

## Music Curation Flow

### Step 1: Analyze Brand Playlist
If the user provided a Spotify playlist URL:
```python
def analyze_playlist(token, playlist_id):
    # Get tracks
    tracks_resp = requests.get(
        f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 50}
    )
    track_ids = [t["track"]["id"] for t in tracks_resp.json()["items"] if t["track"]]

    # Get audio features
    features_resp = requests.get(
        f"https://api.spotify.com/v1/audio-features",
        headers={"Authorization": f"Bearer {token}"},
        params={"ids": ",".join(track_ids[:100])}
    )
    features = features_resp.json()["audio_features"]

    # Calculate averages
    avg = {
        "energy": sum(f["energy"] for f in features if f) / len(features),
        "valence": sum(f["valence"] for f in features if f) / len(features),
        "tempo": sum(f["tempo"] for f in features if f) / len(features),
        "danceability": sum(f["danceability"] for f in features if f) / len(features)
    }
    return avg
```

### Step 2: Find Similar Music for Videos
Use the brand's audio profile to search for background music:
```python
def find_brand_music(token, genre, energy_target, tempo_target):
    # Search by genre + mood
    response = requests.get(
        f"https://api.spotify.com/v1/recommendations",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "seed_genres": genre,
            "target_energy": energy_target,
            "target_tempo": tempo_target,
            "limit": 20
        }
    )
    return response.json()["tracks"]
```

### Step 3: Build Brand Playlist
Create a curated list of tracks that match the brand vibe.
Save to `data/spotify-cache.json`:
```json
{
  "brand_audio_profile": {
    "energy": 0.7,
    "valence": 0.6,
    "tempo": 120,
    "danceability": 0.65
  },
  "podcast_shows": [...],
  "content_ideas_from_podcasts": [...],
  "recommended_tracks": [...],
  "last_refreshed": "ISO-8601"
}
```

---

## Vibe Mapping

Use the audio profile to inform script generation:

| Energy | Valence | Vibe | Script Tone |
|--------|---------|------|-------------|
| High | High | Upbeat/party | Fast-paced, exciting, lots of cuts |
| High | Low | Intense/dark | Dramatic, bold claims, urgent |
| Low | High | Chill/happy | Warm, conversational, storytelling |
| Low | Low | Moody/reflective | Deep, educational, intimate |

Pass this vibe data into the script generation prompt for mood-aligned writing.

---

## Rate Limits

- Spotify API: 100 requests per 30 seconds per app
- Recommendations endpoint: same limit
- Batch track IDs in audio-features calls (max 100 per request)
- Cache aggressively — podcast data doesn't change minute-to-minute
