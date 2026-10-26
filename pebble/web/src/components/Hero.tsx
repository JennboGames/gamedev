import { Body1, Button, Title1, makeStyles, tokens } from '@fluentui/react-components';
import { PALETTE } from '../theme/brand';
import type { ReactElement } from 'react';

const useStyles = makeStyles({
  hero: {
    position: 'relative',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalM,
    padding: `${tokens.spacingVerticalXXXL} ${tokens.spacingHorizontalXXXL}`,
    borderRadius: tokens.borderRadiusLarge,
    color: '#ffffff',
    backgroundImage: `linear-gradient(135deg, ${PALETTE.primary} 0%, #a9506a 55%, ${PALETTE.accent} 130%)`,
    boxShadow: tokens.shadow16,
  },
  mesh: {
    position: 'absolute',
    inset: 0,
    width: '100%',
    height: '100%',
    pointerEvents: 'none',
    opacity: 0.7,
  },
  content: {
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalM,
  },
  eyebrow: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalS,
    textTransform: 'uppercase',
    letterSpacing: '0.12em',
    fontSize: '11px',
    fontWeight: tokens.fontWeightSemibold,
    opacity: 0.9,
    '::before': {
      content: '""',
      width: '6px',
      height: '6px',
      borderRadius: tokens.borderRadiusCircular,
      backgroundColor: PALETTE.accent,
    },
  },
  title: {
    maxWidth: '24ch',
    lineHeight: 1.1,
    letterSpacing: '-0.02em',
    color: '#ffffff',
  },
  subtitle: {
    maxWidth: '60ch',
    opacity: 0.92,
    color: '#ffffff',
  },
  actions: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: tokens.spacingHorizontalM,
    marginTop: tokens.spacingVerticalS,
  },
  ghost: {
    color: '#ffffff',
    ':hover': { color: '#ffffff', backgroundColor: 'rgba(255,255,255,0.16)' },
  },
});

interface HeroProps {
  eyebrow: string;
  title: string;
  subtitle: string;
  primaryAction: { label: string; icon: ReactElement; onClick: () => void };
  secondaryAction: { label: string; onClick: () => void };
}

export function Hero({ eyebrow, title, subtitle, primaryAction, secondaryAction }: HeroProps) {
  const styles = useStyles();
  return (
    <section className={styles.hero}>
      <svg className={styles.mesh} aria-hidden="true" viewBox="0 0 800 400" preserveAspectRatio="none">
        <defs>
          <radialGradient id="hero-mesh-a" cx="0%" cy="0%" r="80%">
            <stop offset="0%" stopColor={PALETTE.accent} stopOpacity="0.55" />
            <stop offset="100%" stopColor={PALETTE.accent} stopOpacity="0" />
          </radialGradient>
          <radialGradient id="hero-mesh-b" cx="100%" cy="100%" r="80%">
            <stop offset="0%" stopColor={PALETTE.primary} stopOpacity="0.55" />
            <stop offset="100%" stopColor={PALETTE.primary} stopOpacity="0" />
          </radialGradient>
        </defs>
        <rect width="800" height="400" fill="url(#hero-mesh-a)" />
        <rect width="800" height="400" fill="url(#hero-mesh-b)" />
      </svg>
      <div className={styles.content}>
        <span className={styles.eyebrow}>{eyebrow}</span>
        <Title1 as="h1" className={styles.title}>
          {title}
        </Title1>
        <Body1 className={styles.subtitle}>{subtitle}</Body1>
        <div className={styles.actions}>
          <Button appearance="primary" size="large" icon={primaryAction.icon} onClick={primaryAction.onClick}
            style={{ backgroundColor: '#ffffff', color: PALETTE.primary }}>
            {primaryAction.label}
          </Button>
          <Button appearance="transparent" size="large" className={styles.ghost} onClick={secondaryAction.onClick}>
            {secondaryAction.label}
          </Button>
        </div>
      </div>
    </section>
  );
}
