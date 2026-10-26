import { useCallback, useEffect, useRef, useState, type CSSProperties, type KeyboardEvent, type PointerEvent } from 'react';
import { Button, Caption1, Caption1Strong, Tooltip, makeStyles, mergeClasses, tokens } from '@fluentui/react-components';
import { ZoomFitRegular, ZoomInRegular, ZoomOutRegular } from '@fluentui/react-icons';
import { IDENTITY_VIEW, MAX_SCALE, MIN_SCALE, clampView, zoomAt, type MapView } from '../lib/zoom';
import { PALETTE } from '../theme/brand';
import type { ColorMap } from '../types';

const BUTTON_ZOOM_STEP = 1.5;
const WHEEL_ZOOM_STEP = 1.0015;
const DRAG_THRESHOLD_PX = 3;

const useStyles = makeStyles({
  frame: {
    position: 'relative',
    width: '100%',
    overflow: 'hidden',
    borderRadius: tokens.borderRadiusLarge,
    border: `1px solid ${tokens.colorNeutralStroke1}`,
    backgroundColor: PALETTE.surface,
    boxShadow: tokens.shadow8,
    userSelect: 'none',
  },
  zoomed: { cursor: 'grab' },
  dragging: { cursor: 'grabbing' },
  layer: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    transformOrigin: '0 0',
  },
  image: {
    display: 'block',
    width: '100%',
    height: '100%',
    objectFit: 'fill',
    pointerEvents: 'none',
  },
  axis: {
    position: 'absolute',
    padding: `2px ${tokens.spacingHorizontalS}`,
    borderRadius: tokens.borderRadiusCircular,
    backgroundColor: 'rgba(255,255,255,0.82)',
    color: PALETTE.text,
    pointerEvents: 'none',
  },
  left: { left: tokens.spacingHorizontalS, top: '50%', transform: 'translateY(-50%)' },
  right: { right: tokens.spacingHorizontalS, top: '50%', transform: 'translateY(-50%)' },
  top: { top: tokens.spacingVerticalS, left: '50%', transform: 'translateX(-50%)' },
  bottom: {
    bottom: tokens.spacingVerticalS,
    left: '50%',
    transform: 'translateX(-50%)',
    backgroundColor: 'rgba(0,0,0,0.6)',
    color: '#ffffff',
  },
  controls: {
    position: 'absolute',
    top: tokens.spacingVerticalS,
    right: tokens.spacingHorizontalS,
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalXS,
    padding: tokens.spacingHorizontalXS,
    borderRadius: tokens.borderRadiusMedium,
    backgroundColor: 'rgba(255,255,255,0.9)',
    boxShadow: tokens.shadow4,
    cursor: 'default',
  },
  level: { minWidth: '40px', textAlign: 'center', color: PALETTE.muted },
  // The layer is scaled, so markers counter-scale to keep a constant on-screen size.
  marker: {
    position: 'absolute',
    width: '18px',
    height: '18px',
    padding: 0,
    transform: 'translate(-50%, -50%) scale(var(--marker-scale, 1))',
    borderRadius: tokens.borderRadiusCircular,
    border: '2px solid #ffffff',
    boxShadow: '0 0 0 1px rgba(0,0,0,0.45), 0 2px 6px rgba(0,0,0,0.35)',
    cursor: 'pointer',
    ':hover': { transform: 'translate(-50%, -50%) scale(calc(var(--marker-scale, 1) * 1.25))' },
  },
  selected: {
    width: '26px',
    height: '26px',
    border: `3px solid ${PALETTE.accent}`,
    zIndex: 2,
  },
});

interface MapCanvasProps {
  colorMap: ColorMap;
  selectedShadeId: string | null;
  onSelect: (shadeId: string) => void;
}

interface DragState {
  pointerId: number;
  startX: number;
  startY: number;
  originX: number;
  originY: number;
  active: boolean;
}

