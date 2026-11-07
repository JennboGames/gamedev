import { useRef, useState, type FormEvent } from 'react';
import {
  Body1,
  Button,
  Card,
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
import type { SearchResult } from '../types';

const MIN_QUERY_LENGTH = 2;
const DEFAULT_MAX_PRODUCTS = 20;

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
});

export function SearchPage() {
  const styles = useStyles();
  const navigate = useNavigate();
  const queryRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState('');
  const [maxProducts, setMaxProducts] = useState(String(DEFAULT_MAX_PRODUCTS));
  const [touched, setTouched] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<SearchResult | null>(null);

  const trimmed = query.trim();
  const queryInvalid = trimmed.length < MIN_QUERY_LENGTH;
  const maxValue = Number(maxProducts);
  const maxInvalid = !Number.isInteger(maxValue) || maxValue < 1 || maxValue > 50;

  const focusQuery = () => queryRef.current?.focus();

  const reset = () => {
    setQuery('');
    setMaxProducts(String(DEFAULT_MAX_PRODUCTS));
    setTouched(false);
    setError(null);
  };

  const runSearch = async () => {
    setSubmitting(true);
    setError(null);
    try {
      setResult(await api.searchFoundations({ query: trimmed, maxProducts: maxValue }));
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setSubmitting(false);
    }
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setTouched(true);
    if (queryInvalid || maxInvalid) return;
    void runSearch();
  };

  return (
    <div className={styles.page}>
      <Hero
        eyebrow="Foundation shade finder"
        title="Find your foundation shade"
        subtitle="Search the foundation catalog and see where each shade lands on the color map and color wheel."
        primaryAction={{ label: 'Search the catalog', icon: <SearchRegular />, onClick: focusQuery }}
        secondaryAction={{ label: 'See the shade map', onClick: () => navigate('/map') }}
      />

      <Card>
        <form className={styles.form} onSubmit={submit} noValidate>
          <div className={styles.row}>
            <Field
              label="Search term"
              required
              validationState={touched && queryInvalid ? 'warning' : 'none'}
              validationMessage={
                touched && queryInvalid ? `Enter at least ${MIN_QUERY_LENGTH} characters to search.` : undefined
              }
            >
              <Input
                ref={queryRef}
                value={query}
                placeholder="Estee Lauder"
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
              {submitting ? 'Searching…' : 'Search the catalog'}
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
            <MessageBarTitle>No catalog match</MessageBarTitle>
            {result.warnings.join(' ')}
          </MessageBarBody>
        </MessageBar>
      ) : null}

      {result && result.products.length > 0 ? (
        <MessageBar intent="success" layout="multiline">
          <MessageBarBody>
            <MessageBarTitle>
              Found {result.products.length} {result.products.length === 1 ? 'foundation' : 'foundations'}
            </MessageBarTitle>
            Every shade comes from the catalog file.
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
          title={result ? 'No foundations matched that search' : 'No search yet'}
          body={result ? 'Try a broader search term.' : 'Search the catalog by brand or product name.'}
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
