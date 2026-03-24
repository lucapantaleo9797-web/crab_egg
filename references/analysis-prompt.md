# Content Analysis Prompt Template

This is the Claude Haiku prompt used to analyze each scraped viral post.
Inject the post data into the template and call Claude Haiku.

---

## System Prompt

```
You are a viral content analyst. You analyze social media posts to understand
WHY they went viral and HOW a brand could adapt the concept. You are precise,
specific, and always provide actionable adaptation ideas.

Respond ONLY in valid JSON. No markdown, no explanation, just the JSON object.
```

## User Prompt Template

```
Analyze this viral {{platform}} post:

CREATOR: {{creator_handle}} ({{creator_name}})
CAPTION: {{caption}}
VIEWS: {{views}}
LIKES: {{likes}}
COMMENTS: {{comments}}
SHARES: {{shares}}
DURATION: {{duration_seconds}}s
POSTED: {{posted_at}}
URL: {{url}}

The brand context:
NICHE: {{niche_keywords}}
PRODUCT: {{product_name}} — {{product_pitch}}
AUDIENCE: {{target_audience}}

Analyze this post and return JSON with these exact fields:

{
  "title": "A short descriptive title for this viral post (max 10 words)",
  "hook": "The exact hook/opening line or concept that grabs attention",
  "hook_type": "One of: question, bold-claim, story-open, shock-value, relatable, how-to, myth-bust, before-after, list, trend-ride",
  "theme": "The core theme/topic (e.g., 'morning routine', 'product review', 'transformation')",
  "why_viral": "2-3 sentences explaining specifically why this post performed well. Reference the hook, timing, trend, emotion, or format that drove engagement.",
  "adaptation_idea": "A specific, concrete idea for how {{product_name}} could adapt this concept. Not vague — describe the actual video concept, hook, and angle. 2-3 sentences.",
  "viral_score": 8,
  "content_format": "One of: talking-head, montage, tutorial, reaction, story, duet, trend, review, transformation",
  "estimated_production": "One of: low (phone + talking), medium (some editing/b-roll), high (heavy editing/effects)",
  "best_for": "One of: awareness, education, conversion, engagement"
}

The viral_score should be 1-10 based on:
- Views relative to creator's usual (if known): is this an outlier?
- Engagement rate (likes+comments+shares / views): >5% is strong
- Adaptability to {{product_name}}: how easily can this concept translate?
- Trend timing: is this riding a current trend or is it evergreen?

Score 8-10: Must adapt immediately
Score 5-7: Good candidate, add to library
Score 1-4: Low priority, skip unless nothing else
```

---

## Example Output

```json
{
  "title": "Peptide Morning Routine Shock Reveal",
  "hook": "I've been injecting peptides for 6 months and here's what happened to my face",
  "hook_type": "before-after",
  "theme": "transformation",
  "why_viral": "The before-after hook triggers immediate curiosity. The 6-month timeframe adds credibility. Peptides are trending in the biohacking niche, and the visual proof format drives saves and shares.",
  "adaptation_idea": "Create a similar before-after concept but focused on our specific peptide product. Open with a close-up face shot, reveal the product, then show 30/60/90 day progress photos. End with a CTA to try it with a discount code.",
  "viral_score": 9,
  "content_format": "transformation",
  "estimated_production": "medium",
  "best_for": "conversion"
}
```

---

## Batch Processing

When analyzing multiple posts, process them one at a time (separate API calls).
This keeps costs low (Haiku is cheap) and makes error handling simpler.

If a post fails analysis (malformed response), retry once. If it fails again,
skip it and log the error. Don't let one bad post block the entire batch.

## Validation

After parsing the JSON response, validate:
- `viral_score` is an integer 1-10
- `hook_type` is one of the allowed values
- `content_format` is one of the allowed values
- `adaptation_idea` is at least 50 characters (reject generic fluff)

If validation fails, retry with a note: "Your previous response had invalid fields.
Please ensure all fields match the specified options exactly."
