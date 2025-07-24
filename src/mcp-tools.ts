/**
 * MCP tools for Agent Computer Interface
 */

import { ACI } from './index.js';

export interface Tool {
  name: string;
  description: string;
  inputSchema: any;
  handler: (args: any) => Promise<any>;
}

// Shared ACI instance
const aci = new ACI({ ocr: true });

export const screenshotTool: Tool = {
  name: 'screenshot',
  description: 'Take a screenshot of the screen or a specific region',
  inputSchema: {
    type: 'object',
    properties: {
      x: { type: 'number', description: 'X coordinate of region' },
      y: { type: 'number', description: 'Y coordinate of region' },
      width: { type: 'number', description: 'Width of region' },
      height: { type: 'number', description: 'Height of region' },
      format: { 
        type: 'string', 
        enum: ['png', 'jpeg'],
        description: 'Image format',
        default: 'png'
      }
    }
  },
  handler: async (args) => {
    try {
      const region = (args.x !== undefined && args.y !== undefined && args.width && args.height)
        ? { x: args.x, y: args.y, width: args.width, height: args.height }
        : undefined;
      
      const screenshot = await aci.screenshot(region);
      
      return {
        content: [{
          type: 'image',
          data: screenshot.buffer.toString('base64'),
          mimeType: `image/${args.format || 'png'}`
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: 'text',
          text: `Error taking screenshot: ${error.message}`
        }],
        isError: true
      };
    }
  }
};

export const clickTool: Tool = {
  name: 'click',
  description: 'Click at a specific position or on an element',
  inputSchema: {
    type: 'object',
    properties: {
      x: { type: 'number', description: 'X coordinate' },
      y: { type: 'number', description: 'Y coordinate' },
      button: { 
        type: 'string',
        enum: ['left', 'right', 'middle'],
        description: 'Mouse button',
        default: 'left'
      },
      image: { type: 'string', description: 'Path to image to click on' },
      text: { type: 'string', description: 'Text to click on (uses OCR)' },
      timeout: { type: 'number', description: 'Timeout in ms for image/text search' }
    }
  },
  handler: async (args) => {
    try {
      if (args.image) {
        const success = await aci.clickImage(args.image, args.timeout);
        return {
          content: [{
            type: 'text',
            text: success ? 'Clicked on image' : 'Image not found'
          }]
        };
      } else if (args.text) {
        const success = await aci.clickText(args.text, args.timeout);
        return {
          content: [{
            type: 'text',
            text: success ? `Clicked on text: ${args.text}` : 'Text not found'
          }]
        };
      } else if (args.x !== undefined && args.y !== undefined) {
        await aci.click(args.x, args.y, args.button || 'left');
        return {
          content: [{
            type: 'text',
            text: `Clicked at (${args.x}, ${args.y})`
          }]
        };
      } else {
        return {
          content: [{
            type: 'text',
            text: 'Must provide either x,y coordinates, image path, or text to click'
          }],
          isError: true
        };
      }
    } catch (error: any) {
      return {
        content: [{
          type: 'text',
          text: `Error clicking: ${error.message}`
        }],
        isError: true
      };
    }
  }
};

export const typeTool: Tool = {
  name: 'type',
  description: 'Type text on the keyboard',
  inputSchema: {
    type: 'object',
    properties: {
      text: { 
        type: 'string',
        description: 'Text to type'
      },
      delay: {
        type: 'number',
        description: 'Delay between keystrokes in ms'
      }
    },
    required: ['text']
  },
  handler: async (args) => {
    try {
      await aci.type(args.text, args.delay);
      return {
        content: [{
          type: 'text',
          text: `Typed: ${args.text}`
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: 'text',
          text: `Error typing: ${error.message}`
        }],
        isError: true
      };
    }
  }
};

export const moveTool: Tool = {
  name: 'move_mouse',
  description: 'Move the mouse cursor to a position',
  inputSchema: {
    type: 'object',
    properties: {
      x: { type: 'number', description: 'X coordinate' },
      y: { type: 'number', description: 'Y coordinate' },
      duration: { type: 'number', description: 'Movement duration in ms' }
    },
    required: ['x', 'y']
  },
  handler: async (args) => {
    try {
      await aci.moveTo(args.x, args.y, args.duration);
      return {
        content: [{
          type: 'text',
          text: `Moved mouse to (${args.x}, ${args.y})`
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: 'text',
          text: `Error moving mouse: ${error.message}`
        }],
        isError: true
      };
    }
  }
};

export const scrollTool: Tool = {
  name: 'scroll',
  description: 'Scroll the mouse wheel',
  inputSchema: {
    type: 'object',
    properties: {
      clicks: { 
        type: 'number',
        description: 'Number of scroll clicks (negative for down)'
      },
      x: { type: 'number', description: 'X coordinate to scroll at' },
      y: { type: 'number', description: 'Y coordinate to scroll at' }
    },
    required: ['clicks']
  },
  handler: async (args) => {
    try {
      await aci.scroll(args.clicks, args.x, args.y);
      return {
        content: [{
          type: 'text',
          text: `Scrolled ${args.clicks} clicks`
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: 'text',
          text: `Error scrolling: ${error.message}`
        }],
        isError: true
      };
    }
  }
};

