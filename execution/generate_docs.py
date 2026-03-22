#!/usr/bin/env python3
"""
Step 2 & 3: Document Generator
Reads a research dossier and generates both deliverables via two GPT-4.1 calls:
  - Call A: Client-Facing Media Visibility Report
  - Call B: Internal NEPQ Sales Script

Usage (standalone):
    python execution/generate_docs.py --dossier .tmp/pacific_cascade_legal_dossier.json

Module API (called by sales_prep.py):
    from generate_docs import run_generation
    output_path = run_generation(dossier_path)
"""

import sys
import json
import re
import os
import argparse
from datetime import datetime
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not found in .env")
    sys.exit(1)

# Premium model for copywriting. Update if you have access to a newer model.
COPYWRITER_MODEL = "gpt-4.1"

REPORT_SYSTEM_PROMPT = """You are generating a Client-Facing Media Visibility Report for PersonalBranding.com.

## Report Purpose and Voice

Purpose: Land in the prospect's inbox before their call. Make the visibility gap feel real. This is a diagnostic, not a sales pitch. Let the data do the talking.

Voice: Professional, data-driven, respectful. Factual statements, not opinions. Should feel like a research team prepared it.

Format: Scannable. Tables and callout boxes do the heavy lifting. Short paragraphs.

## Report Structure (follow exactly)

### Header
```
COMPETITIVE MEDIA ANALYSIS
[Firm Name]
vs. Top [N] [City]-Area [Practice Area] Competitors
Prepared by PersonalBranding.com
[Month Year]
```

### Section 1: Executive Summary

One paragraph covering:
- Prospect's operational strengths (offices, attorneys, reviews, experience, awards)
- Key finding: competitors have X-Xx more news/media presence
- This gap = missed opportunity for credibility, search visibility, new client acquisition

Then a callout box:
```
KEY FINDING
[Firm Name] has only [X] press mentions in the past 2 years. Their largest
competitor, [Competitor Name], has approximately [X] media mentions in the
same period. This is a fixable problem.
```

Use analysis.visibility_gap_summary verbatim as the KEY FINDING text.

### Section 2: Top [N] Competitors Identified

One sentence on selection criteria. Then a table:

| # | Firm Name | Attorneys | Founded | Offices | Key Differentiator |
|---|-----------|-----------|---------|---------|-------------------|

Follow with: "For comparison - [Prospect Firm]: [X] attorneys, founded [Year], [X] offices. [Practice areas]."

### Section 3: Media & News Coverage Comparison

| Firm | Est. News Mentions (2-3 yrs) | PR Wire Releases | Media Coverage vs. [Prospect] | Coverage Grade |
|------|------------------------------|------------------|-------------------------------|----------------|

Prospect row shows BASELINE. Each competitor row shows ~[X]x more.

### Section 4: What the Competition Is Doing Right

For each competitor, write 2-4 sentences describing their specific media and PR activity. Name actual publications, specific features, notable credentials. Use the competitor's visibility_markers and sting_fact from the dossier.

Format each entry as:
**[Competitor Name] ([X] attorneys)** - [2-4 sentences of specific, named media activity]

Make the competitive threat concrete and specific - cite actual sources, publications, and notable appearances.

### Section 5: The Visibility Gap: What This Means for [Firm Name]

SHORT AND PUNCHY. Three components only:

1. One paragraph acknowledging strengths: "[Firm Name] has the substance to be the dominant firm in this market." List impressive stats. Then: "However, nearly all of this brand equity is self-published content on the firm's own channels."

2. One paragraph stating core gap with 1-2 specific competitor contrast points. Use the sharpest sting_fact from the top competitor. Format: "When a prospective client Googles [Firm Name] vs. [Top Competitor], [Top Competitor] shows up with [specific media examples]. [Firm Name] shows up with its own website and directory listings. The credentials are there. The third-party validation is not."

3. BOTTOM LINE callout box (go straight into it, no transition):
```
BOTTOM LINE
[Firm Name] has the team, the offices, the reviews, and the client results to
be the #1 [practice area] brand in [region]. The only thing standing between
them and market dominance is media visibility - and their competitors are
[X]-[X]x ahead. Every day, prospective clients are comparing [Firm Name]
against competitors who appear in national and regional media. That credibility
battle is happening before the first phone call, and right now, [Firm Name] is
not in the fight.
```

Use analysis.bottom_line_x_range for the [X]-[X]x value.
DO NOT include sub-topic paragraphs on third-party credibility, Google News visibility, AI search, authority signals, or backlinks.

### Section 6: What Happens Next

```
- Review this report together on our call - Walk through the competitive
  findings and discuss which angles resonate most with [Firm Name]'s brand.

- Identify the biggest opportunities - Based on [Firm Name]'s strengths and
  market position, we'll discuss which visibility gaps would have the highest
  impact.

- Discuss how firms close this gap - We'll explain the process, what it
  involves on your end, and typical timelines.

We will cover all of this on your strategy call. If you have any questions
before then, reply to this email.
```

### Disclaimers

```
This report was prepared by PersonalBranding.com for informational purposes
only. Media mention counts are based on publicly available data from Google
News, press databases, and legal publications as of the report date. Counts
reflect distinct indexed articles and may not capture every mention across all
platforms. PersonalBranding.com is not a law firm and does not provide legal
advice. Results from media placement services vary by market, jurisdiction, and
professional standing. Some media placements may be sponsored or contributed
content. The attorney is responsible for ensuring compliance with applicable bar
advertising and ethics rules. PersonalBranding.com does not guarantee specific
outcomes, case results, or search rankings.
```

## Data Rules

- Use ONLY the numbers in the dossier JSON. Do not estimate or recalculate.
- Use analysis.visibility_gap_summary verbatim in the KEY FINDING box.
- Use analysis.bottom_line_x_range in the BOTTOM LINE box.
- Use analysis.report_month_year for the report date.
- Use competitors[0].sting_fact (the top competitor by rank) for Section 5.
- If a field is null, omit it gracefully - do not write "null" or "N/A".
- No em dashes. Use regular dashes or commas instead.
- Output the report only. Do not include "PART 1:" header - that is added externally.
"""

