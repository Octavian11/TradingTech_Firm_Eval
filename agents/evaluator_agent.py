#!/usr/bin/env python3
"""
Evaluator Agent - Handles Claude API calls for company evaluation.

This agent is responsible for:
- Making API calls to Claude with company-evaluator skill
- Processing 1-3 companies per batch to avoid context window issues
- Parsing Claude's responses into structured verdicts
- Error handling for API failures

No file operations - purely API interactions.
"""

import os
import logging
from typing import List, Dict
from anthropic import Anthropic

from .excel_manager import Company, EvaluationResult

logger = logging.getLogger(__name__)


class EvaluatorAgent:
    """Agent responsible for evaluating companies via Claude API."""

    def __init__(
        self,
        skill_name: str = "company-evaluator",
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 4096,
        temperature: float = 1.0,
        use_thinking: bool = True,
        thinking_budget: int = 10000
    ):
        """
        Initialize the Evaluator Agent.

        Args:
            skill_name: Name of the Claude skill to use
            model: Claude model ID
            max_tokens: Maximum tokens for response
            temperature: Sampling temperature
            use_thinking: Enable extended thinking for better reasoning (default: True)
            thinking_budget: Token budget for thinking (default: 10000)
        """
        self.skill_name = skill_name
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.use_thinking = use_thinking
        self.thinking_budget = thinking_budget

        # Initialize Anthropic client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic(api_key=api_key)

        thinking_status = f"enabled (budget: {thinking_budget})" if use_thinking else "disabled"
        logger.info(f"Initialized EvaluatorAgent with skill: {skill_name}, model: {model}, thinking: {thinking_status}")

    def evaluate_batch(self, companies: List[Company]) -> List[EvaluationResult]:
        """
        Evaluate a batch of 1-3 companies.

        Args:
            companies: List of Company objects (max 3 recommended)

        Returns:
            List of EvaluationResult objects
        """
        if not companies:
            logger.warning("Empty batch provided to evaluate_batch")
            return []

        if len(companies) > 3:
            logger.warning(f"Batch size {len(companies)} exceeds recommended limit of 3")

        logger.info(f"Evaluating batch of {len(companies)} companies")

        try:
            # Build the prompt for this batch
            prompt = self._build_batch_prompt(companies)

            # Call Claude API
            response_text = self._call_claude_api(prompt)

            # Parse the response
            results = self._parse_batch_response(response_text, companies)

            return results

        except Exception as e:
            logger.error(f"Error evaluating batch: {e}")
            # Return error results for all companies in batch
            return [
                EvaluationResult(
                    index=company.index,
                    verdict="ERROR",
                    rationale=f"API error: {str(e)}",
                    processed="Error"
                )
                for company in companies
            ]

    def _build_batch_prompt(self, companies: List[Company]) -> str:
        """Build prompt for evaluating multiple companies."""
        if len(companies) == 1:
            # Single company - simpler prompt
            return f"""Use the "company-evaluator" skill to evaluate this company for investment/acquisition.

IMPORTANT: First read all skill files to understand the evaluation criteria and research process.

{companies[0].to_context_string()}

Provide your verdict (GREEN/YELLOW/RED) and a detailed rationale that includes specific metrics when available:
- Employee count (if discoverable)
- Revenue estimates (if available)
- Ownership structure (founder-led, PE-backed, etc.)
- Key strengths or concerns
- Overall assessment (2-4 sentences)

Format your response EXACTLY like this:
VERDICT: [GREEN/YELLOW/RED]
RATIONALE: [Your detailed rationale with specific metrics and assessment]"""

        else:
            # Multiple companies - structured prompt
            company_sections = []
            for i, company in enumerate(companies, 1):
                company_sections.append(f"""COMPANY #{i}: {company.name}
{company.to_context_string()}
""")

            prompt = f"""Use the "company-evaluator" skill to evaluate these {len(companies)} companies for investment/acquisition.

IMPORTANT: First read all skill files to understand the evaluation criteria and research process.

{"".join(company_sections)}

For EACH company, provide:
1. A verdict: GREEN ✅ (pursue), YELLOW ⚠️ (research more), or RED ❌ (pass)
2. A detailed rationale that includes specific metrics when available:
   - Employee count (if discoverable)
   - Revenue estimates (if available)
   - Ownership structure (founder-led, PE-backed, etc.)
   - Key strengths or concerns
   - Overall assessment (2-4 sentences)

Format your response EXACTLY like this:

COMPANY #1: {companies[0].name}
VERDICT: [GREEN/YELLOW/RED]
RATIONALE: [Your detailed rationale with specific metrics and assessment]

COMPANY #2: {companies[1].name}
VERDICT: [GREEN/YELLOW/RED]
RATIONALE: [Your detailed rationale with specific metrics and assessment]
""" + (f"""
COMPANY #3: {companies[2].name}
VERDICT: [GREEN/YELLOW/RED]
RATIONALE: [Your detailed rationale with specific metrics and assessment]
""" if len(companies) > 2 else "")

            return prompt

    def _call_claude_api(self, prompt: str) -> str:
        """
        Make API call to Claude.

        Args:
            prompt: The prompt to send

        Returns:
            Response text from Claude
        """
        system_prompt = f"""You have access to the "company-evaluator" skill.

IMPORTANT INSTRUCTIONS:
1. First read all skill files to understand the evaluation criteria and research methodology
2. Use the "company-evaluator" skill to thoroughly evaluate companies for investment/acquisition potential
3. Conduct comprehensive research including:
   - Company website and online presence
   - Employee count and team information
   - Revenue estimates and financial data
   - Ownership structure (founder-led, PE/VC-backed, etc.)
   - Market positioning and competitive advantages
4. Provide detailed rationales (2-4 sentences) with specific metrics and findings
5. Follow the exact format requested in the user prompt
6. Be clear and actionable in your verdicts"""

        logger.debug(f"Calling Claude API with prompt length: {len(prompt)} chars")

        # Build API call parameters
        api_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        # Add thinking parameter if enabled
        if self.use_thinking:
            api_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": self.thinking_budget
            }
            logger.debug(f"Extended thinking enabled with budget: {self.thinking_budget} tokens")

        message = self.client.messages.create(**api_params)

        # Extract thinking content if present
        thinking_content = None
        response_text = None

        for content_block in message.content:
            if content_block.type == "thinking":
                thinking_content = content_block.thinking
                logger.info(f"Thinking output ({len(thinking_content)} chars): {thinking_content[:200]}...")
            elif content_block.type == "text":
                response_text = content_block.text

        if not response_text:
            # Fallback for older format
            response_text = message.content[0].text if message.content else ""

        # Log token usage (including thinking tokens if present)
        usage_msg = f"API call complete. Tokens: {message.usage.input_tokens} in, {message.usage.output_tokens} out"
        if self.use_thinking and hasattr(message.usage, 'thinking_tokens'):
            usage_msg += f", {message.usage.thinking_tokens} thinking"
        logger.info(usage_msg)

        return response_text

    def _parse_batch_response(
        self,
        response_text: str,
        companies: List[Company]
    ) -> List[EvaluationResult]:
        """
        Parse Claude's response for multiple companies.

        Args:
            response_text: Raw response from Claude
            companies: List of Company objects that were evaluated

        Returns:
            List of EvaluationResult objects
        """
        results = []

        if len(companies) == 1:
            # Single company - simple parsing
            verdict, rationale = self._parse_single_verdict(response_text)
            results.append(EvaluationResult(
                index=companies[0].index,
                verdict=verdict,
                rationale=rationale,
                processed="Yes" if verdict != "ERROR" else "Error"
            ))
        else:
            # Multiple companies - parse each section
            sections = self._split_response_by_company(response_text, companies)

            for company, section_text in zip(companies, sections):
                verdict, rationale = self._parse_single_verdict(section_text)
                results.append(EvaluationResult(
                    index=company.index,
                    verdict=verdict,
                    rationale=rationale,
                    processed="Yes" if verdict != "ERROR" else "Error"
                ))

        return results

    def _parse_single_verdict(self, text: str) -> tuple[str, str]:
        """
        Parse verdict and rationale from text.

        Returns:
            Tuple of (verdict, rationale)
        """
        verdict = "UNKNOWN"
        rationale = text.strip()

        lines = text.strip().split('\n')

        # Try to extract verdict
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
            text_upper = text.upper()
            if 'GREEN' in text_upper and '✅' not in text_upper:
                verdict = "GREEN ✅"
            elif 'YELLOW' in text_upper and '⚠️' not in text_upper:
                verdict = "YELLOW ⚠️"
            elif 'RED' in text_upper and '❌' not in text_upper:
                verdict = "RED ❌"

        # Try to extract rationale
        for i, line in enumerate(lines):
            if 'RATIONALE:' in line.upper():
                rationale_parts = [line.split(':', 1)[1].strip()]
                # Get remaining lines until next section
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() and not lines[j].strip().startswith('COMPANY'):
                        rationale_parts.append(lines[j].strip())
                    else:
                        break
                rationale = " ".join(rationale_parts)
                break

        # Clean up rationale
        rationale = rationale.strip()
        if not rationale:
            rationale = "No rationale provided."

        return verdict, rationale

    def _split_response_by_company(
        self,
        response_text: str,
        companies: List[Company]
    ) -> List[str]:
        """
        Split response text into sections for each company.

        Args:
            response_text: Full response text
            companies: List of companies

        Returns:
            List of text sections, one per company
        """
        sections = []
        lines = response_text.split('\n')

        current_section = []
        company_idx = 0

        for line in lines:
            # Check if this line starts a new company section
            if f"COMPANY #{company_idx + 2}" in line.upper() and company_idx < len(companies) - 1:
                # Save current section
                sections.append('\n'.join(current_section))
                current_section = [line]
                company_idx += 1
            else:
                current_section.append(line)

        # Save last section
        if current_section:
            sections.append('\n'.join(current_section))

        # Ensure we have the right number of sections
        while len(sections) < len(companies):
            sections.append("")

        return sections[:len(companies)]
