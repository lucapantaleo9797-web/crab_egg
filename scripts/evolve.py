#!/usr/bin/env python3
"""
CrabEgg Evolver — Self-improvement engine.
Analyzes performance data to learn what content converts,
then adjusts strategy accordingly.

Inspired by ClawHub's Capability Evolver + Self-Improving Agent.
"""

import json
import os
import sys
from datetime import datetime, timezone
from collections import Counter

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

# --- Analysis Functions ---

def analyze_viral_library(library):
    """Find patterns in what content scores highest."""
    posts = library.get("posts", [])
    if not posts:
        return {"status": "no_data"}

    analyzed = [p for p in posts if "analysis" in p]
    if not analyzed:
        return {"status": "no_analyzed_posts"}

    # Hook type distribution
    hook_types = Counter(p["analysis"].get("hook_type", "unknown") for p in analyzed)

    # Theme distribution
    themes = Counter(p["analysis"].get("theme", "unknown") for p in analyzed)

    # Format distribution
    formats = Counter(p["analysis"].get("content_format", "unknown") for p in analyzed)

    # Best performing by hook type
    hook_scores = {}
    for p in analyzed:
        ht = p["analysis"].get("hook_type", "unknown")
        score = p["analysis"].get("viral_score", 0)
        if ht not in hook_scores:
            hook_scores[ht] = []
        hook_scores[ht].append(score)

    hook_avg = {k: sum(v)/len(v) for k, v in hook_scores.items() if v}

    # Top adapted vs unadapted
    adapted = [p for p in analyzed if p.get("adapted")]
    unadapted = [p for p in analyzed if not p.get("adapted")]

    return {
        "total_posts": len(analyzed),
        "adapted_count": len(adapted),
        "unadapted_count": len(unadapted),
        "hook_type_distribution": dict(hook_types.most_common()),
        "theme_distribution": dict(themes.most_common(10)),
        "format_distribution": dict(formats.most_common()),
        "hook_type_avg_score": hook_avg,
        "best_hook_type": max(hook_avg, key=hook_avg.get) if hook_avg else None,
        "best_theme": themes.most_common(1)[0][0] if themes else None,
        "avg_viral_score": sum(p["analysis"].get("viral_score", 0) for p in analyzed) / len(analyzed)
    }

def analyze_performance(performance_log):
    """Analyze which content drove sales."""
    if not performance_log:
        return {"status": "no_sales_data"}

    total_revenue = sum(e.get("revenue", 0) for e in performance_log)
    total_commission = sum(e.get("commission", 0) for e in performance_log)

    # Attribution by content
    content_revenue = Counter()
    for entry in performance_log:
        cid = entry.get("content_id", "unknown")
        content_revenue[cid] += entry.get("revenue", 0)

    # Attribution by platform
    platform_revenue = Counter()
    for entry in performance_log:
        platform = entry.get("source_platform", "unknown")
        platform_revenue[platform] += entry.get("revenue", 0)

    return {
        "total_revenue": total_revenue,
        "total_commission": total_commission,
        "total_orders": len(performance_log),
        "revenue_per_content": dict(content_revenue.most_common(10)),
        "revenue_per_platform": dict(platform_revenue),
        "avg_order_value": total_revenue / len(performance_log) if performance_log else 0
    }

def analyze_sources(sources, library):
    """Analyze which scraping sources produce the best content."""
    posts = library.get("posts", [])

    source_quality = {}
    for post in posts:
        source_query = post.get("source_query", "unknown")
        score = post.get("analysis", {}).get("viral_score", 0)

        if source_query not in source_quality:
            source_quality[source_query] = {"scores": [], "count": 0}
        source_quality[source_query]["scores"].append(score)
        source_quality[source_query]["count"] += 1

    for k, v in source_quality.items():
        v["avg_score"] = sum(v["scores"]) / len(v["scores"]) if v["scores"] else 0
        del v["scores"]

    # Rank sources
    ranked = sorted(source_quality.items(), key=lambda x: x[1]["avg_score"], reverse=True)

    return {
        "source_quality": dict(ranked),
        "best_source": ranked[0][0] if ranked else None,
        "worst_source": ranked[-1][0] if ranked else None
    }

# --- Evolution Actions ---

