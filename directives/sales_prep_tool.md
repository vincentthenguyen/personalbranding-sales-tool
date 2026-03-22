# PersonalBranding.com - Sales Prep Tool
## Standard Operating Procedure for Claude Code

---

## Overview

This SOP defines the behavior of an AI-powered sales prep tool built on Claude. When a sales rep provides a prospect law firm's name, location, practice area, and/or website URL, the system performs deep research and generates two deliverables:

1. **Client-Facing Media Visibility Report** - Sent to the prospect before their sales call
2. **Internal NEPQ Sales Script** - Used by the rep on the phone call

Both documents draw from the same research data so all numbers match exactly.

---

## Required APIs and Integrations

### 1. Anthropic Claude API
- **Endpoint:** `https://api.anthropic.com/v1/messages`
- **Model:** `claude-opus-4-6` (recommended for deep research tasks) or `claude-sonnet-4-6`
- **Use:** Core intelligence layer - research synthesis, report generation, script writing
- **Docs:** https://docs.anthropic.com
- **Auth:** `x-api-key` header with your Anthropic API key
- **Tools needed:** `web_search` tool (built into Claude API) and `web_fetch` capability

### 2. Web Search Tool (via Claude API)
- Enable the `web_search_20250305` tool in your Claude API requests
- This gives Claude real-time Google search access for firm research, competitor analysis, and media mention counts
- No separate API key required - included in Claude API access

```json
{
  "tools": [
    {
      "type": "web_search_20250305",
      "name": "web_search"
    }
  ]
}
```

### 3. Web Fetch / URL Scraping
- Claude's built-in web fetch capability handles prospect website scraping
- No additional API needed for basic URL fetching via Claude API
- Optional enhancement: **Firecrawl API** (`https://api.firecrawl.dev`) for more reliable JS-rendered site scraping if Claude's native fetch misses content

### 4. Document Generation (Optional - for .docx output)
If you want to output polished Word documents instead of markdown:
- **Library:** `docx` npm package (`npm install docx`)
- No API key required - runs locally

---

## System Architecture

```
Input: Firm name / location / practice area / URL
          |
          v
[Step 1: Research Agent]
  - Fetch prospect website (if URL provided)
  - Web search: prospect firm details, reviews, media mentions
  - Web search: competitor identification (3-5 firms)
  - Web search: competitor media mentions and PR activity
          |
          v
[Step 2: Report Generator]
  - Client-Facing Media Visibility Report (markdown or .docx)
          |
          v
[Step 3: Script Generator]
  - Internal NEPQ Sales Script (markdown or .docx)
          |
          v
Output: Part 1 (Report) + Part 2 (Script)
```

---

## Input Handling

The system must accept any of the following input formats without asking follow-up questions:

```
Pacific Cascade Legal, Portland OR, Family Law, https://www.pacificcascadelegal.com
```
```
https://www.smithjoneslaw.com -- personal injury firm in Dallas
```
```
https://www.johnsonlawgroup.com
```

**Rules:**
- If a URL is provided, fetch it first and extract all available data before any web searching
- If only a URL is given, derive firm name, location, and practice area from the site
- Never ask follow-up questions unless the site is genuinely down or unreadable
- The website is the most accurate source for the prospect's own information

---

## Step 1: Research Protocol

### 1A. Prospect Website Research (if URL provided)

Fetch and extract from these pages (try each in sequence):
- Homepage
- `/about` or `/about-us`
- `/attorneys` or `/our-team` or `/lawyers`
- `/results` or `/case-results` or `/testimonials`

**Extract:**
- Firm name, founding year, office locations
- Number of attorneys and their names/titles
- Practice areas
- Case results, notable verdicts/settlements
- Awards, recognitions, "Best of" lists
- Podcast, blog, community involvement
- Any "As Seen On" or media mentions already on site
- Tagline and positioning language

### 1B. Prospect Web Research

Search for and record:
- Google review count and star rating (search: `"[Firm Name]" Google reviews`)
- Founding/managing partner name and title
- Awards: Super Lawyers, Best Lawyers, Martindale-Hubbell, local "Best of" lists
- Podcast, books, bar leadership, speaking engagements
- Current marketing: blog, social media, TV/billboard ads, PR Newswire releases
- **News/media mentions:** Search `"[Firm Name]" site:news.google.com` and note each distinct article from the past 2-3 years with source and headline

