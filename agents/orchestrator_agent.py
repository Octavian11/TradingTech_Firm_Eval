#!/usr/bin/env python3
"""
Orchestrator Agent - Coordinates the multi-agent workflow.

This agent is responsible for:
- Coordinating between ExcelManager and EvaluatorAgent
- Managing batch processing (1-3 companies at a time)
- Progress tracking and reporting
- Error recovery and retry logic

This is the main coordinator that runs the entire screening process.
"""

import time
import logging
from typing import Optional

from .excel_manager import ExcelManager, Company
from .evaluator_agent import EvaluatorAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Agent that orchestrates the company screening workflow."""

    def __init__(
        self,
        excel_manager: ExcelManager,
        evaluator_agent: EvaluatorAgent,
        batch_size: int = 2,
        delay_seconds: float = 1.0
    ):
        """
        Initialize the Orchestrator.

        Args:
            excel_manager: ExcelManager instance
            evaluator_agent: EvaluatorAgent instance
            batch_size: Number of companies to process per batch (1-3 recommended)
            delay_seconds: Delay between batches for rate limiting
        """
        self.excel_manager = excel_manager
        self.evaluator_agent = evaluator_agent
        self.batch_size = min(max(1, batch_size), 3)  # Clamp to 1-3
        self.delay_seconds = delay_seconds

        logger.info(f"Initialized OrchestratorAgent with batch_size={self.batch_size}, "
                   f"delay={self.delay_seconds}s")

    def run(self) -> dict:
        """
        Run the complete screening workflow.

        Returns:
            Dictionary with execution statistics
        """
        logger.info("=" * 60)
        logger.info("STARTING INVESTMENT SCREENING WORKFLOW")
        logger.info("=" * 60)

        start_stats = self.excel_manager.get_statistics()
        logger.info(f"Initial state: {start_stats['pending']} pending companies")

        batch_count = 0
        total_processed = 0
        total_errors = 0

        while True:
            # Get next batch of pending companies
            companies = self.excel_manager.get_pending_companies(limit=self.batch_size)

            if not companies:
                logger.info("No more pending companies to process")
                break

            batch_count += 1
            company_names = [c.name for c in companies]

            logger.info(f"Processing batch #{batch_count}: {company_names}")

            try:
                # Evaluate the batch
                results = self.evaluator_agent.evaluate_batch(companies)

                # Update Excel with results
                self.excel_manager.update_results(results)

                # Count successes and errors
                for result in results:
                    if result.processed == "Yes":
                        total_processed += 1
                        logger.info(f"  ✓ {company_names[results.index(result)]}: {result.verdict}")
                    else:
                        total_errors += 1
                        logger.error(f"  ✗ {company_names[results.index(result)]}: Error")

            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                total_errors += len(companies)

            # Rate limiting delay (except for last batch)
            remaining = self.excel_manager.get_statistics()['pending']
            if remaining > 0 and self.delay_seconds > 0:
                logger.debug(f"Waiting {self.delay_seconds}s before next batch...")
                time.sleep(self.delay_seconds)

        # Final statistics
        final_stats = self.excel_manager.get_statistics()

        logger.info("=" * 60)
        logger.info("WORKFLOW COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Batches processed: {batch_count}")
        logger.info(f"Companies processed: {total_processed}")
        logger.info(f"Errors: {total_errors}")
        logger.info(f"Pending: {final_stats['pending']}")
        logger.info("")
        logger.info("VERDICTS:")
        logger.info(f"  GREEN ✅: {final_stats['green']}")
        logger.info(f"  YELLOW ⚠️: {final_stats['yellow']}")
        logger.info(f"  RED ❌: {final_stats['red']}")
        logger.info("=" * 60)

        return {
            "batches": batch_count,
            "processed": total_processed,
            "errors": total_errors,
            "statistics": final_stats
        }

    def process_single_batch(self, company_indices: Optional[list] = None) -> dict:
        """
        Process a single batch (useful for testing or manual control).

        Args:
            company_indices: Optional list of row indices to process.
                           If None, gets next pending batch.

        Returns:
            Dictionary with batch results
        """
        if company_indices:
            # Manual selection - not implemented yet
            raise NotImplementedError("Manual company selection not yet supported")

        companies = self.excel_manager.get_pending_companies(limit=self.batch_size)

        if not companies:
            logger.info("No pending companies")
            return {"processed": 0, "errors": 0}

        logger.info(f"Processing single batch: {[c.name for c in companies]}")

        results = self.evaluator_agent.evaluate_batch(companies)
        self.excel_manager.update_results(results)

        success_count = sum(1 for r in results if r.processed == "Yes")
        error_count = sum(1 for r in results if r.processed == "Error")

        return {
            "processed": success_count,
            "errors": error_count,
            "results": results
        }

    def get_progress(self) -> dict:
        """
        Get current progress statistics.

        Returns:
            Dictionary with progress info
        """
        stats = self.excel_manager.get_statistics()

        progress_pct = (stats['processed'] / stats['total'] * 100) if stats['total'] > 0 else 0

        return {
            "total": stats['total'],
            "processed": stats['processed'],
            "pending": stats['pending'],
            "progress_percentage": round(progress_pct, 1),
            "verdicts": {
                "green": stats['green'],
                "yellow": stats['yellow'],
                "red": stats['red']
            }
        }
