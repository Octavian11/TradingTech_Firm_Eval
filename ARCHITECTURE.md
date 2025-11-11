# Multi-Agent Architecture

This document explains the multi-agent system design for the Investment Screening Tool.

## Why Multi-Agent Architecture?

### Problem with Single-Agent Approach
- Large context windows when processing many companies
- Risk of hitting token limits (especially with 50-100 companies)
- Mixed responsibilities (file I/O + API calls + coordination)
- Difficult to maintain and test

### Multi-Agent Solution
- **Small context windows**: Process 5 companies per API call (default, configurable 1-10)
- **Automatic rate limiting**: Max 25 records per run (prevents API overuse)
- **Separation of concerns**: Each agent has a single responsibility
- **Better error handling**: Errors isolated to specific agents
- **Scalability**: Easy to add parallel processing later

## Agent Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   OrchestratorAgent                     │
│         (Coordinates the entire workflow)                │
└──────────────┬─────────────────────┬────────────────────┘
               │                     │
               ▼                     ▼
    ┌──────────────────┐    ┌──────────────────┐
    │  ExcelManager    │    │ EvaluatorAgent   │
    │  (File I/O)      │    │  (Claude API)    │
    └──────────────────┘    └──────────────────┘
           │                         │
           ▼                         ▼
    companies.xlsx           Claude AI API
                          (company-evaluator)
```

## The Three Agents

### 1. ExcelManager 📊
**File**: `agents/excel_manager.py`

**Responsibilities:**
- Read company data from Excel files
- Write evaluation results back to Excel
- Track processing status (Processed? column)
- Manage incremental saves
- Provide statistics

**Key Methods:**
```python
- get_pending_companies(limit) → List[Company]
- update_results(results) → None
- save() → None
- get_statistics() → Dict[str, int]
```

**No API calls** - purely file operations.

**Context window impact:** ✅ None (doesn't use Claude API)

---

### 2. EvaluatorAgent 🤖
**File**: `agents/evaluator_agent.py`

**Responsibilities:**
- Make Claude API calls with company-evaluator skill
- Process 1-10 companies per batch (default: 5)
- Parse Claude's responses into structured verdicts
- Handle API errors gracefully

**Key Methods:**
```python
- evaluate_batch(companies: List[Company]) → List[EvaluationResult]
- _build_batch_prompt(companies) → str
- _call_claude_api(prompt) → str
- _parse_batch_response(response, companies) → List[EvaluationResult]
```

**No file operations** - purely API interactions.

**Context window impact:** ✅ Controlled (5 companies per call by default, ~1000 tokens)

---

### 3. OrchestratorAgent 🎯
**File**: `agents/orchestrator_agent.py`

**Responsibilities:**
- Coordinate between ExcelManager and EvaluatorAgent
- Manage batch processing workflow
- Enforce max records per run limit (default: 25)
- Track overall progress
- Handle rate limiting (delays between batches)
- Generate summary reports

**Key Methods:**
```python
- run() → dict  # Run complete workflow (stops at max_records_per_run)
- process_single_batch() → dict  # Process one batch
- get_progress() → dict  # Get current statistics
```

**New Feature:** Tracks records processed this run and stops at max_records_per_run limit.

**Context window impact:** ✅ None (doesn't use Claude API directly)

---

## Workflow

### High-Level Flow

1. **Orchestrator** requests pending companies from **ExcelManager**
2. **ExcelManager** returns batch of 1-3 companies
3. **Orchestrator** sends batch to **EvaluatorAgent**
4. **EvaluatorAgent** calls Claude API with company-evaluator skill
5. **EvaluatorAgent** returns structured results
6. **Orchestrator** sends results to **ExcelManager**
7. **ExcelManager** updates Excel file and saves
8. Repeat until all companies processed

### Detailed Workflow

```
┌─────────────────────────────────────────────────────────┐
│ START: OrchestratorAgent.run()                          │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │ Get pending companies  │
         │ (batch of 1-3)         │
         └────────┬───────────────┘
                  │
                  ▼
         ┌────────────────────────┐
         │ Any companies left?    │
         └────┬───────────┬───────┘
              │ No        │ Yes
              │           │
              │           ▼
              │  ┌─────────────────────┐
              │  │ EvaluatorAgent      │
              │  │ evaluate_batch()    │
              │  └─────┬───────────────┘
              │        │
              │        ▼
              │  ┌─────────────────────┐
              │  │ Claude API call     │
              │  │ (1-3 companies)     │
              │  └─────┬───────────────┘
              │        │
              │        ▼
              │  ┌─────────────────────┐
              │  │ Parse responses     │
              │  │ (GREEN/YELLOW/RED)  │
              │  └─────┬───────────────┘
              │        │
              │        ▼
              │  ┌─────────────────────┐
              │  │ ExcelManager        │
              │  │ update_results()    │
              │  └─────┬───────────────┘
              │        │
              │        ▼
              │  ┌─────────────────────┐
              │  │ Save to Excel       │
              │  └─────┬───────────────┘
              │        │
              │        ▼
              │  ┌─────────────────────┐
              │  │ Rate limit delay    │
              │  │ (e.g., 1 second)    │
              │  └─────┬───────────────┘
              │        │
              └────────┴─────────────────┐
                                         │
                      ┌──────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │ Generate summary stats │
         └────────┬───────────────┘
                  │
                  ▼
         ┌────────────────────────┐
         │ END: Return results    │
         └────────────────────────┘
