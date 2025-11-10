#!/usr/bin/env ts-node
/**
 * Script to invoke Claude AI with a custom skill reference.
 * This script demonstrates how to call the Anthropic Claude API
 * and reference the 'company-evaluator' skill programmatically.
 */

import Anthropic from '@anthropic-ai/sdk';

interface ClaudeResponse {
  response: string;
  model: string;
  role: string;
  stopReason: string | null;
  usage: {
    inputTokens: number;
    outputTokens: number;
  };
}

interface InvokeOptions {
  prompt: string;
  skillName?: string;
  model?: string;
  maxTokens?: number;
  temperature?: number;
}

/**
 * Invoke Claude AI with a specific skill reference.
 */
async function invokeClaudeWithSkill(
  prompt: string,
  skillName: string = 'company-evaluator',
  model: string = 'claude-sonnet-4-5-20250929',
  maxTokens: number = 4096
): Promise<string> {
  // Initialize the Anthropic client
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY environment variable not set');
  }

  const client = new Anthropic({ apiKey });

  // Construct the system prompt with skill reference
  const systemPrompt = `You have access to the '${skillName}' skill.
Use this skill to help answer the user's request.`;

  // Create the message
  const message = await client.messages.create({
    model,
    max_tokens: maxTokens,
    system: systemPrompt,
    messages: [
      {
        role: 'user',
        content: prompt,
      },
    ],
  });

  // Extract and return the response text
  const content = message.content[0];
  if (content.type === 'text') {
    return content.text;
  }

  throw new Error('Unexpected response type from Claude API');
}

/**
 * Invoke Claude AI with skill reference and return detailed response.
 */
async function invokeClaudeWithSkillExtended(
  options: InvokeOptions
): Promise<ClaudeResponse> {
  const {
    prompt,
    skillName = 'company-evaluator',
    model = 'claude-sonnet-4-5-20250929',
    maxTokens = 4096,
    temperature = 1.0,
  } = options;

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY environment variable not set');
  }

  const client = new Anthropic({ apiKey });

  // Reference the skill in the system prompt
  const systemPrompt = `You have access to the '${skillName}' skill.
Please use this skill to assist with the user's request.
Invoke the skill as needed to provide comprehensive analysis.`;

  // Create the message with extended parameters
  const message = await client.messages.create({
    model,
    max_tokens: maxTokens,
    temperature,
    system: systemPrompt,
    messages: [
      {
        role: 'user',
        content: prompt,
      },
    ],
  });

  // Extract response text
  const content = message.content[0];
  if (content.type !== 'text') {
    throw new Error('Unexpected response type from Claude API');
  }

  // Return detailed response information
  return {
    response: content.text,
    model: message.model,
    role: message.role,
    stopReason: message.stop_reason,
    usage: {
      inputTokens: message.usage.input_tokens,
      outputTokens: message.usage.output_tokens,
    },
  };
}

// Example usage
async function main() {
  // Example 1: Simple usage
  console.log('='.repeat(60));
  console.log('Example 1: Simple skill invocation');
  console.log('='.repeat(60));

  try {
    const response = await invokeClaudeWithSkill(
      'Please evaluate Apple Inc. as a potential investment opportunity.',
      'company-evaluator'
    );
    console.log(`\nResponse:\n${response}\n`);
  } catch (error) {
    console.error(`Error: ${error}`);
  }

  // Example 2: Extended usage with detailed response
  console.log('='.repeat(60));
  console.log('Example 2: Extended skill invocation with details');
  console.log('='.repeat(60));

  try {
    const detailedResponse = await invokeClaudeWithSkillExtended({
      prompt: "Analyze Microsoft Corporation's market position and growth potential.",
      skillName: 'company-evaluator',
      temperature: 0.7,
    });

    console.log(`\nResponse: ${detailedResponse.response}`);
    console.log(`\nModel: ${detailedResponse.model}`);
    console.log(`Stop Reason: ${detailedResponse.stopReason}`);
    console.log(`Input Tokens: ${detailedResponse.usage.inputTokens}`);
    console.log(`Output Tokens: ${detailedResponse.usage.outputTokens}`);
  } catch (error) {
    console.error(`Error: ${error}`);
  }
}

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}

// Export functions for use in other modules
export { invokeClaudeWithSkill, invokeClaudeWithSkillExtended };
export type { ClaudeResponse, InvokeOptions };
