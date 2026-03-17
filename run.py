#!/usr/bin/env python3
import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="PPP Candidate Briefing Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python run.py candidates.csv\n"
            "  python run.py candidates.csv --output results.json\n"
            "  python run.py candidates.csv --model claude-opus-4-5\n"
        ),
    )
    parser.add_argument("csv_file", help="Path to candidates CSV")
    parser.add_argument("--output", "-o", default="output.json", help="Output path (default: output.json)")
    parser.add_argument("--model", "-m", default="claude-sonnet-4-5", help="Claude model (default: claude-sonnet-4-5)")

    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"Error: CSV not found: {csv_path}")
        sys.exit(1)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set. Add it to your .env file.")
        sys.exit(1)

    try:
        from agent.pipeline import run_pipeline
    except ImportError as e:
        print(f"Missing dependency: {e}\nRun: pip install -r requirements.txt")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  PPP Candidate Briefing Agent")
    print(f"  Model:  {args.model}")
    print(f"  Input:  {args.csv_file}")
    print(f"  Output: {args.output}")
    print(f"{'='*60}\n")

    try:
        output = run_pipeline(csv_path=str(csv_path), output_path=args.output, model=args.model)
        print(f"\nDone. {len(output.get('candidates', []))} briefings generated.")
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()