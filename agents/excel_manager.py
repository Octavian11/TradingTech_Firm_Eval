#!/usr/bin/env python3
"""
ExcelManager Agent - Handles all Excel file I/O operations.

This agent is responsible for:
- Reading company data from Excel files
- Writing evaluation results back to Excel
- Tracking processing status
- Managing incremental saves

No API calls - purely file operations.
"""

import pandas as pd
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Company:
    """Represents a single company to evaluate."""
    index: int
    name: str
    location: Optional[str] = None
    website: Optional[str] = None
    revenue: Optional[str] = None
    deep_research: Optional[str] = None
    notes: Optional[str] = None

    def to_context_string(self) -> str:
        """Convert company data to a context string for Claude."""
        parts = [f"Company Name: {self.name}"]

        if self.location:
            parts.append(f"Location: {self.location}")
        if self.website:
            parts.append(f"Website: {self.website}")
        if self.revenue:
            parts.append(f"Revenue: {self.revenue}")
        if self.deep_research:
            parts.append(f"Additional Research: {self.deep_research}")
        if self.notes:
            parts.append(f"Notes: {self.notes}")

        return "\n".join(parts)


@dataclass
class EvaluationResult:
    """Represents evaluation results for a company."""
    index: int
    verdict: str
    rationale: str
    processed: str  # "Yes", "No", or "Error"
    est_revenue: str = ""  # Estimated revenue for user manual review
    est_employees: str = ""  # Estimated employee count for user manual review


class ExcelManager:
    """Agent responsible for all Excel file operations."""

    def __init__(self, excel_path: str):
        """
        Initialize the Excel Manager.

        Args:
            excel_path: Path to the Excel file
        """
        self.excel_path = excel_path
        self.df = None
        self._ensure_columns()

    def _ensure_columns(self):
        """Load Excel and ensure all required columns exist."""
        try:
            self.df = pd.read_excel(self.excel_path)
            logger.info(f"Loaded Excel file: {self.excel_path}")
            logger.info(f"Found {len(self.df)} rows")

            # Ensure required columns exist
            required_columns = {
                "Name": None,
                "Location": None,
                "Website": None,
                "Revenue": None,
                "Deep Research": None,
                "Notes": None,
                "Verdict": None,
                "Rationale": None,
                "Est Revenue Claude": None,
                "Est Employees Claude": None,
                "Processed?": "No"
            }

            for col, default_value in required_columns.items():
                if col not in self.df.columns:
                    self.df[col] = default_value
                    logger.info(f"Added missing column: {col}")

            # Initialize Processed? column if all empty
            if self.df["Processed?"].isna().all():
                self.df["Processed?"] = "No"

        except FileNotFoundError:
            logger.error(f"Excel file not found: {self.excel_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading Excel: {e}")
            raise

    def get_pending_companies(self, limit: Optional[int] = None) -> List[Company]:
        """
        Get companies that haven't been processed yet.

        Args:
            limit: Maximum number of companies to return (None = all)

        Returns:
            List of Company objects that need processing
        """
        # Filter for unprocessed companies (handle NaN/None values)
        # Exclude both completed ("YES") and failed ("ERROR") companies
        processed_col = self.df["Processed?"].fillna("No").astype(str)
        pending_mask = (processed_col.str.upper() != "YES") & \
                      (processed_col.str.upper() != "ERROR") & \
                      (self.df["Name"].notna())

        pending_df = self.df[pending_mask]

        if limit:
            pending_df = pending_df.head(limit)

        companies = []
        for idx, row in pending_df.iterrows():
            company = Company(
                index=idx,
                name=str(row["Name"]),
                location=str(row["Location"]) if pd.notna(row["Location"]) else None,
                website=str(row["Website"]) if pd.notna(row["Website"]) else None,
                revenue=str(row["Revenue"]) if pd.notna(row["Revenue"]) else None,
                deep_research=str(row["Deep Research"]) if pd.notna(row["Deep Research"]) else None,
                notes=str(row["Notes"]) if pd.notna(row["Notes"]) else None,
            )
            companies.append(company)

        logger.info(f"Retrieved {len(companies)} pending companies")
        return companies

    def update_results(self, results: List[EvaluationResult]) -> None:
        """
        Update Excel with evaluation results.

        Args:
            results: List of EvaluationResult objects
        """
        for result in results:
            self.df.at[result.index, "Verdict"] = result.verdict
            self.df.at[result.index, "Rationale"] = result.rationale
            self.df.at[result.index, "Est Revenue Claude"] = result.est_revenue
            self.df.at[result.index, "Est Employees Claude"] = result.est_employees
            self.df.at[result.index, "Processed?"] = result.processed

            logger.info(f"Updated row {result.index}: {result.verdict}")

        self.save()

    def save(self) -> None:
        """Save the DataFrame back to Excel."""
        try:
            self.df.to_excel(self.excel_path, index=False, engine='openpyxl')
            logger.debug(f"Saved to: {self.excel_path}")
        except Exception as e:
            logger.error(f"Error saving Excel: {e}")
            raise

    def get_statistics(self) -> Dict[str, int]:
        """Get summary statistics."""
        # Convert columns to string to handle NaN/None values safely
        processed_col = self.df["Processed?"].fillna("No").astype(str)
        verdict_col = self.df["Verdict"].fillna("").astype(str)

        stats = {
            "total": len(self.df),
            "processed": len(self.df[processed_col.str.upper() == "YES"]),
            "pending": len(self.df[processed_col.str.upper() == "NO"]),
            "error": len(self.df[processed_col.str.upper() == "ERROR"]),
            "green": len(self.df[verdict_col.str.contains("GREEN", case=False)]),
            "yellow": len(self.df[verdict_col.str.contains("YELLOW", case=False)]),
            "red": len(self.df[verdict_col.str.contains("RED", case=False)]),
        }
        return stats

    def reload(self) -> None:
        """Reload the Excel file from disk."""
        self._ensure_columns()
        logger.info("Reloaded Excel file")
