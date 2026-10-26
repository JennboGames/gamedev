import { useSyncExternalStore } from 'react';
import { Button, makeStyles, tokens } from '@fluentui/react-components';
import {
  getPreviewState,
  PREVIEW_STATES,
  setPreviewState,
  subscribePreviewState,
  type PreviewDataState,
} from '../api/previewState';

const LABELS: Record<PreviewDataState, string> = {
  data: 'Data',
  loading: 'Loading',
  empty: 'Empty',
  error: 'Error',
};

const useStyles = makeStyles({
  switcher: {
    position: 'fixed',
    right: tokens.spacingHorizontalL,
    bottom: tokens.spacingVerticalL,
    zIndex: 20,
    display: 'flex',
    gap: tokens.spacingHorizontalXS,
    padding: tokens.spacingHorizontalXS,
    borderRadius: tokens.borderRadiusLarge,
    backgroundColor: tokens.colorNeutralBackground1,
    border: `1px solid ${tokens.colorNeutralStroke1}`,
    boxShadow: tokens.shadow16,
  },
});

/** Dev-only corner control that forces the mock client into a data state. */
export function PreviewStateSwitcher() {
  const styles = useStyles();
  const state = useSyncExternalStore(subscribePreviewState, getPreviewState);

  if (!import.meta.env.DEV) return null;

  const select = (next: PreviewDataState) => {
    setPreviewState(next);
    // Pages fetch on mount, so remount them to apply the new state.
    window.location.reload();
  };

  return (
    <div className={styles.switcher} role="group" aria-label="Mock data state">
      {PREVIEW_STATES.map((item) => (
        <Button
          key={item}
          size="small"
          appearance={item === state ? 'primary' : 'subtle'}
          onClick={() => select(item)}
        >
          {LABELS[item]}
        </Button>
      ))}
    </div>
  );
}
