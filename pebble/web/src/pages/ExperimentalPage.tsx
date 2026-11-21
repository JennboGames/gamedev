import { useState, type FormEvent } from 'react';
import {
  Body1,
  Button,
  Caption1,
  Card,
  Field,
  MessageBar,
  MessageBarBody,
  MessageBarTitle,
  Spinner,
  Subtitle2,
  Textarea,
  Title2,
  makeStyles,
  tokens,
} from '@fluentui/react-components';
import { BeakerRegular } from '@fluentui/react-icons';
import { api } from '../api';
import { ErrorBanner } from '../components/StateViews';
import type { AmazonItem, AmazonItemsResponse } from '../types';

const MAX_ASINS = 10;
const ASIN_PATTERN = /^[A-Za-z0-9]{10}$/;

const useStyles = makeStyles({
  page: { display: 'flex', flexDirection: 'column', gap: tokens.spacingVerticalXL },
  form: { display: 'flex', flexDirection: 'column', gap: tokens.spacingVerticalL, padding: tokens.spacingHorizontalXL },
  actions: { display: 'flex', justifyContent: 'flex-end' },
  results: { display: 'flex', flexDirection: 'column', gap: tokens.spacingVerticalM },
  item: { display: 'flex', gap: tokens.spacingHorizontalL, padding: tokens.spacingHorizontalL },
  image: { width: '96px', height: '96px', objectFit: 'contain', flexShrink: 0 },
  itemBody: { display: 'flex', flexDirection: 'column', gap: tokens.spacingVerticalXS, minWidth: 0 },
  raw: {
    maxHeight: '420px',
    overflow: 'auto',
    padding: tokens.spacingHorizontalM,
    backgroundColor: tokens.colorNeutralBackground3,
    borderRadius: tokens.borderRadiusMedium,
    fontSize: tokens.fontSizeBase200,
  },
});

function parseAsins(text: string): string[] {
  return text
    .split(/[\s,;]+/)
    .map((value) => value.trim())
    .filter(Boolean);
}

function pickImage(item: AmazonItem): string | undefined {
  const primary = item.images?.primary;
  return (primary?.medium ?? primary?.large ?? primary?.small)?.url;
}

export function ExperimentalPage() {
  const styles = useStyles();
  const [text, setText] = useState('');
  const [touched, setTouched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [response, setResponse] = useState<AmazonItemsResponse | null>(null);

  const asins = parseAsins(text);
  const invalid = asins.length === 0 || asins.length > MAX_ASINS || asins.some((a) => !ASIN_PATTERN.test(a));
  const items = response?.itemResults?.items ?? response?.itemsResult?.items ?? [];

  const lookUp = async () => {
    setLoading(true);
    setError(null);
    try {
      setResponse(await api.getAmazonItems(asins));
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setTouched(true);
    if (invalid) return;
    void lookUp();
  };

  return (
    <div className={styles.page}>
      <div>
        <Title2>Experimental feature</Title2>
        <Body1 block>
          Look up product details from the Amazon Creators API. This page is a testing ground and may change or be
          removed.
        </Body1>
      </div>

      <Card>
        <form className={styles.form} onSubmit={submit} noValidate>
          <Field
            label="Amazon ASINs"
            hint={`Up to ${MAX_ASINS}, separated by commas, spaces, or new lines.`}
            validationState={touched && invalid ? 'warning' : 'none'}
            validationMessage={
              touched && invalid ? `Enter 1 to ${MAX_ASINS} ASINs, each 10 letters or digits.` : undefined
            }
          >
            <Textarea
              value={text}
              placeholder="B09B2SBHQK, B09B8V1LZ3"
              onChange={(_event, data) => setText(data.value)}
              resize="vertical"
            />
          </Field>
          <div className={styles.actions}>
            <Button
              appearance="primary"
              type="submit"
              disabled={loading}
              icon={loading ? <Spinner size="tiny" /> : <BeakerRegular />}
            >
              {loading ? 'Looking up…' : 'Look up products'}
            </Button>
          </div>
        </form>
      </Card>

      {error ? <ErrorBanner title="Lookup failed" message={error.message} onRetry={() => void lookUp()} /> : null}

      {response?.errors?.length ? (
        <MessageBar intent="warning" layout="multiline">
          <MessageBarBody>
            <MessageBarTitle>Some items were not returned</MessageBarTitle>
            {response.errors.map((e) => e.message ?? e.code).join(' ')}
          </MessageBarBody>
        </MessageBar>
      ) : null}

      {response ? (
        <div className={styles.results}>
          <Subtitle2>
            {items.length} {items.length === 1 ? 'item' : 'items'} returned
          </Subtitle2>
          {items.map((item) => {
            const image = pickImage(item);
            return (
              <Card key={item.asin} className={styles.item} orientation="horizontal">
                {image ? <img className={styles.image} src={image} alt="" /> : null}
                <div className={styles.itemBody}>
                  <Body1>
                    <strong>{item.itemInfo?.title?.displayValue ?? item.asin}</strong>
                  </Body1>
                  <Caption1>
                    {[item.itemInfo?.byLineInfo?.brand?.displayValue, item.asin].filter(Boolean).join(' · ')}
                  </Caption1>
                  {item.detailPageURL ? (
                    <a href={item.detailPageURL} target="_blank" rel="noopener noreferrer">
                      View on Amazon
                    </a>
                  ) : null}
                </div>
              </Card>
            );
          })}
          <details>
            <summary>Raw response</summary>
            <pre className={styles.raw}>{JSON.stringify(response, null, 2)}</pre>
          </details>
        </div>
      ) : null}
    </div>
  );
}
