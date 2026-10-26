import { colorMapPosition, hexToHsl, lerpHex } from '../lib/color';
import type { ColorMap, ColorMapMarker, Product, ProductStatus, Shade } from '../types';

interface SeedShade {
  name: string;
  hex: string;
}

interface ProductSpec {
  id: string;
  asin: string;
  title: string;
  brand: string;
  status: ProductStatus;
  shadeCount: number;
  imageSeed: string;
  lightHex: string;
  darkHex: string;
  seeds: SeedShade[];
}

const GENERATED_TONES = ['Buff', 'Sand', 'Honey', 'Amber', 'Almond', 'Hazel', 'Cocoa', 'Mocha'];

const SPECS: ProductSpec[] = [
  {
    id: 'prod-double-wear',
    asin: 'B0GQVP8RLD',
    title: 'Double Wear Stay-in-Place Foundation',
    brand: 'Estée Lauder',
    status: 'collected',
    shadeCount: 42,
    imageSeed: 'double-wear-foundation',
    lightHex: '#F4DBC3',
    darkHex: '#5A3626',
    seeds: [
      { name: '1N1 Ivory Nude', hex: '#F1D2B5' },
      { name: '2W1 Dawn', hex: '#E6BE98' },
      { name: '3C2 Pebble', hex: '#D7A67F' },
      { name: '4N2 Spiced Sand', hex: '#BC8760' },
      { name: '6N2 Truffle', hex: '#7A4A32' },
    ],
  },
  {
    id: 'prod-fit-me',
    asin: 'B0MOCKFM02',
    title: 'Fit Me Matte + Poreless Foundation',
    brand: 'Maybelline',
    status: 'collected',
    shadeCount: 40,
    imageSeed: 'fit-me-foundation',
    lightHex: '#F5DCC6',
    darkHex: '#5E3A2A',
    seeds: [
      { name: '110 Porcelain', hex: '#F3D6BD' },
      { name: '120 Classic Ivory', hex: '#E8C4A0' },
      { name: '220 Natural Beige', hex: '#D9A77E' },
      { name: '330 Toffee', hex: '#A9744F' },
      { name: '360 Chocolate', hex: '#6B4130' },
    ],
  },
  {
    id: 'prod-studio-fix',
    asin: 'B0MOCKSF03',
    title: 'Studio Fix Fluid SPF 15 Foundation',
    brand: 'MAC',
    status: 'extracting',
    shadeCount: 38,
    imageSeed: 'studio-fix-foundation',
    lightHex: '#F2D3B6',
    darkHex: '#523223',
    seeds: [
      { name: 'NC15', hex: '#EFCDB0' },
      { name: 'NC25', hex: '#E0B48F' },
      { name: 'N5 Golden', hex: '#C58B58' },
      { name: 'NW40', hex: '#9C6A47' },
      { name: 'NW55', hex: '#5E3826' },
    ],
  },
  {
    id: 'prod-true-match',
    asin: 'B0MOCKTM04',
    title: 'True Match Super-Blendable Foundation',
    brand: "L'Oréal",
    status: 'collected',
    shadeCount: 33,
    imageSeed: 'true-match-foundation',
    lightHex: '#F6DDC4',
    darkHex: '#603D2D',
    seeds: [
      { name: 'W1 Porcelain', hex: '#F5DABF' },
      { name: 'N3 Creamy Natural', hex: '#E5BE9A' },
      { name: 'W5 Sand Beige', hex: '#CF9F78' },
      { name: 'W6 Rich Caramel', hex: '#A56D45' },
      { name: 'N9 Coffee', hex: '#6F4533' },
    ],
  },
  {
    id: 'prod-soft-matte',
    asin: 'B0MOCKSM05',
    title: 'Soft Matte Complete Foundation',
    brand: 'NYX',
    status: 'collected',
    shadeCount: 24,
    imageSeed: 'soft-matte-foundation',
    lightHex: '#F1D4B8',
    darkHex: '#4B2E22',
    seeds: [
      { name: 'Pale', hex: '#F0D0B4' },
      { name: 'Natural Buff', hex: '#E2B792' },
      { name: 'Warm Caramel', hex: '#C79A74' },
      { name: 'Cappuccino', hex: '#9A6B49' },
      { name: 'Espresso', hex: '#4B2E22' },
    ],
  },
];