export const hotkeyTool: Tool = {
  name: 'hotkey',
  description: 'Press a keyboard shortcut',
  inputSchema: {
    type: 'object',
    properties: {
      keys: {
        type: 'array',
        items: { type: 'string' },
        description: 'Keys to press together (e.g., ["ctrl", "c"])'
      }
    },
    required: ['keys']
  },
  handler: async (args) => {
    try {
      await aci.hotkey(...args.keys);
      return {
        content: [{
          type: 'text',
          text: `Pressed hotkey: ${args.keys.join('+')}`
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: 'text',
          text: `Error pressing hotkey: ${error.message}`
        }],
        isError: true
      };
    }
  }
};

export const readTextTool: Tool = {
  name: 'read_text',
  description: 'Read text from screen using OCR',
  inputSchema: {
    type: 'object',
    properties: {
      x: { type: 'number', description: 'X coordinate of region' },
      y: { type: 'number', description: 'Y coordinate of region' },
      width: { type: 'number', description: 'Width of region' },
      height: { type: 'number', description: 'Height of region' }
    }
  },
  handler: async (args) => {
    try {
      const region = (args.x !== undefined && args.y !== undefined && args.width && args.height)
        ? { x: args.x, y: args.y, width: args.width, height: args.height }
        : undefined;
      
      const text = await aci.readText(region);
      return {
        content: [{
          type: 'text',
          text: text || 'No text found'
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: 'text',
          text: `Error reading text: ${error.message}`
        }],
        isError: true
      };
    }
  }
};

export const findOnScreenTool: Tool = {
  name: 'find_on_screen',
  description: 'Find an image or text on screen',
  inputSchema: {
    type: 'object',
    properties: {
      image: { type: 'string', description: 'Path to image to find' },
      text: { type: 'string', description: 'Text to find (uses OCR)' },
      confidence: { 
        type: 'number',
        description: 'Confidence threshold (0-1)',
        default: 0.9
      },
      all: {
        type: 'boolean',
        description: 'Find all occurrences',
        default: false
      }
    }
  },
  handler: async (args) => {
    try {
      if (args.image) {
        if (args.all) {
          const locations = await aci.locateAllOnScreen(args.image, args.confidence);
          return {
            content: [{
              type: 'text',
              text: locations.length > 0 
                ? `Found ${locations.length} occurrences:\n${locations.map(l => `(${l.x}, ${l.y})`).join('\n')}`
                : 'Image not found'
            }]
          };
        } else {
          const location = await aci.locateOnScreen(args.image, args.confidence);
          return {
            content: [{
              type: 'text',
              text: location ? `Found at (${location.x}, ${location.y})` : 'Image not found'
            }]
          };
        }
      } else if (args.text) {
        const location = await aci.findText(args.text);
        return {
          content: [{
            type: 'text',
            text: location ? `Found text at (${location.x}, ${location.y})` : 'Text not found'
          }]
        };
      } else {
        return {
          content: [{
            type: 'text',
            text: 'Must provide either image path or text to find'
          }],
          isError: true
        };
      }
    } catch (error: any) {
      return {
        content: [{
          type: 'text',
          text: `Error finding on screen: ${error.message}`
        }],
        isError: true
      };
    }
  }
};

export const dragTool: Tool = {
  name: 'drag',
  description: 'Drag from one position to another',
  inputSchema: {
    type: 'object',
    properties: {
      fromX: { type: 'number', description: 'Starting X coordinate' },
      fromY: { type: 'number', description: 'Starting Y coordinate' },
      toX: { type: 'number', description: 'Ending X coordinate' },
      toY: { type: 'number', description: 'Ending Y coordinate' }
    },
    required: ['fromX', 'fromY', 'toX', 'toY']
  },
  handler: async (args) => {
    try {
      await aci.drag(args.fromX, args.fromY, args.toX, args.toY);
      return {
        content: [{
          type: 'text',
          text: `Dragged from (${args.fromX}, ${args.fromY}) to (${args.toX}, ${args.toY})`
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: 'text',
          text: `Error dragging: ${error.message}`
        }],
        isError: true
      };
    }
  }
};

export const screenInfoTool: Tool = {
  name: 'screen_info',
  description: 'Get screen size and information',
  inputSchema: {
    type: 'object',
    properties: {}
  },
  handler: async (args) => {
    try {
      const size = await aci.getScreenSize();
      return {
        content: [{
          type: 'text',
          text: `Screen size: ${size.width}x${size.height}`
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: 'text',
          text: `Error getting screen info: ${error.message}`
        }],
        isError: true
      };
    }
  }
};

// Export all ACI tools
export const aciTools = [
  screenshotTool,
  clickTool,
  typeTool,
  moveTool,
  scrollTool,
  hotkeyTool,
  readTextTool,
  findOnScreenTool,
  dragTool,
  screenInfoTool
];