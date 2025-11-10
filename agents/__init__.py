"""
Multi-Agent System for Investment Screening

This package contains three specialized agents that work together:

1. ExcelManager: Handles all Excel file I/O operations
2. EvaluatorAgent: Makes Claude API calls with company-evaluator skill
3. OrchestratorAgent: Coordinates the workflow between agents

The multi-agent architecture ensures:
- Separation of concerns (file I/O vs API calls vs coordination)
- Small context windows (1-3 companies per API call)
- Better error handling and recovery
- Scalability for large datasets
"""

from .excel_manager import ExcelManager, Company, EvaluationResult
from .evaluator_agent import EvaluatorAgent
from .orchestrator_agent import OrchestratorAgent

__all__ = [
    'ExcelManager',
    'Company',
    'EvaluationResult',
    'EvaluatorAgent',
    'OrchestratorAgent',
]