```

## Context Window Management

### Problem
Processing 50 companies in a single API call:
- Prompt size: ~50 companies × 200 tokens each = 10,000 tokens
- Response size: ~50 verdicts × 100 tokens each = 5,000 tokens
- **Total: ~15,000 tokens per call** (approaching limits)

### Solution
Processing 5 companies per batch (default):
- Prompt size: ~5 companies × 200 tokens each = 1,000 tokens
- Response size: ~5 verdicts × 100 tokens each = 500 tokens
- **Total: ~1,500 tokens per call** ✅

### Batch Size Recommendations

| Batch Size | Context Window | Speed | Recommended For |
|------------|---------------|-------|-----------------|
| 1 company | Smallest (~300 tokens) | Slowest | Maximum reliability, sensitive data |
| 3 companies | Small (~900 tokens) | Moderate | Conservative approach |
| 5 companies | Medium (~1,500 tokens) | **Default - balanced** | Most use cases |
| 10 companies | Large (~3,000 tokens) | Fastest | Speed priority, trusted data quality |

**We default to batch_size=5** for optimal balance of speed and reliability.

### Max Records Per Run

**Default: 25 records per run**

The system automatically stops after processing 25 records. This:
- Prevents excessive API usage in a single run
- Allows for incremental progress review
- Keeps sessions manageable

To process more, simply run the script again (it auto-skips completed records).

## Error Handling

### Agent-Level Error Handling

Each agent handles its own errors:

**ExcelManager:**
- File not found → Raises exception with clear message
- Permission errors → Logs and raises
- Data validation → Warns but continues

**EvaluatorAgent:**
- API errors → Returns ERROR verdict with reason
- Parse errors → Returns UNKNOWN verdict with raw response
- Network timeout → Retries (future enhancement)

**OrchestratorAgent:**
- Batch failure → Logs error, marks companies as Error, continues
- Keyboard interrupt → Saves progress and exits gracefully
- Fatal errors → Logs with full stack trace

### Incremental Saves

After each batch:
1. Results are immediately written to Excel
2. Progress is saved (Processed? = Yes)
3. If script crashes, already processed companies are skipped on restart

**Resume support:** Run the same command again, and it will automatically skip companies marked "Yes" in Processed? column.

## Usage Examples

### Basic Usage (Batch Size 5, Max 25 Records - Default)
```bash
python multi_agent_screening.py companies.xlsx
```

- Context window: ~1,500 tokens per API call
- Processes up to 25 records per run
- Run again to process more

### Conservative (Batch Size 1)
```bash
python multi_agent_screening.py companies.xlsx --batch-size 1
```

- Context window: ~300 tokens per API call
- Best for: Maximum reliability, sensitive data

### Fast Mode (Batch Size 10)
```bash
python multi_agent_screening.py companies.xlsx --batch-size 10
```

- Context window: ~3,000 tokens per API call
- Best for: Speed priority, trusted data quality

### Process 50 Records
```bash
python multi_agent_screening.py companies.xlsx --max-records 50
```

- Processes up to 50 records in one run
- Uses default batch size of 5

### Custom Configuration
```bash
python multi_agent_screening.py companies.xlsx \
  --batch-size 2 \
  --skill company-evaluator \
  --delay 2.0 \
  --verbose
