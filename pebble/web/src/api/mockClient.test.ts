import { describe, expect, it } from 'vitest';
import { mockClient } from './mockClient';

describe('mockClient', () => {
  it('lists the five sample products', async () => {
    const products = await mockClient.listProducts();
    expect(products).toHaveLength(5);
    expect(products[0].title).toContain('Double Wear');
  });

  it('returns as many shades as the product reports', async () => {
    const [product] = await mockClient.listProducts();
    const shades = await mockClient.listProductShades(product.id);
    expect(shades).toHaveLength(product.shadeCount);
    expect(shades.every((shade) => shade.hex !== null)).toBe(true);
  });

  it('plots every shade with positions inside the map', async () => {
    const map = await mockClient.getColorMap();
    const products = await mockClient.listProducts();
    expect(map?.markers).toHaveLength(products.reduce((sum, product) => sum + product.shadeCount, 0));
    for (const marker of map?.markers ?? []) {
      expect(marker.x).toBeGreaterThanOrEqual(0);
      expect(marker.x).toBeLessThanOrEqual(1);
      expect(marker.y).toBeGreaterThanOrEqual(0);
      expect(marker.y).toBeLessThanOrEqual(1);
    }
  });
});
