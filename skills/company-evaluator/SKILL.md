---
name: company-evaluator
description: Evaluates acquisition target companies against Devonshire Partners' investment thesis for mission-critical trading infrastructure and investment operations businesses. Use when the user asks to evaluate, assess, or analyze a company as a potential acquisition target, or when they provide a company name/URL and want to know if it fits their thesis. Always use this skill when evaluating companies for M&A fit.
---

# Company Evaluator for Devonshire Partners

This skill performs **top-of-funnel screening** of potential acquisition targets using ONLY publicly available information. It evaluates companies against Hassan Tariq's investment thesis for mission-critical trading infrastructure and investment operations businesses.

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
- Service categories: Which Tier (1, 2, or 3) do they fit?

**Research Tools:**
1. `web_fetch` on the company's website URL
2. `web_search` for company information (employees, revenue, ownership, founder)
3. Look for signals: LinkedIn company page, news articles, funding announcements

**Key Questions to Answer:**
- Is this a managed services provider or software product company?
- Do they OPERATE infrastructure or just implement/consult?
- Are they US-based (headquarters, not just presence)?
- What's their approximate size (employees, revenue)?
- Any PE/VC backing?
- Do they fit Tier 1, Tier 2, or Tier 3 categories?

### Step 3: Apply the Evaluation Framework (Public Information Only)

Check against criteria in this order:

**1. AUTOMATIC RED FLAGS (Immediate rejection):**
- PE/VC ownership (any %) - search specifically for funding/investors
- Non-US headquarters - verify location (US presence alone not sufficient)
- Software product company (not services) - check if they sell their own platform
- Generic IT staffing - not specialized trading tech or investment operations
- Already acquired/part of larger company - look for "a [Company] company"

**2. SIZE ASSESSMENT (LinkedIn + Website):**
- 5-50 employees = likely $500K-$2M EBITDA range (✅)
- 50-100 employees = likely $2M-$5M EBITDA range (✅)
- 100-150 employees = borderline, may be too institutionalized (⚠️)
- <5 employees = too small (❌)
- >150 employees + multiple offices = too large/institutionalized (❌)
- Additional signals of too large:
  - 4+ office locations globally
  - "800+ clients" or similar scale mentioned
  - ISO certifications + multi-award-winning + decades old
  - "22 geographies" or similar international reach

**3. TIER CATEGORY FIT:**
Does the company clearly fit one of these tiers?

**Tier 1: Trading Infrastructure Operations (50-55% of deals) - GREEN LIGHT potential**

| Sub-Tier | Services |
|----------|----------|
| 1A. Network Ops | Low-latency network mgmt, exchange connectivity, colocation, FIX protocol ops, 24/7 NOC |
| 1B. Market Data Ops | Bloomberg/Refinitiv entitlements, data feed ops, vendor compliance, DACS/EMRS |
| 1C. Trading Systems Support | OMS/EMS production support (Aladdin, Charles River, Bloomberg AIM, Eze), 24/7 incident response |
| 1D. Trade Surveillance Ops | Alert triage, best execution monitoring, transaction reporting, compliance evidence |
| 1E. Other Trading Infra | DR/BCP for trading systems, execution analytics |

**Tier 2: Middle/Back-Office Operations (30-35% of deals) - GREEN LIGHT potential**

| Sub-Tier | Services |
|----------|----------|
| 2A. Post-Trade Processing | Trade confirmation/matching, settlement ops, fails mgmt, corporate actions |
| 2B. Reconciliation & Settlement | Position/cash/NAV reconciliation, exception management |
| 2C. Regulatory Reporting Ops | EMIR/MiFID/Dodd-Frank reporting, Form PF, 13F filing ops |
| 2D. Investment Ops Support | Portfolio accounting ops, performance measurement, client reporting |

**Tier 3: Adjacent Services (15-20% of deals) - YELLOW LIGHT (selective)**

