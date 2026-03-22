#!/usr/bin/env python3
"""
Step 1: Research Agent (Hybrid - Firecrawl + SerpApi + GPT-4o-mini)

Pipeline:
  1A. Firecrawl   → clean Markdown of prospect's website
  1B. SerpApi     → Google reviews, news counts, competitor names
  1C. SerpApi     → competitor news counts + search snippets
  1D. GPT-4o-mini → maps all raw data into structured dossier JSON

Usage (standalone):
    python execution/research.py "DM Law, Portland OR, Personal Injury, https://www.dmlawusa.com/"
    python execution/research.py "https://www.smithjoneslaw.com"

Module API (called by sales_prep.py):
    from research import run_research
    dossier_path = run_research("Firm Name, City ST, Practice Area")
"""

import sys
import json
import re
import os
import requests
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
SERPAPI_API_KEY   = os.getenv("SERPAPI_API_KEY")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")

for key_name, key_val in [
    ("FIRECRAWL_API_KEY", FIRECRAWL_API_KEY),
    ("SERPAPI_API_KEY",   SERPAPI_API_KEY),
    ("OPENAI_API_KEY",    OPENAI_API_KEY),
]:
    if not key_val:
        print(f"ERROR: {key_name} not found in .env")
        sys.exit(1)

MAPPER_MODEL    = "gpt-4o-mini"
MAX_COMPETITORS = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_url(text: str) -> str | None:
    m = re.search(r'https?://[^\s,]+', text)
    return m.group(0).rstrip('.,)') if m else None


def parse_prospect_input(text: str) -> dict:
    """
    Parse: "Firm Name, City ST, Practice Area, https://..."
    Returns dict with url, firm_name, city, state, practice_area (all may be None).
    """
    url = extract_url(text)
    clean = re.sub(r'https?://[^\s,]+', '', text).strip().strip(',').strip()
    parts = [p.strip() for p in clean.split(',') if p.strip()]

    firm_name = parts[0] if len(parts) > 0 else None
    city = state = None
    practice_area = None

    if len(parts) >= 2:
        m = re.match(r'^(.+?)\s+([A-Z]{2})$', parts[1])
        if m:
            city, state = m.group(1).strip(), m.group(2)
        else:
            city = parts[1]

    if len(parts) >= 3:
        practice_area = parts[2]

    return dict(url=url, firm_name=firm_name, city=city,
                state=state, practice_area=practice_area)


def firm_name_from_url(url: str) -> str:
    """Rough firm name guess from domain slug when no name is given."""
    domain = re.sub(r'https?://(www\.)?', '', url).split('/')[0]
    slug = domain.split('.')[0]
    # camelCase or run-together → spaced title
    spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', slug)
    spaced = spaced.replace('-', ' ').replace('_', ' ')
    return spaced.title()


# ---------------------------------------------------------------------------
# Firecrawl - website scraping
# ---------------------------------------------------------------------------

def scrape_website(url: str, max_chars: int = 14_000) -> tuple[str, dict]:
    """
    Scrape homepage + key sub-pages with Firecrawl.
    Returns (combined_markdown, site_meta) where site_meta contains
    title, site_name, description extracted from the homepage metadata.
    """
    try:
        from firecrawl import FirecrawlApp
    except ImportError:
        print("  [Firecrawl: not installed - skipping website scrape]")
        return "", {}

    app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
    base = url.rstrip('/')
    pages = [base, f"{base}/about", f"{base}/about-us",
             f"{base}/attorneys", f"{base}/our-team",
             f"{base}/results", f"{base}/case-results",
             f"{base}/testimonials"]

    combined = ""
    scraped = 0
    site_meta = {}

    for page in pages:
        if scraped >= 5:        # cap pages to control cost
            break
        try:
            result = app.scrape(page, formats=["markdown"])
            # FirecrawlApp v2 returns a Document object
            md = getattr(result, 'markdown', None) or (
                result.get('markdown') if isinstance(result, dict) else None
            ) or ""

            # Capture homepage metadata on first successful scrape
            if not site_meta and scraped == 0:
                meta = getattr(result, 'metadata', None)
                if meta:
                    site_meta = {
                        "title":       getattr(meta, 'title', '') or '',
                        "site_name":   getattr(meta, 'og_site_name', '') or '',
                        "description": getattr(meta, 'description', '') or '',
                        "og_title":    getattr(meta, 'og_title', '') or '',
                    }

            if md and len(md) > 200:
                combined += f"\n\n=== {page} ===\n{md[:3000]}"
                scraped += 1
        except Exception as e:
            err = str(e).lower()
            if "404" not in err and "not found" not in err and "page not found" not in err:
                print(f"  [Firecrawl: {page} - {e}]")

    return combined[:max_chars], site_meta


