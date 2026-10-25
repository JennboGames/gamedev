# Jennbo Games AI Localization MCP Server

A Model Context Protocol (MCP) server for game development AI localization. This server provides tools and resources for localizing game text using AI-powered techniques while maintaining cultural appropriateness and length constraints.

## Features

- **Localization Tools**: AI-powered text localization for multiple languages
- **Validation Tools**: Validate localized text for length and cultural appropriateness
- **Resource Management**: Access game localization strings through MCP resources
- **Cultural Context**: Support for game-specific context (UI, dialogs, etc.)

## Project Structure

```
.
├── src/
│   └── index.ts          # Main MCP server implementation
├── build/                # Compiled JavaScript output
├── .github/
│   └── copilot-instructions.md
├── .vscode/
│   └── mcp.json          # MCP server configuration
├── package.json
├── tsconfig.json
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- TypeScript

### Installation

```bash
npm install
```

### Development

Build the TypeScript code:

```bash
npm run build
```

Run in development mode:

```bash
npm run dev
```

Start the compiled server:

```bash
npm start
```

## MCP Server Configuration

The server is configured in `.vscode/mcp.json` and exposes:

### Resources

- **ai-loc://game-strings**: Game localization strings in JSON format

### Tools

- **localize_text**: Localize game text for a target language
  - Parameters:
    - `text` (required): The game text to localize
    - `target_language` (required): Target language code (e.g., 'es', 'fr', 'ja')
    - `context` (optional): Game context ('dialog', 'ui_button', etc.)

- **validate_localization**: Validate localized text
  - Parameters:
    - `original_text` (required): Original game text
    - `localized_text` (required): Localized text to validate
    - `language` (required): Language of the localized text

## Implementation Notes

This is a placeholder implementation. To make this fully functional:

1. Integrate with an actual AI localization service (e.g., OpenAI API, translation API)
2. Implement comprehensive validation logic for length constraints
3. Add cultural appropriateness checking
4. Set up database or file storage for game strings
5. Add error handling and logging

## References

- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [MCP Documentation](https://modelcontextprotocol.io/)
- [MCP Specification](https://modelcontextprotocol.io/specification/latest)

## License

MIT