**Accuracy rule:** Never fabricate or estimate data. If exact count is unavailable, write "at least X based on indexed results."

### 1C. Competitor Identification

Run these searches:
- `top [practice area] firms in [city]`
- `best [practice area] attorney [city]`
- `[practice area] lawyer [city] reviews`

**Selection criteria:**
- Practice area overlap
- Geographic proximity
- Similar or larger firm size
- Skip solo practitioners if prospect has 10+ attorneys
- Skip mega-firms if prospect is a boutique (under 10 attorneys)

Select 3-5 competitors.

### 1D. Competitor Research (for each competitor)

Gather:
- Firm name, attorney count, office locations, founding year
- Key differentiator (one phrase)
- **News/media mentions:** Search `"[Competitor Name]" news` and count distinct articles from past 2-3 years
- PR wire releases: Search `"[Competitor Name]" press release` or `"[Competitor Name]" PR Newswire`
- Visibility markers: bar leadership, Wikipedia page, expert quotes in news stories, awards, "As Seen On" credentials
- The one fact about each competitor that would sting most if the prospect heard it on a call

### 1E. Media Grade Assignment

Assign each firm (prospect and competitors) a media grade:

| Grade | Criteria |
|-------|----------|
| A | 15+ mentions, active PR strategy, quoted as experts |
| A- | 12-15 mentions, good PR activity, some expert quotes |
| B+ | 8-12 mentions, some PR releases, occasional coverage |
| B | 5-8 mentions, light PR activity |
| C+ | 3-5 mentions, minimal PR |
| C- | 1-3 mentions, almost no media presence |
| D | 0-1 mentions, nothing |

---

## Step 2: Client-Facing Media Visibility Report

**Purpose:** Land in the prospect's inbox before their call. Make the visibility gap feel real. This is a diagnostic, not a sales pitch. Let the data do the talking.

**Voice:** Professional, data-driven, respectful. Factual statements, not opinions. Should feel like a research team prepared it.

**Format:** Scannable. Tables and callout boxes do the heavy lifting. Short paragraphs.

---

### Report Structure (follow exactly)

```
COMPETITIVE MEDIA ANALYSIS
[Firm Name]
vs. Top [N] [City]-Area [Practice Area] Competitors
Prepared by PersonalBranding.com
[Month Year]
```

#### Section 1: Executive Summary

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

#### Section 2: Top [N] Competitors Identified

One sentence on selection criteria. Then a table:

| # | Firm Name | Attorneys | Founded | Offices | Key Differentiator |
|---|-----------|-----------|---------|---------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

Follow with: "For comparison - [Prospect Firm]: [X] attorneys, founded [Year], [X] offices. [Practice areas]."

#### Section 3: Media & News Coverage Comparison

| Firm | Est. News Mentions (2-3 yrs) | PR Wire Releases | Media Coverage vs. [Prospect] | Coverage Grade |
|------|------------------------------|------------------|-------------------------------|----------------|
| [Prospect] | [X] | [X] | BASELINE | [Grade] |
| [Competitor 1] | [X] | [X] | ~[X]x more | [Grade] |
| [Competitor 2] | [X] | [X] | ~[X]x more | [Grade] |

#### Section 4: What the Competition Is Doing Right

For each competitor (3-5 firms), write 2-4 sentences describing their specific media and PR activity. Name actual publications, specific features, notable credentials. This section makes the competitive threat concrete and specific.

Format: **[Competitor Name] ([X] attorneys)** - Then 2-4 sentences of specific media activity. Use the sting_fact and visibility_markers from research.

Keep factual and specific - cite actual sources, publications, awards, and notable media appearances.

#### Section 5: The Visibility Gap: What This Means for [Firm Name]

**SHORT AND PUNCHY. Three components only:**

1. One paragraph acknowledging strengths: "[Firm Name] has the substance to be the dominant firm in this market." List impressive stats. Then: "However, nearly all of this brand equity is self-published content on the firm's own channels."

2. One paragraph stating core gap with 1-2 specific competitor contrast points. Use the sharpest "sting facts" from competitor research. Example format: "When a prospective client Googles [Firm Name] vs. [Top Competitor], [Top Competitor] shows up with [specific media examples]. [Firm Name] shows up with its own website and directory listings. The credentials are there. The third-party validation is not."