def extract_from_site_meta(site_meta: dict) -> dict:
    """
    Extract firm_name, city, state, practice_area from Firecrawl page metadata.
    """
    # Firm name: og:site_name is usually the cleanest (e.g. "DM Injury Law")
    firm_name = site_meta.get("site_name") or site_meta.get("og_title") or site_meta.get("title") or ""
    # If it's a long page title, strip trailing " - ..." clauses
    firm_name = re.split(r'\s*[-|]\s*', firm_name)[0].strip()
    # Remove trailing "Law Firm", "Attorneys", etc. if it looks like a tagline
    if len(firm_name) > 50:
        firm_name = ""

    # Extract city from title/description
    text = (site_meta.get("title") or "") + " " + (site_meta.get("description") or "")
    city = None
    city_match = re.search(
        r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)?)\s+(?:Personal Injury|Criminal Defense|Family Law|'
        r'Immigration|Employment|Workers|Estate|Bankruptcy|Real Estate|Business|Law Firm|'
        r'Attorney|Lawyers?|Legal)',
        text
    )
    if city_match:
        city = city_match.group(1).strip()

    # Extract practice area from title/description
    combined = text.lower()
    practice_area = None
    for pa in ["personal injury", "family law", "criminal defense", "immigration",
               "employment law", "workers compensation", "estate planning",
               "bankruptcy", "real estate", "business law", "car accident"]:
        if pa in combined:
            practice_area = pa.title()
            break

    return {
        "firm_name":     firm_name or None,
        "city":          city,
        "state":         None,       # hard to extract reliably; let mapper handle
        "practice_area": practice_area,
    }


# ---------------------------------------------------------------------------
# SerpApi - Google Search wrapper
# ---------------------------------------------------------------------------