function toShade(spec: ProductSpec, index: number, seed: SeedShade): Shade {
  const { h, l } = hexToHsl(seed.hex);
  return {
    id: `${spec.id}-shade-${index}`,
    productId: spec.id,
    asin: `${spec.asin}-${index}`,
    name: seed.name,
    swatchUrl: swatchDataUrl(seed.hex),
    hex: seed.hex,
    hue: Math.round(h),
    lightness: Math.round(l * 100),
    status: 'extracted',
    error: null,
  };
}

function buildShades(spec: ProductSpec): Shade[] {
  const shades = spec.seeds.map((seed, index) => toShade(spec, index, seed));
  for (let i = spec.seeds.length; i < spec.shadeCount; i += 1) {
    const hex = lerpHex(spec.lightHex, spec.darkHex, (i + 1) / (spec.shadeCount + 1));
    const name = `${String(i + 1).padStart(2, '0')} ${GENERATED_TONES[i % GENERATED_TONES.length]}`;
    shades.push(toShade(spec, i, { name, hex }));
  }
  return shades;
}

function swatchDataUrl(hex: string): string {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="${hex}"/></svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

const shadesByProduct = new Map<string, Shade[]>(SPECS.map((spec) => [spec.id, buildShades(spec)]));

export const mockProducts: Product[] = SPECS.map((spec) => ({
  id: spec.id,
  retailer: 'amazon',
  asin: spec.asin,
  title: spec.title,
  brand: spec.brand,
  imageUrl: `https://picsum.photos/seed/${spec.imageSeed}/480/300`,
  detailPageUrl: `https://www.amazon.com/dp/${spec.asin}`,
  shadeCount: spec.shadeCount,
  sampleHexes: spec.seeds.map((seed) => seed.hex),
  status: spec.status,
  createdAt: '2026-10-26T12:00:00Z',
}));

export function getMockShades(productId: string): Shade[] | undefined {
  return shadesByProduct.get(productId)?.map((shade) => ({ ...shade }));
}

const MAP_WIDTH = 800;
const MAP_HEIGHT = 600;

/** Red (left) to yellow (right), white at the top and black at the bottom. */
function colorMapImageUrl(): string {
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${MAP_WIDTH}" height="${MAP_HEIGHT}" viewBox="0 0 ${MAP_WIDTH} ${MAP_HEIGHT}">` +
    '<defs>' +
    '<linearGradient id="h" x1="0" y1="0" x2="1" y2="0">' +
    '<stop offset="0" stop-color="#ff0000"/><stop offset="1" stop-color="#ffff00"/>' +
    '</linearGradient>' +
    '<linearGradient id="v" x1="0" y1="0" x2="0" y2="1">' +
    '<stop offset="0" stop-color="#fff" stop-opacity="1"/><stop offset="0.5" stop-color="#fff" stop-opacity="0"/>' +
    '<stop offset="0.5" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="1"/>' +
    '</linearGradient>' +
    '</defs>' +
    `<rect width="${MAP_WIDTH}" height="${MAP_HEIGHT}" fill="url(#h)"/>` +
    `<rect width="${MAP_WIDTH}" height="${MAP_HEIGHT}" fill="url(#v)"/>` +
    '</svg>';
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

export function buildMockColorMap(productIds?: string[]): ColorMap {
  const markers: ColorMapMarker[] = [];
  for (const product of mockProducts) {
    if (productIds && productIds.length > 0 && !productIds.includes(product.id)) continue;
    for (const shade of shadesByProduct.get(product.id) ?? []) {
      if (!shade.hex) continue;
      const { x, y } = colorMapPosition(shade.hex);
      markers.push({
        shadeId: shade.id,
        productId: product.id,
        shadeName: shade.name,
        productTitle: product.title,
        hex: shade.hex,
        hue: shade.hue ?? 0,
        lightness: shade.lightness ?? 0,
        x,
        y,
      });
    }
  }
  return { imageUrl: colorMapImageUrl(), width: MAP_WIDTH, height: MAP_HEIGHT, markers };
}
