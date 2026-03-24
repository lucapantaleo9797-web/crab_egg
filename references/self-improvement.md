# Self-Improvement Reference

Cloned from: self-improving-agent (296K downloads, @pskoett) + Proactive Agent (119K, @halthelobster)

This reference details the full self-improvement system integrated into CrabEgg.

---

## Workspace Structure

CrabEgg maintains these files for continuous improvement:

```
crabegg-workspace/
  .learnings/
    LEARNINGS.md         — corrections, knowledge gaps, best practices
    ERRORS.md            — command failures, API errors
    FEATURE_REQUESTS.md  — user-requested capabilities
  data/
    brand-profile.json   — includes learned_preferences section
    performance-log.json — sales attribution for feedback loop
  logs/
    evolution-log.json   — what the evolver changed and why
    error-log.json       — operational errors
```

---

## Learning Entry Format

```markdown
## [LRN-YYYYMMDD-XXX] category

**Logged**: 2026-03-24T15:00:00Z
**Priority**: medium
**Status**: pending
**Area**: scripts

### Summary
Question hooks outperform bold-claim hooks for peptide niche

### Details
After 3 script generations, scripts using question hooks ("Did you know..."
"What if I told you...") got approved on first try, while bold-claim hooks
("This will change your life") were rejected and revised 2-3 times.

### Suggested Action
Weight question hooks higher in script-prompt-template.md for this brand.
Add to brand-profile learned_preferences.

### Metadata
- Source: performance_data
- Pattern-Key: hooks.question_outperforms_bold_claim
- Recurrence-Count: 3
- First-Seen: 2026-03-20
- Last-Seen: 2026-03-24
- Related Files: references/script-prompt-template.md
```

---

## Error Entry Format

```markdown
## [ERR-YYYYMMDD-XXX] apify_tiktok_scraper

**Logged**: 2026-03-24T14:30:00Z
**Priority**: high
**Status**: pending
**Area**: scraping

### Summary
TikTok profile scraper returning 0 results for @peptide_king

### Error
Apify run SUCCEEDED but dataset was empty. Account may be private or banned.

### Context
- Actor: clockworks/tiktok-profile-scraper
- Input: {"profiles": ["@peptide_king"], "resultsPerPage": 30}
- Previous runs returned 15-25 posts

### Suggested Fix
Check if account still exists. If private/banned, deactivate source and
log auto-discovered replacement.

### Metadata
- Reproducible: yes
- Related Files: data/scraping-sources.json
```

---

## When to Log

### Automatic Triggers (the agent should do this without being asked)

| Event | Log To | Category |
|-------|--------|----------|
| API call fails | ERRORS.md | api_failure |
| Scrape returns 0 results | ERRORS.md | scrape_empty |
| Script rejected by user | LEARNINGS.md | script_feedback |
| Script approved first try | LEARNINGS.md | script_success |
| Video render timeout | ERRORS.md | render_timeout |
| User corrects brand info | LEARNINGS.md | correction |
| Content drives 0 sales after 7 days | LEARNINGS.md | performance |
| Content drives high sales | LEARNINGS.md | performance_win |
| User says "remember this" | LEARNINGS.md | user_flagged |
| User requests new feature | FEATURE_REQUESTS.md | feature |

### User-Triggered

| User Says | Action |
|-----------|--------|
| "Remember this" / "Save this" | Log to LEARNINGS.md |
| "This isn't working" / "Wrong" | Log to ERRORS.md or LEARNINGS.md |
| "Can you also..." / "I wish..." | Log to FEATURE_REQUESTS.md |
| "What have you learned?" | Read and summarize .learnings/ |

---

## Promotion Rules

A learning should be promoted to config files when ALL are true:
- Recurrence-Count >= 3
- Seen across at least 2 distinct tasks/sessions
- Within a 30-day window

### Promotion Targets

| Learning Type | Promote To |
|---------------|-----------|
| Brand voice preference | `data/brand-profile.json` → `learned_preferences` |
| Source quality insight | `data/scraping-sources.json` → adjust min_views/active |
| Hook type performance | `references/script-prompt-template.md` → weight adjustment |
| B-Roll style feedback | `data/brand-profile.json` → `broll_style` |
| API workaround | `references/api-endpoints.md` → add note |
| Scraping pattern | `references/apify-actors.md` → add note |

---

## WAL Protocol (Write-Ahead Log)

From Proactive Agent. The core rule:

**Before responding to any user input, scan for critical details and WRITE them
to the appropriate file BEFORE composing your response.**

Scan every message for:
- Corrections — "It's X, not Y" → update brand-profile.json
- Preferences — "I like/don't like" → update brand-profile.json
- Decisions — "Let's do X" / "Go with" → update relevant config
- Specific values — prices, URLs, codes → update brand-profile.json
- Names/handles — new competitors, creators → update scraping-sources.json

**The protocol:**
1. STOP — do not start composing response
2. WRITE — update the relevant file
3. THEN — respond to the user

---

## VFM Protocol (Value-First Modification)

Before applying any self-improvement change, score it:

| Dimension | Weight | Question |
|-----------|--------|----------|
| High Frequency | 3x | Will this affect daily pipeline runs? |
| Failure Reduction | 3x | Does this prevent script rejections or API failures? |
| User Burden | 2x | Does this reduce revision rounds? |
| Self Cost | 2x | Does this save API calls or processing time? |

**Threshold**: If weighted score < 50, don't make the change.

**The Golden Rule**: "Does this let future runs produce better content with less cost?"
If no, skip it. Optimize for compounding leverage, not marginal improvements.

---

## ADL Protocol (Anti-Drift Limits)

Forbidden evolution:
- Don't add complexity to "look smart" — fake intelligence is prohibited
- Don't make changes you can't verify worked — unverifiable = rejected
- Don't use vague concepts ("intuition") as justification
- Don't sacrifice stability for novelty — shiny isn't better

**Priority ordering**: Stability > Explainability > Reusability > Scalability > Novelty

---

## Periodic Review

At natural breakpoints (after each evolution run, weekly during active use):

```bash
# Count pending learnings
grep -c "Status.*pending" .learnings/LEARNINGS.md

# Find high-priority items
grep -B5 "Priority.*high\|Priority.*critical" .learnings/*.md

# Check recurring patterns
grep "Recurrence-Count" .learnings/LEARNINGS.md | sort -t: -k2 -rn
```

### Review Actions
1. Resolve fixed items (change status to `resolved`)
2. Promote applicable learnings (change status to `promoted`)
3. Link related entries with See Also
4. Escalate recurring issues (bump priority)
5. Archive old resolved items (move to `.learnings/archive/`)