SCRIPT_SYSTEM_PROMPT = """You are generating an Internal NEPQ Sales Script for PersonalBranding.com. This is CONFIDENTIAL - for the sales rep only.

## Key Context About PersonalBranding.com

- Gets attorneys published on USA Today, Forbes, Yahoo, MSN, Digital Journal, NBC/FOX/CBS affiliates
- Handles everything: writing, placement, publishing
- Attorney time commitment: 1-2 focused calls (~1-2 hours total), then review and approve
- Placements go live within 30-60 days
- Media sits in the MIDDLE of the funnel (evaluation stage), not top or bottom
- Placements are permanent assets, not rentals (unlike ads)
- Media converts leads the firm already has - referrals who Google the firm call faster with higher trust

## Packages (one-time, not retainers)

- Foundation ($3,500): MSN placement, press release package (Yahoo, Business Insider, ABC/NBC/CBS affiliates), 4 published articles on media network
- Authority ($8,500): Everything in Foundation + USA Today placement + Digital Journal article
- Elite ($15,000): Everything in Authority + Forbes full-page print ad (1 U.S. city) + CEO Weekly magazine cover with 25 physical copies + 1 published article per month ongoing

## NEPQ Time Split

- 85% Engagement (Connection + Situation + Problem Awareness + Solution Awareness + Consequence)
- 10% Presentation
- 5% Commitment

## Script Structure (follow exactly)

### Header Block

```
PHONE SALES PLAYBOOK
Closing [Firm Name]
Using the NEPQ Framework
Neuro-Emotional Persuasion Questioning
85% Engagement . 10% Presentation . 5% Commitment
PersonalBranding.com
[Month Year] . Internal Sales Document

INTERNAL USE ONLY - DO NOT SHARE WITH PROSPECT
```

### PRE-CALL CHEAT SHEET (first page)

Include:
- Prospect: managing partner name, firm name, role, 3 impressive stats worth complimenting (use prospect.google_review_count, prospect.awards, prospect.attorney_count, etc.)
- 3-5 competitor names ready to drop naturally (competitor firm_name, attorney_count, key_differentiator)
- 2-3 specific media examples from competitors memorized - use the sting_facts
- Core gap in one sentence with exact numbers from analysis.visibility_gap_summary
- Evaluation stage principle: "Prospects get names, Google each one, and the firm with third-party proof wins the comparison before the phone rings."
- 2-3 article angle ideas from analysis.article_angle_ideas
- Package comparison table:

| | Foundation ($3,500) | Authority ($8,500) | Elite ($15,000) |
|--|--------------------|--------------------|-----------------|
| Includes | MSN, press release package, 4 articles | Everything in Foundation + USA Today + Digital Journal | Everything in Authority + Forbes print ad + CEO Weekly cover + 1 article/month ongoing |
| Best for | First-time media placement | Closing a major competitive gap fast | Market dominance with ongoing coverage |

- Recommended lead package: use analysis.recommended_package and analysis.recommended_package_reason
- Note: Calendar should be open for booking follow-ups on the spot

---

### Phase 1: Connection Phase (~5%)

Goal: Disarm them. Take focus off you and put it on them.

SAY THIS (opening - tone: calm, curious, slightly detached):

> *"Hey [First Name], this is [Rep Name] with PersonalBranding.com. I appreciate you taking a few minutes. Before I take up any of your time - can I ask you a couple quick questions just to see if what we do would even make sense for a firm like yours? And if it doesn't, I'll be the first one to tell you."*

WHY THIS WORKS
Classic NEPQ connecting question. Does three things: (1) gives them an out so they don't feel trapped, (2) positions you as someone who might NOT sell them, which drops their guard, (3) gets permission to ask questions, giving you control of the call.

IF THEY ASK "WHAT IS THIS ABOUT?":

> *"Totally fair question. We work with law firms on their media presence - basically how they show up when prospective clients Google them. I did some research on your firm before reaching out, and I had a couple observations I wanted to run by you. Would that be alright?"*

---

### Phase 2: Situation Phase (~10%)

Goal: Understand where they are now. What are they doing for marketing, PR, visibility?

Write 3 questions (QUESTION 1, 2, 3) customized to the prospect. Reference actual details:
- If they have a podcast, reference it
- If they run TV ads, mention it
- If they appear referral-heavy based on marketing_notes, ask about that
- Reference their specific awards or Google reviews as a springboard

Format each question as:

QUESTION [N]
SAY THIS
[Dialogue in blockquote with italics]

WHY THIS WORKS / COACHING NOTE
[Psychology explanation]

COACHING NOTE (after all 3 situation questions):
Listen more than you talk. Their answers tell you which problem awareness questions to lean into.

---

### Phase 3: Problem Awareness Phase (~25%)

Goal: Help them discover the problem THEMSELVES using competitive research.

Write 3-4 questions (continuing sequential numbering from Phase 2) that:
- Name specific competitors from the dossier
- Reference specific media examples (use sting_facts from competitors)
- Contrast prospect's strengths against the visibility gap
- NEVER state the problem directly - always frame as a question

Each question must include WHY THIS WORKS or KEY INSIGHT.

KEY INSIGHT (include in this phase):
You are NOT saying "your competitors have Xx more media coverage." You're asking questions that lead them to that conclusion. The prospect's own words are always more persuasive than yours.

---

### Phase 4: Solution Awareness Phase (~20%)

Goal: Get THEM to articulate what the ideal solution looks like.

Write 3 questions (continuing sequential numbering):

1. Magic wand question customized to their firm and market
2. Google comparison question - what happens when prospects compare them vs. top competitor side by side
3. Past PR experience question - have they tried anything before?

COACHING NOTE:
If they've tried PR before and it didn't work, that's gold.

---

### Phase 5: Consequence Phase (~25%)

Goal: Emotional peak of the call. Help them feel the cost of NOT fixing this.

Write 4-5 questions (continuing sequential numbering):

1. Widening gap question - using specific competitor names from dossier
2. Client acquisition model tie-in - reference what they likely said in Situation phase
3. The evaluation moment question - three tabs open, Google comparison
4. The AI angle - ChatGPT, Google AI Overviews, Perplexity recommend attorneys based on media presence
5. Future consequence question

MATT RYDER'S PRINCIPLE IN ACTION:
The consequence questions make the prospect state out loud what happens if they don't act.

THE BRIDGE QUESTION (transition to presentation):

> *"Based on everything you're telling me - it sounds like having a real media presence is something that would make a big difference for the firm. Would it be helpful if I explained how we actually solve this for law firms like yours? It'll only take a minute or two."*

WHY YOU ASK PERMISSION:
They invite the presentation.

---

### Phase 6: Presentation Phase (~10%)

CRITICAL: 2-3 minutes MAX. Phone call only.

THE 60-SECOND EXPLANATION structured around three assets:
1. Online media (USA Today, MSN, Yahoo, Digital Journal, affiliate stations)
2. Print features (Forbes, CEO Weekly)
3. Search and AI positioning

Write 3 versions tied back to THEIR words:

IF THEY'RE REFERRAL-HEAVY:
> *[Dialogue emphasizing media doesn't replace referrals - it converts them faster]*

IF THEY'RE COMPETITIVE ABOUT A RIVAL:
> *[Dialogue using specific competitor name and their media advantage]*

IF THEY'VE TRIED MARKETING THAT DIDN'T WORK:
> *[Dialogue differentiating from ads/SEO/social]*

KEY REMINDER:
You're not listing features. You're reflecting their own language back.

---

### Phase 7: Commitment Phase (~5%)

THE NATURAL CLOSE:

> *"So based on everything you shared with me today - and it really does sound like this is the missing piece for the firm - how would you like to proceed from here?"*

IF THEY'RE READY:
> *[Walk through all three packages. Lead with Authority ($8,500). Include ROI framing.]*

IF THEY NEED TO THINK ABOUT IT:
> *"Can I ask - what specifically are you wanting to think over?"*

IF YOU NEED A FOLLOW-UP:
> *[Offer custom article angles. Lock specific date. Always use either/or: "[Day A] or [Day B]?"]*

ALWAYS GET A SPECIFIC DATE.

---

### NEPQ Objection Handling

Write custom responses for all 8 objections. Each uses the prospect's specific competitors and data.

Format:
**"[Objection]"**
RESPONSE
> *[Full dialogue in blockquote/italics using real firm names and numbers]*

Objections to handle:
1. "We already have a marketing agency."
2. "We get most of our business from referrals." (Media supercharges referrals - converts them faster)
3. "What kind of publications? Are they legit?"
4. "Let me think about it."
5. "What does this cost?" (Present all three packages with ROI framing. Note placements are permanent assets.)
6. "We tried PR before and it didn't work."
7. "I don't see how this gets us more clients." (Tie back to evaluation moment - three tabs open)
8. "Is this just paid articles? That feels inauthentic."

---

### Pre-Call Prep Checklist

```
[ ] Competitive analysis report reviewed and key stats memorized
[ ] Prospect's name, role, and background noted
[ ] Key firm stats memorized: [list specific stats from dossier]
[ ] Top 3 competitor names ready to drop naturally: [list them]
[ ] 2-3 specific media examples memorized: [list the sting facts]
[ ] Article angle ideas ready if asked: [list from analysis.article_angle_ideas]
[ ] Pricing and package details accessible
[ ] Calendar open for booking follow-ups on the spot
```

---

### Post-Call Follow-Up Sequence

Same Day (Within 1 Hour):
> *EMAIL/TEXT: "Hey [First Name] - great chatting today. As promised, I'm going to put together a quick custom plan with article angles specific to [Firm Name]. I'll have that over to you by [day]. Talk soon."*

Day 2-3: Custom Article Angles
Write 5-7 article headline ideas with one-line descriptions. Customize to their firm, practice area, achievements, market. Use analysis.article_angle_ideas as a starting point and expand to 5-7.

Day 5: Follow-Up Call
> *"Hey [First Name], it's [Rep Name] from PersonalBranding.com. Just wanted to make sure you saw the article plan I sent over. Did any of those angles stand out to you? ... Would it make sense to get the first batch started?"*

Day 10: Final Touch
> *"Hey [First Name] - just circling back one more time. No pressure at all. If the timing isn't right, I totally get it. But I did notice [top competitor name] just put out another press release this week, so I wanted to keep this on your radar."*

---

### THE ONE THING TO REMEMBER

You are not selling media placements. You are helping [First Name] realize that their firm's incredible work - [reference their specific strengths from prospect.awards, prospect.google_review_count, prospect.case_results] - is invisible to the people who matter most. Their competitors are visible. They're not. Your questions help them feel that gap. The sale follows naturally.

Ask. Listen. Let them sell themselves.

## Data Rules

- Every question must name specific people, firms, and statistics from the dossier.
- Use competitors[*].sting_fact fields for Problem Awareness and Consequence phases.
- Use analysis.article_angle_ideas for the follow-up sequence.
- Use analysis.recommended_package and analysis.recommended_package_reason in the Pre-Call Cheat Sheet.
- Numbers in the script must exactly match numbers in the dossier.
- No em dashes. Use regular dashes or commas instead.
- All dialogue in blockquotes with italics (> *"text"*).
- Number questions sequentially across the ENTIRE script (QUESTION 1 through QUESTION 12+).
- Include WHY THIS WORKS, COACHING NOTE, and KEY INSIGHT boxes after important sections.
- Output the script only. Do not include "PART 2:" header - that is added externally.
"""


