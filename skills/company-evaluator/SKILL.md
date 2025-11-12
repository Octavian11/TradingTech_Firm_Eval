---
name: company-evaluator
description: Evaluates acquisition target companies against Devonshire Partners' investment thesis for mission-critical trading infrastructure and regulatory operations businesses. Use when the user asks to evaluate, assess, or analyze a company as a potential acquisition target, or when they provide a company name/URL and want to know if it fits their thesis. Always use this skill when evaluating companies for M&A fit.
---

# Company Evaluator for Devonshire Partners

This skill performs **top-of-funnel screening** of potential acquisition targets using ONLY publicly available information. It evaluates companies against Hassan Tariq's investment thesis for mission-critical trading infrastructure and regulatory operations businesses.

**Purpose**: Initial screening to identify companies worth pursuing for confidential due diligence.

**Does NOT evaluate**: Revenue, EBITDA, margins, GRR/NRR, or other confidential financial metrics. Those come after a company passes this screening.

## When to Use This Skill

Use this skill whenever:
- User asks to evaluate a specific company
- User provides a company name or URL and wants assessment
- User asks "does this company fit my thesis?"
- User wants to know if a company is a good acquisition target
- User asks for a verdict (Green/Yellow/Red) on a company

## Evaluation Process

### Step 1: Read the Investment Criteria
ALWAYS start by reading the detailed investment criteria:
```
file_read: /mnt/skills/user/company-evaluator/references/investment-criteria.md
```

### Step 2: Research the Company
Use web tools to gather information about the company:

**Required Information:**
- Company name, location, founding year
- Number of employees
- Revenue estimate (if available)
- Business model: What services do they provide?
- Customer base: Who do they serve?
- Ownership structure: Founder-owned, PE-backed, or public?
- Service categories: Which of the three Tier 1 categories do they fit?

**Research Tools:**
1. `web_fetch` on the company's website URL
2. `web_search` for company information (employees, revenue, ownership, founder)
3. Look for signals: LinkedIn company page, news articles, funding announcements

**Key Questions to Answer:**
- Is this a managed services provider or software product company?
- Do they OPERATE infrastructure or just implement/consult?
- Are they US-based?
- What's their approximate size (employees, revenue)?
- Any PE/VC backing?
- Do they fit one of the three Tier 1 categories?

### Step 3: Apply the Evaluation Framework (Public Information Only)

Check against criteria in this order:

**1. AUTOMATIC RED FLAGS (Immediate rejection):**
- PE/VC ownership (any %) - search specifically for funding/investors
- Non-US headquarters - verify location
- **Software product company:**
  - **RED LIGHT**: Pure software (minimal services, primarily licensing)
  - **YELLOW LIGHT**: Software + substantial services (unknown revenue mix)
  - **Acceptable (Tier 2)**: Confirmed >70% services revenue
  - Note: Revenue percentage is evaluated AFTER initial screening, not during it
- Generic IT staffing - not specialized trading tech
- Already acquired/part of larger company - look for "a [Company] company"

**2. SIZE ASSESSMENT (LinkedIn + Website):**
- 10-100 employees = likely fits target EBITDA range (✅)
- <10 employees = likely too small (❌)
- >150 employees + multiple offices = likely too institutionalized (❌)
- 100-150 employees = borderline (⚠️)
- Additional signals of too large:
  - 4+ office locations globally
  - "800+ clients" or similar scale mentioned
  - ISO certifications + multi-award-winning + decades old
  - "22 geographies" or similar international reach

**3. TIER 1 OR TIER 2 CATEGORY FIT:**
Does the company clearly fit one of these categories?

**Tier 1 (Highest Priority - GREEN LIGHT potential):**
1. OMS/EMS support/implementation (Aladdin, Charles River, Bloomberg AIM)
2. Market data managed services (Bloomberg/Refinitiv partners, data ops)
3. Trade surveillance/compliance services (RegTech, monitoring, TCA)
4. Execution analytics/consulting

**Tier 2 (Lower Priority - YELLOW LIGHT):**
5. Enterprise software implementation (ServiceNow, Salesforce, Workday - finserv focused)
6. Data/analytics services for financial services
7. Technology-enabled business services (payments, finops outsourcing)
8. B2B SaaS with heavy services component (>70% services revenue)

If fits neither Tier 1 nor Tier 2 = RED LIGHT

**4. BUSINESS MODEL (Website Language):**

**Critical Distinction:**
- ✅ **Operating others' platforms** (TARGET): Provides managed services for Bloomberg, Charles River, Aladdin, etc.
- ⚠️ **Operating own platform as a service** (BORDERLINE): Delivers proprietary platform primarily as managed service
- ❌ **Building competing platforms** (NOT TARGET): Sells software licenses to replace Bloomberg/Charles River

