import { describe, expect, it } from 'vitest';
import { IDENTITY_VIEW, MAX_SCALE, MIN_SCALE, clampView, zoomAt } from './zoom';

const W = 800;
const H = 600;

describe('clampView', () => {
  it('limits the scale', () => {
    expect(clampView({ scale: 20, x: 0, y: 0 }, W, H).scale).toBe(MAX_SCALE);
    expect(clampView({ scale: 0.2, x: 0, y: 0 }, W, H).scale).toBe(MIN_SCALE);
  });

  it('never lets the content leave a gap at any edge', () => {
    const view = clampView({ scale: 2, x: 500, y: -2000 }, W, H);
    expect(view.x).toBe(0);
    expect(view.y).toBe(H * (1 - 2));
  });

  it('forces the identity view at scale 1', () => {
    expect(clampView({ scale: 1, x: -50, y: 30 }, W, H)).toEqual(IDENTITY_VIEW);
  });
});

describe('zoomAt', () => {
  it('keeps the point under the cursor fixed', () => {
    const px = 400;
    const py = 300;
    const next = zoomAt(IDENTITY_VIEW, 2, px, py, W, H);
    expect((px - next.x) / next.scale).toBeCloseTo(px, 5);
    expect((py - next.y) / next.scale).toBeCloseTo(py, 5);
  });

  it('zooming at the top-left corner keeps the origin in place', () => {
    expect(zoomAt(IDENTITY_VIEW, 4, 0, 0, W, H)).toEqual({ scale: 4, x: 0, y: 0 });
  });

  it('returns to the identity view when zooming back out', () => {
    const zoomed = zoomAt(IDENTITY_VIEW, 3, 650, 120, W, H);
    expect(zoomAt(zoomed, 1, 650, 120, W, H)).toEqual(IDENTITY_VIEW);
  });
});
