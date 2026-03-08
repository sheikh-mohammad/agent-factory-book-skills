// Multi-Agent Code Review Example
// Demonstrates orchestrating multiple specialized subagents

import { query } from '@anthropic-ai/claude-agent-sdk';

async function main() {
  console.log('Starting multi-agent code review...\n');

  for await (const message of query({
    prompt: 'Perform a comprehensive code review of this project. Use specialized reviewers for security, performance, and code quality.',
    options: {
      allowedTools: ['Read', 'Grep', 'Glob', 'Agent'],
      maxBudgetUsd: 2.0,
      maxTurns: 100,

      // Define specialized subagents
      agents: {
        'security-reviewer': {
          description: 'Security expert for vulnerability analysis - use for security reviews',
          prompt: 'Analyze code for security vulnerabilities including SQL injection, XSS, authentication issues, and insecure dependencies',
          tools: ['Read', 'Grep', 'Glob'],
          model: 'opus',
          systemPrompt: 'You are a security expert with 10 years of experience in application security'
        },

        'performance-reviewer': {
          description: 'Performance optimization expert - use for performance analysis',
          prompt: 'Identify performance bottlenecks, inefficient algorithms, and optimization opportunities',
          tools: ['Read', 'Grep', 'Bash'],
          model: 'sonnet',
          systemPrompt: 'You are a performance optimization expert'
        },

        'code-quality-reviewer': {
          description: 'Code quality and maintainability expert - use for code quality review',
          prompt: 'Review code quality, readability, maintainability, and adherence to best practices',
          tools: ['Read', 'Grep', 'Glob'],
          model: 'sonnet',
          systemPrompt: 'You are a senior software engineer focused on code quality'
        }
      }
    }
  })) {
    if (message.type === 'text') {
      console.log('\n' + message.text);
    }

    if (message.type === 'tool_use') {
      if (message.name === 'Agent') {
        console.log(`\n[Subagent] Invoking: ${message.input.description}`);
      } else {
        console.log(`[Tool] ${message.name}`);
      }
    }

    if (message.type === 'result') {
      console.log('\n=== Review Complete ===');

      if (message.subtype === 'success') {
        console.log('Status: Success');
        console.log(`Total Cost: $${message.total_cost_usd.toFixed(4)}`);
        console.log(`Total Turns: ${message.turn_count}`);
        console.log('\nFinal Report:');
        console.log(message.result);
      } else {
        console.error('Error:', message.subtype);
      }
    }
  }
}

main().catch(console.error);
