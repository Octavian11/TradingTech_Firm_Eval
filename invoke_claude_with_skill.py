#!/usr/bin/env python3
"""
Script to invoke Claude AI with a custom skill reference.
This script demonstrates how to call the Anthropic Claude API
and reference the 'company-evaluator' skill programmatically.
"""

import os
from anthropic import Anthropic


def invoke_claude_with_skill(
    prompt: str,
    skill_name: str = "company-evaluator",
    model: str = "claude-sonnet-4-5-20250929",
    max_tokens: int = 4096
) -> str:
    """
    Invoke Claude AI with a specific skill reference.

    Args:
        prompt: The user prompt/message to send to Claude
        skill_name: Name of the skill to invoke (default: company-evaluator)
        model: Claude model to use
        max_tokens: Maximum tokens for response

    Returns:
        The response from Claude AI
    """
    # Initialize the Anthropic client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = Anthropic(api_key=api_key)

    # Construct the message with skill reference
    # Skills are invoked by mentioning them in the system prompt or user message
    system_prompt = f"""You have access to the '{skill_name}' skill.
Use this skill to help answer the user's request."""

    # Create the message
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # Extract and return the response
    response_text = message.content[0].text
    return response_text


def invoke_claude_with_skill_extended(
    prompt: str,
    skill_name: str = "company-evaluator",
    model: str = "claude-sonnet-4-5-20250929",
    max_tokens: int = 4096,
    temperature: float = 1.0
) -> dict:
    """
    Invoke Claude AI with skill reference and return detailed response.

    Args:
        prompt: The user prompt/message to send to Claude
        skill_name: Name of the skill to invoke
        model: Claude model to use
        max_tokens: Maximum tokens for response
        temperature: Sampling temperature (0.0 to 1.0)

    Returns:
        Dictionary with response details including text, usage stats, etc.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = Anthropic(api_key=api_key)

    # Reference the skill in the system prompt
    system_prompt = f"""You have access to the '{skill_name}' skill.
Please use this skill to assist with the user's request.
Invoke the skill as needed to provide comprehensive analysis."""

    # Create the message with extended parameters
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # Return detailed response information
    return {
        "response": message.content[0].text,
        "model": message.model,
        "role": message.role,
        "stop_reason": message.stop_reason,
        "usage": {
            "input_tokens": message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens
        }
    }


# Example usage
if __name__ == "__main__":
    # Example 1: Simple usage
    print("=" * 60)
    print("Example 1: Simple skill invocation")
    print("=" * 60)

    try:
        response = invoke_claude_with_skill(
            prompt="Please evaluate Apple Inc. as a potential investment opportunity.",
            skill_name="company-evaluator"
        )
        print(f"\nResponse:\n{response}\n")
    except Exception as e:
        print(f"Error: {e}")

    # Example 2: Extended usage with detailed response
    print("=" * 60)
    print("Example 2: Extended skill invocation with details")
    print("=" * 60)

    try:
        detailed_response = invoke_claude_with_skill_extended(
            prompt="Analyze Microsoft Corporation's market position and growth potential.",
            skill_name="company-evaluator",
            temperature=0.7
        )

        print(f"\nResponse: {detailed_response['response']}")
        print(f"\nModel: {detailed_response['model']}")
        print(f"Stop Reason: {detailed_response['stop_reason']}")
        print(f"Input Tokens: {detailed_response['usage']['input_tokens']}")
        print(f"Output Tokens: {detailed_response['usage']['output_tokens']}")
    except Exception as e:
        print(f"Error: {e}")
