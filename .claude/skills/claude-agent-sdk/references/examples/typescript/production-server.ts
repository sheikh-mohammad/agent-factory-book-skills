// Production Express Server Example
// Demonstrates production-ready agent server with error handling, monitoring, and security

import express from 'express';
import { query } from '@anthropic-ai/claude-agent-sdk';

const app = express();
app.use(express.json());

// Metrics tracking
const metrics = {
  totalRequests: 0,
  successfulRequests: 0,
  failedRequests: 0,
  totalCost: 0
};

// Request logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} ${req.method} ${req.path}`);
  next();
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    uptime: process.uptime(),
    metrics
  });
});

// Agent endpoint
app.post('/agent', async (req, res) => {
  const { prompt, userId } = req.body;

  if (!prompt) {
    return res.status(400).json({ error: 'Prompt is required' });
  }

  metrics.totalRequests++;
  const startTime = Date.now();
  const result = [];

  try {
    for await (const message of query({
      prompt,
      options: {
        allowedTools: ['Read', 'WebSearch', 'Grep'],
        disallowedTools: ['Bash', 'Write', 'Edit'],
        maxBudgetUsd: 0.5,
        maxTurns: 30,

        // Security: Block dangerous operations
        canUseTool: async (toolName, toolInput) => {
          // Log all tool usage
          console.log(`[${userId}] Tool: ${toolName}`);

          // Block any remaining dangerous tools
          if (['Bash', 'Write', 'Edit'].includes(toolName)) {
            return { behavior: 'block', message: 'Tool not allowed' };
          }

          return { behavior: 'allow' };
        }
      }
    })) {
      // Collect text responses
      if (message.type === 'text') {
        result.push(message.text);
      }

      // Handle final result
      if (message.type === 'result') {
        const duration = Date.now() - startTime;

        if (message.subtype === 'success') {
          metrics.successfulRequests++;
          metrics.totalCost += message.total_cost_usd;

          // Log metrics
          console.log(`[${userId}] Success - Cost: $${message.total_cost_usd.toFixed(4)}, Duration: ${duration}ms`);

          return res.json({
            result: result.join('\n'),
            metadata: {
              cost: message.total_cost_usd,
              turns: message.turn_count,
              duration,
              sessionId: message.session_id
            }
          });
        } else {
          metrics.failedRequests++;
          console.error(`[${userId}] Error: ${message.subtype}`);

          return res.status(500).json({
            error: message.subtype,
            message: getErrorMessage(message.subtype)
          });
        }
      }
    }
  } catch (error) {
    metrics.failedRequests++;
    console.error(`[${userId}] Exception:`, error);

    return res.status(500).json({
      error: 'internal_error',
      message: 'An unexpected error occurred'
    });
  }
});

// Metrics endpoint
app.get('/metrics', (req, res) => {
  res.json({
    ...metrics,
    averageCost: metrics.successfulRequests > 0
      ? metrics.totalCost / metrics.successfulRequests
      : 0,
    successRate: metrics.totalRequests > 0
      ? (metrics.successfulRequests / metrics.totalRequests) * 100
      : 0
  });
});

// Helper function for error messages
function getErrorMessage(subtype: string): string {
  switch (subtype) {
    case 'error_max_turns':
      return 'Task exceeded maximum number of turns. Try simplifying the request.';
    case 'error_max_budget_usd':
      return 'Task exceeded budget limit. Try a simpler request.';
    case 'error_during_execution':
      return 'An error occurred during execution. Please try again.';
    default:
      return 'An unknown error occurred.';
  }
}

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully...');
  process.exit(0);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Agent server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Metrics: http://localhost:${PORT}/metrics`);
});