| Sub-Tier | Services |
|----------|----------|
| 3A. Boutique Fund Admin | Small/mid-market fund admin (not SS&C/Apex scale), RIA/family office admin |
| 3B. Middle-Office BPO | Trade lifecycle outsourcing, IBOR ops, order mgmt support |
| 3C. Specialized Tech-Enabled | Financial data ops, pricing/valuation ops (must be >70% recurring) |

**If fits neither Tier 1, 2, nor 3 = RED LIGHT**

**4. BUSINESS MODEL (Website Language):**
- ✅ Managed services: "24/7 support", "operations-as-a-service", "ongoing support", "SLA-backed"
- ⚠️ Mixed model: Both implementation projects AND ongoing support mentioned
- ❌ Project-only: "consulting engagements", "implementation projects", "we build then hand off"
- ❌ Software products: Selling their own platform rather than operating others' platforms

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
  - 5-150 employees (LinkedIn verified)
  - US-based headquarters (not just US presence)
  - Founder-owned (no PE/VC detected after thorough search)
  - Fits **Tier 1 OR Tier 2** category
  - Managed services model (ongoing operations, not just projects)
  - Serves institutional B2B clients
  - No public red flags

**YELLOW LIGHT ⚠️** = Needs additional research before deciding
- Meets MOST requirements but has questions:
  - Fits **Tier 3** category (acceptable but selective)
  - Borderline size (3-5 employees or 120-150 employees)
  - Unclear if fully managed services or mixed with projects
  - Limited public information available
  - Mixed business model signals
  - PE/VC status unclear (needs deeper search)

**RED LIGHT ❌** = Does not fit thesis, do not pursue
- Fails on ANY critical publicly verifiable requirement:
  - PE/VC backed (confirmed)
  - Non-US headquarters
  - <5 or >150 employees (with institutionalization signals)
  - Software product company (not services)
  - Generic IT staffing or project consulting
  - Does NOT fit Tier 1, 2, or 3 categories
  - Project-based only (no ongoing operations)
  - Too institutionalized (4+ offices, 500+ clients)

### Step 5: Format Output

Provide output in this format:

**Verdict:** [GREEN LIGHT ✅ / YELLOW LIGHT ⚠️ / RED LIGHT ❌]

**Tier:** [1A/1B/1C/1D/1E / 2A/2B/2C/2D / 3A/3B/3C / None]

**Rationale:** [2-4 sentences covering:
1. What the company does (business model)
2. Why it fits or doesn't fit (specific criteria)
3. Key concern if Yellow, or deal-breaker if Red]

---

## Important Guidelines

### Research Thoroughly
- Don't guess about PE backing - search specifically for funding/investors
- Use employee count on LinkedIn as size signal
- Look for "managed by" or "portfolio company" language
- Check for office locations to confirm US-based headquarters

### Be Honest About Fit
- Don't force a fit if criteria aren't met
- Yellow Light should be for Tier 3 fits or genuine borderline cases
- Most companies will be Red Light - thesis is narrow and specific

### Stay Concise
- Rationale should be 2-4 sentences maximum
- Focus on WHAT the company does and WHY it fits/doesn't fit
- Don't repeat obvious information from the verdict

### Common Pitfalls to Avoid
- Don't confuse "implements then leaves" with "operates ongoing"
- Don't miss PE/VC backing (search thoroughly)
- Don't overlook size issues (>150 employees + multiple offices = too big)
- Don't approve software products unless services-heavy
- Don't forget: must be US-based HEADQUARTERS (not just US presence)
- Don't give Tier 2 companies Yellow - they are now GREEN eligible

---

## Example Evaluations

### Example 1: Green Light - Tier 1
**Company**: 40-person firm providing 24/7 OMS production support for Charles River and Aladdin

**Verdict**: GREEN LIGHT ✅

**Tier**: 1C

**Rationale**: US-based managed services provider operating critical OMS infrastructure with 24/7 support model. 40 employees suggests $1-2M EBITDA range, founder-owned, serves asset managers with SLA-backed recurring revenue. Perfect Tier 1C thesis fit.