```

## Scalability

### Current Implementation
- Sequential batch processing
- One batch at a time
- Suitable for 1-100 companies

### Future Enhancements
1. **Parallel Processing**: Process multiple batches simultaneously
2. **Caching**: Cache Claude responses for similar companies
3. **Smart Batching**: Group similar companies together
4. **Retry Logic**: Exponential backoff for API errors
5. **Progress Bar**: Visual progress indicator

## Testing the System

### Test with Sample Data
```bash
# Create sample Excel
python create_example_excel.py

# Run with batch size 1 (most conservative)
python multi_agent_screening.py companies_to_screen.xlsx --batch-size 1

# Check results
# Open companies_to_screen.xlsx and verify Verdict/Rationale columns
```

### Monitor Logs
```bash
# Tail the log file
tail -f multi_agent_screening.log
```

### Test Error Handling
```bash
# Interrupt the process (Ctrl+C)
# Then run again - it should skip already processed companies
python multi_agent_screening.py companies_to_screen.xlsx
```

## Files Overview

```
TradingTech_Firm_Eval/
├── agents/
│   ├── __init__.py              # Package exports
│   ├── excel_manager.py         # Agent 1: File I/O
│   ├── evaluator_agent.py       # Agent 2: Claude API
│   └── orchestrator_agent.py    # Agent 3: Coordinator
│
├── multi_agent_screening.py     # Main entry point (NEW)
├── investment_screening_agent.py # Old single-agent version
├── create_example_excel.py      # Generate test data
│
├── ARCHITECTURE.md              # This file
├── README.md                    # User documentation
└── requirements.txt             # Dependencies
```

## Migration Guide

### From Single-Agent to Multi-Agent

**Old way:**
```bash
python investment_screening_agent.py companies.xlsx
```

**New way:**
```bash
python multi_agent_screening.py companies.xlsx
```

### Key Differences

| Feature | Single-Agent | Multi-Agent |
|---------|--------------|-------------|
| Context window | Large (all companies) | Small (5 companies default) |
| Architecture | Monolithic | Modular (3 agents) |
| Batch processing | No | Yes (1-10 configurable) |
| Max records per run | Unlimited | 25 (configurable) |
| Error isolation | No | Yes |
| Testability | Difficult | Easy |
| Scalability | Limited | High |

## Summary

The multi-agent architecture provides:

✅ **Small context windows** (5 companies per API call by default, ~1,500 tokens)
✅ **Automatic rate limiting** (max 25 records per run, prevents API overuse)
✅ **Separation of concerns** (file I/O, API, coordination)
✅ **Better error handling** (isolated, recoverable)
✅ **Incremental saves** (crash-resistant)
✅ **Resume support** (skip already processed)
✅ **Scalability** (easy to parallelize, configurable batch sizes)
✅ **Maintainability** (clear responsibilities)

**Default Configuration:**
- Batch size: 5 companies per API call
- Max records per run: 25
- Context window: ~1,500 tokens per call

Use `multi_agent_screening.py` for all production workloads. Run multiple times for large datasets (auto-resumes).
