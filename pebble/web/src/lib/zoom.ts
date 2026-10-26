export const MIN_SCALE = 1;
export const MAX_SCALE = 8;

export interface MapView {
  scale: number;
  /** Pixel offset of the content's top-left corner inside the frame (0 or negative). */
  x: number;
  y: number;
}

export const IDENTITY_VIEW: MapView = { scale: 1, x: 0, y: 0 };

/** Keeps the content covering the whole frame so empty space never shows. */
export function clampView(view: MapView, width: number, height: number): MapView {
  const scale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, view.scale));
  return {
    scale,
    x: Math.min(0, Math.max(width * (1 - scale), view.x)),
    y: Math.min(0, Math.max(height * (1 - scale), view.y)),
  };
}

/** Zooms to `nextScale` keeping the content point under (px, py) fixed on screen. */
export function zoomAt(view: MapView, nextScale: number, px: number, py: number, width: number, height: number): MapView {
  const scale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, nextScale));
  const ratio = scale / view.scale;
  return clampView({ scale, x: px - (px - view.x) * ratio, y: py - (py - view.y) * ratio }, width, height);
}
