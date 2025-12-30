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
import time
from typing import List, Dict
from anthropic import Anthropic, RateLimitError

from .excel_manager import Company, EvaluationResult
from .tool_executor import ToolExecutor, TOOL_DEFINITIONS

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

        # Initialize tool executor
        self.tool_executor = ToolExecutor()

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
                    est_revenue="Not found",
                    est_employees="Not found",
                    tier_fit="Not specified",
                    processed="Error"
                )
                for company in companies
            ]

    def _build_batch_prompt(self, companies: List[Company]) -> str:
        """Build prompt for evaluating multiple companies."""
        if len(companies) == 1:
            # Single company - detailed prompt with explicit steps
            return f"""Step 1: Read {self.skill_name}/SKILL.md
Step 2: Read {self.skill_name}/references/investment-criteria.md
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

**CRITICAL OUTPUT FORMATTING:**
- DO NOT include your thinking process, working notes, or evaluation steps in the final output
- DO NOT include headers like "FINAL EVALUATION" or "Based on my research"
- ONLY output the clean formatted verdict, revenue estimate, employee estimate, tier fit, and rationale below
- Rationale should be 2-4 concise sentences with key metrics

Format your response EXACTLY like this (and NOTHING ELSE):
VERDICT: [GREEN/YELLOW/RED]
EST_REVENUE: [e.g., "$33M" or "Not found" or "$10-20M" - for USER manual review, does NOT influence verdict]
EST_EMPLOYEES: [e.g., "17" or "Not found" or "11-50" - report what you found, this DOES influence verdict if <5 or >150]
TIER_FIT: [1A/1B/1C/1D/1E or 2A/2B/2C/2D or 3A/3B/3C or None - categorize company regardless of verdict]
RATIONALE: [2-4 concise sentences: employee count, ownership, PE/VC status, business model, key concern/strength]"""

        else:
            # Multiple companies - structured prompt with explicit steps
            company_sections = []
            for i, company in enumerate(companies, 1):
                company_sections.append(f"""COMPANY #{i}: {company.name}
{company.to_context_string()}
""")

            prompt = f"""Step 1: Read {self.skill_name}/SKILL.md
Step 2: Read {self.skill_name}/references/investment-criteria.md
Step 3: Use your thinking process to plan your research strategy for each company
Step 4: Evaluate each company below following the evaluation framework EXACTLY

DO NOT SKIP STEPS 1, 2, AND 3.

🚨 CRITICAL BATCH ISOLATION PROTOCOL 🚨
You are evaluating MULTIPLE companies in this batch. For EACH company:
1. **START FRESH** - Forget all research from previous companies in the batch
2. **VERIFY COMPANY NAME** - Every search result must mention THIS company's exact name
3. **NO COPY-PASTE** - Do NOT reuse rationale, research, or findings from previous companies
4. **SEPARATE RESEARCH** - Each company needs its OWN dedicated searches and analysis
5. **CHECK RATIONALE** - Final rationale should mention ONLY the target company (not other company names)

**COMMON BATCH PROCESSING ERROR TO AVOID:**
- ❌ Search results for Company A mention "FFL Partners" → Copy to Company B's rationale
- ❌ Rationale for Company B mentions Company A's details (merger, investor, offices, etc.)
- ✅ Each company gets completely independent research and rationale

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

**CRITICAL OUTPUT FORMATTING:**
- DO NOT include your thinking process, working notes, or evaluation steps in the final output
- DO NOT include headers like "FINAL EVALUATION" or "Based on my research"
- ONLY output the clean formatted verdicts, revenue estimates, employee estimates, tier fit, and rationales below
- Each rationale should be 2-4 concise sentences with key metrics

Format your response EXACTLY like this (and NOTHING ELSE):

COMPANY #1: {companies[0].name}
VERDICT: [GREEN/YELLOW/RED]
EST_REVENUE: [e.g., "$33M" or "Not found" or "$10-20M" - for USER manual review, does NOT influence verdict]
EST_EMPLOYEES: [e.g., "17" or "Not found" or "11-50" - report what you found, this DOES influence verdict if <5 or >150]
TIER_FIT: [1A/1B/1C/1D/1E or 2A/2B/2C/2D or 3A/3B/3C or None - categorize company regardless of verdict]
RATIONALE: [2-4 concise sentences: employee count, ownership, PE/VC status, business model, key concern/strength]

COMPANY #2: {companies[1].name}
VERDICT: [GREEN/YELLOW/RED]
EST_REVENUE: [e.g., "$33M" or "Not found" or "$10-20M" - for USER manual review, does NOT influence verdict]
EST_EMPLOYEES: [e.g., "17" or "Not found" or "11-50" - report what you found, this DOES influence verdict if <5 or >150]
TIER_FIT: [1A/1B/1C/1D/1E or 2A/2B/2C/2D or 3A/3B/3C or None - categorize company regardless of verdict]
RATIONALE: [2-4 concise sentences: employee count, ownership, PE/VC status, business model, key concern/strength]
""" + (f"""
COMPANY #3: {companies[2].name}
VERDICT: [GREEN/YELLOW/RED]
EST_REVENUE: [e.g., "$33M" or "Not found" or "$10-20M" - for USER manual review, does NOT influence verdict]
EST_EMPLOYEES: [e.g., "17" or "Not found" or "11-50" - report what you found, this DOES influence verdict if <5 or >150]
TIER_FIT: [1A/1B/1C/1D/1E or 2A/2B/2C/2D or 3A/3B/3C or None - categorize company regardless of verdict]
RATIONALE: [2-4 concise sentences: employee count, ownership, PE/VC status, business model, key concern/strength]
""" if len(companies) > 2 else "")

            return prompt

    def _call_claude_api(self, prompt: str) -> str:
        """
        Make API call to Claude with multi-turn tool handling.

        Implements a conversation loop:
        1. Send initial prompt with tools
        2. Execute any tool_use blocks Claude returns
        3. Send tool results back
        4. Repeat until Claude returns final text response

        Args:
            prompt: The prompt to send

        Returns:
            Response text from Claude
        """
        system_prompt = f"""You are an expert at evaluating acquisition targets for private equity and investment firms.

You have access to the company evaluation skill at:
- {self.skill_name}/SKILL.md
- {self.skill_name}/references/investment-criteria.md

CRITICAL PROCESS (DO NOT SKIP):
1. ALWAYS start by reading BOTH skill files using the file_read tool
2. Use thinking to plan your multi-stage research strategy
3. Follow the comprehensive search strategy from SKILL.md EXACTLY

**REFERENCE EXAMPLES - Learn from these before evaluating:**

⚠️ YELLOW EXAMPLE #1: Market Data Management Solutions (MDMS)
Company Profile:
- Location: New York, NY (US-based) ✓
- Size: 11-13 employees ✓
- Industry: Market data operations (Tier 1B fit) ✓

Why YELLOW - Family Office Exception (Not External PE):
- Search: site:pitchbook.com "Market Data Management Solutions" → Found PitchBook profile
- PitchBook snippet shows "Private Equity-Backed" label
- Search: "Market Data Management Solutions" "Private Equity-Backed" OR "VC-Backed" → Found 9 results mentioning PE
- Search: "Market Data Management Solutions" investor → Found "Vareton Group has invested"
- Search: "Vareton Group" "family office" OR "family investment" → Found evidence it's founders' family investment vehicle
- CRITICAL FINDING: Vareton Group is the FOUNDERS' FAMILY investment vehicle (not external PE firm)

**WHAT MAKES THIS YELLOW (NOT RED) - FAMILY OFFICE EXCEPTION:**
- ✓ Investor identified: "Vareton Group"
- ✓ BUT: Vareton is founders' FAMILY OFFICE / family investment vehicle
- ✓ Family offices = founders still control the company (not external PE takeover)
- ✓ This is an EXTREME EDGE CASE (highly unlikely to see in other companies)

**CRITICAL DISTINCTION - External PE vs Family Office:**
- EXTERNAL PE/VC firm (KKR, Accel Partners, Sequoia, Vista Equity) → RED ❌
  * Third-party investors control the company
  * Automatic disqualification
- FAMILY OFFICE of founders (family investment vehicle) → YELLOW ⚠️
  * Founders/family still control the company through their investment vehicle
  * Borderline case, needs verification
  * Example: MDMS + Vareton Group (founders' family office)

**HOW TO VERIFY FAMILY OFFICE:**
1. After finding PE investor name, search: "[Investor Name]" "family office"
2. Search: "[Investor Name]" "family investment vehicle" OR "founders' investment firm"
3. If confirmed family office → YELLOW (exception)
4. If external PE firm → RED (disqualified)

Verdict: YELLOW ⚠️ (borderline RED - elevated concern, but family office exception applies)
Rationale: NY-based market data operations provider (Tier 1B), 11-13 employees. PitchBook shows "Private Equity-Backed" label and Vareton Group identified as investor. However, Vareton Group is the founders' family investment vehicle (not external PE firm), so company remains founder/family-controlled. This is an extreme edge case qualifying for family office exception. Needs verification before advancing or ruling out.

Key Lesson: EXTERNAL PE/VC = RED. FAMILY OFFICE (founders' investment vehicle) = YELLOW exception. Always verify if investor is external PE firm or family office.

---

❌ RED EXAMPLE #1: BST Americas
Company Profile:
- Location: US-based ✓
- Size: ~13 employees ✓
- Industry: Market data/Bloomberg ecosystem ✓
- Ownership: Founder-owned, no PE/VC detected ✓

Why RED - Wrong Business Model (Management Consultant):
- Website analysis: "vendor contract negotiation", "cost optimization", "compliance advisory"
- Search: "BST Americas" "services" → Found "help clients negotiate better rates with Bloomberg"
- Search: "BST Americas" "optimization" → Found "invoice audit", "spend management"
- NO OPERATIONS FOUND: No "24/7 monitoring", no "we operate", no "production support"

CRITICAL DISTINCTION:
✗ "We help you negotiate Bloomberg contracts" = CONSULTING (not operations)
✗ "We optimize your vendor spending" = ADVISORY (not operations)
✗ "We audit your invoices" = CONSULTING (not operations)

Verdict: RED ❌
Rationale: Management consultancy providing vendor negotiation and cost optimization advisory services. Does NOT operate mission-critical infrastructure. Wrong business model - consulting, not operations.

Key Lesson: "Negotiation", "optimization", "advisory" = consulting red flags → RED

---

❌ RED EXAMPLE #2: Hypothetical PE-Backed Trading Tech Firm
Company Profile:
- Location: New York, NY (US-based) ✓
- Size: 35 employees ✓
- Industry: Trade surveillance operations (Tier 1D fit) ✓
- Business model: Managed services ✓

Why RED - Confirmed PE/VC Ownership (AUTOMATIC DISQUALIFICATION):
- Search: site:pitchbook.com "[Company Name]" → Found PitchBook profile
- PitchBook snippet: "Private Equity-Backed" label present
- Search: "[Company]" "Accel Partners" → Found press release
- CONFIRMED FINDING: "Accel Partners led $15M Series A investment, taking 40% equity stake"
- Additional confirmation: Company LinkedIn shows "Part of Accel portfolio" badge

CRITICAL DISTINCTION from MDMS example above:
- MDMS = PitchBook label but UNCERTAIN ownership → YELLOW (needs research)
- This company = PitchBook label + CONFIRMED equity stake → RED (disqualified)

Verdict: RED ❌
Rationale: Despite fitting Tier 1D category with 35 employees and managed services model, company has confirmed VC backing (Accel Partners owns 40% equity stake). Any confirmed equity PE/VC ownership = automatic disqualification regardless of other positive factors.

Key Lesson: CONFIRMED equity ownership (with investor name + stake %) = RED. Uncertain PE signals = YELLOW.

---

⚠️ YELLOW EXAMPLE #2: EZX Inc
Company Profile:
- Location: Westfield, NJ (US-based) ✓
- Size: 8-10 employees (verified via LinkedIn)
- Ownership: Founder-owned (Paul Savin, founded 2004), no PE/VC ✓
- Industry: Trading infrastructure/FIX connectivity ✓

Why YELLOW - Mixed Business Model:
- Website analysis: Found BOTH products AND services language
- Products found: iServer, FIXengine, FIXhub, EZX OMS (proprietary software)
- Services found: "delivered as a fully managed Service", "24/7 operations", "production monitoring"
- Search: "EZX Inc" "managed service" → Confirmed managed service delivery
- Search: "EZX Inc" "products software" → Confirmed multiple software products

BUSINESS MODEL CLASSIFICATION:
✓ Has proprietary software products (software vendor aspect)
✓ Has "fully managed service" delivery (operations aspect)
→ MIXED MODEL: Software + Services hybrid

Verdict: YELLOW ⚠️
Rationale: Founder-owned with no PE/VC backing. Small team (8-10 employees). Mixed business model with proprietary software products AND managed service delivery. Size and mixed model create uncertainty.

Key Lesson: Products + "managed service" language = YELLOW (not pure operations)

---

⚠️ YELLOW EXAMPLE #3: DataBP
Company Profile:
- Location: New York, NY (US-based) ✓
- Size: 29-32 employees (verified via LinkedIn and PitchBook)
- Industry: Market data licensing and administration platform (Tier 1) ✓

Why YELLOW - Debt Financing + Mixed Model (NOT Red - Debt is NOT disqualifying):
- Search: site:pitchbook.com "DataBP" → Found PitchBook profile
- Search: "DataBP" "SaaS Capital" → Found "MRR-based credit facility from SaaS Capital"
- Search: "DataBP" "SaaS Capital" equity OR investment → NO equity investment found
- Search: "DataBP" "SaaS Capital" debt OR "credit facility" → Confirmed it's DEBT financing (line of credit)
- CRITICAL FINDING: SaaS Capital provides DEBT (not equity) - company is still founder-owned
- Business model: Mixed platform (SaaS) + managed services for data operations

EQUITY vs DEBT ANALYSIS:
✓ SaaS Capital = Debt lender (MRR-based credit facility), NOT equity investor
✓ Company still founder-owned (debt doesn't transfer ownership)
✓ PitchBook profile exists, but only shows debt financing (not equity PE/VC)
✗ Mixed software platform + managed services model (unclear if services >70%)
✗ Employee count borderline/unclear in some sources (1-10 vs 29-32 conflicting data)

Verdict: YELLOW ⚠️
Rationale: US-based market data licensing platform serving exchanges (Tier 1B - Market Data Ops). Company has SaaS Capital credit facility (debt financing, NOT equity - still founder-owned). Mixed SaaS platform + managed services model where it's unclear if services exceed 70% threshold. Employee count needs verification. Debt financing alone does NOT disqualify - only equity PE/VC ownership disqualifies.

Key Lesson:
- Debt financing (SaaS Capital, credit facilities) ≠ Equity PE/VC → NOT automatic RED
- Always verify if lender/investor is providing DEBT or taking EQUITY
- PitchBook profiles can exist for debt-financed companies
- YELLOW for legitimate uncertainty (mixed model, unclear size), NOT for debt financing

---

✅ GREEN EXAMPLE (Hypothetical): MarketOps Solutions LLC
Company Profile:
- Location: Chicago, IL (US-based) ✓
- Size: 25 employees (verified via LinkedIn) ✓
- Ownership: Founder-owned (founded 2016), no PE/VC ✓
- Industry: Market data operations ✓

Why GREEN - Pure Operations Provider:
- Website analysis: "We operate your Bloomberg and Refinitiv platforms 24/7"
- Services found: "24/7 NOC for market data infrastructure", "production environment management"
- Search: "MarketOps Solutions" "we operate" → Found "we operate mission-critical trading infrastructure"
- Search: "MarketOps Solutions" "24/7" → Found "round-the-clock monitoring", "NOC team"
- Search: site:pitchbook.com "MarketOps Solutions" → NO profile found ✓
- Search: "MarketOps Solutions" "Private Equity-Backed" → NO results ✓

OPERATIONS INDICATORS FOUND:
✓ "We operate your platforms" (not "we help you select platforms")
✓ "24/7 monitoring and operations" (not "advisory services")
✓ "Production environment management" (not "vendor negotiation")
✓ "NOC team provides technical support" (not "staff augmentation")
✓ NO consulting/advisory language found
✓ NO proprietary software products (pure services)

Verdict: GREEN ✅
Rationale: US-based with 25 employees. Founder-owned with no PE/VC backing detected across comprehensive searches. Pure operations provider running mission-critical market data infrastructure 24/7 for clients. Clear Tier 1B fit (Market Data Ops) - platform operations with NOC and technical support team.

Key Lesson: "We operate" + "24/7" + NO products + NO PE/VC = GREEN (very rare!)

---

✅ GREEN EXAMPLE #2: Generic Network Systems (GNS)
Company Profile:
- Location: New York, NY (US-based) ✓
- Size: 20-25 employees (verified via LinkedIn) ✓
- Ownership: Founder-owned (founded 2001), no PE/VC ✓
- Industry: Boutique MSP for investment firms (Tier 2D or 3B) ✓

Why GREEN - Boutique Investment Ops Support:
- Website analysis: MSP services for hedge funds and asset managers
- Specialization: Geneva/Advent specialist (portfolio accounting systems for investment firms)
- Certifications: SOC 1 & 2 certified (shows operational maturity)
- Search: "Generic Network Systems" funding investors → NO PE/VC found ✓
- Search: site:pitchbook.com "Generic Network Systems" → NO profile found ✓
- Revenue: ~$6.3M (appropriate for 20-25 person boutique MSP)

TIER CLASSIFICATION:
- Tier 2D: Investment Ops Support (portfolio accounting operations for asset managers) → GREEN eligible
- OR Tier 3B: Boutique IT for financial firms → YELLOW eligible
- DECISION: Tier 2D fit (Geneva/Advent ops specialist) → GREEN

**CRITICAL LESSON - Don't confuse "generic MSP" with wrong business model:**
- "Generic Network Systems" (company name) ≠ "generic MSP" (wrong business model)
- This is a SPECIALIZED boutique MSP for investment firms (Tier 2D/3B)
- 20+ years in business (founded 2001), SOC certified, financial services specialist
- NO PE/VC detected → Passes ownership test
- Serves investment firms with portfolio accounting ops → Tier 2D (GREEN eligible)

Verdict: GREEN ✅
Rationale: NYC-based boutique MSP founded 2001, 20-25 employees, ~$6.3M revenue. Specializes in Geneva/Advent portfolio accounting operations for hedge funds and asset managers (Tier 2D - Investment Ops Support). SOC 1 & 2 certified. Founder-owned with no PE/VC backing detected. Perfect middle/back-office operations provider for investment firms.

Key Lesson: Boutique MSPs specializing in investment ops (Geneva/Advent, portfolio accounting) fit Tier 2D = GREEN eligible. Don't mark RED just because company name has "Generic" in it.

---

⚠️ YELLOW EXAMPLE #4: Apex Technology Services
Company Profile:
- Location: Norwalk, CT (US-based) ✓
- Size: ~10 employees ✓
- Ownership: Founder-owned (founded 2012), no PE/VC ✓
- Industry: Generic MSP with multiple verticals ✓

Why YELLOW - Tier 3B (Generalist MSP with Financial Vertical):
- Website analysis: MSP serving financial, medical, legal, and government sectors
- Search: "apex technology services" financial → Financial services is ONE of many verticals
- Search: "apex technology services" Norwalk → Confirmed CT-based (US headquarters) ✓
- Search: site:pitchbook.com "apex technology services" → NO profile found ✓
- Revenue: ~$5.1M, 10 employees (appropriate for small MSP)

TIER CLASSIFICATION:
- NOT Tier 1/2: Not specialized in trading/financial operations (serves medical, legal, government too)
- Tier 3B: Generalist MSP that INCLUDES financial clients among other verticals
- Per V2.0 criteria: Tier 3 (3A-3C) = YELLOW (adjacent services, selective)

**CRITICAL LESSON - Tier 3 = YELLOW (NOT RED):**
- Generic MSP serving multiple verticals (financial is just one) = Tier 3B
- Tier 3B is YELLOW (adjacent services, worth investigating further)
- Do NOT mark RED just because they're "generic MSP" or serve non-financial clients
- RED is for: (1) confirmed PE/VC, (2) consulting/advisory model, (3) too small (<5), (4) too large (>150)
- Generalist MSP with fin vertical = YELLOW (not RED)

Verdict: YELLOW ⚠️
Rationale: Norwalk CT-based MSP founded 2012, ~10 employees, ~$5.1M revenue. Generic MSP serving financial, medical, legal, and government sectors - NOT specialized in fintech operations. Financial services is just one of multiple verticals (Tier 3B - Generalist with fin vertical). Founder-owned, no PE/VC detected. YELLOW for Tier 3 classification (adjacent services, selective).

Key Lesson: Tier 3 = YELLOW (not RED). Generic MSPs with financial vertical fit Tier 3B and should be YELLOW for further research, not automatically disqualified.

---

**CRITICAL LESSONS FROM EXAMPLES:**

1. **PE/VC VERIFICATION - EXTERNAL PE = RED, FAMILY OFFICE = YELLOW EXCEPTION, DEBT = NOT disqualifying**

   **WHAT IS "EXTERNAL PE/VC" (AUTOMATIC RED):**
   - ✓ External PE/VC firm (KKR, Accel Partners, Sequoia, Vista Equity, etc.)
   - ✓ Evidence of equity ownership (any stake %, regardless of percentage)
   - ✓ Third-party investors control or own stake in company
   - ✓ Phrases: "majority stake", "minority stake", "investor", "backed by", "portfolio company", "Series A/B/C"

   **ALL PE/VC-RELATED LANGUAGE = RED (regardless of stake %)**
   - "majority stake" = RED
   - "minority stake" = RED
   - "investor" = RED
   - "backed by" = RED
   - "portfolio company" = RED
   - "lead investor" = RED
   - "strategic investor" = RED
   - Board seats without ownership % = RED

   **FAMILY OFFICE EXCEPTION (YELLOW, not RED) - EXTREME EDGE CASE:**
   - IF investor is founders' FAMILY OFFICE / family investment vehicle → YELLOW ⚠️
   - Founders/family still control company through their investment vehicle
   - NOT external PE takeover
   - **HOW TO VERIFY:** After finding PE investor, search "[Investor]" "family office"
   - Example: MDMS + Vareton Group (founders' family office) → YELLOW ⚠️ (not RED)
   - **NOTE:** This is EXTREMELY RARE - unlikely to encounter in other companies

   **DEBT FINANCING (NOT disqualifying - can be GREEN/YELLOW):**
   - SaaS Capital credit facility, bank loans, venture debt, revenue-based financing
   - Lender gets interest payments, NOT equity ownership
   - Company remains founder-owned → Still qualifies for GREEN/YELLOW

   Examples:
   * Company + "Accel Partners owns stake" (EXTERNAL PE) → RED ❌
   * Company + "minority investment by KKR" (EXTERNAL PE, any %) → RED ❌
   * Company + "strategic investor Sequoia" (EXTERNAL PE) → RED ❌
   * MDMS + Vareton Group (FAMILY OFFICE verified) → YELLOW ⚠️ (exception)
   * DataBP + SaaS Capital credit facility (DEBT, not equity) → YELLOW ⚠️ (for mixed model, not PE)

2. **TIER 3 = YELLOW (NOT RED) - Don't auto-disqualify generic MSPs**

   - **Tier 3A/3B/3C = YELLOW** (adjacent services, worth investigating further)
   - Generic MSP with financial vertical = Tier 3B = YELLOW (not RED)
   - RED is ONLY for: (1) confirmed PE/VC, (2) consulting/advisory model, (3) too small (<5), (4) too large (>150)
   - DO NOT mark RED just because they're "generic MSP" or serve multiple industries

   Examples:
   * Apex Tech: Generic MSP serving financial, medical, legal, government → Tier 3B = YELLOW ⚠️ (not RED)
   * Generic name doesn't mean RED (GNS = "Generic Network Systems" but specialized = GREEN)

3. **BOUTIQUE MSPs FOR INVESTMENT FIRMS = Can be GREEN (Tier 2D)**

   - Geneva/Advent portfolio accounting operations = Tier 2D (Investment Ops Support)
   - Back-office/middle-office ops for hedge funds = Tier 2D
   - Tier 2D is GREEN eligible (if all other criteria met)
   - Don't confuse "generic MSP" (Tier 3B) with "boutique investment ops MSP" (Tier 2D)

   Example:
   * GNS: Geneva/Advent specialist, 20-25 employees, SOC certified, no PE/VC → Tier 2D = GREEN ✅

4. Consulting/Advisory = RED, Operations = Potential GREEN (Example: BST vs MarketOps)
   - RED FLAGS: "negotiate contracts", "optimize spending", "advisory", "invoice audit", "staff augmentation"
   - GREEN FLAGS: "we operate", "24/7 monitoring", "production support", "NOC team", "we manage production"

5. Mixed Models = YELLOW (Examples: EZX, DataBP)
   - Software products + managed services = YELLOW
   - Size concerns (too small <5 or borderline employee count) = YELLOW
   - Mixed model uncertainty (unclear if services >70%) = YELLOW
   - When uncertain about business model → YELLOW

6. GREEN is EXTREMELY RARE (<5% of companies)
   - Must pass ALL criteria: size, location, no EQUITY PE/VC, pure operations OR boutique investment ops
   - Debt financing alone does NOT disqualify
   - When uncertain → Default to YELLOW, not GREEN
   - Only mark GREEN if 100% confident on all factors

**CRITICAL V2.0 TIER VERDICT RULES:**

GREEN ✅ Eligibility (Must meet ALL requirements):
- **Tier 1 (1A-1E) OR Tier 2 (2A-2D)** = GREEN eligible if all other criteria met
- 5-150 employees ✓
- US headquarters ✓
- Founder-owned (no equity PE/VC) ✓
- Managed services model ✓
- Institutional B2B clients ✓

YELLOW ⚠️ Cases:
- **Tier 3 (3A-3C)** = YELLOW (adjacent services, selective)
- Tier 1/2 with borderline size (3-5 or 120-150 employees)
- Tier 1/2 with mixed business model (products + services)
- Tier 1/2 with unclear PE/VC status (needs more research)
- Any genuine uncertainty about criteria

RED ❌ Automatic Disqualification:
- Equity PE/VC backing (confirmed)
- Non-US headquarters
- <5 or >150 employees with institutionalization
- Software product company (not services)
- Does NOT fit Tier 1, 2, or 3 (no fit = RED)
- Pure consulting/advisory (no ongoing operations) - BUT if mixed consulting + managed services → YELLOW
- Project-based only (no ongoing operations)

**IMPORTANT:** "Generic MSP" or "generalist IT" that serves financial clients = Tier 3B = YELLOW (NOT RED)

**KEY V2.0 CHANGE**: Tier 2 (middle/back-office operations like reconciliation, regulatory reporting, post-trade processing) is now GREEN eligible, not YELLOW. If a company fits Tier 2A/2B/2C/2D and meets all other criteria, mark it GREEN.

**MANDATORY SEARCH STRATEGY (10-12 searches minimum for GREEN verdict):**

STAGE 1: Initial Discovery (6-7 searches)
- web_fetch: Company website → Extract service/product language, team, offices
- web_search: "[Company]" [Location] employees services → Find LinkedIn URL, employee mentions
- web_search: "[Company]" site:linkedin.com/company employees → Get employee count (PRIMARY for verdict)
- web_search: "[Company]" founder CEO owner leadership → Identify key people, year founded
- web_search: "[Company]" revenue OR "$" OR "million" → Find revenue estimates
- web_search: "[Company]" employees count size team → Find additional employee count mentions

**CRITICAL CLARIFICATION - Revenue vs Employee Count:**

EMPLOYEE COUNT (DOES influence verdict):
- LinkedIn employee count is PRIMARY source for verdict decisions
- MUST be 5-150 employees to qualify for GREEN/YELLOW
- <5 employees = too small (automatic RED)
- >150 employees with institutionalization = too large (automatic RED)
- 100-150 employees = borderline (YELLOW)
- 3-5 employees = borderline (YELLOW - too small but worth investigating)
- Also extract employee count for EST_EMPLOYEES field (for user to verify your verdict)
- May be ranges like "11-50" or specific counts like "17"
- Use LinkedIn count for verdict sizing, but report all sources found

REVENUE (does NOT influence verdict - for USER manual review ONLY):
- Extract what you find: "$33M", "$10-20M", "Not found"
- Store ranges as-is, don't calculate midpoints
- DO NOT use revenue to influence verdict
- DO NOT analyze revenue-per-employee ratios
- Revenue is ONLY for USER post-screening manual analysis
- User will manually check for software vendor patterns (high $/employee)

STAGE 2: PE/VC Detection (CRITICAL - MANDATORY 4-6 searches)
**THIS IS THE MOST IMPORTANT SCREENING CRITERION - ANY EQUITY PE/VC = AUTOMATIC RED**

**🚨 CRITICAL: COMPANY NAME VERIFICATION (MANDATORY FOR EVERY SEARCH RESULT) 🚨**

**EVERY search result MUST mention the TARGET COMPANY by exact name. Do NOT cite information about different companies!**

**RULE #1: Verify company name BEFORE citing ANY information**
1. **Check exact company name in search result snippet**
   - Does the snippet mention the TARGET company by name?
   - Or does it mention a DIFFERENT company with similar positioning?
   - If snippet doesn't mention target company → DISCARD (do not cite this information)

2. **Common error pattern to AVOID - Wrong PE Attribution:**
   - ❌ WRONG: Target "Computronix USA" → Search "Computronix funding" → Result mentions "FFL Partners invested in Abacus Group" → ERROR: Attributing Abacus's PE to Computronix
   - ✅ CORRECT: Target "Computronix USA" → Search "Computronix USA" "FFL Partners" → No results linking them → No PE backing found
   - **WHY THIS MATTERS:** In batch processing, search results may return info about Company A when researching Company B

3. **Common error pattern to AVOID - Copy-Paste Rationale:**
   - ❌ WRONG: Evaluating CJC but rationale mentions "FFL Partners," "Medicus IT merger," "10+ office locations" (copied from Abacus Group)
   - ✅ CORRECT: Every company gets FRESH research mentioning that company's name ONLY
   - **RED FLAG:** If your rationale mentions company names OTHER than the target → You used the WRONG company's research

4. **If investor/PE firm appears in results:**
   - Search: "[TARGET COMPANY EXACT NAME]" "[Investor Name]"
   - Verify the investor is linked to THIS company, not a similar company
   - Example: Search "Computronix USA" "FFL Partners" (not just "Computronix" + "FFL")
   - Only cite PE backing if search result shows BOTH company name AND investor name in SAME sentence/snippet

5. **Only cite PE backing if ALL of these are true:**
   - Search result explicitly mentions the target company's exact name ✓
   - AND the investor/PE firm name ✓
   - AND evidence of equity ownership (stake %, "portfolio company", etc.) ✓
   - AND they appear in the same sentence/context (not just same page) ✓

**BATCH ISOLATION REMINDER:**
- If evaluating multiple companies in batch: FORGET previous companies, START FRESH
- Do NOT reuse research from Company A when evaluating Company B
- Each company needs its OWN dedicated searches with company name verification

**DO NOT attribute another company's PE backing to the target company!**

**CRITICAL DISTINCTION - EQUITY vs DEBT:**

EQUITY INVESTMENT = AUTOMATIC RED (DISQUALIFYING):
- Private Equity ownership (PE firms taking stake in company)
- Venture Capital investment (VC firms taking equity stake)
- Institutional investors owning company shares
- "Portfolio company" of PE/VC firms
- Sold to PE firm or taken over by VC-backed entity
- Keywords: "Private Equity-Backed", "VC-Backed", "Series A/B/C/D", "equity investment", "portfolio company"

DEBT FINANCING = NOT DISQUALIFYING (Yellow if uncertain, can be Green):
- Bank loans, lines of credit, credit facilities
- Revenue-based financing (RBF) / MRR-based credit lines
- Venture debt (debt, not equity - lender gets interest, NOT ownership)
- Equipment financing, working capital loans
- SaaS Capital credit facilities (MRR-based debt lending)
- Lighter Capital, Clearco, etc. (revenue-based lenders)
- Keywords: "credit facility", "line of credit", "debt financing", "loan", "MRR-based lending"

**WHY THIS MATTERS:**
- Equity PE/VC = Investor OWNS the company → Not founder-owned → RED
- Debt financing = Founder still OWNS company, just borrowed money → Still founder-owned → Can be GREEN/YELLOW
- Example: DataBP with SaaS Capital credit facility = DEBT (not equity) → Can be YELLOW (not auto-RED)
- Example: MDMS with Vareton Group equity = EQUITY PE-backed → RED

SEARCH 1: Broad funding search
- web_search: "[Company Name]" funding investors venture capital private equity

SEARCH 2: PitchBook direct search with EXACT company name (MANDATORY - DO NOT SKIP)
- web_search: site:pitchbook.com "[Full Legal Company Name]"
- Example: site:pitchbook.com "Market Data Management Solutions"
- PARSE SNIPPET CAREFULLY for: "Private Equity-Backed", "VC-Backed", "Financing Status", investor names, "The [Investor] has invested"
- **CRITICAL PAYWALL RULE - CHECK FOR EQUITY vs DEBT**:
  → If PitchBook profile EXISTS but snippet is vague/paywalled: INVESTIGATE FURTHER
  → Search for "[Company]" "equity" OR "investment" OR "portfolio company" vs "[Company]" "debt" OR "credit facility" OR "loan"
  → If you find EQUITY keywords → RED
  → If you find ONLY DEBT keywords (e.g., "SaaS Capital credit facility", "MRR-based lending") → NOT disqualifying → Can be YELLOW or GREEN
  → If uncertain after investigation → YELLOW (not GREEN, but also not auto-RED)
  → PitchBook profiles can exist for debt-financed companies (e.g., SaaS Capital clients)

SEARCH 3: PitchBook search with variations/acronyms (MANDATORY if Search 2 finds nothing)
- web_search: site:pitchbook.com "[Company Acronym]" OR "[Short Name]"
- Example: site:pitchbook.com "MDMS" OR "Market Data Management"
- Same PAYWALL RULE applies: Investigate for equity vs debt

SEARCH 4: Crunchbase search (MANDATORY)
- web_search: site:crunchbase.com "[Company Name]" funding
- PARSE SNIPPET for: funding rounds, investor names, "Last Funding Type"
- Check if "Last Funding Type" is equity (Series A/B/C, PE) vs debt (Venture Debt, Credit Line)

SEARCH 5: Portfolio company / acquisition check
- web_search: "[Company]" "portfolio company" OR "acquired by" OR "backed by"

SEARCH 6: Direct search for PE/VC status phrases (MANDATORY for GREEN verdicts)
- web_search: "[Company Name]" "Private Equity-Backed" OR "VC-Backed" OR "Financing Status"
- Example: "Market Data Management Solutions" "Private Equity-Backed" OR "VC-Backed"
- This catches paywalled information that leaked into web snippets, press releases, or databases

SEARCH 7: IF ANY investor/lender name appears → VERIFY IF EQUITY OR DEBT (MANDATORY)
- web_search: "[Company Name]" "[Investor/Lender Name]" equity OR investment OR ownership
- web_search: "[Company Name]" "[Investor/Lender Name]" debt OR loan OR "credit facility"
- Example for DEBT: "DataBP" "SaaS Capital" → Confirms MRR-based debt facility → NOT disqualifying

SEARCH 8: IF EQUITY PE/VC INVESTOR FOUND → VERIFY IF EXTERNAL PE OR FAMILY OFFICE (MANDATORY)
- web_search: "[Investor Name]" "family office" OR "family investment vehicle"
- web_search: "[Investor Name]" "[Company Founder Names]" family
- IF family office CONFIRMED → YELLOW ⚠️ (exception - founders still control via family vehicle)
- IF external PE firm → RED ❌ (automatic disqualification)
- Example for FAMILY OFFICE: "Vareton Group" "family office" → MDMS founders' family vehicle → YELLOW ⚠️
- Example for EXTERNAL PE: "Accel Partners" (VC firm) → RED ❌

**CRITICAL EQUITY PE/VC SNIPPET INDICATORS (Any one = CHECK IF FAMILY OFFICE, if not = RED):**
- "Private Equity-Backed" → Verify if family office, if not → RED
- "VC-Backed" → Verify if family office, if not → RED
- "The [PE/VC Firm] has invested in [Company]" → Verify if family office, if not → RED
- "raised $X in Series A/B/C/D" (equity rounds) → Verify if family office, if not → RED
- "[Company], a portfolio company of [PE/VC Firm]" → Verify if family office, if not → RED
- "backed by [PE/VC Firm]" → Verify if family office, if not → RED
- "led by [VC Firm]" → Verify if family office, if not → RED
- "majority stake" OR "minority stake" → Verify if family office, if not → RED
- "strategic investor" OR "lead investor" → Verify if family office, if not → RED
- "acquired by [PE Firm]" → RED (no family office exception for acquisitions)
- Equity investor names: Sequoia, Accel, a16z, KKR, Blackstone, Vista Equity, etc. → RED (external PE firms)

**DEBT FINANCING INDICATORS (NOT disqualifying - investigate but can be GREEN/YELLOW):**
- "SaaS Capital credit facility" (MRR-based debt) → NOT RED
- "revenue-based financing" or "RBF" → NOT RED
- "line of credit" or "credit facility" → NOT RED
- "venture debt" (debt, not equity) → NOT RED (but investigate to confirm it's debt)
- "Lighter Capital", "Clearco", "Pipe" (revenue-based lenders) → NOT RED
- "equipment loan" or "working capital loan" → NOT RED

**FAILSAFE FOR GREEN VERDICTS (Check BEFORE giving GREEN):**
Before marking a company GREEN, ask yourself these 10 questions:
1. Did I search PitchBook with the exact full company name? (site:pitchbook.com "[Full Name]")
2. Did I search PitchBook with variations/acronyms? (if exact name found nothing)
3. Did I search Crunchbase? (site:crunchbase.com)
4. **Did I find a PitchBook or Crunchbase profile for this company?**
   → If YES: INVESTIGATE - profile could indicate equity PE/VC OR just debt financing
   → Search for equity indicators: "[Company]" "equity" OR "investment" OR "portfolio company"
   → Search for debt indicators: "[Company]" "debt" OR "credit facility" OR "loan"
   → If EQUITY found → CHECK IF FAMILY OFFICE → If external PE = RED, if family office = YELLOW
   → If ONLY DEBT found (e.g., SaaS Capital credit facility) → Can be YELLOW or GREEN (debt is NOT disqualifying)
   → If uncertain → YELLOW (not GREEN)
5. Did I carefully parse ALL snippets for investor/lender names?
6. **If ANY investor/lender name appeared, did I verify if it's EQUITY or DEBT?**
   → Search: "[Company]" "[Name]" equity OR investment → If found → CHECK IF FAMILY OFFICE
   → Search: "[Company]" "[Name]" debt OR loan OR "credit facility" → If found → NOT disqualifying
   → Examples:
     - "Vareton Group" with MDMS → Search "Vareton" "family office" → Family office → YELLOW ⚠️
     - "Accel Partners" with Company X → External VC firm → RED ❌
     - "SaaS Capital" with DataBP → Debt lender → NOT disqualifying (can be YELLOW/GREEN)
7. **If EQUITY PE/VC investor found, did I verify if it's EXTERNAL PE or FAMILY OFFICE?**
   → Search: "[Investor Name]" "family office" OR "family investment vehicle"
   → If family office → YELLOW (exception - founders still control)
   → If external PE firm → RED (automatic disqualification)
8. Am I 100% confident NO EXTERNAL EQUITY PE/VC backing exists?
   → Debt financing is OK (not disqualifying)
   → Family office equity is OK for YELLOW (not GREEN, but not RED either)
   → Only EXTERNAL EQUITY PE/VC is disqualifying (RED)
9. If debt financing exists (e.g., SaaS Capital), did I confirm the company is still founder-owned?
   → Debt = borrowing money, founder still owns company → Can be GREEN/YELLOW
   → Equity = investor owns company → RED
10. **Does my VERDICT contradict my RATIONALE?** 🚨 CRITICAL SELF-VALIDATION CHECK 🚨
    → If rationale mentions PE/VC/investor/backing → Verdict CANNOT be GREEN (must be YELLOW or RED)
    → If rationale mentions "founder-owned, no PE/VC" → Verdict can be GREEN/YELLOW
    → If rationale mentions company names OTHER than target company → ERROR (copy-paste mistake)
    → Examples of CONTRADICTIONS to avoid:
      * Rationale: "PE-backed by FFL Partners" → Verdict: GREEN ❌ WRONG! (should be RED)
      * Rationale: "70-500 employees" → Verdict: GREEN ❌ WRONG! (too large, should be RED)
      * Rationale mentions "Abacus Group" when evaluating CJC ❌ WRONG! (wrong company research)

→ IF ANY ANSWER IS "NO" OR "UNCERTAIN" → GIVE YELLOW (NOT GREEN)
→ ONLY give GREEN if all 10 answers are "YES" with high confidence
→ SPECIAL RULE: Debt financing alone does NOT disqualify - check for equity ownership instead

STAGE 3: Business Model Classification (CRITICAL - 3-4 searches)
**IMPORTANT: Check for consulting RED FLAGS before operations GREEN FLAGS**

STEP 3A: Check for Consulting Red Flags (MANDATORY - Check FIRST)
- web_search: "[Company]" "contract negotiation" OR "vendor negotiation" OR "cost optimization"
- web_search: "[Company]" "advisory" OR "consulting" OR "staff augmentation" OR "invoice audit"
- IF ANY consulting red flags found → Likely CONSULTING (not operations) → Lean toward RED

**CONSULTING RED FLAGS (Any of these = HIGH RISK for RED):**
- "contract negotiation" / "vendor negotiation"
- "cost optimization" / "spend management" / "invoice audit"
- "advisory services" / "consulting services"
- "staff augmentation" / "temporary consultants"
- "we help you select" / "we help you negotiate"
- "optimization" as core service (not infrastructure optimization)

**⚠️ IMPORTANT: Mixed Model Rule**
- IF consulting flags found AND "Managed Services" also explicitly mentioned → YELLOW (mixed model)
- IF consulting flags found BUT NO managed services/operations → RED (pure consulting)
- Example: BST America lists both "Consulting" and "Managed Services" → YELLOW (not RED)

STEP 3B: Check for Operations Green Flags (ONLY if 3A shows NO strong consulting signals)
- web_search: "[Company]" "we operate" OR "we manage production" OR "24/7 monitoring"
- web_search: "[Company]" "NOC" OR "operations center" OR "production support"
- web_search: "[Company]" platform products software proprietary → Software product detection
- web_fetch: [website]/services OR /solutions → Detailed service descriptions

**OPERATIONS GREEN FLAGS (Need at least 2 for GREEN consideration):**
- "We operate your infrastructure" / "We manage your production"
- "24/7 monitoring" / "24x7 operations" / "round-the-clock"
- "NOC team" / "operations center" / "technical support team"
- "Production environment management"
- "Uptime SLA" / "SLA-backed operations"

**BUSINESS MODEL DECISION TREE:**
IF consulting red flags found + "Managed Services" explicitly mentioned → YELLOW (mixed consulting + managed services)
IF consulting red flags found + NO operations/managed services green flags → RED (pure consulting firm)
IF operations green flags found + proprietary products found → YELLOW (mixed model)
IF operations green flags found + NO products + NO consulting → Potential GREEN (pure operations)
IF uncertain or mixed signals → YELLOW (default to caution)

STAGE 4: Verification (As needed)
- Additional searches if employee count unclear
- Additional searches if PE/VC uncertain (default to YELLOW if unsure)
- Additional searches if business model mixed

**CONSERVATIVE DEFAULT FOR EQUITY PE/VC:**
- If uncertain about EQUITY PE/VC after 4-6 searches → YELLOW (NOT GREEN)
- If investor name appears but cannot verify if equity or debt → YELLOW (NOT GREEN)
- If PitchBook/Crunchbase profile exists but unclear if equity or debt → YELLOW (NOT GREEN)
- **CRITICAL: Debt financing (SaaS Capital, credit facilities, loans) is NOT disqualifying**
  → Only EQUITY PE/VC ownership is disqualifying
  → Debt = Company still founder-owned → Can be GREEN/YELLOW
  → Equity = Company owned by PE/VC → RED
- Only mark GREEN if EQUITY PE/VC search is thorough AND conclusive (debt is OK)

**MINIMUM SEARCH COUNTS:**
- GREEN verdict: 10-12 searches (thorough PE/VC verification required)
- YELLOW verdict: 8-10 searches (acceptable uncertainty)
- RED verdict: 6-8 searches (can stop if disqualifying factor found)

4. Use thinking to reason through EACH criterion systematically
5. Apply MANDATORY FINAL CHECK before verdict (as specified in SKILL.md)
6. Output ONLY the Verdict and Rationale in the exact format specified

Available tools: web_search, web_fetch, file_read

QUALITY REQUIREMENTS:
- Use extended thinking throughout the evaluation process
- Follow the staged search strategy (don't stop after 4-5 searches)
- Parse search result snippets for investor names and verify them
- Always search PitchBook directly for PE/VC verification
- Include specific metrics: employee count, ownership details
- Be conservative: uncertain about PE/VC → YELLOW (not GREEN)
- Provide evidence-based rationales (2-4 sentences)

**🔥 MANDATORY FINAL VERDICT DECISION LOGIC (Apply in Order) 🔥**

**Step 0: CHECK TIER CLASSIFICATION FIRST (BEFORE checking red flags):**
□ Is this company Tier 3 (3A, 3B, or 3C)?
  → YES: **DEFAULT VERDICT = YELLOW ⚠️**
  → ONLY mark RED if: Non-US HQ, Public company, or External PE/VC
  → DO NOT mark RED for: "generic MSP," "generalist," "IT support," "wrong business focus"
  → **Tier 3 = AUTOMATIC YELLOW** unless disqualified by Non-US/Public/External PE

**CRITICAL TIER 3 RULE:**
- Tier 3A/3B/3C companies serve financial services but lack deep specialization
- They are borderline candidates that need manual review → YELLOW by definition
- Examples: Generic MSP with financial vertical, boutique fund admin, niche fintech IT
- RED is ONLY for: Non-US HQ, Public company, or External PE/VC (not for being "generic")

→ IF Tier 3 → Skip to Step 2 (YELLOW flags) - DO NOT apply Step 1 red flags except Non-US/Public/External PE

Step 1: Check for AUTOMATIC RED FLAGS (any one of these = RED):
□ Confirmed EXTERNAL EQUITY PE/VC backing (investor name verified AND NOT family office)
□ Non-US headquarters
□ <5 employees (too small)
□ >150 employees with institutionalization
□ Software product company (not services)
□ Does NOT fit Tier 1, 2, or 3 (no category fit = RED)
□ Pure consulting/advisory with NO managed services mentioned

→ IF ANY checked → VERDICT = RED ❌

**CRITICAL:** Before marking RED for PE/VC, verify investor is NOT family office!
- If PE investor found, search: "[Investor]" "family office"
- If family office = YELLOW (exception), NOT RED

Step 2: Check for YELLOW FLAGS (if no automatic red flags):
□ Tier 3 fit (3A/3B/3C) - "Tier 3 = YELLOW by definition" ← CHECK THIS IN STEP 0 FIRST!
□ Mixed business model (consulting + managed services)
□ Mixed business model (products + services)
□ Borderline employee count (3-5 or 120-150)
□ Uncertain PE/VC status (signals but can't verify)
□ FAMILY OFFICE PE/VC (founders' investment vehicle - extreme edge case)
□ Any genuine uncertainty about criteria

→ IF ANY checked → VERDICT = YELLOW ⚠️

Step 3: Check for GREEN eligibility (if no red or yellow flags):
□ Fits Tier 1 (1A-1E) or Tier 2 (2A-2D)
□ 5-150 employees (ideal range)
□ US headquarters
□ Founder-owned (NO equity PE/VC - debt is OK)
□ Managed services/operations model
□ Institutional B2B clients

→ IF ALL checked → VERDICT = GREEN ✅ (rare - only ~5% of companies)

**FAILSAFE:** If uncertain → Default to YELLOW (not GREEN, not RED)

**COMMON ERRORS TO AVOID:**

**ERROR #1: Tier 3 marked RED instead of YELLOW**
- ❌ WRONG: Tier 3B "generic MSP" → RED for "wrong business focus"
- ✅ CORRECT: Tier 3B "generic MSP" → YELLOW (borderline, needs manual review)
- **RULE:** Tier 3 (3A/3B/3C) = AUTOMATIC YELLOW unless Non-US HQ, Public, or External PE

**ERROR #2: Verdict contradicts rationale (CRITICAL)**
- ❌ WRONG: Rationale says "PE-backed by FFL Partners, 70-500 employees" → Verdict: GREEN
- ✅ CORRECT: Rationale says "PE-backed by FFL Partners" → Verdict: RED (automatic disqualification)
- **RULE:** If rationale mentions PE/VC/investor → Verdict CANNOT be GREEN

**ERROR #3: Copy-paste rationale from different company in batch**
- ❌ WRONG: Evaluating CJC but rationale mentions "FFL Partners," "Medicus IT merger" (from Abacus Group)
- ✅ CORRECT: Each company gets FRESH research, rationale mentions ONLY that company's name
- **RULE:** Rationale should NEVER mention other company names (batch isolation error)

**ERROR #4: Wrong PE attribution (company name verification failure)**
- ❌ WRONG: Search "Computronix funding" → Find "FFL Partners invested in Abacus" → Attribute to Computronix
- ✅ CORRECT: Search "Computronix USA" "FFL Partners" → No results → No PE backing found
- **RULE:** Only cite PE backing if search result mentions TARGET company name + investor in same context

**ERROR #5: Mixed consulting + managed services marked RED**
- ❌ WRONG: Company lists "Consulting" and "Managed Services" → RED (pure consulting)
- ✅ CORRECT: Both consulting + managed services → YELLOW (mixed model)
- **RULE:** Mixed model = YELLOW, ONLY pure consulting (no operations) = RED

**ERROR #6: Confusing debt financing with equity PE/VC**
- ❌ WRONG: "SaaS Capital credit facility" → RED (PE-backed)
- ✅ CORRECT: "SaaS Capital credit facility" → Debt (not equity) → Can be GREEN/YELLOW
- **RULE:** Debt financing is NOT disqualifying, only EQUITY PE/VC is RED

**ERROR #7: PE/VC marked RED without family office check**
- ❌ WRONG: Found "PE-backed" → Immediate RED (without verifying if family office)
- ✅ CORRECT: Found "PE-backed" → Check if family office → If yes = YELLOW, if external PE = RED
- **RULE:** When PE investor found → MUST search "[Investor]" "family office" before verdict

**ERROR #8: Returning empty/nan values**
- ❌ WRONG: EST_EMPLOYEES: "nan", RATIONALE: "nan"
- ✅ CORRECT: If research insufficient, explain why (e.g., "Company website offline, no LinkedIn profile")
- **RULE:** Never return empty values, always provide explanation

**FAMILY OFFICE CHECK (MANDATORY when PE investor found):**
- If ANY PE/VC investor found → MUST search "[Investor]" "family office"
- If family office confirmed → YELLOW ⚠️ (founders still control via family vehicle)
- If external PE firm → RED ❌ (third-party ownership)
- Example: Vareton Group + MDMS → Family office → YELLOW (not RED)"""

        logger.debug(f"Calling Claude API with prompt length: {len(prompt)} chars")

        # Initialize conversation with user prompt
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Track all tool calls and thinking blocks across all turns
        all_tool_calls = []
        all_thinking_blocks = []

        # Multi-turn conversation loop
        max_turns = 20  # Prevent infinite loops
        turn = 0

        while turn < max_turns:
            turn += 1
            logger.debug(f"API turn {turn}/{max_turns}")

            # Build API call parameters
            api_params = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "system": system_prompt,
                "messages": messages,
                "tools": TOOL_DEFINITIONS
            }

            # Add thinking parameter if enabled
            if self.use_thinking:
                api_params["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": self.thinking_budget
                }

            # Make API call with retry logic for rate limits
            max_retries = 4
            retry_delays = [2, 4, 8, 16]  # Exponential backoff in seconds

            for retry_attempt in range(max_retries + 1):
                try:
                    message = self.client.messages.create(**api_params)
                    break  # Success - exit retry loop

                except RateLimitError as e:
                    if retry_attempt < max_retries:
                        wait_time = retry_delays[retry_attempt]
                        logger.warning(
                            f"Rate limit hit (429). Retry {retry_attempt + 1}/{max_retries} "
                            f"after {wait_time}s... (Error: {str(e)[:100]})"
                        )
                        time.sleep(wait_time)
                    else:
                        # Final retry failed - re-raise the error
                        logger.error(f"Rate limit error after {max_retries} retries: {e}")
                        raise

            # Extract content blocks
            thinking_blocks = []
            text_blocks = []
            tool_use_blocks = []

            for content_block in message.content:
                if content_block.type == "thinking":
                    thinking_blocks.append(content_block.thinking)
                    all_thinking_blocks.append(content_block.thinking)
                    logger.debug(f"Thinking block ({len(content_block.thinking)} chars): {content_block.thinking[:100]}...")
                elif content_block.type == "text":
                    text_blocks.append(content_block.text)
                elif content_block.type == "tool_use":
                    tool_use_blocks.append(content_block)
                    all_tool_calls.append({
                        "name": content_block.name,
                        "input": content_block.input
                    })
                    logger.info(f"Tool request: {content_block.name}({content_block.input})")

            # Check stop reason
            stop_reason = message.stop_reason

            # If we have tool uses, execute them and continue conversation
            if tool_use_blocks:
                logger.info(f"Executing {len(tool_use_blocks)} tools...")

                # Build assistant message with tool uses
                assistant_content = []

                # Include any thinking or text blocks before tool uses
                for block in message.content:
                    if block.type in ["thinking", "text", "tool_use"]:
                        assistant_content.append(block)

                messages.append({
                    "role": "assistant",
                    "content": assistant_content
                })

                # Execute tools and build tool results
                tool_results = []
                for tool_block in tool_use_blocks:
                    result = self.tool_executor.execute_tool(
                        tool_block.name,
                        tool_block.input
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": result
                    })
                    logger.debug(f"Tool {tool_block.name} returned {len(result)} chars")

                # Add tool results as user message
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # Continue loop to get next response
                continue

            # No tool uses - we have final response
            if text_blocks:
                final_response = "\n".join(text_blocks)
                logger.info(f"Final response received ({len(final_response)} chars)")

                # Validate and log quality metrics
                self._log_quality_metrics(all_thinking_blocks, all_tool_calls)

                # Log token usage
                usage_msg = f"API call complete. Tokens: {message.usage.input_tokens} in, {message.usage.output_tokens} out"
                if self.use_thinking and hasattr(message.usage, 'thinking_tokens'):
                    usage_msg += f", {message.usage.thinking_tokens} thinking"
                logger.info(usage_msg)

                return final_response

            # No tool uses and no text - unexpected
            logger.warning(f"Unexpected response - no tools and no text. Stop reason: {stop_reason}")
            break

        # Exceeded max turns
        logger.error(f"Exceeded maximum turns ({max_turns}) without getting final response")
        return "Error: Evaluation incomplete - exceeded maximum conversation turns"

    def _log_quality_metrics(self, thinking_blocks: List[str], tool_calls: List[Dict]) -> None:
        """
        Log quality validation metrics.

        Args:
            thinking_blocks: All thinking blocks from conversation
            tool_calls: All tool calls from conversation
        """
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
            verdict, est_revenue, est_employees, tier_fit, rationale = self._parse_single_verdict(response_text)
            results.append(EvaluationResult(
                index=companies[0].index,
                verdict=verdict,
                rationale=rationale,
                est_revenue=est_revenue,
                est_employees=est_employees,
                tier_fit=tier_fit,
                processed="Yes" if verdict != "ERROR" else "Error"
            ))
        else:
            # Multiple companies - parse each section
            sections = self._split_response_by_company(response_text, companies)

            for company, section_text in zip(companies, sections):
                verdict, est_revenue, est_employees, tier_fit, rationale = self._parse_single_verdict(section_text)
                results.append(EvaluationResult(
                    index=company.index,
                    verdict=verdict,
                    rationale=rationale,
                    est_revenue=est_revenue,
                    est_employees=est_employees,
                    tier_fit=tier_fit,
                    processed="Yes" if verdict != "ERROR" else "Error"
                ))

        return results

    def _parse_single_verdict(self, text: str) -> tuple[str, str, str, str, str]:
        """
        Parse verdict, revenue estimate, employee estimate, tier fit, and rationale from text.

        Returns:
            Tuple of (verdict, est_revenue, est_employees, tier_fit, rationale)
        """
        verdict = "UNKNOWN"
        est_revenue = "Not found"
        est_employees = "Not found"
        tier_fit = "Not specified"
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

        # Try to extract EST_REVENUE
        for line in lines:
            line_upper = line.upper().strip()
            if 'EST_REVENUE:' in line_upper:
                est_revenue = line.split(':', 1)[1].strip()
                break

        # Try to extract EST_EMPLOYEES
        for line in lines:
            line_upper = line.upper().strip()
            if 'EST_EMPLOYEES:' in line_upper:
                est_employees = line.split(':', 1)[1].strip()
                break

        # Try to extract TIER_FIT
        for line in lines:
            line_upper = line.upper().strip()
            if 'TIER_FIT:' in line_upper or 'TIER FIT:' in line_upper:
                tier_fit = line.split(':', 1)[1].strip()
                break

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

        return verdict, est_revenue, est_employees, tier_fit, rationale

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
