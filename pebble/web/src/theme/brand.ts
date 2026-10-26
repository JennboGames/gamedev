import { createDarkTheme, createLightTheme, type BrandVariants, type Theme } from '@fluentui/react-components';
import { hexToHsl, hslToHex } from '../lib/color';

export const PALETTE = {
  primary: '#8c3f52',
  accent: '#d9a066',
  surface: '#faf6f2',
  text: '#2b2321',
  muted: '#7a6d68',
  border: '#e6dcd5',
} as const;

// Lightness per Fluent brand step; step 80 anchors on the primary color.
const RAMP_LIGHTNESS: Array<[keyof BrandVariants, number]> = [
  [10, 0.05],
  [20, 0.09],
  [30, 0.13],
  [40, 0.17],
  [50, 0.22],
  [60, 0.27],
  [70, 0.32],
  [80, 0.38],
  [90, 0.43],
  [100, 0.49],
  [110, 0.55],
  [120, 0.62],
  [130, 0.7],
  [140, 0.79],
  [150, 0.88],
  [160, 0.95],
];

export function makeBrandRamp(hex: string): BrandVariants {
  const { h, s } = hexToHsl(hex);
  const ramp: Partial<BrandVariants> = {};
  for (const [step, l] of RAMP_LIGHTNESS) {
    const edgeFade = 1 - Math.abs(l - 0.5) * 0.6;
    ramp[step] = hslToHex({ h, s: s * edgeFade, l });
  }
  return ramp as BrandVariants;
}

export const FONT_FAMILY = "'Inter', 'Segoe UI Variable', system-ui, -apple-system, 'Segoe UI', sans-serif";

const brandRamp = makeBrandRamp(PALETTE.primary);

function withBrandTokens(theme: Theme, overrides: Partial<Theme>): Theme {
  return { ...theme, fontFamilyBase: FONT_FAMILY, ...overrides };
}

export const lightTheme: Theme = withBrandTokens(createLightTheme(brandRamp), {
  colorNeutralBackground2: PALETTE.surface,
  colorNeutralBackground3: '#f3ece6',
  colorNeutralForeground1: PALETTE.text,
  colorNeutralForeground2: PALETTE.text,
  colorNeutralForeground3: PALETTE.muted,
  colorNeutralStroke1: PALETTE.border,
  colorNeutralStroke2: PALETTE.border,
  borderRadiusMedium: '10px',
  borderRadiusLarge: '14px',
});

export const darkTheme: Theme = withBrandTokens(createDarkTheme(brandRamp), {
  borderRadiusMedium: '10px',
  borderRadiusLarge: '14px',
});
