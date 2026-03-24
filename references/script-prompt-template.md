# Script Generation Prompt Template

This is the Claude Sonnet prompt used to generate branded video scripts.
Assemble from brand profile + viral post data + user preferences.

---

## System Prompt

```
You are an expert short-form video scriptwriter. You write scripts that:
- Hook viewers in the first 2 seconds
- Maintain attention through pattern interrupts every 5-7 seconds
- Drive a specific action (follow, click link, buy)
- Sound natural when read aloud (conversational, not corporate)
- Include precise B-Roll direction for video production

You write for {{brand_voice}} brands targeting {{target_audience}}.
Your primary language is {{language}}.

Respond ONLY in valid JSON. No markdown wrapping, no explanation.
```

## User Prompt Template

```
Write a short-form video script for {{product_name}}.

BRAND CONTEXT:
- Product: {{product_name}} — {{product_pitch}}
- Price: {{price}}
- Voice: {{brand_voice}}
- Audience: {{target_audience}}
- Language: {{language}}
- B-Roll Style: {{broll_style}}
- Content Split: {{talking_head_pct}}% talking head / {{broll_pct}}% B-Roll

VIRAL INSPIRATION:
This script is adapted from a viral {{platform}} post:
- Title: {{viral_title}}
- Hook: {{viral_hook}}
- Hook Type: {{viral_hook_type}}
- Theme: {{viral_theme}}
- Why it went viral: {{viral_why}}
- Adaptation idea: {{viral_adaptation_idea}}
- Original format: {{viral_content_format}}

{{#if spotify_suggestion}}
MUSIC/VIBE CONTEXT:
- Brand playlist vibe: {{spotify_genre}} (energy: {{spotify_energy}}, tempo: {{spotify_tempo}} BPM)
- Consider pacing the script to match this energy level
{{/if}}

{{#if revision_feedback}}
REVISION REQUEST:
The previous version was rejected with this feedback:
"{{revision_feedback}}"

Please address this feedback while keeping what worked.
Previous script for reference:
{{previous_script}}
{{/if}}

Generate a complete video script as JSON:

{
  "title": "Video title (catchy, SEO-friendly, max 60 chars)",
  "hook": "The exact opening line (must grab attention in <2 seconds)",
  "voiceover": "The full voiceover script. Write it as natural spoken text. Include [PAUSE] markers where the speaker should breathe or let a point land. Keep it {{target_length}} seconds when read aloud (~2.5 words per second).",
  "estimated_length_seconds": 45,
  "broll_segments": [
    {
      "segment_number": 1,
      "timestamp_start": 0.0,
      "timestamp_end": 3.0,
      "type": "talking-head",
      "voiceover_excerpt": "The words being spoken during this segment",
      "visual_description": "What the viewer sees",
      "camera_direction": "Close-up, eye contact, high energy"
    },
    {
      "segment_number": 2,
      "timestamp_start": 3.0,
      "timestamp_end": 7.0,
      "type": "ai-video",
      "voiceover_excerpt": "...",
      "visual_description": "...",
      "ai_prompt": "Detailed prompt for Higgsfield to generate this visual. Be specific about style, colors, movement, and mood. Reference the brand's B-Roll style: {{broll_style}}.",
      "camera_direction": "Slow zoom, cinematic lighting"
    },
    {
      "segment_number": 3,
      "timestamp_start": 7.0,
      "timestamp_end": 12.0,
      "type": "ai-still",
      "voiceover_excerpt": "...",
      "visual_description": "...",
      "ai_prompt": "Detailed prompt for Higgsfield Nano Banana 2 to generate this still image.",
      "camera_direction": "Static, centered"
    }
  ],
  "music_suggestion": "Describe the ideal background music mood and tempo",
  "hashtags": ["#relevant", "#hashtags", "#for", "#discovery"],
  "cta": "The specific call-to-action (e.g., 'Link in bio for 20% off')",
  "caption": "The post caption with hashtags and CTA. Optimized for {{platform}} algorithm.",
  "thumbnail_concept": "Description of the ideal thumbnail image for this video"
}

RULES:
1. The hook MUST be adapted from the viral inspiration but made original for {{product_name}}
2. Every B-Roll segment must have a clear type: talking-head, ai-video, ai-still, or personal
3. The voiceover must sound like natural {{language}} speech, not a script
4. Include at least one pattern interrupt (unexpected visual, tone shift, or question)
5. The CTA must reference {{product_name}} and create urgency
6. Total B-Roll segments should cover the full video duration with no gaps
7. ai_prompt fields should be detailed enough for AI image/video generation (50+ words)
8. Respect the content split: ~{{talking_head_pct}}% talking-head segments, ~{{broll_pct}}% other types
```

---

## Target Lengths

| Format | Seconds | Words (~2.5/sec) |
|--------|---------|-------------------|
| TikTok short | 15-30 | 40-75 |
| TikTok medium | 30-60 | 75-150 |
| Reel/TikTok long | 60-90 | 150-225 |
| YouTube Short | 30-60 | 75-150 |

Default to 45 seconds unless user specifies otherwise.

---

## Revision Handling

When the user requests changes:
1. Append their feedback to the prompt under REVISION REQUEST
2. Include the full previous script as reference
3. Re-call Sonnet with the updated prompt
4. Max 5 revision rounds — after that, suggest the user rewrite the hook manually

Track revision count in the content-pipeline entry.