export function MapCanvas({ colorMap, selectedShadeId, onSelect }: MapCanvasProps) {
  const styles = useStyles();
  const frameRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<DragState | null>(null);
  const [view, setView] = useState<MapView>(IDENTITY_VIEW);
  const [dragging, setDragging] = useState(false);
  const viewRef = useRef(view);
  viewRef.current = view;

  const frameSize = () => {
    const rect = frameRef.current?.getBoundingClientRect();
    return { width: rect?.width ?? 0, height: rect?.height ?? 0 };
  };

  const zoomBy = useCallback((factor: number, px?: number, py?: number) => {
    const rect = frameRef.current?.getBoundingClientRect();
    const width = rect?.width ?? 0;
    const height = rect?.height ?? 0;
    setView((current) => zoomAt(current, current.scale * factor, px ?? width / 2, py ?? height / 2, width, height));
  }, []);

  // React registers wheel listeners as passive, so zooming needs a native non-passive one.
  useEffect(() => {
    const frame = frameRef.current;
    if (!frame) return undefined;
    const onWheel = (event: WheelEvent) => {
      // Let the page scroll when the map is already fully zoomed out.
      if (viewRef.current.scale <= MIN_SCALE && event.deltaY > 0) return;
      event.preventDefault();
      const rect = frame.getBoundingClientRect();
      zoomBy(WHEEL_ZOOM_STEP ** -event.deltaY, event.clientX - rect.left, event.clientY - rect.top);
    };
    frame.addEventListener('wheel', onWheel, { passive: false });
    return () => frame.removeEventListener('wheel', onWheel);
  }, [zoomBy]);

  const onPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    if (event.button !== 0 || (event.target as HTMLElement).closest('[data-map-controls]')) return;
    dragRef.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      originX: viewRef.current.x,
      originY: viewRef.current.y,
      active: false,
    };
  };

  const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== event.pointerId || viewRef.current.scale <= MIN_SCALE) return;
    const dx = event.clientX - drag.startX;
    const dy = event.clientY - drag.startY;
    if (!drag.active) {
      if (Math.hypot(dx, dy) < DRAG_THRESHOLD_PX) return;
      // Capture only once it is a real drag, so a plain click still reaches the marker.
      drag.active = true;
      event.currentTarget.setPointerCapture(event.pointerId);
      setDragging(true);
    }
    const { width, height } = frameSize();
    setView((current) => clampView({ ...current, x: drag.originX + dx, y: drag.originY + dy }, width, height));
  };

  const endDrag = (event: PointerEvent<HTMLDivElement>) => {
    if (dragRef.current?.pointerId !== event.pointerId) return;
    dragRef.current = null;
    setDragging(false);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === '+' || event.key === '=') zoomBy(BUTTON_ZOOM_STEP);
    else if (event.key === '-') zoomBy(1 / BUTTON_ZOOM_STEP);
    else if (event.key === '0') setView(IDENTITY_VIEW);
    else return;
    event.preventDefault();
  };

  const zoomed = view.scale > MIN_SCALE;
  const layerStyle = {
    transform: `translate(${view.x}px, ${view.y}px) scale(${view.scale})`,
    '--marker-scale': 1 / view.scale,
  } as CSSProperties;

  return (
    <div
      ref={frameRef}
      className={mergeClasses(styles.frame, zoomed && styles.zoomed, dragging && styles.dragging)}
      style={{ aspectRatio: `${colorMap.width} / ${colorMap.height}`, touchAction: zoomed ? 'none' : 'auto' }}
      role="group"
      aria-label="Foundation shade map. Scroll or use plus and minus to zoom, drag to pan, 0 to reset."
      tabIndex={0}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
      onKeyDown={onKeyDown}
    >
      <div className={styles.layer} style={layerStyle}>
        <img
          className={styles.image}
          src={colorMap.imageUrl}
          alt="Color map: red on the left to yellow on the right; white at the top to black at the bottom"
          draggable={false}
        />
        {colorMap.markers.map((marker) => (
          <Tooltip
            key={marker.shadeId}
            content={`${marker.shadeName} · ${marker.productTitle} · ${marker.hex}`}
            relationship="label"
          >
            <button
              type="button"
              className={mergeClasses(styles.marker, marker.shadeId === selectedShadeId && styles.selected)}
              style={{ left: `${marker.x * 100}%`, top: `${marker.y * 100}%`, backgroundColor: marker.hex }}
              onClick={() => onSelect(marker.shadeId)}
              aria-pressed={marker.shadeId === selectedShadeId}
            />
          </Tooltip>
        ))}
      </div>
      <Caption1Strong className={mergeClasses(styles.axis, styles.left)}>Red</Caption1Strong>
      <Caption1Strong className={mergeClasses(styles.axis, styles.right)}>Yellow</Caption1Strong>
      <Caption1Strong className={mergeClasses(styles.axis, styles.top)}>White</Caption1Strong>
      <Caption1Strong className={mergeClasses(styles.axis, styles.bottom)}>Black</Caption1Strong>
      <div className={styles.controls} data-map-controls>
        <Button
          size="small"
          appearance="subtle"
          icon={<ZoomOutRegular />}
          aria-label="Zoom out"
          disabled={view.scale <= MIN_SCALE}
          onClick={() => zoomBy(1 / BUTTON_ZOOM_STEP)}
        />
        <Caption1 className={styles.level} aria-live="polite">
          {Math.round(view.scale * 100)}%
        </Caption1>
        <Button
          size="small"
          appearance="subtle"
          icon={<ZoomInRegular />}
          aria-label="Zoom in"
          disabled={view.scale >= MAX_SCALE}
          onClick={() => zoomBy(BUTTON_ZOOM_STEP)}
        />
        <Button
          size="small"
          appearance="subtle"
          icon={<ZoomFitRegular />}
          aria-label="Reset zoom"
          disabled={!zoomed}
          onClick={() => setView(IDENTITY_VIEW)}
        />
      </div>
    </div>
  );
}
