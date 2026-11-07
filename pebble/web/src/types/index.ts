/** Wire types; mirror the backend contracts in api/src/models/api.py (camelCase JSON). */

export type ProductStatus = 'collected' | 'extracting' | 'partial';
export type ShadeStatus = 'extracted' | 'failed';
export type Retailer = 'ulta' | 'sephora';
/** Where a product came from; 'catalog' is catalog/products.json. */
export type ProductSource = Retailer | 'catalog';

export const RETAILER_LABELS: Record<ProductSource, string> = {
  ulta: 'Ulta',
  sephora: 'Sephora',
  catalog: 'Catalog',
};

export interface Product {
  id: string;
  retailer: ProductSource;
  /** The product's id within its source. */
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
  undertone: string | null;
  status: ShadeStatus;
  error: string | null;
}

export interface SearchRequest {
  query: string;
  maxProducts?: number;
}

export interface SearchResult {
  searchId: string;
  products: Product[];
  /** Notes about the search, such as no catalog product matching. */
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
  undertone: string | null;
  /** Horizontal position in [0, 1] of the image: red to yellow on the rectangle map, the wheel's x on the wheel. */
  x: number;
  /** Vertical position in [0, 1] of the image: white (top) to black (bottom) on the rectangle map. */
  y: number;
}

/** 'rectangle' plots hue left to right and lightness top to bottom; 'wheel' is the full color wheel. */
export type ColorMapShape = 'rectangle' | 'wheel';

export interface ColorMapRequest {
  productIds?: string[];
  shape?: ColorMapShape;
}

export interface ColorMap {
  /** Plain background shown in the app; markers and labels are drawn over it. */
  imageUrl: string;
  /** Full image with labels and markers, for download. */
  downloadUrl: string;
  width: number;
  height: number;
  shape: ColorMapShape;
  markers: ColorMapMarker[];
}

export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

export interface HealthResponse {
  status: HealthStatus;
  services: Record<string, boolean>;
}
