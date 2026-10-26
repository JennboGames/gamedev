import { buildMockColorMap, getMockShades, mockProducts } from '../mocks/data';
import type { ColorMap, Product, SearchRequest, SearchResult, Shade } from '../types';
import { getPreviewState } from './previewState';
import type { ApiClient } from './types';

const DELAY_MS = 350;

function delay(): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, DELAY_MS);
  });
}

/** Honors the dev-only preview state: loading never settles, error rejects. */
async function gate(errorMessage: string): Promise<'data' | 'empty'> {
  const state = getPreviewState();
  if (state === 'loading') {
    return new Promise<never>(() => undefined);
  }
  await delay();
  if (state === 'error') {
    throw new Error(errorMessage);
  }
  return state;
}

export const mockClient: ApiClient = {
  async getHealth() {
    await gate('Health check failed');
    return { status: 'healthy', services: { database: true, storage: true, amazonPaapi: true } };
  },

  async searchFoundations(request: SearchRequest): Promise<SearchResult> {
    const state = await gate('Search failed. Try again in a moment.');
    const limit = request.maxProducts ?? 20;
    const products = state === 'empty' ? [] : mockProducts.slice(0, limit);
    const warnings = (request.retailers ?? []).includes('sephora')
      ? ['Sephora: blocks automated access (HTTP 403), so its products cannot be collected.']
      : [];
    return { searchId: 'search-mock-1', products: products.map((product) => ({ ...product })), warnings };
  },

  async listProducts(): Promise<Product[]> {
    const state = await gate("Couldn't load collected foundations.");
    return state === 'empty' ? [] : mockProducts.map((product) => ({ ...product }));
  },

  async getProduct(productId: string): Promise<Product> {
    await gate("Couldn't load this foundation.");
    const product = mockProducts.find((item) => item.id === productId);
    if (!product) throw new Error(`Product ${productId} not found`);
    return { ...product };
  },

  async listProductShades(productId: string): Promise<Shade[]> {
    const state = await gate("Couldn't load shades for this foundation.");
    if (state === 'empty') return [];
    const shades = getMockShades(productId);
    if (!shades) throw new Error(`Product ${productId} not found`);
    return shades;
  },

  async extractShadeHex(shadeId: string): Promise<Shade> {
    await gate("Couldn't load swatch for 3C2 Pebble");
    for (const product of mockProducts) {
      const shade = getMockShades(product.id)?.find((item) => item.id === shadeId);
      if (shade) return shade;
    }
    throw new Error(`Shade ${shadeId} not found`);
  },

  async generateColorMap(request): Promise<ColorMap> {
    const state = await gate("Couldn't generate the shade map.");
    if (state === 'empty') throw new Error('No shades with hex colors to plot yet.');
    return buildMockColorMap(request?.productIds);
  },

  async getColorMap(): Promise<ColorMap | null> {
    const state = await gate("Couldn't load the shade map.");
    return state === 'empty' ? null : buildMockColorMap();
  },
};
