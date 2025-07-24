/**
 * @hanzo/aci - Agent Computer Interface
 * Cross-platform automation for AI agents
 */

import JsAutoGUI from 'jsautogui';
import { mouse, keyboard, screen, imageResource } from '@nut-tree/nut-js';
import sharp from 'sharp';
import Tesseract from 'tesseract.js';

// Export types
export interface Point {
  x: number;
  y: number;
}

export interface Size {
  width: number;
  height: number;
}

export interface Region {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Screenshot {
  buffer: Buffer;
  width: number;
  height: number;
}

export interface ACIOptions {
  defaultDelay?: number;
  screenshotFormat?: 'png' | 'jpeg';
  ocr?: boolean;
}

/**
 * Main ACI class - wraps multiple automation libraries for cross-platform support
 */
export class ACI {
  private jsAutoGUI: typeof JsAutoGUI;
  private options: ACIOptions;
  private ocrWorker?: Tesseract.Worker;

  constructor(options: ACIOptions = {}) {
    this.jsAutoGUI = JsAutoGUI;
    this.options = {
      defaultDelay: 100,
      screenshotFormat: 'png',
      ocr: false,
      ...options
    };

    if (this.options.ocr) {
      this.initOCR();
    }
  }

  private async initOCR() {
    this.ocrWorker = await Tesseract.createWorker('eng');
  }

  // Mouse operations
  async moveTo(x: number, y: number, duration?: number): Promise<void> {
    if (duration) {
      // Smooth movement
      await mouse.move([{ x, y }]);
    } else {
      await mouse.setPosition({ x, y });
    }
  }

  async click(x?: number, y?: number, button: 'left' | 'right' | 'middle' = 'left'): Promise<void> {
    if (x !== undefined && y !== undefined) {
      await this.moveTo(x, y);
    }
    
    switch (button) {
      case 'left':
        await mouse.leftClick();
        break;
      case 'right':
        await mouse.rightClick();
        break;
      case 'middle':
        await mouse.click(2); // Middle button
        break;
    }
  }

  async doubleClick(x?: number, y?: number): Promise<void> {
    if (x !== undefined && y !== undefined) {
      await this.moveTo(x, y);
    }
    await mouse.doubleClick();
  }

  async drag(fromX: number, fromY: number, toX: number, toY: number): Promise<void> {
    await this.moveTo(fromX, fromY);
    await mouse.drag([{ x: toX, y: toY }]);
  }

  async scroll(clicks: number, x?: number, y?: number): Promise<void> {
    if (x !== undefined && y !== undefined) {
      await this.moveTo(x, y);
    }
    await mouse.scrollUp(clicks);
  }

  // Keyboard operations
  async type(text: string, delay?: number): Promise<void> {
    await keyboard.type(text);
    if (delay) {
      await this.sleep(delay);
    }
  }

  async press(key: string): Promise<void> {
    await keyboard.pressKey(key);
  }

  async hotkey(...keys: string[]): Promise<void> {
    const modifiers = keys.slice(0, -1);
    const key = keys[keys.length - 1];
    
    // Press modifiers
    for (const mod of modifiers) {
      await keyboard.pressKey(mod);
    }
    
    // Press final key
    await keyboard.pressKey(key);
    
    // Release in reverse order
    await keyboard.releaseKey(key);
    for (const mod of modifiers.reverse()) {
      await keyboard.releaseKey(mod);
    }
  }

  // Screen operations
  async screenshot(region?: Region): Promise<Screenshot> {
    const screenSize = await screen.width();
    const screenHeight = await screen.height();
    
    let image: any;
    if (region) {
      image = await screen.grabRegion({
        left: region.x,
        top: region.y,
        width: region.width,
        height: region.height
      });
    } else {
      image = await screen.grab();
    }
    
    // Convert to buffer
    const buffer = await image.toBuffer(this.options.screenshotFormat);
    
    return {
      buffer,
      width: region?.width || screenSize,
      height: region?.height || screenHeight
    };
  }

  async getScreenSize(): Promise<Size> {
    return {
      width: await screen.width(),
      height: await screen.height()
    };
  }

  async locateOnScreen(imagePath: string, confidence: number = 0.9): Promise<Point | null> {
    try {
      const location = await screen.find(imageResource(imagePath));
      return { x: location.x, y: location.y };
    } catch {
      return null;
    }
  }

  async locateAllOnScreen(imagePath: string, confidence: number = 0.9): Promise<Point[]> {
    try {
      const locations = await screen.findAll(imageResource(imagePath));
      return locations.map(loc => ({ x: loc.x, y: loc.y }));
    } catch {
      return [];
    }
  }

  // OCR operations
  async readText(region?: Region): Promise<string> {
    if (!this.ocrWorker) {
      throw new Error('OCR not initialized. Set ocr: true in options.');
    }
    
    const screenshot = await this.screenshot(region);
    const result = await this.ocrWorker.recognize(screenshot.buffer);
    return result.data.text;
  }

  async findText(text: string): Promise<Point | null> {
    if (!this.ocrWorker) {
      throw new Error('OCR not initialized. Set ocr: true in options.');
    }
    
    const screenshot = await this.screenshot();
    const result = await this.ocrWorker.recognize(screenshot.buffer);
    
    // Search for text in OCR results
    const words = result.data.words;
    for (const word of words) {
      if (word.text.toLowerCase().includes(text.toLowerCase())) {
        return {
          x: word.bbox.x0 + (word.bbox.x1 - word.bbox.x0) / 2,
          y: word.bbox.y0 + (word.bbox.y1 - word.bbox.y0) / 2
        };
      }
    }
    
    return null;
  }

  // Utility operations
  async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async waitForImage(imagePath: string, timeout: number = 10000): Promise<Point | null> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      const location = await this.locateOnScreen(imagePath);
      if (location) {
        return location;
      }
      await this.sleep(500);
    }
    
    return null;
  }

  async waitForText(text: string, timeout: number = 10000): Promise<Point | null> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      const location = await this.findText(text);
      if (location) {
        return location;
      }
      await this.sleep(500);
    }
    
    return null;
  }

  // High-level operations
  async clickImage(imagePath: string, timeout?: number): Promise<boolean> {
    const location = timeout 
      ? await this.waitForImage(imagePath, timeout)
      : await this.locateOnScreen(imagePath);
    
    if (location) {
      await this.click(location.x, location.y);
      return true;
    }
    
    return false;
  }

  async clickText(text: string, timeout?: number): Promise<boolean> {
    const location = timeout
      ? await this.waitForText(text, timeout)
      : await this.findText(text);
    
    if (location) {
      await this.click(location.x, location.y);
      return true;
    }
    
    return false;
  }

  // Cleanup
  async dispose(): Promise<void> {
    if (this.ocrWorker) {
      await this.ocrWorker.terminate();
    }
  }
}

// Export convenience functions
export async function screenshot(region?: Region): Promise<Screenshot> {
  const aci = new ACI();
  return aci.screenshot(region);
}

export async function click(x: number, y: number): Promise<void> {
  const aci = new ACI();
  return aci.click(x, y);
}

export async function type(text: string): Promise<void> {
  const aci = new ACI();
  return aci.type(text);
}

export async function moveTo(x: number, y: number): Promise<void> {
  const aci = new ACI();
  return aci.moveTo(x, y);
}

// Export default instance
export default new ACI();