// MCP Weather Agent Example
// Demonstrates creating custom MCP tools and using them in an agent

import { query, tool, createSdkMcpServer } from '@anthropic-ai/claude-agent-sdk';
import { z } from 'zod';

// Define weather tool
const weatherTool = tool(
  'get_weather',
  'Get current temperature and conditions for a location',
  {
    latitude: z.number().describe('Latitude coordinate (-90 to 90)'),
    longitude: z.number().describe('Longitude coordinate (-180 to 180)')
  },
  async (args) => {
    try {
      console.log(`Fetching weather for ${args.latitude}, ${args.longitude}`);

      const response = await fetch(
        `https://api.open-meteo.com/v1/forecast?latitude=${args.latitude}&longitude=${args.longitude}&current=temperature_2m,weathercode`
      );

      if (!response.ok) {
        return {
          content: [{
            type: 'text',
            text: `API error: ${response.status} ${response.statusText}`
          }]
        };
      }

      const data = await response.json();

      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            temperature: `${data.current.temperature_2m}°C`,
            weatherCode: data.current.weathercode,
            location: { latitude: args.latitude, longitude: args.longitude }
          }, null, 2)
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Failed to fetch weather: ${error.message}`
        }]
      };
    }
  }
);

// Create MCP server
const weatherServer = createSdkMcpServer({
  name: 'weather',
  version: '1.0.0',
  tools: [weatherTool]
});

// Streaming input generator (required for MCP)
async function* generateMessages() {
  yield {
    role: 'user',
    content: 'What is the weather like in San Francisco (37.7749, -122.4194) and New York (40.7128, -74.0060)?'
  };
}

async function main() {
  console.log('Starting weather agent with custom MCP tool...\n');

  for await (const message of query({
    prompt: generateMessages(),
    options: {
      mcpServers: { weather: weatherServer },
      allowedTools: ['mcp__weather__get_weather'],
      maxBudgetUsd: 0.5
    }
  })) {
    if (message.type === 'text') {
      console.log('Claude:', message.text);
    }

    if (message.type === 'tool_use') {
      console.log(`\n[Tool] ${message.name}`, message.input);
    }

    if (message.type === 'result') {
      console.log('\n--- Result ---');
      if (message.subtype === 'success') {
        console.log('Status: Success');
        console.log(`Cost: $${message.total_cost_usd.toFixed(4)}`);
      } else {
        console.error('Error:', message.subtype);
      }
    }
  }
}

main().catch(console.error);
