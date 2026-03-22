#!/usr/bin/env python3
"""
Sales Prep Tool - PersonalBranding.com
Generates a Client-Facing Media Visibility Report and Internal NEPQ Sales Script
for a given law firm prospect.

Usage:
    python execution/generate_sales_prep.py "Firm Name, City ST, Practice Area, https://url.com"
    python execution/generate_sales_prep.py "https://www.firmwebsite.com"
    python execution/generate_sales_prep.py  # will prompt for input
"""

import sys
import os
import re
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(Path(__file__).parent.parent / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not found. Add it to your .env file.")
    sys.exit(1)

# Read the full SOP to use as the system prompt
SOP_PATH = Path(__file__).parent.parent / "directives" / "sales_prep_tool.md"
with open(SOP_PATH, "r") as f:
    SOP_CONTENT = f.read()

SYSTEM_PROMPT = f"""You are the PersonalBranding.com Sales Prep Tool.

When given a law firm name, location, practice area, and/or website URL, you will:
1. Research the firm and competitors using web search
2. Generate a Client-Facing Media Visibility Report
3. Generate an Internal NEPQ Sales Script

Follow all instructions in this SOP exactly:

{SOP_CONTENT}
"""

def generate_sales_prep(prospect_input: str) -> None:
    """
    Generate the sales prep documents for a given prospect.
    Streams the output to stdout and saves to .tmp/.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    print(f"\n{'='*70}")
    print(f"PersonalBranding.com Sales Prep Tool")
    print(f"Researching: {prospect_input}")
    print(f"{'='*70}\n")
    print("Researching prospect and competitors (this takes 60-120 seconds)...\n")

    full_response = ""

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
            }
        ],
        messages=[
            {
                "role": "user",
                "content": prospect_input,
            }
        ],
    ) as stream:
        for event in stream:
            if event.type == "content_block_start":
                if hasattr(event, "content_block"):
                    if event.content_block.type == "tool_use":
                        tool_name = event.content_block.name
                        if tool_name == "web_search":
                            print("[Searching web...]", end="", flush=True)
            elif event.type == "content_block_delta":
                if hasattr(event, "delta"):
                    if event.delta.type == "text_delta":
                        text = event.delta.text
                        print(text, end="", flush=True)
                        full_response += text
                    elif event.delta.type == "input_json_delta":
                        # Tool input being streamed - show query when available
                        pass
            elif event.type == "content_block_stop":
                pass

        final_message = stream.get_final_message()

    print(f"\n\n{'='*70}")
    print(f"Generation complete. Tokens used: {final_message.usage.output_tokens} output / {final_message.usage.input_tokens} input")
    print(f"{'='*70}\n")

    # Save to .tmp/
    if full_response:
        tmp_dir = Path(__file__).parent.parent / ".tmp"
        tmp_dir.mkdir(exist_ok=True)

        # Create a safe filename from the prospect input
        safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", prospect_input[:50]).strip("_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = tmp_dir / f"{safe_name}_{timestamp}.md"

        with open(output_path, "w") as f:
            f.write(f"# Sales Prep: {prospect_input}\n")
            f.write(f"Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')}\n\n")
            f.write(full_response)

        print(f"Saved to: {output_path}")


def main():
    if len(sys.argv) > 1:
        prospect_input = " ".join(sys.argv[1:])
    else:
        print("PersonalBranding.com Sales Prep Tool")
        print("-" * 40)
        print("Enter prospect info (any of the following formats):")
        print("  Pacific Cascade Legal, Portland OR, Family Law, https://example.com")
        print("  https://www.smithjoneslaw.com -- personal injury firm in Dallas")
        print("  https://www.johnsonlawgroup.com")
        print()
        prospect_input = input("Prospect info: ").strip()

    if not prospect_input:
        print("No input provided. Exiting.")
        sys.exit(1)

    generate_sales_prep(prospect_input)


if __name__ == "__main__":
    main()
