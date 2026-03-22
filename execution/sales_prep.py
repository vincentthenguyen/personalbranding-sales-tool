#!/usr/bin/env python3
"""
PersonalBranding.com Sales Prep Tool - Entry Point
Orchestrates research + document generation for a law firm prospect.

Usage:
    # Full run (research + both docs)
    python execution/sales_prep.py "Firm Name, City ST, Practice Area, https://..."
    python execution/sales_prep.py "https://www.firmwebsite.com"

    # Skip research, reuse an existing dossier
    python execution/sales_prep.py --skip-research .tmp/firm_dossier.json

    # Interactive mode (no args)
    python execution/sales_prep.py
"""

import sys
import os
import argparse
from pathlib import Path

# Allow importing sibling modules
sys.path.insert(0, str(Path(__file__).parent))

from research import run_research
from generate_docs import run_generation
from generate_pdf import generate_pdfs


def list_dossiers(tmp_dir: Path) -> list[Path]:
    """Return all dossier files in .tmp/, sorted newest first."""
    return sorted(tmp_dir.glob("*_dossier.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def pick_dossier_interactively(tmp_dir: Path) -> Path:
    """Show available dossiers and let user pick one."""
    dossiers = list_dossiers(tmp_dir)
    if not dossiers:
        print("No dossiers found in .tmp/. Run without --skip-research first.")
        sys.exit(1)

    print("\nAvailable dossiers in .tmp/:")
    for i, d in enumerate(dossiers, 1):
        mtime = d.stat().st_mtime
        from datetime import datetime
        ts = datetime.fromtimestamp(mtime).strftime("%b %d, %Y %I:%M %p")
        print(f"  {i}. {d.name} ({ts})")

    print()
    choice = input("Enter number or full path: ").strip()

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(dossiers):
            return dossiers[idx]
        else:
            print("Invalid selection.")
            sys.exit(1)
    else:
        p = Path(choice)
        if p.exists():
            return p
        print(f"File not found: {choice}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="PersonalBranding.com Sales Prep Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python execution/sales_prep.py "Pacific Cascade Legal, Portland OR, Family Law"
  python execution/sales_prep.py "https://www.smithjoneslaw.com"
  python execution/sales_prep.py --skip-research .tmp/pacific_cascade_legal_dossier.json
        """
    )
    parser.add_argument(
        "prospect",
        nargs="?",
        help="Prospect info: firm name, city, practice area, and/or URL"
    )
    parser.add_argument(
        "--skip-research",
        metavar="DOSSIER",
        nargs="?",
        const="",
        help="Skip research and use an existing dossier file (optional: path to dossier)"
    )

    args = parser.parse_args()
    tmp_dir = Path(__file__).parent.parent / ".tmp"
    tmp_dir.mkdir(exist_ok=True)

    dossier_path = None

    # --- Determine mode ---
    if args.skip_research is not None:
        # --skip-research mode
        if args.skip_research:
            # Path provided: --skip-research .tmp/firm_dossier.json
            dossier_path = Path(args.skip_research)
            if not dossier_path.exists():
                print(f"ERROR: Dossier not found: {dossier_path}")
                sys.exit(1)
        else:
            # --skip-research with no path: show picker
            dossier_path = pick_dossier_interactively(tmp_dir)

        print(f"\nUsing existing dossier: {dossier_path}")

    else:
        # Research mode - need prospect input
        if args.prospect:
            prospect_input = args.prospect
        else:
            # Interactive mode
            print("PersonalBranding.com Sales Prep Tool")
            print("-" * 45)
            print("Enter prospect info (any format):")
            print("  Pacific Cascade Legal, Portland OR, Family Law, https://example.com")
            print("  https://www.smithjoneslaw.com -- personal injury firm in Dallas")
            print("  https://www.johnsonlawgroup.com")
            print()
            prospect_input = input("Prospect info: ").strip()

        if not prospect_input:
            print("No input provided. Exiting.")
            sys.exit(1)

        dossier_path = run_research(prospect_input)

    # --- Generate documents ---
    output_path = run_generation(dossier_path)

    # --- Generate PDFs ---
    report_pdf, script_pdf = generate_pdfs(output_path)

    # --- Done ---
    print(f"\n{'='*65}")
    print("COMPLETE")
    print(f"Dossier:  {dossier_path}")
    print(f"Output:   {output_path}")
    print(f"Report:   {report_pdf}")
    if script_pdf:
        print(f"Script:   {script_pdf}")
    print(f"{'='*65}")
    print("\nNext steps:")
    print("  Report PDF: Send to prospect before the call")
    print("  Script PDF: For the rep only - DO NOT share")

    os.system("afplay /System/Library/Sounds/Glass.aiff")


if __name__ == "__main__":
    main()
