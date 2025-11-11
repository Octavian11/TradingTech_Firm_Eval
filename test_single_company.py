#!/usr/bin/env python3
"""
Quick test script to evaluate a single company.
Tests the EvaluatorAgent with all the Desktop-consistency improvements.
"""

import os
import logging
from dotenv import load_dotenv
from agents.evaluator_agent import EvaluatorAgent
from agents.excel_manager import Company

# Load environment variables
load_dotenv()

# Set up logging to see all the validation warnings and info
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_company_evaluation():
    """Test evaluating EZX Inc."""

    # Check API key is set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY not set in environment or .env file")
        return

    logger.info("=" * 80)
    logger.info("Testing Company Evaluation with Desktop-Consistency Improvements")
    logger.info("=" * 80)

    # Create the evaluator agent
    evaluator = EvaluatorAgent(
        skill_name="company-evaluator",
        model="claude-sonnet-4-5-20250929",
        max_tokens=16000,
        temperature=1.0,
        use_thinking=True,
        thinking_budget=10000
    )

    logger.info("✓ EvaluatorAgent initialized")

    # Create the test company
    test_company = Company(
        index=1,
        name="EZX Inc.",
        location="Westfield, NJ",
        website="https://www.ezxinc.com",
        revenue=None,
        deep_research=None,
        notes=None
    )

    logger.info(f"\n{'=' * 80}")
    logger.info("COMPANY TO EVALUATE:")
    logger.info(f"{'=' * 80}")
    logger.info(test_company.to_context_string())
    logger.info(f"{'=' * 80}\n")

    # Evaluate the company
    logger.info("Starting evaluation...")
    logger.info("Watch for these quality indicators:")
    logger.info("  ✓ Extended thinking used")
    logger.info("  ✓ Research depth adequate (4+ tool calls)")
    logger.info("  ✓ PE/VC funding search performed")
    logger.info("")

    results = evaluator.evaluate_batch([test_company])

    # Print results
    logger.info(f"\n{'=' * 80}")
    logger.info("EVALUATION RESULTS:")
    logger.info(f"{'=' * 80}")

    if results:
        result = results[0]
        logger.info(f"Verdict: {result.verdict}")
        logger.info(f"Rationale: {result.rationale}")
        logger.info(f"Status: {result.processed}")
    else:
        logger.error("No results returned")

    logger.info(f"{'=' * 80}\n")

if __name__ == "__main__":
    test_company_evaluation()
