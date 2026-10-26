import { useState } from 'react';
import {
  Body1,
  Button,
  Caption1,
  Divider,
  Skeleton,
  SkeletonItem,
  Tooltip,
  makeStyles,
  tokens,
} from '@fluentui/react-components';
import { ArrowClockwiseRegular } from '@fluentui/react-icons';
import { api } from '../api';
import { useAsync } from '../hooks/useAsync';
import type { Shade } from '../types';
import { ErrorBanner } from './StateViews';
import { ShadeChip } from './ShadeChip';

const PREVIEW_COUNT = 5;

const useStyles = makeStyles({
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalXS,
  },
  row: {
    display: 'grid',
    gridTemplateColumns: '1fr auto auto',
    alignItems: 'center',
    gap: tokens.spacingHorizontalM,
    padding: `${tokens.spacingVerticalXS} 0`,
  },
  actions: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalS,
    marginTop: tokens.spacingVerticalS,
  },
});

interface ShadeSublistProps {
  productId: string;
  shadeCount: number;
}

export function ShadeSublist({ productId, shadeCount }: ShadeSublistProps) {
  const styles = useStyles();
  const [showAll, setShowAll] = useState(false);
  const [overrides, setOverrides] = useState<Record<string, Shade>>({});
  const [retryError, setRetryError] = useState<string | null>(null);
  const [busyShadeId, setBusyShadeId] = useState<string | null>(null);
  const { data, loading, error, reload } = useAsync(() => api.listProductShades(productId), [productId]);

  const retryExtraction = async (shade: Shade) => {
    setBusyShadeId(shade.id);
    setRetryError(null);
    try {
      const updated = await api.extractShadeHex(shade.id);
      setOverrides((prev) => ({ ...prev, [shade.id]: updated }));
    } catch (err) {
      setRetryError(err instanceof Error ? err.message : `Couldn't load swatch for ${shade.name}`);
    } finally {
      setBusyShadeId(null);
    }
  };

  if (loading) {
    return (
      <Skeleton aria-label="Loading shades">
        {Array.from({ length: 3 }, (_, index) => (
          <SkeletonItem key={index} size={20} style={{ marginBottom: tokens.spacingVerticalS }} />
        ))}
      </Skeleton>
    );
  }

  if (error) {
    return <ErrorBanner title="Couldn't load shades" message={error.message} onRetry={reload} />;
  }

  const shades = data ?? [];
  if (shades.length === 0) {
    return <Body1>No shades were found for this foundation.</Body1>;
  }

  const visible = showAll ? shades : shades.slice(0, PREVIEW_COUNT);

  return (
    <div>
      {retryError ? <ErrorBanner title="Couldn't re-extract this swatch" message={retryError} /> : null}
      <div className={styles.list} role="list">
        {visible.map((shade, index) => {
          const current = overrides[shade.id] ?? shade;
          return (
            <div key={shade.id} role="listitem">
              {index > 0 ? <Divider /> : null}
              <div className={styles.row}>
                <Body1>{current.name}</Body1>
                {current.status === 'failed' ? (
                  <Caption1 style={{ color: tokens.colorPaletteRedForeground1 }}>
                    {current.error ?? 'Swatch failed'}
                  </Caption1>
                ) : (
                  <ShadeChip hex={current.hex} />
                )}
                <Tooltip content="Re-extract hex from swatch" relationship="label">
                  <Button
                    appearance="subtle"
                    size="small"
                    icon={<ArrowClockwiseRegular />}
                    disabled={busyShadeId === shade.id}
                    onClick={() => void retryExtraction(shade)}
                    aria-label={`Re-extract hex for ${current.name}`}
                  />
                </Tooltip>
              </div>
            </div>
          );
        })}
      </div>
      <div className={styles.actions}>
        <Caption1>
          Showing {visible.length} of {Math.max(shadeCount, shades.length)} shades
        </Caption1>
        {shades.length > PREVIEW_COUNT ? (
          <Button appearance="transparent" size="small" onClick={() => setShowAll((value) => !value)}>
            {showAll ? 'Show fewer shades' : 'Show all shades'}
          </Button>
        ) : null}
      </div>
    </div>
  );
}
