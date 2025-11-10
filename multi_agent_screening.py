#!/usr/bin/env python3
"""
Multi-Agent Investment Screening System

This script uses a three-agent architecture to screen companies:
1. ExcelManager - Handles all Excel file I/O
2. EvaluatorAgent - Makes Claude API calls (processes 1-3 companies per batch)
3. OrchestratorAgent - Coordinates the workflow

Benefits of multi-agent architecture:
- Avoids context window issues by processing small batches
- Separates concerns (file I/O, API calls, coordination)
- Better error handling and recovery
- Incremental progress saving
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add agents directory to path
sys.path.insert(0, str(Path(__file__).parent / "agents"))

from agents import ExcelManager, EvaluatorAgent, OrchestratorAgent


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application."""
    log_level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('multi_agent_screening.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Reduce noise from external libraries
    logging.getLogger('anthropic').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)


def main():
    """Main entry point for the multi-agent screening system."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Investment Screening System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with default settings (batch size 2)
  python multi_agent_screening.py companies.xlsx

  # Process 1 company at a time (smallest context window)
  python multi_agent_screening.py companies.xlsx --batch-size 1

  # Process 3 companies at a time (faster, larger context)
  python multi_agent_screening.py companies.xlsx --batch-size 3

  # Use custom skill and longer delay
  python multi_agent_screening.py companies.xlsx --skill my-evaluator --delay 2.0

  # Verbose logging for debugging
  python multi_agent_screening.py companies.xlsx --verbose
        """
    )

    parser.add_argument(
        "excel_file",
        help="Path to Excel file with company data"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=2,
        choices=[1, 2, 3],
        help="Number of companies to process per API call (default: 2). "
             "Smaller batches = smaller context windows but slower."
    )
    parser.add_argument(
        "--skill",
        default="company-evaluator",
        help="Name of Claude skill to use (default: company-evaluator)"
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-5-20250929",
        help="Claude model to use (default: claude-sonnet-4-5-20250929)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between batches for rate limiting (default: 1.0)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=1.0,
        help="Sampling temperature 0.0-1.0 (default: 1.0)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Validate API key
        if not os.environ.get("ANTHROPIC_API_KEY"):
            logger.error("ANTHROPIC_API_KEY environment variable not set")
            logger.error("Please set your API key:")
            logger.error("  export ANTHROPIC_API_KEY=sk-ant-api03-xxx...")
            sys.exit(1)

        # Validate Excel file exists
        if not Path(args.excel_file).exists():
            logger.error(f"Excel file not found: {args.excel_file}")
            sys.exit(1)

        logger.info("Initializing Multi-Agent Screening System")
        logger.info(f"Configuration:")
        logger.info(f"  Excel file: {args.excel_file}")
        logger.info(f"  Batch size: {args.batch_size} companies per API call")
        logger.info(f"  Skill: {args.skill}")
        logger.info(f"  Model: {args.model}")
        logger.info(f"  Delay: {args.delay}s between batches")
        logger.info("")

        # Initialize agents
        logger.info("Initializing agents...")

        excel_manager = ExcelManager(excel_path=args.excel_file)
        logger.info("  ✓ ExcelManager initialized")

        evaluator_agent = EvaluatorAgent(
            skill_name=args.skill,
            model=args.model,
            temperature=args.temperature
        )
        logger.info("  ✓ EvaluatorAgent initialized")

        orchestrator = OrchestratorAgent(
            excel_manager=excel_manager,
            evaluator_agent=evaluator_agent,
            batch_size=args.batch_size,
            delay_seconds=args.delay
        )
        logger.info("  ✓ OrchestratorAgent initialized")
        logger.info("")

        # Run the workflow
        results = orchestrator.run()

        # Print summary
        print("\n" + "=" * 60)
        print("SCREENING COMPLETE")
        print("=" * 60)
        print(f"Batches processed: {results['batches']}")
        print(f"Companies processed: {results['processed']}")
        print(f"Errors: {results['errors']}")
        print()
        stats = results['statistics']
        print(f"Total companies: {stats['total']}")
        print(f"Processed: {stats['processed']}")
        print(f"Pending: {stats['pending']}")
        print()
        print("VERDICTS:")
        print(f"  GREEN ✅ (pursue): {stats['green']}")
        print(f"  YELLOW ⚠️ (research): {stats['yellow']}")
        print(f"  RED ❌ (pass): {stats['red']}")
        print("=" * 60)
        print(f"\nResults saved to: {args.excel_file}")
        print(f"Log file: multi_agent_screening.log")

        sys.exit(0)

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user. Progress has been saved.")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
