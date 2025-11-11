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
        max_tokens: int = 16000,
        temperature: float = 1.0,
        use_thinking: bool = True,
        thinking_budget: int = 10000
    ):
        """
        Initialize the Evaluator Agent.

        Args:
            skill_name: Name of the Claude skill to use
            model: Claude model ID
            max_tokens: Maximum tokens for response (must be > thinking_budget, default: 16000)
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

        # Validate that max_tokens > thinking_budget when thinking is enabled
        if use_thinking and max_tokens <= thinking_budget:
            raise ValueError(
                f"max_tokens ({max_tokens}) must be greater than thinking_budget ({thinking_budget}). "
                f"Recommended: max_tokens >= thinking_budget + 5000 to allow for response content."
            )

        # Initialize Anthropic client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic(api_key=api_key)

        thinking_status = f"enabled (budget: {thinking_budget})" if use_thinking else "disabled"
        logger.info(f"Initialized EvaluatorAgent with skill: {skill_name}, model: {model}, max_tokens: {max_tokens}, thinking: {thinking_status}")

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
            # Single company - detailed prompt with explicit steps
            return f"""Step 1: Read /mnt/skills/user/{self.skill_name}/SKILL.md
Step 2: Read /mnt/skills/user/{self.skill_name}/references/investment-criteria.md
Step 3: Use your thinking process to plan your research strategy
Step 4: Evaluate the company below following the evaluation framework EXACTLY

DO NOT SKIP STEPS 1, 2, AND 3.

Company to evaluate:
{companies[0].to_context_string()}

CRITICAL RESEARCH REQUIREMENTS (minimum 4-6 tool calls):
- web_fetch the company website
- web_search for company info (employees, location, services)
- web_search specifically for PE/VC funding or acquisitions
- web_search for ownership structure and leadership
- LinkedIn search for employee count verification
- Additional searches as needed for thorough evaluation

THINKING REQUIREMENTS:
- Use thinking to plan your research strategy before starting
- Use thinking to reason through EACH criterion from investment-criteria.md
- Use thinking to weigh conflicting information
- Use thinking to arrive at a well-reasoned verdict

Provide your verdict (GREEN/YELLOW/RED) and a detailed rationale that includes specific metrics:
- Employee count (verify via LinkedIn if possible)
- Revenue estimates (if discoverable)
- Ownership structure (founder-led, PE-backed, recently acquired, etc.)
- Key strengths or concerns based on investment criteria
- Overall assessment (2-4 sentences with evidence)

Format your response EXACTLY like this:
VERDICT: [GREEN/YELLOW/RED]
RATIONALE: [Your detailed rationale with specific metrics and assessment]"""

        else:
            # Multiple companies - structured prompt with explicit steps
            company_sections = []
            for i, company in enumerate(companies, 1):
                company_sections.append(f"""COMPANY #{i}: {company.name}
{company.to_context_string()}
""")

            prompt = f"""Step 1: Read /mnt/skills/user/{self.skill_name}/SKILL.md
Step 2: Read /mnt/skills/user/{self.skill_name}/references/investment-criteria.md
Step 3: Use your thinking process to plan your research strategy for each company
Step 4: Evaluate each company below following the evaluation framework EXACTLY

DO NOT SKIP STEPS 1, 2, AND 3.

Companies to evaluate:
{"".join(company_sections)}

CRITICAL RESEARCH REQUIREMENTS FOR EACH COMPANY (minimum 4-6 tool calls per company):
- web_fetch the company website
- web_search for company info (employees, location, services)
- web_search specifically for PE/VC funding or acquisitions
- web_search for ownership structure and leadership
- LinkedIn search for employee count verification
- Additional searches as needed for thorough evaluation

THINKING REQUIREMENTS:
- Use thinking to plan your research strategy for each company
- Use thinking to reason through EACH criterion from investment-criteria.md
- Use thinking to weigh conflicting information
- Use thinking to arrive at well-reasoned verdicts

