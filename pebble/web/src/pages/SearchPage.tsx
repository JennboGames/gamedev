import { useRef, useState, type FormEvent } from 'react';
import {
  Body1,
  Button,
  Caption1,
  Card,
  Checkbox,
  Field,
  Input,
  MessageBar,
  MessageBarActions,
  MessageBarBody,
  MessageBarTitle,
  Spinner,
  makeStyles,
  tokens,
} from '@fluentui/react-components';
import { AddRegular, ArrowRightRegular, BoxMultipleRegular, SearchRegular } from '@fluentui/react-icons';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { Hero } from '../components/Hero';
import { EmptyState, ErrorBanner } from '../components/StateViews';
import { RETAILER_LABELS, type Retailer, type SearchResult } from '../types';

const MIN_QUERY_LENGTH = 2;
const DEFAULT_MAX_PRODUCTS = 20;
const RETAILER_OPTIONS: Retailer[] = ['amazon', 'ulta', 'sephora'];
const RETAILER_HINTS: Partial<Record<Retailer, string>> = {
  ulta: 'Reads the public foundation listing, filtered by your search words',
  sephora: 'Currently blocks automated access, so it returns no products',
};

const useStyles = makeStyles({
  page: { display: 'flex', flexDirection: 'column', gap: tokens.spacingVerticalXL },
  form: { display: 'flex', flexDirection: 'column', gap: tokens.spacingVerticalL, padding: tokens.spacingHorizontalXL },
  row: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr 2fr',
    gap: tokens.spacingHorizontalL,
    '@media (max-width: 800px)': { gridTemplateColumns: '1fr' },
  },
  actions: { display: 'flex', justifyContent: 'flex-end', gap: tokens.spacingHorizontalM },
  retailers: { display: 'flex', flexWrap: 'wrap', columnGap: tokens.spacingHorizontalXL },
});

