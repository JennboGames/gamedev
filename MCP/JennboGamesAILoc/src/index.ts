#!/usr/bin/env node

import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  {
    name: "jennbo-games-ai-loc-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      resources: {},
      tools: {},
    },
  }
);

server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "ai-loc://game-strings",
        name: "Game Localization Strings",
        description: "Game text strings that need AI-powered localization",
        mimeType: "application/json",
      },
    ],
  };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  if (request.params.uri === "ai-loc://game-strings") {
    return {
      contents: [
        {
          uri: "ai-loc://game-strings",
          mimeType: "application/json",
          text: JSON.stringify({
            strings: [
              {
                id: "welcome_message",
                text: "Welcome to the game!",
                context: "Main menu greeting",
              },
              {
                id: "play_button",
                text: "Play",
                context: "Main menu button",
              },
            ],
          }),
        },
      ],
    };
  }
  throw new Error(`Unknown resource: ${request.params.uri}`);
});

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "localize_text",
        description:
          "Localize game text using AI for a specific language and cultural context",
        inputSchema: {
          type: "object" as const,
          properties: {
            text: {
              type: "string",
              description: "The game text to localize",
            },
            target_language: {
              type: "string",
              description:
                "The target language code (e.g., 'es', 'fr', 'ja')",
            },
            context: {
              type: "string",
              description:
                "Game context for the text (e.g., 'dialog', 'ui_button')",
            },
          },
          required: ["text", "target_language"],
        },
      },
      {
        name: "validate_localization",
        description:
          "Validate localized text for length constraints and cultural appropriateness",
        inputSchema: {
          type: "object" as const,
          properties: {
            original_text: {
              type: "string",
              description: "The original game text",
            },
            localized_text: {
              type: "string",
              description: "The localized text to validate",
            },
            language: {
              type: "string",
              description: "The language of the localized text",
            },
          },
          required: ["original_text", "localized_text", "language"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "localize_text") {
    const { text, target_language, context } = request.params.arguments as {
      text: string;
      target_language: string;
      context?: string;
    };

    return {
      content: [
        {
          type: "text",
          text: `Localized "${text}" to ${target_language}${context ? ` (${context})` : ""}\nNote: This is a placeholder. Integrate with actual AI localization service.`,
        },
      ],
    };
  }

  if (request.params.name === "validate_localization") {
    const { original_text, localized_text, language } =
      request.params.arguments as {
        original_text: string;
        localized_text: string;
        language: string;
      };

    return {
      content: [
        {
          type: "text",
          text: `Validation for "${localized_text}" in ${language}:\n- Length check: PASS\n- Cultural appropriateness: PENDING (requires manual review)\nNote: This is a placeholder validation. Implement full validation logic.`,
        },
      ],
    };
  }

  throw new Error(`Unknown tool: ${request.params.name}`);
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP Server started");
}

main().catch(console.error);
