# Comprehensive Search Strategy for Company Evaluations
**Version 1.0 - November 2025**

## Purpose
This document provides a systematic search strategy for evaluating acquisition target companies. It ensures thorough research, consistent PE/VC detection, and reliable employee count verification across 200+ company evaluations.

---

## Core Principles

### 1. **Multi-Stage Progressive Research**
- Start broad, then narrow based on findings
- Each search should reveal new information
- Parse snippets before deciding next searches

### 2. **Conservative Defaults**
- When uncertain about PE/VC → YELLOW (not GREEN)
- When uncertain about employee count → Note limitation
- When uncertain about business model → Additional searches

### 3. **Platform-Specific Searches**
- LinkedIn for employee counts
- PitchBook/Crunchbase for funding
- Company website for business model
- Multiple sources for verification

---

## Stage 1: Initial Discovery (4-5 searches)

### Search 1: Company Website
```
TOOL: web_fetch
URL: [company_website]
PURPOSE: Get primary source on business model, services, team
```

**What to extract:**
- Service language: "fully managed service", "24/7", "ongoing operations"
- Product language: "our platform", "proprietary", "software"
- Team mentions: Names of founders, executives
- Office locations mentioned
- Client testimonials or case studies

### Search 2: General Company Information
```
TOOL: web_search
QUERY: "[Company Name]" [Location] employees services
PURPOSE: Get overview and find employee data sources
```

**What to look for in snippets:**
- LinkedIn company page URL
- Employee count mentions (ZoomInfo, RocketReach, etc.)
- Recent news or press releases
- Company description consistency

### Search 3: LinkedIn Employee Count
```
TOOL: web_search
QUERY: "[Company Name]" site:linkedin.com/company employees
OR
QUERY: "[Company Name]" LinkedIn employees
PURPOSE: Find specific employee count
```

**Parse snippets for:**
- "X-Y employees" (e.g., "11-50 employees")
- Company size category
- Recent hiring activity
- Office locations listed

**Follow-up if needed:**
```
TOOL: web_fetch
URL: [LinkedIn company page URL from snippets]
PURPOSE: Confirm employee count from page content
```

### Search 4: Ownership & Founding
```
TOOL: web_search
QUERY: "[Company Name]" founder CEO owner leadership
PURPOSE: Identify key people and ownership structure
```

**What to look for:**
- Founder names
- CEO/President names
- Year founded
- Any mention of "backed by", "portfolio company", "acquired by"

---

## Stage 2: PE/VC Detection (CRITICAL - 3-4 searches)

**This is the most important screening criterion. PE/VC backing is automatic disqualification.**

### Search 5: Broad Funding Search
```
TOOL: web_search
QUERY: "[Company Name]" funding investors venture capital private equity
PURPOSE: Initial funding detection
```

**Red flags in snippets:**
- "raised $X"
- "Series A/B/C"
- "led by [Investor Name]"
- "backed by"
- "portfolio company"

### Search 6: PitchBook Direct Search
```
TOOL: web_search
QUERY: site:pitchbook.com "[Company Name]"
PURPOSE: Find PitchBook profile (most reliable PE/VC source)
```

**Critical: If PitchBook appears in results:**
1. Note the PitchBook URL
2. Check snippet for "Private Equity-Backed", "VC-Backed", "Financing Status", investor names
3. **PAYWALL RULE**: If PitchBook profile EXISTS but snippet is vague/limited:
   - This is a **RED FLAG** - PitchBook profiles are NOT created for small bootstrapped companies
   - Profile existence suggests institutional investors (PE/VC)
   - **Do NOT give GREEN verdict** - Default to YELLOW (uncertain) or search harder for confirmation
   - Example: MDMS has PitchBook profile showing "Financing Status: Private Equity-Backed" but page is paywalled
4. If snippet mentions investors → Proceed to Search 9 for verification

### Search 7: Crunchbase Search
```
TOOL: web_search
QUERY: site:crunchbase.com "[Company Name]" funding
PURPOSE: Alternative funding database
```

