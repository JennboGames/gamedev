import {
  Body1,
  Button,
  Card,
  MessageBar,
  MessageBarActions,
  MessageBarBody,
  MessageBarTitle,
  Skeleton,
  SkeletonItem,
  Title3,
  makeStyles,
  tokens,
} from '@fluentui/react-components';
import { ArrowClockwiseRegular } from '@fluentui/react-icons';
import type { ReactNode } from 'react';

const useStyles = makeStyles({
  skeletonCard: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalS,
    padding: tokens.spacingHorizontalL,
  },
  empty: {
    alignItems: 'center',
    textAlign: 'center',
    gap: tokens.spacingVerticalM,
    padding: `${tokens.spacingVerticalXXL} ${tokens.spacingHorizontalXL}`,
  },
  emptyIcon: {
    display: 'grid',
    placeItems: 'center',
    width: '88px',
    height: '88px',
    borderRadius: tokens.borderRadiusCircular,
    backgroundColor: tokens.colorBrandBackground2,
    color: tokens.colorBrandForeground1,
    fontSize: '44px',
  },
});

export function LoadingCards({ count = 3 }: { count?: number }) {
  const styles = useStyles();
  return (
    <div aria-busy="true" aria-label="Loading">
      {Array.from({ length: count }, (_, index) => (
        <Card key={index} className={styles.skeletonCard} style={{ marginBottom: tokens.spacingVerticalM }}>
          <Skeleton>
            <SkeletonItem size={24} style={{ width: '55%' }} />
            <SkeletonItem size={16} style={{ marginTop: tokens.spacingVerticalS, width: '35%' }} />
            <SkeletonItem size={16} style={{ marginTop: tokens.spacingVerticalS, width: '70%' }} />
          </Skeleton>
        </Card>
      ))}
    </div>
  );
}

interface ErrorBannerProps {
  title: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorBanner({ title, message, onRetry }: ErrorBannerProps) {
  return (
    <MessageBar intent="error" layout="multiline" role="alert">
      <MessageBarBody>
        <MessageBarTitle>{title}</MessageBarTitle>
        {message}
      </MessageBarBody>
      {onRetry ? (
        <MessageBarActions>
          <Button icon={<ArrowClockwiseRegular />} onClick={onRetry}>
            Retry
          </Button>
        </MessageBarActions>
      ) : null}
    </MessageBar>
  );
}

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  body: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, body, action }: EmptyStateProps) {
  const styles = useStyles();
  return (
    <Card appearance="filled-alternative" className={styles.empty}>
      <span className={styles.emptyIcon} aria-hidden="true">
        {icon}
      </span>
      <Title3>{title}</Title3>
      <Body1>{body}</Body1>
      {action}
    </Card>
  );
}