### Example 2: Green Light - Tier 2
**Company**: 55-person firm providing reconciliation and settlement operations for hedge funds

**Verdict**: GREEN LIGHT ✅

**Tier**: 2B

**Rationale**: US-based reconciliation services provider with ongoing operations model serving institutional clients. 55 employees suggests $2-3M EBITDA range, founder-owned, SLA-backed services. Strong Tier 2B fit - middle/back-office operations is now a core focus area.

### Example 3: Yellow Light - Tier 3
**Company**: 30-person boutique fund administrator serving emerging managers

**Verdict**: YELLOW LIGHT ⚠️

**Tier**: 3A

**Rationale**: Fits Tier 3A (boutique fund admin) with right size and appears founder-owned. Adjacent service category requires strong fit on other criteria. Worth additional research to confirm operations-heavy model vs pure accounting focus.

### Example 4: Yellow Light - Mixed Signals
**Company**: 25-person Bloomberg entitlements firm, shows both ongoing management and implementation projects

**Verdict**: YELLOW LIGHT ⚠️

**Tier**: 1B

**Rationale**: Fits Tier 1B (market data operations) and right size. Website mentions both ongoing entitlements administration AND implementation projects - unclear which is primary. Worth additional research to clarify if managed services are core offering.

### Example 5: Red Light - Wrong Business Model
**Company**: OMS software vendor with 80 employees selling their own trading platform

**Verdict**: RED LIGHT ❌

**Tier**: None

**Rationale**: Software product company that sells proprietary OMS platform rather than providing managed services for other vendors' platforms. Hassan's thesis requires services providers who operate Bloomberg/Charles River/Aladdin for clients, not software vendors.

### Example 6: Red Light - Too Large
**Company**: Market data consultancy with 4 offices, 800+ clients, 200+ employees, ISO certified

**Verdict**: RED LIGHT ❌

**Tier**: None (would be 1B if right size)

**Rationale**: Perfect business model (market data managed services) but far too large and institutionalized. 4 global offices, 200+ employees, and 800+ clients suggests $15-30M+ EBITDA vs $500K-5M target. This is the end-state platform Hassan wants to build, not acquire.

### Example 7: Red Light - PE Backed
**Company**: 35-person trade surveillance services firm, recently raised Series A

**Verdict**: RED LIGHT ❌

**Tier**: None (would be 1D if founder-owned)

**Rationale**: Despite fitting Tier 1D category and right size, company has VC backing which is automatic disqualification. Hassan's thesis requires 100% founder-owned businesses only.

---

## Final Reminders

### This is Top-of-Funnel Screening
- Use ONLY publicly available information
- Do NOT try to estimate revenue, EBITDA, or margins
- Do NOT guess about recurring revenue percentages
- Do NOT evaluate GRR, NRR, client concentration, or DSO
- Those metrics come AFTER passing this initial screening

### Key V2.0 Changes to Remember
- Employee range is now **5-150** (was 10-100)
- EBITDA floor is now **$500K** (was $1M)
- **Tier 2 is now GREEN eligible** (was Yellow only)
- Tier 2 is now middle/back-office operations (reconciliation, regulatory reporting, post-trade)
- **Tier 3 added** for adjacent services (boutique fund admin, BPO)
- Deal allocation: 50-55% Tier 1, 30-35% Tier 2, 15-20% Tier 3

### Research Thoroughly But Stay Public
- Check specifically for PE/VC backing (search "[company] funding", "[company] investors")
- Use LinkedIn for employee count
- Look for "managed by" or "portfolio company" language
- Verify US headquarters (not just US presence)
- Check if they sell software or provide services

### Be Honest About Fit
- Don't force a fit if criteria aren't met
- Yellow Light is now primarily for Tier 3 or genuinely unclear cases
- Most companies will be Red Light - thesis is narrow and specific
- GREEN means "worth pursuing for confidential diligence", not "definitely acquire"