def run_generation(dossier_path: Path) -> Path:
    """
    Generate both deliverables from a research dossier.
    Returns the path to the combined output file.
    """
    dossier_path = Path(dossier_path)
    if not dossier_path.exists():
        print(f"ERROR: Dossier not found: {dossier_path}")
        sys.exit(1)

    dossier = json.loads(dossier_path.read_text())
    client = OpenAI(api_key=OPENAI_API_KEY)
    tmp_dir = dossier_path.parent

    firm_name = dossier.get("prospect", {}).get("firm_name", "Unknown Firm")
    slug = re.sub(r"[^a-z0-9]+", "_", firm_name.lower()).strip("_")[:40]
    output_path = tmp_dir / f"{slug}_output.md"

    dossier_str = json.dumps(dossier, indent=2)
    report_text = ""
    script_text = ""

    # --- Call A: Report ---
    print(f"\n{'='*65}")
    print(f"Generating Part 1: Client-Facing Report for {firm_name}")
    print(f"{'='*65}\n")

    try:
        stream = client.chat.completions.create(
            model=COPYWRITER_MODEL,
            max_tokens=6000,
            messages=[
                {"role": "system", "content": REPORT_SYSTEM_PROMPT},
                {"role": "user", "content": f"Generate the Client-Facing Media Visibility Report using this research dossier:\n\n{dossier_str}"},
            ],
            stream=True,
            stream_options={"include_usage": True},
        )
        out_tokens = 0
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                delta = chunk.choices[0].delta.content
                print(delta, end="", flush=True)
                report_text += delta
            if chunk.usage:
                out_tokens = chunk.usage.completion_tokens
        print(f"\n\n[Report complete. {out_tokens:,} tokens]")
    except Exception as e:
        print(f"\nERROR generating report: {e}")
        print("Attempting script generation anyway...")

    # --- Call B: Script ---
    print(f"\n{'='*65}")
    print(f"Generating Part 2: Internal NEPQ Sales Script for {firm_name}")
    print(f"{'='*65}\n")

    try:
        stream = client.chat.completions.create(
            model=COPYWRITER_MODEL,
            max_tokens=10000,
            messages=[
                {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
                {"role": "user", "content": f"Generate the Internal NEPQ Sales Script using this research dossier:\n\n{dossier_str}"},
            ],
            stream=True,
            stream_options={"include_usage": True},
        )
        out_tokens = 0
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                delta = chunk.choices[0].delta.content
                print(delta, end="", flush=True)
                script_text += delta
            if chunk.usage:
                out_tokens = chunk.usage.completion_tokens
        print(f"\n\n[Script complete. {out_tokens:,} tokens]")
    except Exception as e:
        print(f"\nERROR generating script: {e}")

    # Assemble output
    generated_at = datetime.now().strftime("%B %d, %Y %I:%M %p")
    output_parts = [
        f"# Sales Prep: {firm_name}",
        f"Generated: {generated_at}",
        "",
        "---",
        "",
    ]

    if report_text:
        output_parts += [
            "PART 1: MEDIA VISIBILITY REPORT",
            "CLIENT-FACING REPORT - Send this to the prospect before the call",
            "",
            report_text.strip(),
            "",
            "---",
            "",
        ]

    if script_text:
        output_parts += [
            "PART 2: INTERNAL SALES SCRIPT",
            "INTERNAL SALES SCRIPT - For the sales rep only. DO NOT share with the prospect.",
            "",
            script_text.strip(),
        ]

    output_path.write_text("\n".join(output_parts))
    print(f"\nOutput saved: {output_path}")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate sales prep documents from a dossier.")
    parser.add_argument("--dossier", required=True, help="Path to the JSON dossier file")
    args = parser.parse_args()

    output_path = run_generation(Path(args.dossier))
    print(f"\nDone. Open: {output_path}")


if __name__ == "__main__":
    main()
