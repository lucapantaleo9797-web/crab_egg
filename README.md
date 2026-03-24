# CrabEgg

From product to revenue in one hatch. A meta-skill for OpenClaw that builds your entire content-to-sales infrastructure from scratch.

```
                    ___
                 .-'   '-.
                /   .-.   \
               |   (   )   |
               |    '-'    |
                \  .---.  /
                 '-.___.~'
                   /   \
                  /     \
             ~~~~~/~~~~~~~\~~~~~
```

## What is CrabEgg?

CrabEgg is an OpenClaw skill that takes a single input — your product — and autonomously builds:

- **Content Discovery** — Scrapes TikTok + Instagram for viral posts via Apify, analyzes them with Claude Haiku
- **Creator Auto-Discovery** — Finds new creators in your niche automatically
- **Script Generation** — Claude Sonnet writes branded video scripts with B-Roll markers
- **Video Production** — ElevenLabs (voice) + Creatify (talking head) + Higgsfield (B-Roll)
- **Spotify Integration** — Podcast discovery + brand-aligned music curation
- **Commerce** — Shopify storefront, checkout links, sales attribution via Stripe
- **Self-Improvement** — Learns from performance data and gets smarter over time

You answer 22 questions once. CrabEgg does the rest.

## Install

### One-liner (recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/lucapantaleo9797-web/crab_egg/main/install.sh | bash
```

### Manual

```bash
git clone https://github.com/lucapantaleo9797-web/crab_egg.git ~/.openclaw/skills/crabegg
chmod +x ~/.openclaw/skills/crabegg/scripts/*.py
pip install requests
```

### Verify

```bash
openclaw skills list
```

You should see `crabegg` in the output.

## Usage

In your OpenClaw chat, say any of:

```
Hatch a CrabEgg
Set up my product
Build my content pipeline
I want to sell online
```

CrabEgg will display the hatching ceremony, ask you 22 questions, then build everything.

### Post-Hatch Commands

| Command | What it does |
|---------|-------------|
| `scrape` | Discover viral content on TikTok + Instagram |
| `write script` | Generate a branded video script from top viral post |
| `produce video` | Generate audio, talking head, and B-Roll from approved script |
| `spotify refresh` | Update podcast ideas and music recommendations |
| `check sales` | Show sales attribution report |
| `evolve` | Self-improve based on performance data |
| `status` | Full pipeline dashboard |
| `hatch new` | Start over with a new product |

## API Keys Required

| Service | What it does | Required? |
|---------|-------------|-----------|
| Anthropic | Content analysis (Haiku) + script generation (Sonnet) | Yes |
| Apify | TikTok + Instagram scraping | Yes |
| ElevenLabs | Voice generation | For video production |
| Creatify | Talking head video | For video production |
| Higgsfield | AI stills + video B-Roll | For video production |
| Spotify | Podcast discovery + music curation | Optional |
| Shopify | Storefront + product listing | For commerce |
| Stripe | Payment + sales attribution | For commerce |

Start with just Anthropic + Apify. Add the rest as you need them.

## Architecture

```
crabegg/
  SKILL.md                          # The brain — 655 lines of orchestration
  .gitignore
  assets/
    hatching-art.md                 # 6-stage ASCII art hatching ceremony
  references/
    api-endpoints.md                # Full API reference (all 8 services)
    apify-actors.md                 # Apify actor IDs + field mappings
    analysis-prompt.md              # Claude Haiku analysis prompt template
    script-prompt-template.md       # Claude Sonnet script generation prompt
    broll-format.md                 # B-Roll segment JSON schema
    spotify-integration.md          # Spotify auth, podcast discovery, music curation
    shopify-setup.md                # Shopify storefront + sales attribution
    humanizer-patterns.md           # AI writing pattern detection (from Humanizer skill)
    self-improvement.md             # Self-improvement protocols (from self-improving-agent)
  scripts/
    hatch.py                        # Workspace setup + status dashboard
    scout.py                        # Content discovery (Apify + Claude Haiku)
    writer.py                       # Script generation (Claude Sonnet)
    producer.py                     # Video production (ElevenLabs + Creatify + Higgsfield)
    spotify_scout.py                # Spotify podcast + music discovery
    evolve.py                       # Self-improvement engine
```

## Built From

CrabEgg combines and improves on:

| Source | What we took |
|--------|-------------|
| [Malte's Content Pipeline](https://www.notion.so/bioxyz/System-Architecture-32d567ab84068077be8fd6814ad93584) | Scout → Analyze → Script → Produce pipeline, Apify integration, multi-niche architecture |
| [Biofy Platform](https://www.notion.so/bioxyz/Instructions-32d567ab84068084bb81ed4687402069) | Commerce layer, sales attribution, builder program concepts |
| [self-improving-agent](https://clawhub.ai/pskoett/self-improving-agent) (296K downloads) | `.learnings/` system, error detection, learning promotion, pattern tracking |
| [Proactive Agent](https://clawhub.ai/halthelobster/proactive-agent) (119K downloads) | WAL Protocol, VBR, relentless resourcefulness, VFM/ADL protocols, heartbeat system |
| [Humanizer](https://clawhub.ai/biostartechnology/humanizer) (69K downloads) | AI writing pattern detection for natural-sounding scripts |
| [Automation Workflows](https://clawhub.ai/jk-0001/automation-workflows) (50.6K downloads) | ROI calculator, scheduling patterns, monitoring workflows |

## Estimated Costs

| Component | Monthly Cost |
|-----------|-------------|
| Apify (scraping) | ~$8 |
| Anthropic (Haiku analysis) | ~$3 |
| Anthropic (Sonnet scripts) | ~$5 |
| ElevenLabs (voice) | ~$20 |
| Creatify (talking head) | ~$30 |
| Higgsfield (B-Roll) | ~$50 |
| **Total** | **~$116/month** |

Saves ~24 hours/month of manual content work. That's $4.83/hour.

## License

MIT-0 — Free to use, modify, and redistribute. No attribution required.