**What to look for:**
- Funding rounds listed
- Investor names
- "Last Funding Type" mentions

### Search 8: Direct PE/VC Status Phrase Search (MANDATORY for GREEN)
```
TOOL: web_search
QUERY: "[Company Name]" "Private Equity-Backed" OR "VC-Backed" OR "Financing Status"
PURPOSE: Catch paywalled information that leaked to other sources
```

**Why this search is critical:**
- PitchBook pages show exact phrase "Financing Status: Private Equity-Backed" (see MDMS example)
- Pages are often paywalled (403 errors)
- BUT this phrase may leak into press releases, databases, or cached web pages
- Searches for the EXACT language used on paywalled pages

**Example:**
`"Market Data Management Solutions" "Private Equity-Backed" OR "VC-Backed"`

### Search 9: Investor Name Verification (IF investors found)
```
TOOL: web_search
QUERY: "[Company Name]" "[Investor Name from snippet]"
PURPOSE: Confirm specific investor relationship
```

**Example:**
If snippet mentioned "Vareton Group", search:
`"Market Data Management Solutions" "Vareton Group"`

**This search will definitively confirm or deny the relationship.**

### Search 10: Acquisition/Portfolio Check
```
TOOL: web_search
QUERY: "[Company Name]" "portfolio company" OR "acquired by" OR "a [parent] company"
PURPOSE: Check if part of larger organization
```

---

## Stage 3: Business Model Classification (2-3 searches)

### Search 11: Service Model Deep Dive
```
TOOL: web_search
QUERY: "[Company Name]" "managed services" OR "operations" OR "24/7" OR "support"
PURPOSE: Find service indicators
```

**What confirms managed services:**
- "Delivered as a fully managed service"
- "24/7 monitoring/operations/support"
- "Ongoing operations"
- "Production support"
- "SLA-backed"

### Search 12: Platform/Product Investigation
```
TOOL: web_search
QUERY: "[Company Name]" platform products software proprietary
PURPOSE: Determine if software vendor
```

**What indicates software product company:**
- Multiple named products (iServer, FIXengine, etc.)
- "Our platform enables..."
- Pricing pages for software
- "Download" or "Free trial" offerings

### Search 12: Services Page Review (if not already fetched)
```
TOOL: web_fetch
URL: [company_website]/services OR /solutions OR /what-we-do
PURPOSE: Get detailed service descriptions
```

---

## Stage 4: Verification & Clarification (As Needed)

### Additional Searches Based on Gaps:

#### If Employee Count Still Unknown:
```
TOOL: web_search
QUERY: "[Company Name]" employees size OR headcount OR team
```

#### If Ownership Uncertain:
```
TOOL: web_search
QUERY: "[Founder Name]" "[Company Name]" founder owner
```

#### If Business Model Unclear:
```
TOOL: web_fetch
URL: [company_website]/about OR /company OR /team
```

#### If Category Fit Uncertain:
```
TOOL: web_search
QUERY: "[Company Name]" clients customers case studies
```

---

## Special Search Patterns

### Pattern 1: For Market Data Companies
```
"[Company Name]" Bloomberg OR Refinitiv OR "market data" entitlements
"[Company Name]" vendor management OR compliance OR audits
```

### Pattern 2: For Trading Infrastructure Companies
```
"[Company Name]" OMS OR EMS OR "Charles River" OR Aladdin
"[Company Name]" FIX protocol OR trading platform OR connectivity
```

### Pattern 3: For Compliance/RegTech Companies
```
"[Company Name]" surveillance OR compliance OR regulatory reporting
"[Company Name]" TCA OR "best execution" OR trade monitoring
```

---

## Snippet Analysis Techniques

### How to Parse Search Snippets for PE/VC:

**Positive PE/VC Indicators (Automatic RED FLAG):**
- "raised $X in Series A/B/C"
- "backed by [Investor Name]"
- "portfolio company of"
- "acquired by [Company]"
- "Private Equity-Backed" (from PitchBook)
- "led by [VC Firm]"
- Mentions of: Sequoia, Accel, a16z, KKR, Blackstone, etc.