export function SearchPage() {
  const styles = useStyles();
  const navigate = useNavigate();
  const queryRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState('');
  const [maxProducts, setMaxProducts] = useState(String(DEFAULT_MAX_PRODUCTS));
  const [retailers, setRetailers] = useState<Retailer[]>(['amazon']);
  const [touched, setTouched] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<SearchResult | null>(null);

  const trimmed = query.trim();
  const queryInvalid = trimmed.length < MIN_QUERY_LENGTH;
  const maxValue = Number(maxProducts);
  const maxInvalid = !Number.isInteger(maxValue) || maxValue < 1 || maxValue > 50;
  const retailersInvalid = retailers.length === 0;

  const toggleRetailer = (retailer: Retailer, checked: boolean) =>
    setRetailers((current) =>
      checked ? RETAILER_OPTIONS.filter((item) => item === retailer || current.includes(item)) : current.filter((item) => item !== retailer),
    );

  const focusQuery = () => queryRef.current?.focus();

  const reset = () => {
    setQuery('');
    setMaxProducts(String(DEFAULT_MAX_PRODUCTS));
    setRetailers(['amazon']);
    setTouched(false);
    setError(null);
  };

  const runSearch = async () => {
    setSubmitting(true);
    setError(null);
    try {
      setResult(await api.searchFoundations({ query: trimmed, maxProducts: maxValue, retailers }));
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setSubmitting(false);
    }
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setTouched(true);
    if (queryInvalid || maxInvalid || retailersInvalid) return;
    void runSearch();
  };

  return (
    <div className={styles.page}>
      <Hero
        eyebrow="Foundation shade finder"
        title="Find your foundation shade"
        subtitle="Search Amazon, Ulta and Sephora foundations, pull every shade's swatch, and see where each one lands on the color map."
        primaryAction={{ label: 'Collect foundations', icon: <SearchRegular />, onClick: focusQuery }}
        secondaryAction={{ label: 'See the shade map', onClick: () => navigate('/map') }}
      />

      <Card>
        <form className={styles.form} onSubmit={submit} noValidate>
          <div className={styles.row}>
            <Field
              label="Search term"
              required
              hint="Search phrase; brand and product words narrow Ulta results"
              validationState={touched && queryInvalid ? 'warning' : 'none'}
              validationMessage={
                touched && queryInvalid ? `Enter at least ${MIN_QUERY_LENGTH} characters to search.` : undefined
              }
            >
              <Input
                ref={queryRef}
                value={query}
                placeholder="skin foundation"
                onChange={(_event, data) => setQuery(data.value)}
                onBlur={() => setTouched(true)}
              />
            </Field>
            <Field
              label="Max products"
              validationState={touched && maxInvalid ? 'warning' : 'none'}
              validationMessage={touched && maxInvalid ? 'Use a whole number from 1 to 50.' : undefined}
            >
              <Input
                type="number"
                value={maxProducts}
                min={1}
                max={50}
                onChange={(_event, data) => setMaxProducts(data.value)}
              />
            </Field>
            <Field label="Category">
              <Input value="Beauty > Makeup > Foundation" readOnly />
            </Field>
          </div>
          <Field
            label="Retailers"
            validationState={touched && retailersInvalid ? 'warning' : 'none'}
            validationMessage={touched && retailersInvalid ? 'Pick at least one retailer.' : undefined}
          >
            <div className={styles.retailers}>
              {RETAILER_OPTIONS.map((retailer) => (
                <Checkbox
                  key={retailer}
                  label={RETAILER_LABELS[retailer]}
                  checked={retailers.includes(retailer)}
                  onChange={(_event, data) => toggleRetailer(retailer, data.checked === true)}
                />
              ))}
            </div>
          </Field>
          <Caption1>
            {retailers
              .map((retailer) => RETAILER_HINTS[retailer])
              .filter(Boolean)
              .join('. ')}
          </Caption1>
          <div className={styles.actions}>
            <Button appearance="secondary" type="button" onClick={reset} disabled={submitting}>
              Cancel
            </Button>
            <Button
              appearance="primary"
              type="submit"
              disabled={submitting}
              icon={submitting ? <Spinner size="tiny" /> : <SearchRegular />}
            >
              {submitting ? 'Collecting foundations…' : 'Collect foundations'}
            </Button>
          </div>
        </form>
      </Card>

      {error ? (
        <ErrorBanner title="Search failed" message={error.message} onRetry={() => void runSearch()} />
      ) : null}

      {result && result.warnings.length > 0 ? (
        <MessageBar intent="warning" layout="multiline">
          <MessageBarBody>
            <MessageBarTitle>Some retailers could not be searched</MessageBarTitle>
            {result.warnings.join(' ')}
          </MessageBarBody>
        </MessageBar>
      ) : null}

      {result && result.products.length > 0 ? (
        <MessageBar intent="success" layout="multiline">
          <MessageBarBody>
            <MessageBarTitle>
              Collected {result.products.length} {result.products.length === 1 ? 'foundation' : 'foundations'}
            </MessageBarTitle>
            Every shade swatch was queued for hex extraction.
          </MessageBarBody>
          <MessageBarActions>
            <Button icon={<ArrowRightRegular />} iconPosition="after" onClick={() => navigate('/products')}>
              View products
            </Button>
          </MessageBarActions>
        </MessageBar>
      ) : null}

      {!result || result.products.length === 0 ? (
        <EmptyState
          icon={<BoxMultipleRegular />}
          title={result ? 'No foundations matched that search' : 'No foundations collected yet'}
          body={result ? 'Try a broader search term or another retailer.' : 'Search a retailer to build your first product list.'}
          action={
            <Button appearance="primary" icon={<AddRegular />} onClick={focusQuery}>
              Run first search
            </Button>
          }
        />
      ) : (
        <Body1>Open the Products page to browse every shade with its extracted hex.</Body1>
      )}
    </div>
  );
}
