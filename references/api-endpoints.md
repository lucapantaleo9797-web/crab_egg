# API Endpoints Reference

Complete API reference for all services used by CrabEgg.

## Table of Contents
1. [Apify](#apify)
2. [Anthropic (Claude)](#anthropic)
3. [ElevenLabs](#elevenlabs)
4. [Creatify](#creatify)
5. [Higgsfield](#higgsfield)
6. [Shopify](#shopify)
7. [Spotify](#spotify)
8. [Stripe](#stripe)

---

## Apify

Base URL: `https://api.apify.com/v2`

### Run an Actor
```
POST /acts/{actorId}/runs
Headers:
  Authorization: Bearer {APIFY_API_KEY}
Body:
  { "input": { ... } }
Response:
  { "data": { "id": "run-id", "status": "RUNNING" } }
```

### Get Run Results
```
GET /actor-runs/{runId}/dataset/items
Headers:
  Authorization: Bearer {APIFY_API_KEY}
Response:
  [ { ...post data... }, ... ]
```

### Polling Pattern
Poll `GET /actor-runs/{runId}` every 10 seconds.
Status values: READY, RUNNING, SUCCEEDED, FAILED, TIMED-OUT, ABORTED

---

## Anthropic

Base URL: `https://api.anthropic.com/v1`

### Create Message (for content analysis + script generation)
```
POST /messages
Headers:
  x-api-key: {ANTHROPIC_API_KEY}
  anthropic-version: 2023-06-01
  content-type: application/json
Body:
  {
    "model": "claude-haiku-4-5-20251001",   // for analysis
    // OR "claude-sonnet-4-6"               // for script generation
    "max_tokens": 4096,
    "messages": [
      {"role": "user", "content": "..."}
    ]
  }
Response:
  {
    "content": [{"type": "text", "text": "..."}]
  }
```

### Model Selection
- **Analysis (Phase 3)**: Use `claude-haiku-4-5-20251001` — fast, cheap, good for scoring
- **Script Generation (Phase 4)**: Use `claude-sonnet-4-6` — better creative quality
- **Architect tasks**: Use `claude-opus-4-6` — only for meta-level changes

### Cost Estimates
- Haiku: ~$0.001 per analysis call (~50 posts = $0.05)
- Sonnet: ~$0.01 per script generation call
- Opus: ~$0.05 per architect call

---

## ElevenLabs

Base URL: `https://api.elevenlabs.io/v1`

### Text to Speech (with timestamps)
```
POST /text-to-speech/{voice_id}/with-timestamps
Headers:
  xi-api-key: {ELEVENLABS_API_KEY}
  content-type: application/json
Body:
  {
    "text": "The voiceover script...",
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
      "stability": 0.5,
      "similarity_boost": 0.75,
      "style": 0.5,
      "use_speaker_boost": true
    },
    "output_format": "mp3_44100_128"
  }
Response:
  {
    "audio_base64": "...",
    "alignment": {
      "characters": ["T","h","e",...],
      "character_start_times_seconds": [0.0, 0.05, ...],
      "character_end_times_seconds": [0.05, 0.1, ...]
    }
  }
```

### List Voices
```
GET /voices
Headers:
  xi-api-key: {ELEVENLABS_API_KEY}
```

### Clone Voice
```
POST /voices/add
Headers:
  xi-api-key: {ELEVENLABS_API_KEY}
Body (multipart/form-data):
  name: "Brand Voice"
  files: [audio_sample.mp3]
  description: "Brand voice clone"
```

---

## Creatify

Base URL: `https://api.creatify.ai/api`

### Create Talking Head Video (Aurora)
```
POST /lipsyncs/
Headers:
  X-API-ID: {CREATIFY_API_ID}
  X-API-KEY: {CREATIFY_API_KEY}
Body:
  {
    "text": "voiceover text",
    "creator": "avatar_id",
    "audio_url": "https://...",    // ElevenLabs output URL
    "aspect_ratio": "9:16"         // vertical for short-form
  }
Response:
  { "id": "render-id", "status": "pending" }
```

### Check Render Status
```
GET /lipsyncs/{render_id}/
Headers:
  X-API-ID: {CREATIFY_API_ID}
  X-API-KEY: {CREATIFY_API_KEY}
Response:
  { "status": "done", "output": "https://video-url.mp4" }
```

### Polling Pattern
Poll every 30 seconds. Status values: pending, processing, done, failed.
Typical render time: 2-5 minutes for 60s video.

---

## Higgsfield

Base URL: `https://api.higgsfield.ai/v1`

### Generate AI Still (Nano Banana 2)
```
POST /generations
Headers:
  Authorization: Bearer {HIGGSFIELD_API_KEY}
Body:
  {
    "model": "nano-banana-2",
    "prompt": "...",
    "aspect_ratio": "9:16",
    "num_images": 1
  }
Response:
  { "id": "gen-id", "status": "processing" }
```

### Generate AI Video (Kling 3.0)
```
POST /generations
Headers:
  Authorization: Bearer {HIGGSFIELD_API_KEY}
Body:
  {
    "model": "kling-3.0",
    "prompt": "...",
    "image_url": "https://...",    // from Nano Banana 2 output
    "duration": 5,                  // seconds
    "aspect_ratio": "9:16"
  }
Response:
  { "id": "gen-id", "status": "processing" }
```

### Check Generation Status
```
GET /generations/{gen_id}
Headers:
  Authorization: Bearer {HIGGSFIELD_API_KEY}
Response:
  {
    "status": "completed",
    "output_url": "https://...",
    "thumbnail_url": "https://..."
  }
```

### Polling Pattern
Poll every 15 seconds. Status: processing, completed, failed.
Stills: ~30 seconds. Videos: ~2-5 minutes.

---

## Shopify

Base URL: `https://{store}.myshopify.com/admin/api/2024-01`

### Get Products
```
GET /products.json
Headers:
  X-Shopify-Access-Token: {SHOPIFY_ACCESS_TOKEN}
```

### Create Product
```
POST /products.json
Headers:
  X-Shopify-Access-Token: {SHOPIFY_ACCESS_TOKEN}
Body:
  {
    "product": {
      "title": "...",
      "body_html": "...",
      "vendor": "...",
      "product_type": "...",
      "variants": [
        { "price": "29.99", "sku": "..." }
      ]
    }
  }
```

### Storefront API (for checkout links)
```
POST https://{store}.myshopify.com/api/2024-01/graphql.json
Headers:
  X-Shopify-Storefront-Access-Token: {STOREFRONT_TOKEN}
Body:
  {
    "query": "mutation { checkoutCreate(input: { lineItems: [{ variantId: \"...\", quantity: 1 }] }) { checkout { webUrl } } }"
  }
```

---

## Spotify

Base URL: `https://api.spotify.com/v1`

### Get Access Token
```
POST https://accounts.spotify.com/api/token
Headers:
  Content-Type: application/x-www-form-urlencoded
Body:
  grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}
Response:
  { "access_token": "...", "token_type": "Bearer", "expires_in": 3600 }
```

### Search Podcasts
```
GET /search?q={keywords}&type=show&market=US&limit=10
Headers:
  Authorization: Bearer {ACCESS_TOKEN}
```

### Get Show Episodes
```
GET /shows/{show_id}/episodes?limit=10
Headers:
  Authorization: Bearer {ACCESS_TOKEN}
```

### Search Playlists
```
GET /search?q={keywords}&type=playlist&limit=10
Headers:
  Authorization: Bearer {ACCESS_TOKEN}
```

### Get Playlist Tracks
```
GET /playlists/{playlist_id}/tracks
Headers:
  Authorization: Bearer {ACCESS_TOKEN}
```

### Get Audio Features (for vibe matching)
```
GET /audio-features?ids={track_id_1},{track_id_2}
Headers:
  Authorization: Bearer {ACCESS_TOKEN}
Response:
  {
    "audio_features": [
      { "energy": 0.8, "valence": 0.6, "tempo": 120, "danceability": 0.7 }
    ]
  }
```

---

## Stripe

Base URL: `https://api.stripe.com/v1`

### Create Payment Link (for product attribution)
```
POST /payment_links
Headers:
  Authorization: Bearer {STRIPE_SECRET_KEY}
Body:
  {
    "line_items": [{"price": "price_xxx", "quantity": 1}],
    "metadata": {"content_id": "...", "builder_id": "..."}
  }
```

### Webhook Events
Listen for `checkout.session.completed` events.
Extract `metadata.content_id` for attribution tracking.

### Verify Webhook Signature
```python
import stripe
stripe.Webhook.construct_event(
    payload=request_body,
    sig_header=request.headers['Stripe-Signature'],
    secret=webhook_secret
)
```