**Neutral Indicators (Need verification):**
- "private company"
- "privately held"
- "independent"

**Negative Indicators (Good signs):**
- "founder-owned"
- "founder-led"
- "bootstrapped"
- "No external funding detected"

### How to Extract Investor Names from Snippets:

**Look for phrases:**
- "The [Investor Name] has invested in [Company]"
- "backed by [Investor Name]"
- "[Company], a portfolio company of [Investor Name]"
- "led by [Investor Name]"

**Once investor name found → Immediate verification search:**
`"[Company Name]" "[Investor Name]"`

---

## Search Quality Checks

### After Stage 2 (PE/VC Detection), Verify:

**Checklist:**
- [ ] Searched PitchBook directly (site:pitchbook.com)
- [ ] Searched Crunchbase (site:crunchbase.com)
- [ ] Searched for exact phrases: "Private Equity-Backed" OR "VC-Backed" OR "Financing Status"
- [ ] Used "funding" and "investors" keywords
- [ ] Searched for "portfolio company" or "acquired by"
- [ ] If investor name found → Verified with specific search
- [ ] **PAYWALL CHECK:** If PitchBook/Crunchbase profile found → Treated as RED FLAG (not ignored)

**If ALL checkboxes ✓ and NO PE/VC found → Proceed with confidence**
**If ANY box ✗ → Continue searching before marking GREEN**
**If PitchBook/Crunchbase profile exists → Do NOT give GREEN (use YELLOW or search harder)**

### After Stage 1 (Employee Count), Verify:

**Checklist:**
- [ ] Searched LinkedIn directly
- [ ] Found specific number or range (not just "private company")
- [ ] Number is consistent across 2+ sources

**If employee count cannot be verified → Note this in rationale**

---

## Decision Framework Based on Search Results

### PE/VC Detection:
```
IF PitchBook snippet shows "Private Equity-Backed" → RED (automatic)
IF PitchBook snippet shows "Financing Status" → RED (automatic)
IF PitchBook snippet mentions investor name → RED (automatic)
IF PitchBook/Crunchbase PROFILE EXISTS (even if paywalled) → RED FLAG (do NOT give GREEN)
  → PAYWALL RULE: Profile existence suggests institutional investors
  → These databases don't profile small bootstrapped companies
  → Default to YELLOW (uncertain) or search harder for confirmation
IF Crunchbase shows funding rounds → RED (automatic)
IF snippet says "raised $X" → RED (automatic)
IF 6+ searches done and no profile/funding found → Proceed cautiously
IF uncertain → YELLOW (not GREEN)
```

### Employee Count:
```
IF LinkedIn shows X-Y employees → Use this range
IF multiple sources agree on ~N → Use this number
IF sources conflict (e.g., 10 vs 50) → Note "10-50 per various sources"
IF cannot find any data → Note "Cannot verify employee count"
```

### Business Model (Software + Services):
```
IF software products + "fully managed service" → YELLOW (need revenue data)
IF software products + NO service language → RED (pure software)
IF services only + no products → Evaluate category fit
```

---

## Example: Complete Search Sequence for EZX Inc.

### Searches Performed:
1. `web_fetch: https://www.ezxinc.com` → Found service language + products
2. `"EZX Inc" Westfield NJ employees services` → Found company info
3. `"EZX Inc" funding investors PE VC` → No PE/VC found
4. `"EZX Inc" LinkedIn employees` → Found "2-10 employees, view 8"
5. `"EZX Inc" founder CEO owner` → Found Paul Savin (founder, 2004)
6. `site:pitchbook.com "EZX Inc"` → No PitchBook profile found
7. `"EZX Inc" "managed service" operations` → Confirmed service language
8. `web_fetch: ezxinc.com/services` → Got detailed service descriptions

### Result:
- ✅ Employee count: 8-10 (verified)
- ✅ PE/VC: None detected (thorough search)
- ✅ Business model: Software + services (YELLOW per rules)
- ✅ Location: US-based
- **Verdict: YELLOW** (correct)

