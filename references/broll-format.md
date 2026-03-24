# B-Roll Segment Format Reference

## Segment Types

| Type | Description | Generation Method |
|------|-------------|-------------------|
| `talking-head` | Speaker on camera | Creatify Aurora avatar |
| `ai-video` | AI-generated video clip | Higgsfield Kling 3.0 |
| `ai-still` | AI-generated static image | Higgsfield Nano Banana 2 |
| `personal` | User-supplied footage | Manual — flag for user |

## Segment JSON Schema

```json
{
  "segment_number": 1,
  "timestamp_start": 0.0,
  "timestamp_end": 5.0,
  "type": "talking-head|ai-video|ai-still|personal",
  "voiceover_excerpt": "The words spoken during this segment",
  "visual_description": "Human-readable description of what's shown",
  "ai_prompt": "Prompt for AI generation (only for ai-video and ai-still)",
  "camera_direction": "Cinematic direction notes",
  "generated_asset_path": null,
  "status": "pending|generating|complete|failed"
}
```

## AI Prompt Guidelines for Higgsfield

### For Nano Banana 2 (Stills)
- Be specific about subject, composition, lighting, and color palette
- Include style reference: "in the style of [broll_style]"
- Specify aspect ratio context: "vertical 9:16 composition"
- Good: "A close-up of golden peptide capsules scattered on a white marble surface, warm morning light from the left, shallow depth of field, clean minimal aesthetic, vertical 9:16 composition"
- Bad: "Some pills on a table"

### For Kling 3.0 (Videos)
- ALWAYS generate the still frame first with Nano Banana 2
- Use the still as the `image_url` input for Kling
- Describe the MOTION you want: what moves, how, and for how long
- Good: "Slow push-in on the peptide capsules, one capsule rolls gently toward camera, soft bokeh background shifts"
- Bad: "Video of pills"

## Production Sequence

For each B-Roll segment:
1. If `ai-still`: Generate with Nano Banana 2 → save path → mark complete
2. If `ai-video`: Generate still first → then Kling 3.0 with still as input → save path → mark complete
3. If `talking-head`: Already handled by Creatify pipeline → mark complete
4. If `personal`: Save placeholder → flag for user → mark pending

## Validation Rules

- No timestamp gaps between segments (end of N = start of N+1)
- No overlapping timestamps
- Total segment duration = estimated video length (+/- 2 seconds)
- Every `ai-video` and `ai-still` segment must have an `ai_prompt`
- Every segment must have a `voiceover_excerpt`