3. Bottom Line callout box (go straight into it, no transition):

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

**DO NOT include sub-topic paragraphs** on third-party credibility, Google News visibility, AI search, authority signals, or backlinks. Those are phone call talking points, not reading material.

#### Section 6: What Happens Next

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

#### Disclaimers (small text at bottom)

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

---

## Step 3: Internal NEPQ Sales Script

**Purpose:** Complete phone sales script for the rep. CONFIDENTIAL. Never shown to prospect.

**Voice:** Exact dialogue the rep can say aloud or riff from. Confident but not aggressive. Curious, not pushy. Rep is a peer, not a salesperson.

**Key Context About PersonalBranding.com:**
- Gets attorneys published on USA Today, Forbes, Yahoo, MSN, Digital Journal, NBC/FOX/CBS affiliates
- Handles everything: writing, placement, publishing
- Attorney time commitment: 1-2 focused calls (~1-2 hours total), then review and approve
- Placements go live within 30-60 days
- Media sits in the MIDDLE of the funnel (evaluation stage), not top or bottom
- Placements are permanent assets, not rentals (unlike ads)
- Media converts leads the firm already has - referrals who Google the firm call faster with higher trust

**Packages (one-time, not retainers):**
- **Foundation ($3,500):** MSN placement, press release package (Yahoo, Business Insider, ABC/NBC/CBS affiliates), 4 published articles on media network
- **Authority ($8,500):** Everything in Foundation + USA Today placement + Digital Journal article
- **Elite ($15,000):** Everything in Authority + Forbes full-page print ad (1 U.S. city) + CEO Weekly magazine cover with 25 physical copies + 1 published article per month ongoing

**NEPQ Time Split:**
- 85% Engagement (Connection + Situation + Problem Awareness + Solution Awareness + Consequence)
- 10% Presentation
- 5% Commitment

---

### Script Structure (follow exactly)

#### Header Block

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

#### PRE-CALL CHEAT SHEET (first page)

Include:
- Prospect: name, firm, role, key stats worth complimenting
- 3-5 competitor names ready to drop naturally (with attorney count and key differentiator)
- 2-3 specific media examples from competitors memorized (the sting facts)
- 3 impressive facts about the prospect's own firm (for compliments)
- Core gap in one sentence with exact numbers
- Evaluation stage principle: "Prospects get names, Google each one, and the firm with third-party proof wins the comparison before the phone rings."
- 2-3 article angle ideas ready if asked
- Package comparison table:

| | Foundation ($3,500) | Authority ($8,500) | Elite ($15,000) |
|--|--------------------|--------------------|-----------------|
| Includes | MSN, press release package, 4 articles | Everything in Foundation + USA Today + Digital Journal | Everything in Authority + Forbes print ad + CEO Weekly cover + 1 article/month ongoing |
| Best for | First-time media placement | Closing a major competitive gap fast | Market dominance with ongoing coverage |

- Recommended lead package for this prospect and why
- When to move up to Elite or down to Foundation
- Note: Calendar should be open for booking follow-ups on the spot

---

#### Phase 1: Connection Phase (~5%)

**Goal:** Disarm them. Take focus off you and put it on them. You're not pitching - you're having a conversation about their business.

**SAY THIS (opening - tone: calm, curious, slightly detached):**

> *"Hey [First Name], this is [Rep Name] with PersonalBranding.com. I appreciate you taking a few minutes. Before I take up any of your time - can I ask you a couple quick questions just to see if what we do would even make sense for a firm like yours? And if it doesn't, I'll be the first one to tell you."*

**WHY THIS WORKS**
Classic NEPQ connecting question. Does three things: (1) gives them an out so they don't feel trapped, (2) positions you as someone who might NOT sell them, which drops their guard, (3) gets permission to ask questions, giving you control of the call.

**IF THEY ASK "WHAT IS THIS ABOUT?":**

> *"Totally fair question. We work with law firms on their media presence - basically how they show up when prospective clients Google them. I did some research on your firm before reaching out, and I had a couple observations I wanted to run by you. Would that be alright?"*

---

#### Phase 2: Situation Phase (~10%)

**Goal:** Understand where they are now. What are they doing for marketing, PR, visibility? Let them talk. Gather intel.