def evolve_brand_profile(workspace, content_analysis, performance_analysis):
    """Update brand profile based on learnings."""
    brand_path = os.path.join(workspace, 'data', 'brand-profile.json')
    brand = load_json(brand_path)

    # Add learned preferences
    if "learned_preferences" not in brand:
        brand["learned_preferences"] = {}

    prefs = brand["learned_preferences"]

    if content_analysis.get("best_hook_type"):
        prefs["preferred_hook_type"] = content_analysis["best_hook_type"]
        print(f"    Learned: best hook type = {content_analysis['best_hook_type']}")

    if content_analysis.get("best_theme"):
        prefs["preferred_theme"] = content_analysis["best_theme"]
        print(f"    Learned: best theme = {content_analysis['best_theme']}")

    if content_analysis.get("hook_type_avg_score"):
        prefs["hook_type_scores"] = content_analysis["hook_type_avg_score"]

    prefs["last_evolved"] = datetime.now(timezone.utc).isoformat()
    save_json(brand_path, brand)

def evolve_sources(workspace, source_analysis, sources):
    """Adjust scraping sources based on quality data."""
    sources_path = os.path.join(workspace, 'data', 'scraping-sources.json')
    quality = source_analysis.get("source_quality", {})

    adjustments = []
    for source in sources["sources"]:
        source_key = source.get("handle") or source.get("query") or source.get("tag", "")
        if source_key in quality:
            avg_score = quality[source_key].get("avg_score", 5)
            if avg_score < 3 and source.get("auto_discovered"):
                source["active"] = False
                adjustments.append(f"    Deactivated low-quality source: {source_key} (avg: {avg_score:.1f})")
            elif avg_score >= 8:
                source["min_views"] = max(source.get("min_views", 0) - 10000, 10000)
                adjustments.append(f"    Lowered threshold for high-quality source: {source_key}")

    if adjustments:
        save_json(sources_path, sources)
        for adj in adjustments:
            print(adj)

# --- Main Evolution Flow ---

def run_evolve(workspace):
    print("\n  ,;;,")
    print(" ( o o)  CrabEgg Evolver: Learning from performance...")
    print("/'   '\\")
    print()

    # Load data
    library = load_json(os.path.join(workspace, 'data', 'viral-library.json'))
    sources = load_json(os.path.join(workspace, 'data', 'scraping-sources.json'))

    perf_path = os.path.join(workspace, 'data', 'performance-log.json')
    performance_log = load_json(perf_path) if os.path.exists(perf_path) else []

    # Analyze
    print("  Analyzing viral library patterns...")
    content_analysis = analyze_viral_library(library)

    print("  Analyzing sales performance...")
    performance_analysis = analyze_performance(performance_log)

    print("  Analyzing source quality...")
    source_analysis = analyze_sources(sources, library)

    # Report
    print(f"\n  === EVOLUTION REPORT ===\n")

    if content_analysis.get("total_posts"):
        print(f"  Content Library: {content_analysis['total_posts']} analyzed posts")
        print(f"    Adapted: {content_analysis['adapted_count']} | Remaining: {content_analysis['unadapted_count']}")
        print(f"    Avg viral score: {content_analysis['avg_viral_score']:.1f}/10")
        print(f"    Best hook type: {content_analysis.get('best_hook_type', 'N/A')}")
        print(f"    Top theme: {content_analysis.get('best_theme', 'N/A')}")
    else:
        print(f"  Content Library: {content_analysis.get('status', 'no data')}")

    print()
    if performance_analysis.get("total_orders"):
        print(f"  Sales: {performance_analysis['total_orders']} orders")
        print(f"    Total revenue: ${performance_analysis['total_revenue']:.2f}")
        print(f"    Avg order value: ${performance_analysis['avg_order_value']:.2f}")
    else:
        print(f"  Sales: {performance_analysis.get('status', 'no data yet')}")

    print()
    if source_analysis.get("best_source"):
        print(f"  Best source: {source_analysis['best_source']}")
        print(f"  Worst source: {source_analysis['worst_source']}")

    # Evolve
    print(f"\n  Applying learnings...")
    evolve_brand_profile(workspace, content_analysis, performance_analysis)
    evolve_sources(workspace, source_analysis, sources)

    # Log evolution event
    evolution_log_path = os.path.join(workspace, 'logs', 'evolution-log.json')
    log = load_json(evolution_log_path) if os.path.exists(evolution_log_path) else []
    log.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "content_analysis": content_analysis,
        "performance_analysis": performance_analysis,
        "source_analysis": source_analysis
    })
    save_json(evolution_log_path, log)

    print(f"\n  ,;;,")
    print(f" ( o o)  Evolution complete! Strategy updated.")
    print(f"/'   '\\")
    print(f"  Your crab got smarter. Run 'write script' to use the new insights.")
    print()

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    run_evolve(workspace)