**Service Model Indicators to Look For:**
- "Fully managed service" / "delivered as a service"
- "24/7 monitoring" / "proactive support"
- "We handle certification, testing, production monitoring"
- "Operations-as-a-service" / "SLA-backed"

**Verdict Guidance for Software Companies:**
- ✅ Managed services (operating others' platforms): GREEN if Tier 1, YELLOW if Tier 2
- ⚠️ Mixed model with substantial services: YELLOW LIGHT (needs due diligence to verify >70%)
- ⚠️ Own platform delivered primarily as service: YELLOW LIGHT (borderline case)
- ❌ Pure software products (minimal services): RED LIGHT
- ❌ Project-only: "consulting engagements", "implementation projects", "we build then hand off" = RED LIGHT

**5. CUSTOMER BASE:**
- ✅ Institutional B2B: Asset managers, broker-dealers, banks
- ⚠️ Mixed: Both institutional and retail
- ❌ Retail/consumer fintech only

**DO NOT EVALUATE** (requires confidential information):
- Exact revenue or EBITDA figures
- Recurring revenue percentage
- GRR/NRR metrics
- Margin analysis
- Client concentration percentages
- DSO or AR aging
- Revenue growth trends

### Step 4: Determine Verdict (Top-of-Funnel Screening)

**GREEN LIGHT ✅** = Pass initial screening, advance to confidential due diligence
- Meets ALL publicly verifiable requirements:
  - 10-100 employees (LinkedIn verified)
  - US-based headquarters
  - Founder-owned (no PE/VC detected)
  - Fits **Tier 1** category with managed services model
  - Serves institutional B2B clients
  - Clear signals of ongoing operations
  - No public red flags

**YELLOW LIGHT ⚠️** = Needs additional research before deciding
- Meets MOST requirements but has questions:
  - Fits **Tier 2** category (acceptable but lower priority than Tier 1)
  - Borderline size (8-12 or 100-120 employees)
  - Unclear if fully managed services or mixed with projects
  - Software company with substantial services but cannot verify if >70% services revenue
  - Limited public information available
  - Recently founded (<3 years) but fits category
  - Worth proceeding to due diligence to clarify

**RED LIGHT ❌** = Does not fit thesis, do not pursue
- Fails on ANY critical publicly verifiable requirement:
  - PE/VC backed
  - Non-US headquarters
  - Wrong size (<10 or >150 employees with institutionalization)
  - Pure software product company (minimal services, primarily licensing)
  - Generic IT staffing or project consulting
  - Does NOT fit Tier 1 or Tier 2 categories
  - Too institutionalized (4+ offices, 800+ clients)

### Step 5: Format Output for Excel

Provide output in TWO parts optimized for Excel columns:

**Column A - Verdict:**
One of: "GREEN LIGHT ✅" or "YELLOW LIGHT ⚠️" or "RED LIGHT ❌"

**Column B - Rationale:**
Concise 2-4 sentence summary covering:
1. What the company does (business model)
2. Why it fits or doesn't fit (specific criteria)
3. Key concern if Yellow, or deal-breaker if Red

**Example Output Format:**

```
Verdict: RED LIGHT ❌

Rationale: CJC is a market data managed services provider (perfect Tier 1 fit) offering Bloomberg/Refinitiv operations support with 70%+ recurring revenue. However, company is far too large with 4 global offices, 800+ clients, and 22 geographies - likely $15-30M+ EBITDA vs target of $1-5M. This is the platonic ideal of what Hassan wants to BUILD, not acquire.
```

## Important Guidelines

### Research Thoroughly
- Don't guess about PE backing - search specifically for funding/investors
- Use employee count on LinkedIn as size signal
- Look for "managed by" or "portfolio company" language
- Check for office locations to confirm US-based

### Be Honest About Fit
- Don't force a fit if criteria aren't met
- Yellow Light should be rare - only for minor issues
- Most companies will be Red Light - thesis is narrow and specific

### Stay Concise
- Rationale should be 2-4 sentences maximum
- Focus on WHAT the company does and WHY it fits/doesn't fit
- Don't repeat obvious information from the verdict

### Common Pitfalls to Avoid
- Don't confuse "implements then leaves" with "operates ongoing"
- Don't automatically reject software companies if they emphasize managed services
- Don't assume you can determine revenue mix from public info - use YELLOW when uncertain
- Don't confuse "operating own platform as a service" with "operating others' platforms"
- Don't miss PE/VC backing (search thoroughly)
- Don't overlook size issues (150+ employees = too big)
- Don't forget: must be US-based

## Example Evaluations

### Example 1: Green Light
**Company**: 40-person firm providing 24/7 OMS production support for Charles River and Aladdin

**Verdict**: GREEN LIGHT ✅

**Rationale**: US-based managed services provider operating critical OMS infrastructure with 24/7 support model (Tier 1 fit). 40 employees suggests $3-5M EBITDA range, founder-owned, serves asset managers with SLA-backed recurring revenue. Perfect thesis fit.

### Example 2: Yellow Light - Tier 2 Category
**Company**: 55-person Salesforce Financial Services Cloud implementation firm, finserv-focused

**Verdict**: YELLOW LIGHT ⚠️

**Rationale**: Fits Tier 2 (enterprise software implementation for financial services) and right size range. Lower priority than Tier 1 mission-critical trading infrastructure, but acceptable category. Worth pursuing if Tier 1 pipeline is thin.

### Example 2b: Yellow Light - Tier 1 with Mixed Model
**Company**: 60-person Bloomberg entitlements firm, shows both ongoing management and implementation projects

**Verdict**: YELLOW LIGHT ⚠️

**Rationale**: Fits Tier 1 (market data operations) and right size. Website mentions both ongoing entitlements administration AND implementation projects - unclear which is primary. Worth additional research to clarify if managed services are core offering or if it's primarily project-based.

### Example 2c: Yellow Light - Own Platform as Managed Service
**Company**: 10-person trading infrastructure firm with proprietary platform delivered as managed service

**Verdict**: YELLOW LIGHT ⚠️

**Rationale**: Company operates own trading infrastructure platform but delivers it primarily as fully managed service with 24/7 monitoring and support. Right size (10 employees) and US-based with institutional clients. Cannot determine revenue mix from public information - needs due diligence to verify if >70% services revenue vs software licensing.

### Example 3: Red Light - Wrong Business Model
**Company**: OMS software vendor with 80 employees selling their own trading platform

**Verdict**: RED LIGHT ❌

**Rationale**: Software product company that sells proprietary OMS platform rather than providing managed services for other vendors' platforms. Hassan's thesis requires services providers (not software vendors) who operate Bloomberg/Charles River/Aladdin for clients.

### Example 4: Red Light - Too Large
**Company**: Market data consultancy with 4 offices, 800+ clients, 200+ employees, ISO certified

**Verdict**: RED LIGHT ❌

**Rationale**: Perfect business model (market data managed services) but far too large and institutionalized. 4 global offices and 800+ clients suggests $15-30M+ EBITDA vs $1-5M target. This is the end-state platform Hassan wants to build, not acquire.

### Example 5: Red Light - PE Backed
**Company**: 35-person trade surveillance services firm, recently raised Series A from Accel Partners

**Verdict**: RED LIGHT ❌

**Rationale**: Despite fitting Tier 1 category and right size, company has VC backing (Accel Partners) which is automatic disqualification per investment criteria. Hassan's thesis requires 100% founder-owned businesses only.

## Final Reminders

### This is Top-of-Funnel Screening
- Use ONLY publicly available information
- Do NOT try to estimate revenue, EBITDA, or margins
- Do NOT guess about recurring revenue percentages
- Do NOT evaluate GRR, NRR, client concentration, or DSO
- Those metrics come AFTER passing this initial screening

### Research Thoroughly But Stay Public
- Check specifically for PE/VC backing (search "[company] funding", "[company] investors")
- Use LinkedIn for employee count
- Look for "managed by" or "portfolio company" language
- Verify US headquarters (not just US presence)
- Check if they sell software or provide services

### Be Honest About Fit
- Don't force a fit if criteria aren't met
- Yellow Light should be uncommon - only when genuinely borderline
- Most companies will be Red Light - thesis is narrow and specific
- GREEN means "worth pursuing for confidential diligence", not "definitely acquire"

### Stay Concise
- Rationale should be 2-4 sentences maximum
- Focus on WHAT they do and WHY it fits/doesn't fit
- Don't repeat obvious information from the verdict

### Common Pitfalls to Avoid
- Don't confuse "implements then leaves" with "operates ongoing"
- Don't automatically reject software companies if they emphasize managed services
- Don't assume you can determine revenue mix from public info - use YELLOW when uncertain
- Don't confuse "operating own platform as a service" with "operating others' platforms"
- Don't miss PE/VC backing (search thoroughly before saying founder-owned)
- Don't overlook size signals (150+ employees + 4 offices = too big)
- Don't forget: MUST be US-based