Write **3 questions (QUESTION 1, 2, 3)** customized to what was found in research. Examples:
- If they have a podcast, reference it
- If they run TV ads, mention it
- If they appear referral-heavy, ask about that

Format each question as:

```
QUESTION [N]
SAY THIS
[Dialogue in italics/blockquote]

WHY THIS WORKS / COACHING NOTE / KEY INSIGHT
[Psychology explanation]
```

**COACHING NOTE (after all 3 situation questions):**
Listen more than you talk. Their answers tell you which problem awareness questions to lean into. If they say "it's all referrals," use that in the consequence phase. Every answer is a doorway to the next question.

---

#### Phase 3: Problem Awareness Phase (~25%)

**Goal:** Help them discover the problem THEMSELVES using competitive research as question fuel.

Write **3-4 questions (continuing sequential numbering)** that:
- Name specific competitors from research
- Reference specific media examples (bar presidency, Wikipedia page, featured in [publication], Super Lawyers, etc.)
- Contrast prospect's strengths against the visibility gap
- NEVER state the problem directly - always frame as a question

Each question must include a **WHY THIS WORKS** or **KEY INSIGHT** box.

Example structure:
- Question naming a specific competitor and their media presence
- Question contrasting prospect's reviews/awards with lack of media coverage
- Question about what prospects find when they Google the firm vs. a competitor
- DIG DEEPER question at end of phase

**KEY INSIGHT (include in this phase):**
You are NOT saying "your competitors have Xx more media coverage." You're asking questions that lead them to that conclusion. The prospect's own words are always more persuasive than yours.

---

#### Phase 4: Solution Awareness Phase (~20%)

**Goal:** Get THEM to articulate what the ideal solution looks like. Not pitching yet.

Write **3 questions (continuing sequential numbering):**

1. **Magic wand question** - customized to their firm and market: "If you could wave a magic wand and fix one thing about how [Firm Name] shows up online compared to [Competitor], what would that look like?"

2. **Google comparison question** - what happens when prospects compare them vs. competitors side by side

3. **Past PR experience question** - have they tried anything before? What happened?

**COACHING NOTE:**
If they've tried PR before and it didn't work, that's gold. Ask what went wrong - it perfectly sets up your differentiation. If they haven't tried anything, ask why not - the answer reveals the real objection.

---

#### Phase 5: Consequence Phase (~25%)

**Goal:** Emotional peak of the call. Help them feel the cost of NOT fixing this. Internal urgency from their own realizations, not your pressure.

Write **4-5 questions (continuing sequential numbering):**

1. **Widening gap question** - using specific competitor names: what happens to this gap in 12-24 months if nothing changes?

2. **Client acquisition model tie-in** - reference what they said in Situation phase (referrals, Google, etc.)

3. **The evaluation moment question** - ask what happens when a potential client has their name and two competitors' names, opens three browser tabs, and compares what Google shows. Makes funnel logic concrete without a slide.

4. **The AI angle** - ChatGPT, Google AI Overviews, and Perplexity recommend attorneys based on media presence. Are they showing up there?

5. **Future consequence question** - where does this go in a year or two if competitors keep building and they don't?

**MATT RYDER'S PRINCIPLE IN ACTION:**
The consequence questions make the prospect state out loud what happens if they don't act. This is NOT fear-based selling. Their own answers create urgency. Done right, by the end they're practically asking "so what can we do about this?"

**THE BRIDGE QUESTION (transition to presentation):**

> *"Based on everything you're telling me - it sounds like having a real media presence is something that would make a big difference for the firm. Would it be helpful if I explained how we actually solve this for law firms like yours? It'll only take a minute or two."*

**WHY YOU ASK PERMISSION:**
They invite the presentation. They're not being pitched - they're asking you to explain. They're leaning in, not leaning back.

---

#### Phase 6: Presentation Phase (~10%)

**CRITICAL: 2-3 minutes MAX. Phone call only. No screen sharing, no slides, no report walkthrough.**

**THE 60-SECOND EXPLANATION**

Structure around three assets:

1. **Online media** that shows up when prospects Google you - USA Today, MSN, Yahoo, Digital Journal, affiliate stations. Real articles in search results and Google News.

2. **Print features** you can put in your lobby and hand to referral sources - Forbes, CEO Weekly. Tangible proof that builds trust before the consultation even starts.

