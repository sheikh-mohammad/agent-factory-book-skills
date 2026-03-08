// Session Management Example
// Demonstrates continue, resume, and fork patterns

import { query } from '@anthropic-ai/claude-agent-sdk';

async function demonstrateContinue() {
  console.log('=== Demonstrating Continue ===\n');

  // First query
  console.log('Query 1: Analyze auth module');
  for await (const message of query({
    prompt: 'Read and analyze the authentication module',
    options: { allowedTools: ['Read', 'Grep'] }
  })) {
    if (message.type === 'result' && message.subtype === 'success') {
      console.log('Analysis complete\n');
    }
  }

  // Continue from most recent session
  console.log('Query 2: Continue with refactoring');
  for await (const message of query({
    prompt: 'Now refactor it to use OAuth2',
    options: {
      continue: true,
      allowedTools: ['Read', 'Edit']
    }
  })) {
    if (message.type === 'result' && message.subtype === 'success') {
      console.log('Refactoring complete\n');
    }
  }
}

async function demonstrateResume() {
  console.log('=== Demonstrating Resume ===\n');

  let sessionId: string;

  // First query - capture session ID
  console.log('Starting initial analysis...');
  for await (const message of query({
    prompt: 'Analyze the codebase structure',
    options: { allowedTools: ['Glob', 'Read'] }
  })) {
    if (message.type === 'result') {
      sessionId = message.session_id;
      console.log(`Session ID: ${sessionId}\n`);
    }
  }

  // Simulate doing other work...
  console.log('Doing other work...\n');

  // Resume specific session later
  console.log('Resuming previous session...');
  for await (const message of query({
    prompt: 'Based on your previous analysis, suggest improvements',
    options: {
      resume: sessionId,
      allowedTools: ['Read']
    }
  })) {
    if (message.type === 'result' && message.subtype === 'success') {
      console.log('Suggestions complete\n');
    }
  }
}

async function demonstrateFork() {
  console.log('=== Demonstrating Fork ===\n');

  let originalSessionId: string;

  // Original implementation
  console.log('Original: Implementing with JWT');
  for await (const message of query({
    prompt: 'Implement authentication using JWT',
    options: { allowedTools: ['Read', 'Write'] }
  })) {
    if (message.type === 'result') {
      originalSessionId = message.session_id;
      console.log('JWT implementation complete\n');
    }
  }

  // Fork to try OAuth2
  console.log('Fork 1: Trying OAuth2 instead');
  for await (const message of query({
    prompt: 'Try implementing with OAuth2 instead',
    options: {
      resume: originalSessionId,
      forkSession: true,
      allowedTools: ['Read', 'Write']
    }
  })) {
    if (message.type === 'result' && message.subtype === 'success') {
      console.log('OAuth2 implementation complete\n');
    }
  }

  // Fork to try session-based
  console.log('Fork 2: Trying session-based auth');
  for await (const message of query({
    prompt: 'Try implementing with session-based authentication',
    options: {
      resume: originalSessionId,
      forkSession: true,
      allowedTools: ['Read', 'Write']
    }
  })) {
    if (message.type === 'result' && message.subtype === 'success') {
      console.log('Session-based implementation complete\n');
    }
  }

  console.log('All three approaches preserved in separate sessions!');
}

async function main() {
  try {
    await demonstrateContinue();
    await demonstrateResume();
    await demonstrateFork();
  } catch (error) {
    console.error('Error:', error);
  }
}

main();