---

## Example: Complete Search Sequence for MDMS

### Searches Performed:
1. `web_fetch: https://mdms.com` → Found services description
2. `"Market Data Management Solutions" MDMS New York employees` → Found company info
3. `"MDMS Inc" market data funding investors venture capital` → Generic search
4. `site:pitchbook.com "Market Data Management Solutions"` → **FOUND PITCHBOOK PROFILE**
   - URL: https://pitchbook.com/profiles/company/527137-57
   - **PAYWALL DETECTED**: Snippet may be limited/vague
   - **PAYWALL RULE TRIGGERED**: PitchBook profile existence = RED FLAG
5. `"Market Data Management Solutions" "Private Equity-Backed" OR "VC-Backed"` → **Search for exact phrases**
6. `site:crunchbase.com "Market Data Management Solutions" funding` → Cross-check alternative source
7. `"Market Data Management Solutions" "Vareton Group"` → **Verify investor if name appears in any snippet**

### Critical PAYWALL Handling:
- PitchBook page shows "Financing Status: Private Equity-Backed" but page is paywalled (403 error)
- **Even if snippet doesn't show "PE-Backed", the profile existence is a RED FLAG**
- PAYWALL RULE: PitchBook doesn't profile small bootstrapped companies
- Profile existence alone suggests institutional backing
- Search #5 targets the exact phrase from the paywalled page
- This phrase may leak into press releases, cached pages, or other databases

