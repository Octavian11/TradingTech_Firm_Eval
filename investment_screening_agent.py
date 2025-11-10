#!/usr/bin/env python3
"""
Investment Screening Agent

Automated tool that reads company data from Excel, evaluates each company
using Claude AI's "company-evaluator" skill, and writes verdicts back to Excel.

Verdicts:
- GREEN ✅: Worth pursuing for acquisition
- YELLOW ⚠️: Requires more research
- RED ❌: Pass on this opportunity
"""

import os
import sys
import time
from typing import Optional, Dict, Any
import pandas as pd
from anthropic import Anthropic
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('screening_agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class InvestmentScreeningAgent:
    """Agent that screens companies for investment potential using Claude AI."""

    def __init__(self,
                 excel_path: str,
                 skill_name: str = "company-evaluator",
                 model: str = "claude-sonnet-4-5-20250929",
                 max_tokens: int = 4096):
        """
        Initialize the screening agent.

        Args:
            excel_path: Path to the Excel file with company data
            skill_name: Name of the Claude skill to use
            model: Claude model ID
            max_tokens: Maximum tokens for responses
        """
        self.excel_path = excel_path
        self.skill_name = skill_name
        self.model = model
        self.max_tokens = max_tokens

        # Initialize Anthropic client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic(api_key=api_key)

        # Load Excel data
        self.df = None
        self.load_excel()

    def load_excel(self):
        """Load the Excel file into a pandas DataFrame."""
        try:
            self.df = pd.read_excel(self.excel_path)
            logger.info(f"Loaded Excel file: {self.excel_path}")
            logger.info(f"Found {len(self.df)} companies to process")

            # Ensure required columns exist
            required_columns = ["Name", "Verdict", "Rationale", "Processed?"]
            for col in required_columns:
                if col not in self.df.columns:
                    self.df[col] = None if col != "Processed?" else "No"

            # Initialize Processed? column if needed
            if self.df["Processed?"].isna().all():
                self.df["Processed?"] = "No"

        except FileNotFoundError:
            logger.error(f"Excel file not found: {self.excel_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading Excel file: {e}")
            raise

    def save_excel(self):
        """Save the DataFrame back to Excel."""
        try:
            self.df.to_excel(self.excel_path, index=False, engine='openpyxl')
            logger.info(f"Saved results to: {self.excel_path}")
        except Exception as e:
            logger.error(f"Error saving Excel file: {e}")
            raise

    def build_company_context(self, row: pd.Series) -> str:
        """
        Build context string from company data.

        Args:
            row: DataFrame row containing company data

        Returns:
            Formatted context string
        """
        context_parts = []

        if pd.notna(row.get("Name")):
            context_parts.append(f"Company Name: {row['Name']}")

        if pd.notna(row.get("Location")):
            context_parts.append(f"Location: {row['Location']}")

        if pd.notna(row.get("Website")):
            context_parts.append(f"Website: {row['Website']}")

        if pd.notna(row.get("Revenue")):
            context_parts.append(f"Revenue: {row['Revenue']}")

        if pd.notna(row.get("Deep Research")):
            context_parts.append(f"Additional Research: {row['Deep Research']}")

        if pd.notna(row.get("Notes")):
            context_parts.append(f"Notes: {row['Notes']}")

        return "\n".join(context_parts)

    def evaluate_company(self, company_context: str, company_name: str) -> Dict[str, str]:
        """
        Evaluate a company using Claude AI with the company-evaluator skill.

        Args:
            company_context: Company information context
            company_name: Name of the company

        Returns:
            Dictionary with 'verdict' and 'rationale'
        """
        system_prompt = f"""You have access to the '{self.skill_name}' skill.
Use this skill to evaluate the company for investment/acquisition potential.

IMPORTANT: Your response must include:
1. A clear verdict: GREEN ✅ (pursue), YELLOW ⚠️ (research more), or RED ❌ (pass)
2. A rationale: 2-4 sentences explaining your verdict

Format your response EXACTLY like this:
VERDICT: [GREEN/YELLOW/RED]
RATIONALE: [Your 2-4 sentence explanation]"""

        user_prompt = f"""Evaluate this company for investment/acquisition:

{company_context}

Provide your verdict (GREEN/YELLOW/RED) and rationale (2-4 sentences)."""

        try:
            logger.info(f"Evaluating: {company_name}")

            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )

            response_text = message.content[0].text
            logger.info(f"Received response for: {company_name}")
            logger.debug(f"Response: {response_text}")

            # Parse the response
            verdict, rationale = self.parse_response(response_text)

            return {
                "verdict": verdict,
                "rationale": rationale
            }

        except Exception as e:
            logger.error(f"Error evaluating {company_name}: {e}")
            return {
                "verdict": "ERROR",
                "rationale": f"Error during evaluation: {str(e)}"
            }

    def parse_response(self, response_text: str) -> tuple[str, str]:
        """
        Parse Claude's response to extract verdict and rationale.

        Args:
            response_text: Raw response from Claude

        Returns:
            Tuple of (verdict, rationale)
        """
        verdict = "UNKNOWN"
        rationale = response_text

        # Try to extract verdict
        lines = response_text.strip().split('\n')
        for line in lines:
            line_upper = line.upper().strip()
            if 'VERDICT:' in line_upper:
                verdict_text = line.split(':', 1)[1].strip().upper()
                if 'GREEN' in verdict_text:
                    verdict = "GREEN ✅"
                elif 'YELLOW' in verdict_text:
                    verdict = "YELLOW ⚠️"
                elif 'RED' in verdict_text:
                    verdict = "RED ❌"
                break

        # If verdict not found in structured format, check entire text
        if verdict == "UNKNOWN":
            text_upper = response_text.upper()
            if 'GREEN' in text_upper:
                verdict = "GREEN ✅"
            elif 'YELLOW' in text_upper:
                verdict = "YELLOW ⚠️"
            elif 'RED' in text_upper:
                verdict = "RED ❌"

        # Try to extract rationale
        for line in lines:
            if 'RATIONALE:' in line.upper():
                rationale = line.split(':', 1)[1].strip()
                # Get remaining lines too
                idx = lines.index(line)
                if idx < len(lines) - 1:
                    rationale += " " + " ".join(lines[idx+1:])
                break

        # Clean up rationale
        rationale = rationale.strip()

        return verdict, rationale

    def process_all_companies(self, skip_processed: bool = True, delay_seconds: float = 1.0):
        """
        Process all companies in the Excel file.

        Args:
            skip_processed: If True, skip companies marked as "Yes" in Processed?
            delay_seconds: Delay between API calls to avoid rate limits
        """
        total = len(self.df)
        processed_count = 0
        skipped_count = 0
        error_count = 0

        logger.info(f"Starting processing of {total} companies...")

        for idx, row in self.df.iterrows():
            company_name = row.get("Name", f"Company {idx+1}")

            # Skip if already processed
            if skip_processed and str(row.get("Processed?", "No")).upper() == "YES":
                logger.info(f"Skipping already processed: {company_name}")
                skipped_count += 1
                continue

            # Build context and evaluate
            try:
                company_context = self.build_company_context(row)

                if not company_context.strip():
                    logger.warning(f"No data for company at row {idx+1}, skipping")
                    skipped_count += 1
                    continue

                result = self.evaluate_company(company_context, company_name)

                # Update DataFrame
                self.df.at[idx, "Verdict"] = result["verdict"]
                self.df.at[idx, "Rationale"] = result["rationale"]
                self.df.at[idx, "Processed?"] = "Yes" if result["verdict"] != "ERROR" else "Error"

                # Save incrementally
                self.save_excel()

                processed_count += 1

                if result["verdict"] == "ERROR":
                    error_count += 1

                logger.info(f"Progress: {processed_count}/{total-skipped_count} | {company_name} → {result['verdict']}")

                # Rate limiting delay
                if idx < len(self.df) - 1:  # Don't delay after last item
                    time.sleep(delay_seconds)

            except Exception as e:
                logger.error(f"Unexpected error processing {company_name}: {e}")
                self.df.at[idx, "Processed?"] = "Error"
                error_count += 1
                self.save_excel()

        # Final summary
        logger.info("=" * 60)
        logger.info("PROCESSING COMPLETE")
        logger.info(f"Total companies: {total}")
        logger.info(f"Processed: {processed_count}")
        logger.info(f"Skipped (already done): {skipped_count}")
        logger.info(f"Errors: {error_count}")
        logger.info("=" * 60)

    def get_summary_stats(self) -> Dict[str, int]:
        """Get summary statistics of verdicts."""
        stats = {
            "total": len(self.df),
            "processed": len(self.df[self.df["Processed?"] == "Yes"]),
            "green": len(self.df[self.df["Verdict"].str.contains("GREEN", na=False)]),
            "yellow": len(self.df[self.df["Verdict"].str.contains("YELLOW", na=False)]),
            "red": len(self.df[self.df["Verdict"].str.contains("RED", na=False)]),
            "error": len(self.df[self.df["Processed?"] == "Error"]),
            "pending": len(self.df[self.df["Processed?"] == "No"])
        }
        return stats


