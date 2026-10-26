import { describe, expect, it } from 'vitest';
import { colorMapPosition, hexToHsl, hexToRgb, hslToHex, rgbToHex } from './color';

describe('color helpers', () => {
  it('round-trips hex through rgb', () => {
    expect(rgbToHex(hexToRgb('#F1D2B5'))).toBe('#F1D2B5');
  });

  it('round-trips hex through hsl within one step per channel', () => {
    const [r, g, b] = hexToRgb(hslToHex(hexToHsl('#C58B58')));
    const [er, eg, eb] = hexToRgb('#C58B58');
    expect(Math.abs(r - er)).toBeLessThanOrEqual(1);
    expect(Math.abs(g - eg)).toBeLessThanOrEqual(1);
    expect(Math.abs(b - eb)).toBeLessThanOrEqual(1);
  });

  it('rejects malformed hex', () => {
    expect(() => hexToRgb('#12')).toThrow();
  });

  it('puts pure red at the left edge and pure yellow at the right edge', () => {
    expect(colorMapPosition('#FF0000').x).toBe(0);
    expect(colorMapPosition('#FFFF00').x).toBe(1);
  });

  it('puts orange halfway', () => {
    expect(colorMapPosition('#FF8000').x).toBeCloseTo(0.5, 2);
  });

  it('puts white at the top and black at the bottom', () => {
    expect(colorMapPosition('#FFFFFF').y).toBe(0);
    expect(colorMapPosition('#000000').y).toBe(1);
  });

  it('places lighter shades above darker shades', () => {
    expect(colorMapPosition('#F1D2B5').y).toBeLessThan(colorMapPosition('#4B2E22').y);
  });
});