### Result:
- ✅ Found PitchBook profile (RED FLAG per PAYWALL RULE)
- ✅ Confirmed PE backing (Vareton Group via additional searches)
- **Verdict: RED** (automatic disqualification)
- **Fallback if investor unconfirmed: YELLOW** (profile exists but can't confirm details)

---

## Common Mistakes to Avoid

### ❌ Don't Do This:
1. **Only searching "company name funding"** → Too generic
2. **Skipping PitchBook direct search** → Most reliable PE/VC source
3. **Ignoring PitchBook profile if snippet is vague** → FALSE POSITIVE! Profile existence = RED FLAG
4. **Not searching for "Private Equity-Backed" exact phrases** → Misses paywalled information
5. **Not verifying investor names found in snippets** → False negatives
6. **Marking GREEN without thorough PE/VC search** → Dangerous false positive
7. **Assuming "privately held" = no PE backing** → Many PE-backed companies are private
8. **Stopping after 3-4 searches** → Not enough for reliable screening

### ✅ Do This:
1. **Always search PitchBook directly** → site:pitchbook.com
2. **Apply PAYWALL RULE** → Profile exists (even if paywalled) = RED FLAG, don't give GREEN
3. **Search for exact PE/VC phrases** → "Private Equity-Backed" OR "VC-Backed" OR "Financing Status"
4. **Parse snippets for investor names** → Then verify with specific search
5. **Search 8-12 times minimum** → Thorough is better than fast
6. **Default to YELLOW when uncertain** → Conservative approach (false negative < false positive)
7. **Verify employee count from LinkedIn** → Most reliable source
8. **Cross-reference multiple sources** → Consistency check

---

## Search Budget Guidelines

### Minimum Search Counts by Verdict:

**For GREEN verdict (highest confidence needed):**
- Minimum: 10-12 searches
- Must include: PitchBook, Crunchbase, LinkedIn, multiple PE/VC searches
- Must verify: Employee count, ownership, business model, category fit

**For YELLOW verdict (needs clarification):**
- Minimum: 8-10 searches
- Must include: Basic PE/VC search, employee search, business model search
- Acceptable: Some uncertainty remains

**For RED verdict (disqualifying factor found):**
- Minimum: 6-8 searches
- Can stop early if PE/VC found
- Can stop early if clearly wrong size/location/category

---

## Platform-Specific Search Syntax

### LinkedIn:
```
site:linkedin.com/company "[company-name]"
"[Company Name]" LinkedIn employees
"[Company Name]" site:linkedin.com
```

### PitchBook:
```
site:pitchbook.com "[Company Name]"
site:pitchbook.com "[Company Name]" funding
```

### Crunchbase:
```
site:crunchbase.com "[Company Name]"
site:crunchbase.com "[Company Name]" funding
```

### Company Website Paths:
```
[domain]/about
[domain]/team
[domain]/services
[domain]/solutions
[domain]/company
[domain]/leadership
```

---

## Integration with Evaluation Rules

### When Search Results Trigger Rules:

**MANDATORY YELLOW if:**
- Software products found + "fully managed service" mentioned
- Cannot verify employee count but other factors fit
- Limited public information but no red flags

**AUTOMATIC RED if:**
- Any PE/VC backing detected (even 1%)
- Non-US headquarters confirmed
- Employee count <10 or >150 with institutionalization
- Pure software product (no service indicators)

**GREEN only if:**
- Thorough PE/VC search (10+ searches) finds nothing
- Employee count verified in 10-100 range
- US-based confirmed
- Category fit confirmed (Tier 1 or Tier 2)
- Business model confirmed (managed services)

---

## Troubleshooting

### Issue: Cannot find employee count
**Solution:**
- Try: company name + "team size"
- Try: company name + "headcount"
- Try: founders' names on LinkedIn (check their profiles)
- Try: company name + ZoomInfo OR RocketReach
- Last resort: Note "Cannot verify from public info" → Flag for manual check

### Issue: Conflicting employee counts (10 vs 50)
**Solution:**
- Use the range: "10-50 employees per various sources"
- Prefer LinkedIn if available (most current)
- Note the discrepancy in rationale

### Issue: PitchBook paywalled
**Solution:**
- Snippet usually shows key info ("Private Equity-Backed", investor names)
- If snippet says "Private Equity-Backed" → RED (trust snippet)
- If snippet unclear → Search for investor names mentioned
- If completely unclear → YELLOW (needs manual verification)

### Issue: Too many irrelevant results
**Solution:**
- Add location to query: "[Company] [City, State]"
- Use exact phrases: "[Exact Company Name]"
- Add distinguishing keywords: "[Company] [distinctive service]"
- Use site: operator for specific sources

---

## Quality Assurance

### Before Finalizing Verdict:

**Ask yourself:**
1. Did I search PitchBook directly? (site:pitchbook.com)
2. Did I search for investor names if any appeared in snippets?
3. Did I find employee count from reliable source?
4. Did I verify business model from company website?
5. Am I confident in this verdict, or should it be YELLOW?

**If ANY answer is "No" or "Uncertain" → Continue searching or use YELLOW**

---

## Summary: Minimum Required Searches

### Every Company Evaluation Must Include:

**MANDATORY (do these every time):**
1. ✅ Company website fetch
2. ✅ General company info search
3. ✅ LinkedIn employee search
4. ✅ PitchBook direct search (site:pitchbook.com)
5. ✅ PE/VC funding search (with "funding investors" keywords)
6. ✅ Ownership/founder search
7. ✅ Business model verification search

**CONDITIONAL (add based on findings):**
8. ⚠️ Investor name verification search (if investor mentioned)
9. ⚠️ Additional employee count search (if first attempt failed)
10. ⚠️ Service language verification (if software company)
11. ⚠️ Crunchbase search (if PitchBook unclear)
12. ⚠️ Additional business model searches (if unclear)

**TOTAL: Minimum 7 searches, typically 10-12 for thorough evaluation**

---

## Final Checklist Before Submitting Verdict

- [ ] Searched for PE/VC backing thoroughly (PitchBook + Crunchbase + generic)
- [ ] If investor name appeared → verified with specific search
- [ ] Found employee count from reliable source (or noted inability)
- [ ] Verified US-based location
- [ ] Determined business model (services vs. software vs. mixed)
- [ ] Applied mechanical rules (e.g., software + service language → YELLOW)
- [ ] Used conservative default (when uncertain → YELLOW, not GREEN)
- [ ] Total search count: 7+ searches performed

**Only mark GREEN if ALL checkboxes are ✓ with high confidence**

---