def main():
    """Main entry point for the investment screening agent."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Automated investment screening using Claude AI"
    )
    parser.add_argument(
        "excel_file",
        help="Path to Excel file with company data"
    )
    parser.add_argument(
        "--skill",
        default="company-evaluator",
        help="Name of Claude skill to use (default: company-evaluator)"
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-5-20250929",
        help="Claude model to use"
    )
    parser.add_argument(
        "--reprocess",
        action="store_true",
        help="Reprocess companies even if already processed"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between API calls (default: 1.0)"
    )

    args = parser.parse_args()

    try:
        # Initialize agent
        agent = InvestmentScreeningAgent(
            excel_path=args.excel_file,
            skill_name=args.skill,
            model=args.model
        )

        # Process all companies
        agent.process_all_companies(
            skip_processed=not args.reprocess,
            delay_seconds=args.delay
        )

        # Print summary
        stats = agent.get_summary_stats()
        print("\n" + "=" * 60)
        print("SUMMARY STATISTICS")
        print("=" * 60)
        print(f"Total companies: {stats['total']}")
        print(f"Processed: {stats['processed']}")
        print(f"Pending: {stats['pending']}")
        print(f"Errors: {stats['error']}")
        print()
        print(f"GREEN ✅ (pursue): {stats['green']}")
        print(f"YELLOW ⚠️ (research): {stats['yellow']}")
        print(f"RED ❌ (pass): {stats['red']}")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
