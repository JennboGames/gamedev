/** Wire types; mirror the backend contracts in api/src/models/api.py (camelCase JSON). */

export type ProductStatus = 'collected' | 'extracting' | 'partial';
export type ShadeStatus = 'extracted' | 'failed';
export type Retailer = 'amazon' | 'ulta' | 'sephora';

export const RETAILER_LABELS: Record<Retailer, string> = {
  amazon: 'Amazon',
  ulta: 'Ulta',
  sephora: 'Sephora',
};

export interface Product {
  id: string;
  retailer: Retailer;
  /** The retailer's own product id (an ASIN on Amazon). */
  asin: string;
  title: string;
  brand: string | null;
  detailPageUrl: string | null;
  imageUrl: string | null;
  shadeCount: number;
  /** Up to five hex colors spread from lightest to darkest. */
  sampleHexes: string[];
  status: ProductStatus;
  createdAt: string;
}

export interface Shade {
  id: string;
  productId: string;
  asin: string;
  name: string;
  swatchUrl: string | null;
  hex: string | null;
  /** Degrees, 0-360. */
  hue: number | null;
  /** Percent, 0-100. */
  lightness: number | null;
  status: ShadeStatus;
  error: string | null;
}

export interface SearchRequest {
  query: string;
  maxProducts?: number;
  /** Defaults to Amazon on the server. */
  retailers?: Retailer[];
}

export interface SearchResult {
  searchId: string;
  products: Product[];
  /** Retailers that could not be searched; the rest of the results are still returned. */
  warnings: string[];
}

export interface ColorMapMarker {
  shadeId: string;
  productId: string;
  shadeName: string;
  productTitle: string;
  hex: string;
  hue: number;
  lightness: number;
  /** Horizontal position in [0, 1]: 0 = red edge, 1 = yellow edge. */
  x: number;
  /** Vertical position in [0, 1]: 0 = white (top), 1 = black (bottom). */
  y: number;
}

export interface ColorMapRequest {
  productIds?: string[];
}

export interface ColorMap {
  imageUrl: string;
  width: number;
  height: number;
  markers: ColorMapMarker[];
}

export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

export interface HealthResponse {
  status: HealthStatus;
  services: Record<string, boolean>;
}
