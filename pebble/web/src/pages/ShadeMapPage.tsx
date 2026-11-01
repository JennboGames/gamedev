import { useMemo, useState } from 'react';
import {
  Button,
  Caption1,
  Dropdown,
  Field,
  Option,
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
import { ArrowClockwiseRegular, ArrowDownloadRegular, ChartMultipleRegular, DismissRegular } from '@fluentui/react-icons';
import { api } from '../api';
import { MapCanvas } from '../components/MapCanvas';
import { ShadeChip } from '../components/ShadeChip';
import { EmptyState, ErrorBanner } from '../components/StateViews';
import { useAsync } from '../hooks/useAsync';
import type { ColorMap, ColorMapShape } from '../types';

const COPY: Record<
  ColorMapShape,
  { title: string; plotted: string; emptyTitle: string; emptyBody: string; generate: string; file: string; hint?: string }
> = {
  rectangle: {
    title: 'Foundation shade map',
    plotted: 'shades plotted',
    emptyTitle: 'No shade map yet',
    emptyBody: 'Collect foundations first, then generate the map to plot every shade by its hex color.',
    generate: 'Generate shade map',
    file: 'shade-map.png',
  },
  wheel: {
    title: 'Foundation color wheel',
    plotted: 'shades plotted',
    emptyTitle: 'No color wheel yet',
    emptyBody: 'Collect foundations first, then generate the wheel to plot every shade by its hex color.',
    generate: 'Generate color wheel',
    file: 'color-wheel.png',
    hint: 'Hue runs around the wheel, starting at red on top. Lighter shades sit near the white center and deeper shades toward the black rim.',
  },
};

const NO_UNDERTONE = '__none__';

const undertoneLabel = (undertone: string) =>
  undertone === NO_UNDERTONE ? 'Not specified' : undertone.replace(/\b\w/g, (letter) => letter.toUpperCase());

// Named undertones alphabetically, shades without one last.
const compareUndertones = (a: string, b: string) =>
  a === NO_UNDERTONE ? 1 : b === NO_UNDERTONE ? -1 : a.localeCompare(b);

const useStyles = makeStyles({
  page: { display: 'flex', flexDirection: 'column', gap: tokens.spacingVerticalL },
  filter: { display: 'flex', alignItems: 'flex-end', gap: tokens.spacingHorizontalM, flexWrap: 'wrap' },
  filterField: { minWidth: '280px', maxWidth: '420px', flexGrow: 1 },
  title: { display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: tokens.spacingHorizontalL },
  split: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
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
  undertone: { textTransform: 'capitalize' },
  actions: { display: 'flex', justifyContent: 'flex-end', gap: tokens.spacingHorizontalM },
});

export function ShadeMapPage() {
  return <ShadeMapView shape="rectangle" />;
}

export function ShadeMapView({ shape }: { shape: ColorMapShape }) {
  const styles = useStyles();
  const copy = COPY[shape];
  const { data, loading, error, reload } = useAsync(() => api.getColorMap(shape), [shape]);
  const [generated, setGenerated] = useState<ColorMap | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<Error | null>(null);
  const [selectedShadeId, setSelectedShadeId] = useState<string | null>(null);
  const [selectedUndertones, setSelectedUndertones] = useState<string[]>([]);

  const colorMap = generated ?? data ?? null;

  const undertoneOptions = useMemo(
    () => [...new Set((colorMap?.markers ?? []).map((marker) => marker.undertone ?? NO_UNDERTONE))].sort(compareUndertones),
    [colorMap],
  );
  const visibleMap = useMemo(() => {
    if (!colorMap || selectedUndertones.length === 0) return colorMap;
    const markers = colorMap.markers.filter((marker) => selectedUndertones.includes(marker.undertone ?? NO_UNDERTONE));
    return { ...colorMap, markers };
  }, [colorMap, selectedUndertones]);

  const generate = async () => {
    setGenerating(true);
    setGenerateError(null);
    try {
      setGenerated(await api.generateColorMap({ shape }));
      setSelectedShadeId(null);
    } catch (err) {
      setGenerateError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setGenerating(false);
    }
  };

  const generateButtonLabel = colorMap ? 'Regenerate' : copy.generate;

  return (
    <div className={styles.page}>
      <div className={styles.title}>
        <Title2>{copy.title}</Title2>
        {colorMap ? (
          <Caption1>
            {visibleMap?.markers.length === colorMap.markers.length
              ? `${colorMap.markers.length} ${copy.plotted}`
              : `${visibleMap?.markers.length} of ${colorMap.markers.length} ${copy.plotted}`}
          </Caption1>
        ) : null}
      </div>
      {copy.hint ? <Caption1>{copy.hint}</Caption1> : null}

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
          title={copy.emptyTitle}
          body={copy.emptyBody}
          action={
            <Button
              appearance="primary"
              icon={generating ? <Spinner size="tiny" /> : <ChartMultipleRegular />}
              disabled={generating}
              onClick={() => void generate()}
            >
              {copy.generate}
            </Button>
          }
        />
      ) : null}

      {colorMap && visibleMap ? (
        <>
          <div className={styles.filter}>
            <Field label="Filter by undertone" className={styles.filterField}>
              <Dropdown
                multiselect
                placeholder="All undertones"
                selectedOptions={selectedUndertones}
                value={selectedUndertones.map(undertoneLabel).join(', ')}
                onOptionSelect={(_event, data) => setSelectedUndertones(data.selectedOptions)}
              >
                {undertoneOptions.map((undertone) => (
                  <Option key={undertone} value={undertone} text={undertoneLabel(undertone)}>
                    {undertoneLabel(undertone)}
                  </Option>
                ))}
              </Dropdown>
            </Field>
            <Button
              appearance="subtle"
              icon={<DismissRegular />}
              disabled={selectedUndertones.length === 0}
              onClick={() => setSelectedUndertones([])}
            >
              Clear filter
            </Button>
          </div>
          <div className={styles.split}>
            <div className={styles.tableWrap}>
              <Table aria-label="Plotted shades" size="small">
                <TableHeader>
                  <TableRow>
                    <TableHeaderCell>Shade</TableHeaderCell>
                    <TableHeaderCell>Product</TableHeaderCell>
                    <TableHeaderCell>Hex</TableHeaderCell>
                    <TableHeaderCell>Undertone</TableHeaderCell>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {visibleMap.markers.map((marker) => (
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
                      <TableCell>
                        <TableCellLayout className={styles.undertone}>{marker.undertone ?? '—'}</TableCellLayout>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <MapCanvas colorMap={visibleMap} selectedShadeId={selectedShadeId} onSelect={setSelectedShadeId} />
          </div>
          <div className={styles.actions}>
            <Button
              as="a"
              appearance="secondary"
              icon={<ArrowDownloadRegular />}
              href={colorMap.downloadUrl}
              download={copy.file}
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
