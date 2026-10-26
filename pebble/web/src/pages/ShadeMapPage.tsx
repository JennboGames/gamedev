import { useState } from 'react';
import {
  Button,
  Caption1,
  Skeleton,
  SkeletonItem,
  Table,
  TableBody,
  TableCell,
  TableCellLayout,
  TableHeader,
  TableHeaderCell,
  TableRow,
  Spinner,
  Title2,
  makeStyles,
  mergeClasses,
  tokens,
} from '@fluentui/react-components';
import { ArrowClockwiseRegular, ArrowDownloadRegular, ChartMultipleRegular } from '@fluentui/react-icons';
import { api } from '../api';
import { MapCanvas } from '../components/MapCanvas';
import { ShadeChip } from '../components/ShadeChip';
import { EmptyState, ErrorBanner } from '../components/StateViews';
import { useAsync } from '../hooks/useAsync';
import type { ColorMap } from '../types';

const useStyles = makeStyles({
  page: { display: 'flex', flexDirection: 'column', gap: tokens.spacingVerticalL },
  title: { display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: tokens.spacingHorizontalL },
  split: {
    display: 'grid',
    gridTemplateColumns: '1fr 2fr',
    gap: tokens.spacingHorizontalXL,
    alignItems: 'start',
    '@media (max-width: 900px)': { gridTemplateColumns: '1fr' },
  },
  tableWrap: {
    overflow: 'auto',
    maxHeight: '640px',
    borderRadius: tokens.borderRadiusLarge,
    border: `1px solid ${tokens.colorNeutralStroke1}`,
    backgroundColor: tokens.colorNeutralBackground1,
    boxShadow: tokens.shadow4,
  },
  row: { cursor: 'pointer' },
  rowSelected: { backgroundColor: tokens.colorBrandBackground2 },
  actions: { display: 'flex', justifyContent: 'flex-end', gap: tokens.spacingHorizontalM },
});

export function ShadeMapPage() {
  const styles = useStyles();
  const { data, loading, error, reload } = useAsync(() => api.getColorMap());
  const [generated, setGenerated] = useState<ColorMap | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<Error | null>(null);
  const [selectedShadeId, setSelectedShadeId] = useState<string | null>(null);

  const colorMap = generated ?? data ?? null;

  const generate = async () => {
    setGenerating(true);
    setGenerateError(null);
    try {
      setGenerated(await api.generateColorMap());
      setSelectedShadeId(null);
    } catch (err) {
      setGenerateError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setGenerating(false);
    }
  };

  const generateButtonLabel = colorMap ? 'Regenerate map' : 'Generate shade map';

  return (
    <div className={styles.page}>
      <div className={styles.title}>
        <Title2>Foundation shade map</Title2>
        {colorMap ? <Caption1>{colorMap.markers.length} shades plotted</Caption1> : null}
      </div>

      {error ? <ErrorBanner title="Couldn't load the shade map" message={error.message} onRetry={reload} /> : null}
      {generateError ? (
        <ErrorBanner title="Couldn't generate the shade map" message={generateError.message} onRetry={() => void generate()} />
      ) : null}

      {loading ? (
        <Skeleton aria-label="Loading shade map" aria-busy="true">
          <SkeletonItem style={{ height: '320px', borderRadius: tokens.borderRadiusLarge }} />
        </Skeleton>
      ) : null}

      {!loading && !error && !colorMap ? (
        <EmptyState
          icon={<ChartMultipleRegular />}
          title="No shade map yet"
          body="Collect foundations first, then generate the map to plot every shade by its hex color."
          action={
            <Button
              appearance="primary"
              icon={generating ? <Spinner size="tiny" /> : <ChartMultipleRegular />}
              disabled={generating}
              onClick={() => void generate()}
            >
              Generate shade map
            </Button>
          }
        />
      ) : null}

      {colorMap ? (
        <>
          <div className={styles.split}>
            <div className={styles.tableWrap}>
              <Table aria-label="Plotted shades" size="small">
                <TableHeader>
                  <TableRow>
                    <TableHeaderCell>Shade</TableHeaderCell>
                    <TableHeaderCell>Product</TableHeaderCell>
                    <TableHeaderCell>Hex</TableHeaderCell>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {colorMap.markers.map((marker) => (
                    <TableRow
                      key={marker.shadeId}
                      className={mergeClasses(styles.row, marker.shadeId === selectedShadeId && styles.rowSelected)}
                      onClick={() => setSelectedShadeId(marker.shadeId)}
                      aria-selected={marker.shadeId === selectedShadeId}
                    >
                      <TableCell>
                        <TableCellLayout>{marker.shadeName}</TableCellLayout>
                      </TableCell>
                      <TableCell>
                        <TableCellLayout>{marker.productTitle}</TableCellLayout>
                      </TableCell>
                      <TableCell>
                        <ShadeChip hex={marker.hex} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <MapCanvas colorMap={colorMap} selectedShadeId={selectedShadeId} onSelect={setSelectedShadeId} />
          </div>
          <div className={styles.actions}>
            <Button
              as="a"
              appearance="secondary"
              icon={<ArrowDownloadRegular />}
              href={colorMap.imageUrl}
              download="shade-map.png"
            >
              Download PNG
            </Button>
            <Button
              appearance="primary"
              icon={generating ? <Spinner size="tiny" /> : <ArrowClockwiseRegular />}
              disabled={generating}
              onClick={() => void generate()}
            >
              {generateButtonLabel}
            </Button>
          </div>
        </>
      ) : null}
    </div>
  );
}
