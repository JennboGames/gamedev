import type { ColorMap, Product, Shade } from '../types';
import type { ApiClient } from './types';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError('Could not reach the server.', 0);
  }

  const text = await response.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    const message = (payload as { error?: { message?: string } } | null)?.error?.message;
    throw new ApiError(message ?? `Request failed (HTTP ${response.status}).`, response.status);
  }
  return payload as T;
}

export const liveClient: ApiClient = {
  getHealth: () => request('GET', '/health'),

  searchFoundations: (searchRequest) => request('POST', '/searches', searchRequest),

  async listProducts() {
    return (await request<{ items: Product[] }>('GET', '/products')).items;
  },

  getProduct: (productId) => request('GET', `/products/${encodeURIComponent(productId)}`),

  async listProductShades(productId) {
    return (await request<{ items: Shade[] }>('GET', `/products/${encodeURIComponent(productId)}/shades`)).items;
  },

  extractShadeHex: (shadeId) => request('POST', `/shades/${encodeURIComponent(shadeId)}/extract-hex`),

  generateColorMap: (colorMapRequest) => request<ColorMap>('POST', '/color-map', colorMapRequest ?? {}),

  async getColorMap(shape) {
    try {
      return await request<ColorMap>('GET', shape ? `/color-map?shape=${shape}` : '/color-map');
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) return null;
      throw error;
    }
  },
};
