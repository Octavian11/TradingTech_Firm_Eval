# Claude AI Skill Invocation

This project demonstrates how to programmatically invoke Claude AI with a custom skill reference (specifically the "company-evaluator" skill).

## Overview

The code provides both Python and TypeScript implementations for calling the Anthropic Claude API and referencing custom skills that you've configured in Claude Desktop.

## Prerequisites

- Python 3.8+ (for Python implementation)
- Node.js 18+ (for TypeScript implementation)
- Anthropic API key
- Access to the "company-evaluator" skill in your Claude Desktop settings

## Setup

### 1. Get Your Anthropic API Key

1. Visit https://console.anthropic.com/
2. Sign in or create an account
3. Navigate to API Keys section
4. Generate a new API key
5. Copy the key for use in the next step

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```
ANTHROPIC_API_KEY=sk-ant-api03-xxx...
```

### 3. Python Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Or using a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. TypeScript/Node.js Setup

Install Node.js dependencies:

```bash
npm install
```

## Usage

### Python

Run the Python script:

```bash
python invoke_claude_with_skill.py
```

Or use in your own code:

```python
from invoke_claude_with_skill import invoke_claude_with_skill, invoke_claude_with_skill_extended

# Simple usage
response = invoke_claude_with_skill(
    prompt="Evaluate Tesla Inc. as an investment opportunity.",
    skill_name="company-evaluator"
)
print(response)

# Extended usage with details
detailed = invoke_claude_with_skill_extended(
    prompt="Analyze Amazon's market position.",
    skill_name="company-evaluator",
    temperature=0.7
)
print(f"Response: {detailed['response']}")
print(f"Tokens used: {detailed['usage']['input_tokens']} in, {detailed['usage']['output_tokens']} out")
```

### TypeScript/Node.js

Run the TypeScript script:

```bash
npm start
```

Or for development with auto-reload:

```bash
npm run dev
```

Or use in your own code:

```typescript
import { invokeClaudeWithSkill, invokeClaudeWithSkillExtended } from './invoke_claude_with_skill';

// Simple usage
const response = await invokeClaudeWithSkill(
  'Evaluate Tesla Inc. as an investment opportunity.',
  'company-evaluator'
);
console.log(response);

// Extended usage with details
const detailed = await invokeClaudeWithSkillExtended({
  prompt: "Analyze Amazon's market position.",
  skillName: 'company-evaluator',
  temperature: 0.7
});
console.log(`Response: ${detailed.response}`);
console.log(`Tokens: ${detailed.usage.inputTokens} in, ${detailed.usage.outputTokens} out`);
```

## How Skills Work

### Skill Reference

When you invoke Claude with a skill reference, you include the skill name in the system prompt:

```
You have access to the 'company-evaluator' skill.
Use this skill to help answer the user's request.
```

Claude will then automatically have access to the capabilities defined in your skill when processing the request.

### Custom Skills

The "company-evaluator" skill should be configured in your Claude Desktop under:
**Settings → Capabilities → Skills**

Ensure the skill is:
- ✅ Created and saved
- ✅ Enabled/turned on
- ✅ Accessible via your API key

### Skill Invocation Flow

1. Your code creates an API request to Claude
2. The system prompt includes the skill reference
3. Claude loads the skill's capabilities
4. Claude processes your prompt using the skill
5. You receive the response with skill-enhanced analysis

## API Parameters

### Common Parameters

- **prompt** (string, required): The user's question or request
- **skill_name** (string): Name of the skill to use (default: "company-evaluator")
- **model** (string): Claude model ID (default: "claude-sonnet-4-5-20250929")
- **max_tokens** (int): Maximum response length (default: 4096)
- **temperature** (float): Sampling temperature 0.0-1.0 (default: 1.0)

### Available Models

- `claude-sonnet-4-5-20250929` - Latest Sonnet (recommended for most tasks)
- `claude-opus-4-20250514` - Opus for complex reasoning
- `claude-haiku-4-5-20251001` - Haiku for fast, simple tasks

## Examples

### Example 1: Company Evaluation

```python
response = invoke_claude_with_skill(
    prompt="Evaluate NVIDIA Corporation focusing on their AI chip market dominance and future growth potential.",
    skill_name="company-evaluator"
)
```

### Example 2: Comparative Analysis

```python
response = invoke_claude_with_skill(
    prompt="Compare Meta Platforms and Alphabet as investments in the AI and advertising sectors.",
    skill_name="company-evaluator"
)
```

### Example 3: Risk Assessment

```python
response = invoke_claude_with_skill(
    prompt="Analyze the risks associated with investing in emerging market tech companies, using Alibaba as a case study.",
    skill_name="company-evaluator"
)
```

## Response Format

### Simple Response

Returns just the text content from Claude.

### Extended Response

Returns a dictionary/object with:

```json
{
  "response": "The analysis text...",
  "model": "claude-sonnet-4-5-20250929",
  "role": "assistant",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 156,
    "output_tokens": 892
  }
}
```

## Troubleshooting

### API Key Issues

If you see `ANTHROPIC_API_KEY environment variable not set`:
- Ensure your `.env` file exists
- Check the API key is correctly formatted
- Verify the key starts with `sk-ant-api03-`

### Skill Not Found

If the skill doesn't seem to work:
- Verify the skill is enabled in Claude Desktop
- Check the skill name matches exactly (case-sensitive)
- Ensure your API key has access to custom skills

### Rate Limits

If you hit rate limits:
- The API has rate limits based on your plan tier
- Add delays between requests
- Consider upgrading your Anthropic plan

## Cost Considerations

API usage is billed based on:
- **Input tokens**: Your prompt + system prompt + skill context
- **Output tokens**: Claude's response

Current pricing (check Anthropic's website for latest):
- Sonnet 4.5: $3 per million input tokens, $15 per million output tokens

The extended response includes token counts to help you track costs.

## Security

- **Never commit `.env` files** to version control
- Store API keys securely
- Use environment variables or secret management systems in production
- Rotate API keys regularly

## Additional Resources

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Claude API Reference](https://docs.anthropic.com/en/api)
- [Skills Documentation](https://docs.anthropic.com/en/docs/build-with-claude/skills)
- [Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- [TypeScript SDK](https://github.com/anthropics/anthropic-sdk-typescript)

## License

MIT
