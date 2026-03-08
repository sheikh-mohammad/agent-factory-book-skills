// Simple Query Example
// Demonstrates basic agent usage with built-in tools

import { query } from '@anthropic-ai/claude-agent-sdk';

async function main() {
  console.log('Starting simple agent query...\n');

  for await (const message of query({
    prompt: 'Analyze the files in the current directory and summarize what this project does',
    options: {
      allowedTools: ['Bash', 'Glob', 'Read'],
      maxBudgetUsd: 0.5,
      maxTurns: 20
    }
  })) {
    // Log text responses
    if (message.type === 'text') {
      console.log('Claude:', message.text);
    }

    // Log tool usage
    if (message.type === 'tool_use') {
      console.log(`\n[Tool] ${message.name}`);
    }

    // Handle final result
    if (message.type === 'result') {
      console.log('\n--- Result ---');

      if (message.subtype === 'success') {
        console.log('Status: Success');
        console.log('Result:', message.result);
        console.log(`Cost: $${message.total_cost_usd.toFixed(4)}`);
        console.log(`Turns: ${message.turn_count}`);
      } else {
        console.error('Status: Error');
        console.error('Error type:', message.subtype);
      }
    }
  }
}

main().catch(console.error);