def serpapi_search(query: str, tbm: str = None, num: int = 10) -> dict:
    """Run a single SerpApi Google search. Returns JSON response dict."""
    params = {
        "q":       query,
        "api_key": SERPAPI_API_KEY,
        "num":     num,
        "hl":      "en",
        "gl":      "us",
    }
    if tbm:
        params["tbm"] = tbm

    resp = requests.get(
        "https://serpapi.com/search.json",
        params=params,
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def extract_news(data: dict) -> tuple[int, list[dict]]:
    """
    From a SerpApi news search result, return (count, mentions_list).
    mentions_list items: {source, headline, year}
    """
    results = data.get("news_results", [])
    mentions = []
    for r in results[:15]:
        raw_date = r.get("date", "")
        year = datetime.now().year   # default to current year
        year_match = re.search(r'\b(20\d{2})\b', raw_date)
        if year_match:
            year = int(year_match.group(1))
        mentions.append({
            "source":   r.get("source", ""),
            "headline": r.get("title", ""),
            "year":     year,
        })
    return len(results), mentions


def extract_reviews(data: dict, firm_name_hint: str) -> tuple[int | None, float | None]:
    """
    Pull review count and rating from SerpApi local results or knowledge graph.
    """
    kg = data.get("knowledge_graph", {})
    try:
        if kg.get("rating") and kg.get("reviews"):
            r = kg["reviews"]
            if isinstance(r, (int, float)):
                return int(r), float(kg["rating"])
            # SerpApi sometimes puts a URL or text here - skip if not numeric
    except (ValueError, TypeError):
        pass

    places = data.get("local_results", {}).get("places", [])
    hint = firm_name_hint.lower()[:12]
    for place in places:
        if hint in place.get("title", "").lower():
            return place.get("reviews"), place.get("rating")

    # Fallback: first local result
    if places:
        p = places[0]
        return p.get("reviews"), p.get("rating")

    return None, None


def extract_competitor_names(
    searches: list[dict],
    exclude_name: str,
    max_count: int = MAX_COMPETITORS,
) -> list[str]:
    """
    Pull candidate competitor firm names from organic + local search results.
    Deduplicates and strips the prospect firm.
    """
    seen = set()
    names = []
    exclude_lower = exclude_name.lower()

    for data in searches:
        # Local results (Google Maps pack)
        for place in data.get("local_results", {}).get("places", []):
            n = place.get("title", "").strip()
            if n and n.lower() not in seen and exclude_lower not in n.lower():
                seen.add(n.lower())
                names.append(n)

        # Organic results - only those that look like law firms
        for r in data.get("organic_results", []):
            title = r.get("title", "")
            snippet = r.get("snippet", "")
            combined = (title + " " + snippet).lower()
            if any(kw in combined for kw in ["law firm", "attorney", "legal", "lawyers", "injury", "llp", "pc", "pllc"]):
                # Clean up "Firm Name - City | Law Firm" patterns
                name = re.split(r'[\|\-–]', title)[0].strip()
                if name and len(name) < 60 and name.lower() not in seen and exclude_lower not in name.lower():
                    seen.add(name.lower())
                    names.append(name)

        if len(names) >= max_count:
            break

    return names[:max_count]


# ---------------------------------------------------------------------------
# Compute media grades
# ---------------------------------------------------------------------------

def compute_media_grade(mention_count: int) -> str:
    if mention_count >= 15: return "A"
    if mention_count >= 12: return "A-"
    if mention_count >= 8:  return "B+"
    if mention_count >= 5:  return "B"
    if mention_count >= 3:  return "C+"
    if mention_count >= 1:  return "C-"
    return "D"


# ---------------------------------------------------------------------------
# GPT-4o-mini: map raw data → dossier JSON
# ---------------------------------------------------------------------------

DOSSIER_SCHEMA = """
{
  "meta": {"generated_at": "ISO 8601", "prospect_input": "str", "model_used": "str", "input_tokens": 0, "output_tokens": 0},
  "prospect": {
    "firm_name": "str", "city": "str", "state": "2-letter str",
    "region_label": "str (e.g. 'Portland-area')",
    "practice_area": "str", "website_url": "str|null",
    "founding_year": "str|null", "attorney_count": "int|null",
    "office_count": "int", "office_locations": ["str"],
    "managing_partner": "str|null", "key_attorneys": ["str"],
    "practice_areas": ["str"], "tagline": "str|null",
    "case_results": ["str"], "awards": ["str"],
    "google_review_count": "int|null", "google_rating": "float|null",
    "has_podcast": false, "has_blog": false, "has_tv_ads": false,
    "marketing_notes": "str",
    "as_seen_on_site": ["str"],
    "news_mentions": [{"source": "str", "headline": "str", "year": 0}],
    "news_mention_count": 0, "pr_wire_count": 0,
    "media_grade": "str", "bar_leadership": false,
    "wikipedia_page": false, "speaking_engagements": ["str"]
  },
  "competitors": [{
    "rank": 1, "firm_name": "str", "city": "str", "state": "str",
    "attorney_count": "int|null", "founding_year": "str|null",
    "office_count": 1, "key_differentiator": "str",
    "news_mentions": [{"source": "str", "headline": "str", "year": 0}],
    "news_mention_count": 0, "pr_wire_count": 0,
    "media_grade": "str",
    "visibility_markers": ["str"],
    "sting_fact": "str (one powerful sentence)"
  }],
  "analysis": {
    "report_month_year": "str",
    "competitor_count": 0,
    "top_competitor_name": "str",
    "top_competitor_mention_count": 0,
    "prospect_to_top_competitor_ratio": "str (e.g. '9x')",
    "visibility_gap_summary": "str (one sentence)",
    "prospect_strengths_summary": "str (one sentence)",
    "bottom_line_x_range": "str (e.g. '5-9x')",
    "recommended_package": "Foundation|Authority|Elite",
    "recommended_package_reason": "str (one sentence)",
    "article_angle_ideas": ["str", "str", "str"]
  }
}
"""


def map_to_dossier(
    prospect_input: str,
    website_md: str,
    precomputed: dict,
) -> dict:
    """
    GPT-4o-mini maps all raw research into the structured dossier JSON.
    precomputed contains already-calculated numbers so the model doesn't have to guess.
    """
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""You are a research formatter for PersonalBranding.com. Your ONLY job is to map the raw research data below into a clean JSON dossier. Output ONLY valid JSON. Begin with {{ and end with }}. No preamble, no explanation.

## PROSPECT INPUT
{prospect_input}

## WEBSITE CONTENT (Firecrawl markdown)
{website_md[:7000] if website_md else "(no website data)"}

## PRE-COMPUTED FACTS (use these numbers exactly - do not recalculate)
{json.dumps(precomputed, indent=2)}

## TASK
Fill in every field of the schema below. Rules:
- Use precomputed.prospect_news_count for prospect.news_mention_count
- Use precomputed.competitor_news_counts[name] for each competitor's news_mention_count
- Use precomputed.review_count / precomputed.rating for google_review_count / google_rating
- Rank competitors 1 = highest news count. Sort them accordingly.
- Compute analysis.prospect_to_top_competitor_ratio = round(top_competitor_count / prospect_count) + "x". If prospect_count is 0, use top_competitor_count + "x".
- Compute analysis.bottom_line_x_range = "[lowest ratio]x-[highest ratio]x" across all competitors.
- Assign media grades using: A=15+, A-=12-14, B+=8-11, B=5-7, C+=3-4, C-=1-2, D=0
- Write sting_fact as ONE punchy sentence: the competitive fact that would sting most if prospect heard it on a sales call.
- Write 3 article angle ideas customized to their practice area and market.
- Recommend Foundation ($3,500) for <5 attorneys or minimal gap; Authority ($8,500) for most firms; Elite ($15,000) for large firms or maximum gap.
- Use null (not "null") for unknown values. Use [] for unknown lists.
- No em dashes anywhere.
- Today's date: {datetime.now().strftime('%B %Y')}

## OUTPUT SCHEMA
{DOSSIER_SCHEMA}

Begin your response with {{"""

    resp = client.chat.completions.create(
        model=MAPPER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
        temperature=0.1,
    )

    raw = resp.choices[0].message.content.strip()
    usage = resp.usage

    # Parse JSON (with fallback)
    dossier = None
    try:
        dossier = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                dossier = json.loads(match.group())
            except json.JSONDecodeError:
                pass

    if not dossier:
        raise ValueError(f"GPT-4o-mini returned invalid JSON.\nRaw:\n{raw[:500]}")

    # Inject token counts
    if "meta" not in dossier:
        dossier["meta"] = {}
    dossier["meta"]["input_tokens"]  = usage.prompt_tokens
    dossier["meta"]["output_tokens"] = usage.completion_tokens
    dossier["meta"]["model_used"]    = MAPPER_MODEL

    return dossier


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_research(prospect_input: str) -> Path:
    """
    Research a prospect and save a JSON dossier to .tmp/.
    Returns the path to the saved dossier file.
    """
    tmp_dir = Path(__file__).parent.parent / ".tmp"
    tmp_dir.mkdir(exist_ok=True)

    print(f"\n{'='*65}")
    print("PersonalBranding.com - Research Phase (Hybrid)")
    print(f"Prospect: {prospect_input}")
    print(f"{'='*65}\n")

    parsed = parse_prospect_input(prospect_input)
    url = parsed["url"]

    # --- Step 1A: Firecrawl ---
    website_md = ""
    site_meta  = {}
    if url:
        print("[1A] Firecrawl: scraping website...")
        website_md, site_meta = scrape_website(url)
        print(f"     {len(website_md):,} chars scraped")
    else:
        print("[1A] No URL provided - skipping website scrape")

    # Resolve firm name, city, practice area (needed for SerpApi searches)
    meta_extract = extract_from_site_meta(site_meta) if site_meta else {}

    firm_name     = (parsed["firm_name"]     or meta_extract.get("firm_name")
                     or (firm_name_from_url(url) if url else "Unknown Firm"))
    city          = parsed["city"]          or meta_extract.get("city")          or ""
    state         = parsed["state"]         or meta_extract.get("state")         or ""
    practice_area = (parsed["practice_area"] or meta_extract.get("practice_area")
                     or "personal injury")

    print(f"\n     Firm: {firm_name}  |  {city}, {state}  |  {practice_area}\n")

    # --- Step 1B: Prospect Research ---
    print("[1B] SerpApi: prospect research...")

    print(f"  [Searching: \"{firm_name}\" Google reviews]")
    reviews_data = serpapi_search(f'"{firm_name}" {city} {state}'.strip())
    review_count, rating = extract_reviews(reviews_data, firm_name)

    print(f"  [Searching: \"{firm_name}\" news]")
    prospect_news_data = serpapi_search(f'"{firm_name}"', tbm='nws', num=20)
    p_news_count, p_news_mentions = extract_news(prospect_news_data)

    print(f"  [Searching: \"{firm_name}\" press releases]")
    pr_data = serpapi_search(
        f'"{firm_name}" site:prnewswire.com OR site:businesswire.com OR site:prweb.com',
        num=10,
    )
    pr_count = len(pr_data.get("organic_results", []))

    # --- Step 1C: Competitor Identification ---
    print("\n[1C] SerpApi: finding competitors...")
    comp_searches = []
    for query in [
        f"top {practice_area} law firms {city} {state}".strip(),
        f"best {practice_area} attorney {city} {state}".strip(),
        f"{practice_area} lawyer {city} reviews".strip(),
    ]:
        print(f"  [Searching: {query}]")
        comp_searches.append(serpapi_search(query, num=10))

    competitor_names = extract_competitor_names(comp_searches, firm_name, MAX_COMPETITORS)
    print(f"     Identified {len(competitor_names)} competitors: {', '.join(competitor_names)}")

    # --- Step 1D: Competitor Research ---
    print("\n[1D] SerpApi: researching each competitor...")
    competitor_research = {}
    for comp in competitor_names:
        print(f"  [Searching: \"{comp}\" news]")
        comp_news = serpapi_search(f'"{comp}"', tbm='nws', num=20)
        c_count, c_mentions = extract_news(comp_news)

        print(f"  [Searching: \"{comp}\" general]")
        comp_general = serpapi_search(f'"{comp}" {city}', num=10)

        competitor_research[comp] = {
            "news_count":    c_count,
            "news_mentions": c_mentions,
            "general_snippets": [
                {"title": r.get("title", ""), "snippet": r.get("snippet", "")}
                for r in comp_general.get("organic_results", [])[:5]
            ],
            "local_info": comp_general.get("local_results", {}).get("places", [])[:3],
        }

    # --- Build precomputed block ---
    competitor_news_counts = {
        name: data["news_count"]
        for name, data in competitor_research.items()
    }

    prospect_grade    = compute_media_grade(p_news_count)
    competitor_grades = {n: compute_media_grade(c) for n, c in competitor_news_counts.items()}

    precomputed = {
        "firm_name":            firm_name,
        "city":                 city,
        "state":                state,
        "practice_area":        practice_area,
        "website_url":          url,
        "review_count":         review_count,
        "rating":               rating,
        "prospect_news_count":  p_news_count,
        "prospect_news_mentions": p_news_mentions,
        "prospect_pr_count":    pr_count,
        "prospect_media_grade": prospect_grade,
        "competitor_names":     competitor_names,
        "competitor_news_counts":    competitor_news_counts,
        "competitor_news_mentions":  {n: d["news_mentions"] for n, d in competitor_research.items()},
        "competitor_snippets":       {n: d["general_snippets"] for n, d in competitor_research.items()},
        "competitor_local_info":     {n: d["local_info"] for n, d in competitor_research.items()},
        "competitor_media_grades":   competitor_grades,
        "report_month_year":    datetime.now().strftime("%B %Y"),
    }

    # --- Step 1E: GPT-4o-mini Mapping ---
    print("\n[1E] GPT-4o-mini: mapping to dossier JSON...")
    dossier = map_to_dossier(prospect_input, website_md, precomputed)

    # Inject / overwrite meta fields
    dossier["meta"].update({
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "prospect_input": prospect_input,
    })

    # Validate required keys
    missing = [k for k in ["prospect", "competitors", "analysis"] if k not in dossier]
    if missing:
        raw_path = tmp_dir / f"raw_mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        raw_path.write_text(json.dumps(precomputed, indent=2))
        print(f"\nERROR: Dossier missing keys: {missing}")
        print(f"Precomputed data saved to: {raw_path}")
        sys.exit(1)

    # Derive slug
    slug_name = dossier["prospect"].get("firm_name") or firm_name
    slug = re.sub(r"[^a-z0-9]+", "_", slug_name.lower()).strip("_")[:40]
    dossier_path = tmp_dir / f"{slug}_dossier.json"
    dossier_path.write_text(json.dumps(dossier, indent=2))

    tokens_in  = dossier["meta"].get("input_tokens", 0)
    tokens_out = dossier["meta"].get("output_tokens", 0)
    print(f"\nResearch complete. Mapping tokens: {tokens_in:,} in / {tokens_out:,} out")
    print(f"Dossier saved: {dossier_path}")

    return dossier_path


def main():
    if len(sys.argv) > 1:
        prospect_input = " ".join(sys.argv[1:])
    else:
        print("PersonalBranding.com - Research Agent")
        print("Enter prospect info:")
        prospect_input = input("> ").strip()

    if not prospect_input:
        print("No input provided.")
        sys.exit(1)

    dossier_path = run_research(prospect_input)
    print(f"\nDone. Run doc generation with:")
    print(f"  python execution/generate_docs.py --dossier {dossier_path}")


if __name__ == "__main__":
    main()
