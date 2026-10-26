import { Caption1, Tooltip, makeStyles, tokens } from '@fluentui/react-components';

const useStyles = makeStyles({
  chip: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalS,
  },
  swatch: {
    width: '18px',
    height: '18px',
    flexShrink: 0,
    borderRadius: tokens.borderRadiusCircular,
    border: `1px solid ${tokens.colorNeutralStroke1}`,
    boxShadow: tokens.shadow2,
  },
  hex: {
    fontFamily: 'ui-monospace, SFMono-Regular, Consolas, monospace',
    color: tokens.colorNeutralForeground3,
  },
});

interface ShadeChipProps {
  hex: string | null;
  showHex?: boolean;
}

export function ShadeChip({ hex, showHex = true }: ShadeChipProps) {
  const styles = useStyles();
  if (!hex) {
    return <Caption1 className={styles.hex}>No hex yet</Caption1>;
  }
  return (
    <Tooltip content={hex} relationship="label">
      <span className={styles.chip}>
        <span className={styles.swatch} style={{ backgroundColor: hex }} aria-hidden="true" />
        {showHex ? <Caption1 className={styles.hex}>{hex}</Caption1> : null}
      </span>
    </Tooltip>
  );
}
