import type {
  ColorMap,
  ColorMapRequest,
  ColorMapShape,
  HealthResponse,
  Product,
  SearchRequest,
  SearchResult,
  Shade,
} from '../types';

/** One typed method per plan route; implemented by the live client. */
export interface ApiClient {
  /** GET /api/health */
  getHealth(): Promise<HealthResponse>;
  /** POST /api/searches */
  searchFoundations(request: SearchRequest): Promise<SearchResult>;
  /** GET /api/products */
  listProducts(): Promise<Product[]>;
  /** GET /api/products/{id} */
  getProduct(productId: string): Promise<Product>;
  /** GET /api/products/{id}/shades */
  listProductShades(productId: string): Promise<Shade[]>;
  /** POST /api/shades/{id}/extract-hex */
  extractShadeHex(shadeId: string): Promise<Shade>;
  /** POST /api/color-map */
  generateColorMap(request?: ColorMapRequest): Promise<ColorMap>;
  /** GET /api/color-map; resolves null when none of that shape has been generated (404). */
  getColorMap(shape?: ColorMapShape): Promise<ColorMap | null>;
}
