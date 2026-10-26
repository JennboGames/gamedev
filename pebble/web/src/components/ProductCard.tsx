import { useState } from 'react';
import {
  Badge,
  Body1,
  Button,
  Caption1,
  Card,
  CardHeader,
  CardPreview,
  Link,
  Subtitle2,
  makeStyles,
  tokens,
} from '@fluentui/react-components';
import { ChevronDownRegular, ChevronUpRegular, ColorRegular, OpenRegular } from '@fluentui/react-icons';
import { motion, useReducedMotion } from 'framer-motion';
import { RETAILER_LABELS, type Product, type ProductStatus } from '../types';
import { ShadeSublist } from './ShadeSublist';

const STATUS_LABEL: Record<ProductStatus, string> = {
  collected: 'Collected',
  extracting: 'Extracting',
  partial: 'Some swatches failed',
};

const STATUS_COLOR: Record<ProductStatus, 'success' | 'warning' | 'danger'> = {
  collected: 'success',
  extracting: 'warning',
  partial: 'danger',
};

const useStyles = makeStyles({
  card: {
    padding: 0,
    overflow: 'hidden',
  },
  body: {
    display: 'grid',
    gridTemplateColumns: '160px 1fr',
    '@media (max-width: 600px)': { gridTemplateColumns: '1fr' },
  },
  image: {
    width: '100%',
    height: '100%',
    minHeight: '140px',
    objectFit: 'cover',
  },
  imageFallback: {
    display: 'grid',
    placeItems: 'center',
    width: '100%',
    height: '100%',
    minHeight: '140px',
    backgroundColor: tokens.colorBrandBackground2,
    color: tokens.colorBrandForeground1,
    fontSize: '48px',
  },
  content: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalS,
    padding: tokens.spacingHorizontalL,
    minWidth: 0,
  },
  meta: {
    display: 'flex',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: tokens.spacingHorizontalM,
    color: tokens.colorNeutralForeground3,
  },
  swatches: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalXS,
  },
  swatch: {
    width: '22px',
    height: '22px',
    borderRadius: tokens.borderRadiusCircular,
    border: `1px solid ${tokens.colorNeutralStroke1}`,
  },
  sublist: {
    paddingTop: tokens.spacingVerticalS,
    borderTop: `1px solid ${tokens.colorNeutralStroke2}`,
  },
});

export function ProductCard({ product }: { product: Product }) {
  const styles = useStyles();
  const reduceMotion = useReducedMotion();
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      whileHover={reduceMotion ? undefined : { y: -2 }}
      transition={{ duration: 0.18, ease: [0.4, 0, 0.2, 1] }}
    >
      <Card className={styles.card}>
        <div className={styles.body}>
          <CardPreview>
            {product.imageUrl ? (
              <img className={styles.image} src={product.imageUrl} alt={`${product.title} packaging`} loading="lazy" />
            ) : (
              <span className={styles.imageFallback} aria-hidden="true">
                <ColorRegular />
              </span>
            )}
          </CardPreview>
          <div className={styles.content}>
            <CardHeader
              header={<Subtitle2>{product.title}</Subtitle2>}
              action={
                <Badge appearance="tint" color={STATUS_COLOR[product.status]} shape="rounded">
                  {STATUS_LABEL[product.status]}
                </Badge>
              }
            />
            <div className={styles.meta}>
              {product.brand ? <Body1>{product.brand}</Body1> : null}
              <Caption1>{product.shadeCount} shades</Caption1>
              <Caption1>{product.asin}</Caption1>
              {product.detailPageUrl ? (
                <Link href={product.detailPageUrl} target="_blank" rel="noopener noreferrer" inline>
                  <OpenRegular /> View on {RETAILER_LABELS[product.retailer]}
                </Link>
              ) : null}
            </div>
            <div className={styles.swatches} aria-label="Sample shades">
              {product.sampleHexes.map((hex) => (
                <span key={hex} className={styles.swatch} style={{ backgroundColor: hex }} title={hex} />
              ))}
              <Button
                appearance="transparent"
                size="small"
                icon={expanded ? <ChevronUpRegular /> : <ChevronDownRegular />}
                iconPosition="after"
                aria-expanded={expanded}
                onClick={() => setExpanded((value) => !value)}
              >
                {expanded ? 'Hide shades' : 'Show shades'}
              </Button>
            </div>
            {expanded ? (
              <div className={styles.sublist}>
                <ShadeSublist productId={product.id} shadeCount={product.shadeCount} />
              </div>
            ) : null}
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
