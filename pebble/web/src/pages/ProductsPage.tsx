import { useState } from 'react';
import { Button, Caption1, Tab, TabList, Title2, makeStyles, tokens } from '@fluentui/react-components';
import { BoxMultipleRegular, SearchRegular } from '@fluentui/react-icons';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { ProductCard } from '../components/ProductCard';
import { EmptyState, ErrorBanner, LoadingCards } from '../components/StateViews';
import { useAsync } from '../hooks/useAsync';
import type { ProductStatus } from '../types';

type Filter = 'all' | ProductStatus;

const useStyles = makeStyles({
  page: { display: 'flex', flexDirection: 'column', gap: tokens.spacingVerticalL },
  title: { display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: tokens.spacingHorizontalL },
  list: { display: 'flex', flexDirection: 'column', gap: tokens.spacingVerticalM },
});

export function ProductsPage() {
  const styles = useStyles();
  const navigate = useNavigate();
  const [filter, setFilter] = useState<Filter>('all');
  const { data, loading, error, reload } = useAsync(() => api.listProducts());

  const products = data ?? [];
  const totalShades = products.reduce((sum, product) => sum + product.shadeCount, 0);
  const visible = filter === 'all' ? products : products.filter((product) => product.status === filter);

  return (
    <div className={styles.page}>
      <div className={styles.title}>
        <Title2>Collected foundations</Title2>
        {!loading && !error ? (
          <Caption1>
            {products.length} products · {totalShades} shades
          </Caption1>
        ) : null}
      </div>

      <TabList selectedValue={filter} onTabSelect={(_event, tab) => setFilter(tab.value as Filter)}>
        <Tab value="all">All products</Tab>
        <Tab value="extracting">Extracting</Tab>
        <Tab value="collected">Collected</Tab>
        <Tab value="partial">Needs attention</Tab>
      </TabList>

      {loading ? <LoadingCards count={3} /> : null}

      {error ? <ErrorBanner title="Couldn't load foundations" message={error.message} onRetry={reload} /> : null}

      {!loading && !error && products.length === 0 ? (
        <EmptyState
          icon={<BoxMultipleRegular />}
          title="No foundations collected yet"
          body="Search Amazon to build your first product list."
          action={
            <Button appearance="primary" icon={<SearchRegular />} onClick={() => navigate('/')}>
              Run first search
            </Button>
          }
        />
      ) : null}

      {!loading && !error && products.length > 0 ? (
        visible.length > 0 ? (
          <div className={styles.list}>
            {visible.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        ) : (
          <Caption1>No products match this filter.</Caption1>
        )
      ) : null}
    </div>
  );
}
