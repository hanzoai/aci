# @hanzo/aci

Agent Computer Interface - Cross-platform automation for AI agents.

## Features

- 🖱️ **Mouse Control**: Click, drag, scroll, and move
- ⌨️ **Keyboard Control**: Type, press keys, and use hotkeys
- 📸 **Screen Capture**: Take screenshots of full screen or regions
- 🔍 **Image Recognition**: Find images on screen
- 📝 **OCR**: Read text from screen using Tesseract.js
- 🤖 **MCP Integration**: Ready-to-use MCP tools for AI agents
- 🌐 **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

```bash
npm install @hanzo/aci
```

## Usage

### Basic Usage

```typescript
import { ACI } from '@hanzo/aci';

const aci = new ACI();

// Take a screenshot
const screenshot = await aci.screenshot();

// Click at coordinates
await aci.click(100, 200);

// Type text
await aci.type('Hello, world!');

// Find and click on an image
await aci.clickImage('button.png');

// Read text from screen (requires OCR)
const aci = new ACI({ ocr: true });
const text = await aci.readText();
```

### MCP Tools

```typescript
import { aciTools } from '@hanzo/aci/mcp-tools';

// Use with your MCP server
const tools = aciTools;
```

## API Reference

### Mouse Operations
- `moveTo(x, y, duration?)` - Move mouse to position
- `click(x?, y?, button?)` - Click at position
- `doubleClick(x?, y?)` - Double click
- `drag(fromX, fromY, toX, toY)` - Drag from one position to another
- `scroll(clicks, x?, y?)` - Scroll mouse wheel

### Keyboard Operations
- `type(text, delay?)` - Type text
- `press(key)` - Press a single key
- `hotkey(...keys)` - Press keyboard shortcut

### Screen Operations
- `screenshot(region?)` - Take screenshot
- `getScreenSize()` - Get screen dimensions
- `locateOnScreen(imagePath, confidence?)` - Find image on screen
- `locateAllOnScreen(imagePath, confidence?)` - Find all occurrences

### OCR Operations
- `readText(region?)` - Read text using OCR
- `findText(text)` - Find text location on screen

### High-Level Operations
- `clickImage(imagePath, timeout?)` - Click on an image
- `clickText(text, timeout?)` - Click on text
- `waitForImage(imagePath, timeout?)` - Wait for image to appear
- `waitForText(text, timeout?)` - Wait for text to appear

## Requirements

- Node.js 18+
- Platform-specific requirements:
  - **Windows**: No additional requirements
  - **macOS**: Accessibility permissions required
  - **Linux**: X11 and dependencies for robotjs

## License

MIT © Hanzo AI