For EACH company, provide:
1. A verdict: GREEN ✅ (pursue), YELLOW ⚠️ (research more), or RED ❌ (pass)
2. A detailed rationale that includes specific metrics:
   - Employee count (verify via LinkedIn if possible)
   - Revenue estimates (if discoverable)
   - Ownership structure (founder-led, PE-backed, recently acquired, etc.)
   - Key strengths or concerns based on investment criteria
   - Overall assessment (2-4 sentences with evidence)

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
        system_prompt = f"""You are an expert at evaluating acquisition targets for private equity and investment firms.

You have access to the company evaluation skill at:
- /mnt/skills/user/{self.skill_name}/SKILL.md
- /mnt/skills/user/{self.skill_name}/references/investment-criteria.md

CRITICAL PROCESS (DO NOT SKIP):
1. ALWAYS start by reading BOTH skill files using the file_read tool
2. Use your thinking process to plan your research strategy
3. Follow the evaluation framework EXACTLY as written in SKILL.md
4. Conduct thorough research (minimum 4-6 tool calls):
   - web_fetch the company website
   - web_search for company info (employees, location, services)
   - web_search specifically for PE/VC funding or acquisitions
   - web_search for ownership structure and leadership
   - web_search LinkedIn for employee count verification
   - Additional research as needed for comprehensive evaluation
5. Use thinking to reason through EACH criterion from investment-criteria.md systematically
6. Use thinking to weigh conflicting information and arrive at a well-reasoned verdict
7. Output ONLY the Verdict and Rationale in the exact format specified

Available tools: web_search, web_fetch, file_read

QUALITY REQUIREMENTS:
- Use extended thinking throughout the evaluation process
- Include specific metrics: employee count, revenue estimates, ownership details
- Verify information from multiple sources when possible
- Check specifically for PE/VC backing or recent acquisitions (disqualifiers)
- Provide evidence-based rationales (2-4 sentences)
- Be clear and actionable in your verdicts"""

        logger.debug(f"Calling Claude API with prompt length: {len(prompt)} chars")

        # Build API call parameters
        # NOTE: We do NOT pass tools parameter here - the skill system provides
        # web_search, web_fetch, and file_read automatically when the skill is loaded.
        # Adding tools parameter would require a multi-turn conversation loop.
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

        # Extract thinking content, response text, and tool calls
        thinking_blocks = []
        response_text = None
        tool_calls = []

        for content_block in message.content:
            if content_block.type == "thinking":
                thinking_blocks.append(content_block.thinking)
                logger.info(f"Thinking output ({len(content_block.thinking)} chars): {content_block.thinking[:200]}...")
            elif content_block.type == "text":
                response_text = content_block.text
            elif content_block.type == "tool_use":
                tool_calls.append({
                    "name": content_block.name,
                    "input": content_block.input
                })

        if not response_text:
            # Fallback for older format
            response_text = message.content[0].text if message.content else ""

        # Validate extended thinking was used
        if self.use_thinking and not thinking_blocks:
            logger.warning(
                "⚠️  NO THINKING DETECTED: Extended thinking is enabled but no thinking blocks found. "
                "Results may lack depth and reasoning quality."
            )
        elif thinking_blocks:
            total_thinking_chars = sum(len(block) for block in thinking_blocks)
            logger.info(f"✓ Extended thinking used: {len(thinking_blocks)} blocks, {total_thinking_chars} total characters")

        # Validate research depth (minimum 4 tool calls recommended)
        tool_use_count = len(tool_calls)
        if tool_use_count < 4:
            logger.warning(
                f"⚠️  INSUFFICIENT RESEARCH: Only {tool_use_count} tool calls made. "
                f"Recommended minimum: 4-6 tool calls for thorough evaluation. "
                f"Results may be incomplete or less accurate."
            )
        else:
            logger.info(f"✓ Research depth adequate: {tool_use_count} tool calls made")

        # Log tool calls for debugging
        if tool_calls:
            logger.debug("Tool calls made:")
            for i, call in enumerate(tool_calls, 1):
                logger.debug(f"  {i}. {call['name']}: {call['input']}")

        # Validate PE/VC funding search
        pe_search_found = any(
            'funding' in str(call['input']).lower() or
            'investor' in str(call['input']).lower() or
            'private equity' in str(call['input']).lower() or
            'venture capital' in str(call['input']).lower() or
            'pe-backed' in str(call['input']).lower() or
            'vc-backed' in str(call['input']).lower() or
            'acquisition' in str(call['input']).lower()
            for call in tool_calls if call['name'] in ['web_search', 'web_fetch']
        )

        if not pe_search_found:
            logger.warning(
                "⚠️  NO PE/VC SEARCH DETECTED: No searches found for funding/investors/PE/VC. "
                "This is a critical disqualifier that should be checked for every company."
            )
        else:
            logger.info("✓ PE/VC funding search performed")

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
