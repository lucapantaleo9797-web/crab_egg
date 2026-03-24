# Apify Actor Reference

Actor IDs, input schemas, and response field mappings for all scrapers used by CrabEgg.

---

## TikTok Profile Scraper

**Actor ID**: `clockworks/tiktok-profile-scraper`

### Input Schema
```json
{
  "profiles": ["@handle1", "@handle2"],
  "resultsPerPage": 30,
  "shouldDownloadVideos": false,
  "shouldDownloadCovers": false,
  "shouldDownloadSubtitles": false
}
```

### Response Fields → CrabEgg Mapping
| Apify Field | CrabEgg Field | Notes |
|-------------|--------------|-------|
| `id` | `external_id` | TikTok post ID |
| `webVideoUrl` | `url` | Full post URL |
| `text` | `caption` | Post caption/text |
| `diggCount` | `likes` | |
| `shareCount` | `shares` | |
| `commentCount` | `comments` | |
| `playCount` | `views` | **Use for min_views filter** |
| `createTimeISO` | `posted_at` | ISO timestamp |
| `authorMeta.name` | `creator_handle` | |
| `authorMeta.nickName` | `creator_name` | |
| `videoMeta.duration` | `duration_seconds` | |
| `covers.default` | `thumbnail_url` | |

---

## TikTok Hashtag Scraper

**Actor ID**: `clockworks/tiktok-hashtag-scraper`

### Input Schema
```json
{
  "hashtags": ["peptides", "biohacking"],
  "resultsPerPage": 50,
  "shouldDownloadVideos": false
}
```

Response fields: same mapping as profile scraper.

---

## TikTok Search Scraper

**Actor ID**: `clockworks/tiktok-scraper`

### Input Schema
```json
{
  "searchQueries": ["peptides benefits", "korean skincare routine"],
  "resultsPerPage": 30,
  "searchSection": "video",
  "shouldDownloadVideos": false
}
```

Response fields: same mapping as profile scraper.

---

## Instagram Profile Scraper

**Actor ID**: `apify/instagram-profile-scraper`

### Input Schema
```json
{
  "usernames": ["handle1", "handle2"],
  "resultsLimit": 30
}
```

### Response Fields → CrabEgg Mapping
| Apify Field | CrabEgg Field | Notes |
|-------------|--------------|-------|
| `id` | `external_id` | Instagram post ID |
| `url` | `url` | Full post URL |
| `caption` | `caption` | |
| `likesCount` | `likes` | |
| `commentsCount` | `comments` | |
| `videoViewCount` | `views` | **Use for min_views filter** (video posts) |
| `timestamp` | `posted_at` | Unix timestamp → convert to ISO |
| `ownerUsername` | `creator_handle` | |
| `ownerFullName` | `creator_name` | |
| `videoDuration` | `duration_seconds` | |
| `displayUrl` | `thumbnail_url` | |
| `type` | `content_type` | "Video", "Image", "Sidecar" |

**Note**: For image posts, use `likesCount` as proxy for `views` since Instagram
doesn't expose view counts for images.

---

## Instagram Hashtag Scraper

**Actor ID**: `apify/instagram-hashtag-scraper`

### Input Schema
```json
{
  "hashtags": ["peptides", "biohacking"],
  "resultsLimit": 50
}
```

Response fields: same mapping as Instagram profile scraper.

---

## Normalized Post Schema

All scraped posts are normalized into this format before analysis:

```json
{
  "external_id": "string",
  "platform": "tiktok|instagram",
  "url": "string",
  "caption": "string",
  "creator_handle": "string",
  "creator_name": "string",
  "views": 0,
  "likes": 0,
  "comments": 0,
  "shares": 0,
  "duration_seconds": 0,
  "posted_at": "ISO-8601",
  "thumbnail_url": "string",
  "content_type": "video|image|carousel",
  "source_type": "account|keyword|hashtag",
  "source_query": "string",
  "scraped_at": "ISO-8601"
}
```

---

## Rate Limits & Best Practices

- **Apify concurrency**: Max 1 actor run at a time on free plan, 5 on paid
- **Results per run**: Keep under 100 to avoid timeout
- **Polling interval**: Check status every 10 seconds
- **Retry on failure**: Max 3 retries with 30s/60s/120s backoff
- **Dedup strategy**: Check `url` field against existing viral-library entries
- **Cost per run**: ~$0.10-0.50 depending on results volume