3. **Search and AI positioning** - ensures you show up when someone asks ChatGPT or Google AI who the best attorney is. Future-proof media footprint.

Tie each asset to the specific pain THEY described. Packages are the delivery mechanism for these three assets. Unlike ads, placements are permanent.

**WRITE 3 VERSIONS TIED BACK TO THEIR WORDS:**

**IF THEY'RE REFERRAL-HEAVY:**

> *[Dialogue emphasizing that media doesn't replace referrals - it converts them faster. A referral who Googles the firm and sees USA Today coverage calls with less hesitation and higher trust.]*

**IF THEY'RE COMPETITIVE ABOUT A RIVAL:**

> *[Dialogue using specific competitor name and their media advantage - frame media as winning the comparison before the phone even rings.]*

**IF THEY'VE TRIED MARKETING THAT DIDN'T WORK:**

> *[Dialogue differentiating from ads/SEO/social - we don't do any of that. This is the piece that sits on top of everything else. Third-party proof that no agency can manufacture.]*

**KEY REMINDER:**
You're not listing features. You're reflecting their own language back and explaining how you solve what THEY said was the problem.

---

#### Phase 7: Commitment Phase (~5%)

**Goal:** Clear next step. Either they move forward now or you lock a specific follow-up date.

**THE NATURAL CLOSE:**

> *"So based on everything you shared with me today - and it really does sound like this is the missing piece for the firm - how would you like to proceed from here?"*

**WHY THIS PHRASING:**
Not asking "do you want to buy?" You're asking them to tell you the next step. NEPQ commitment - let them direct the close.

**IF THEY'RE READY:**

> *[Walk through all three packages conversationally. Lead with Authority. Let them self-select up or down. Include ROI framing - what is one new case worth for their practice area?]*

**IF THEY NEED TO THINK ABOUT IT:**

> *"Can I ask - what specifically are you wanting to think over?"*

**IF YOU NEED A FOLLOW-UP:**

> *[Offer custom article angles. Lock a specific date and time. Always use either/or: "[Day A] or [Day B]?"]*

**ALWAYS GET A SPECIFIC DATE:**
Never end with "I'll send this over and you can get back to me." Lock a date. Lock a time. Calendar while still on the phone.

---

#### NEPQ Objection Handling

In NEPQ, objections are invitations to ask better questions. Never argue. Always respond with a question that helps them work through it themselves.

For each objection, write:
- Bold header with the objection
- **RESPONSE** label
- Full dialogue in italics/blockquote using the prospect's specific competitors, data, and situation

**Write custom responses for all of these:**

1. "We already have a marketing agency."
2. "We get most of our business from referrals." *(Emphasize media supercharges referrals - converts them faster. A referral who Googles and sees USA Today coverage calls with less hesitation.)*
3. "What kind of publications? Are they legit?"
4. "Let me think about it."
5. "What does this cost?" *(Present all three packages with ROI framing. Note that unlike ads, placements are permanent assets.)*
6. "We tried PR before and it didn't work."
7. "I don't see how this gets us more clients." *(Tie back to evaluation moment - three tabs open, Google comparison. Also converts referrals faster.)*
8. "Is this just paid articles? That feels inauthentic."

---

#### Pre-Call Prep Checklist

```
[ ] Competitive analysis report reviewed and key stats memorized
[ ] Prospect's name, role, and background noted
[ ] Key firm stats memorized: [list specific stats from research]
[ ] Top 3 competitor names ready to drop naturally: [list them]
[ ] 2-3 specific media examples memorized: [list them]
[ ] Article angle ideas ready if asked: [list 2-3]
[ ] Pricing and package details accessible
[ ] Calendar open for booking follow-ups on the spot
```

---

#### Post-Call Follow-Up Sequence

**Same Day (Within 1 Hour):**

> *EMAIL/TEXT: "Hey [First Name] - great chatting today. As promised, I'm going to put together a quick custom plan with article angles specific to [Firm Name]. I'll have that over to you by [day]. Talk soon."*

**Day 2-3: Custom Article Angles**

Write 5-7 article headline ideas with one-line descriptions. Make them tangible - the attorney should picture each article existing. Customize to their firm, practice area, achievements, market, and recent news.

**Day 5: Follow-Up Call**

Call, don't email.

> *SAY THIS: "Hey [First Name], it's [Rep Name] from PersonalBranding.com. Just wanted to make sure you saw the article plan I sent over. Did any of those angles stand out to you? ... [Let them talk.] ... Would it make sense to get the first batch started?"*

**Day 10: Final Touch**

If no response, one last short text or voicemail.

> *SAY THIS: "Hey [First Name] - just circling back one more time. No pressure at all. If the timing isn't right, I totally get it. But I did notice [competitor name] just put out another press release this week, so I wanted to keep this on your radar. Happy to reconnect whenever it makes sense."*

---

#### THE ONE THING TO REMEMBER

You are not selling media placements. You are helping [First Name] realize that their firm's incredible work - [reference their specific strengths from research] - is invisible to the people who matter most. Their competitors are visible. They're not. Your questions help them feel that gap. The sale follows naturally.

**Ask. Listen. Let them sell themselves.**

---

## Output Format Rules

Always output in this exact order:

```
PART 1: MEDIA VISIBILITY REPORT
CLIENT-FACING REPORT - Send this to the prospect before the call
[Full report]

---

PART 2: INTERNAL SALES SCRIPT
INTERNAL SALES SCRIPT - For the sales rep only. DO NOT share with the prospect.
[Full script]
```

---

## Quality Rules

1. **Search thoroughly before writing anything.** Both documents live or die on real data.
2. **Never fabricate** media mentions, review counts, or competitor details. If unverifiable, leave it out or note "at least X based on indexed results."
3. **Numbers must match exactly** across both documents. If the report says a competitor has 18 mentions, the script says 18 everywhere.
4. **No follow-up questions** unless input is genuinely ambiguous. Just do the work.
5. **No em dashes** in output. Use regular dashes or commas instead.
6. **Report = professional and data-driven.** Script = conversational and natural.
7. **Every script question must use real names and data** from research. No generic placeholders.
8. **Script must include WHY THIS WORKS, COACHING NOTE, and KEY INSIGHT boxes** after important dialogue sections.
9. **Number questions sequentially** across the entire script (QUESTION 1 through QUESTION 12+).
10. **All dialogue must be in italics inside blockquotes.**

---

## Claude Code Implementation Notes

### Architecture: 3-Step Pipeline

This tool is implemented as three Python scripts in `execution/`:

```
Input: prospect info (firm name, city, practice area, URL)
         |
         v
[execution/research.py]        <- Claude API call 1 (with web_search)
  - Runs Steps 1A-1E of this SOP
  - Outputs structured JSON dossier to .tmp/{slug}_dossier.json
         |
         v
[execution/generate_docs.py]   <- Two Claude API calls (no web search)
  Call A: reads dossier -> generates Part 1 (Report)
  Call B: reads dossier -> generates Part 2 (Script)
  - Saves combined output to .tmp/{slug}_output.md
         |
         v
[execution/sales_prep.py]      <- Entry point (orchestrates both)
```

### How to Run

```bash
# Full run (research + both documents)
python execution/sales_prep.py "Firm Name, City ST, Practice Area, https://url.com"
python execution/sales_prep.py "https://www.firmwebsite.com"

# Skip research, reuse an existing dossier
python execution/sales_prep.py --skip-research .tmp/firm_dossier.json

# Interactive mode (prompts for input)
python execution/sales_prep.py
```

### Token Budget Per Call

| Script | Call | max_tokens | Purpose |
|--------|------|-----------|---------|
| research.py | Research | 8,000 | Web research + JSON dossier output |
| generate_docs.py | Report | 6,000 | Client-facing report (Step 2) |
| generate_docs.py | Script | 10,000 | Internal NEPQ sales script (Step 3) |

Total: ~24,000 output tokens per prospect across 3 API calls.

### Why This Architecture

- **Research cached separately**: If doc generation fails, re-run with `--skip-research` - no need to repeat the expensive web search step
- **Numbers match exactly**: Both documents read from the same JSON dossier, so figures are guaranteed consistent
- **Focused system prompts**: Each call gets only the relevant SOP section (research / report / script), improving output quality
- **Streaming throughout**: All three calls stream output to the terminal so the user sees progress live

### Intermediate Files (.tmp/)

- `{slug}_dossier.json` - Structured research data (reusable)
- `{slug}_output.md` - Final combined Part 1 + Part 2 document
- `raw_research_{timestamp}.txt` - Only written if JSON parsing fails (debug artifact)