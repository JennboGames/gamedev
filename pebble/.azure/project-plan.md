# Project Plan

**Status**: Awaiting Integration
**Created**: 2026-10-26
**Mode**: NEW

---

## 1. Project Overview

**Goal**: A tool that finds skin foundation makeup on Amazon, builds a product list with a sublist of shades per product, extracts a hex color for each shade from its swatch image, and plots every shade on a generated color-map image (red left, yellow right, white top, black bottom). The project is designed so that every module is independently testable.

**App Type**: SPA + API

**API Login**: No

**Mode**: NEW

**Deployment Plan**: No deployment plan found

---

## 2. Foundation Collector API — backend

| Component | Technology |
|-----------|-----------|
| **Language** | Python |
| **Runtime** | CPython |
| **Package Manager** | pip |
| **Test Runner** | pytest |
| **Mocking Library** | unittest.mock |
| **Test Command** | pytest |
| **Orchestration** | docker-compose |

---

## 3. Shade Map Viewer — frontend

| Component | Technology |
|-----------|-----------|
| **Language** | TypeScript |
| **Framework** | React + Vite |
| **Package Manager** | npm |
| **Test Runner** | vitest |
| **Mocking Library** | vi.mock |
| **Test Command** | npm test |

---

## 4. Services Required

| Azure Service | Role in App | Environment Variable | Default Value (Local) | Classification |
|---------------|------------|---------------------|----------------------|----------------|
| Blob Storage | Store downloaded shade swatch images and the generated color-map image | STORAGE_CONNECTION_STRING | UseDevelopmentStorage=true | Essential |
| PostgreSQL | Primary data store for products, shades, hex colors, and map positions | DATABASE_URL | postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/foundationdb | Essential |
| Amazon Product Advertising API (external) | Search foundation products and fetch shade variations and swatch image URLs | AMAZON_PAAPI_ACCESS_KEY, AMAZON_PAAPI_SECRET_KEY, AMAZON_PARTNER_TAG | _(no local emulator; use recorded fixtures in tests)_ | Essential |

---

## 5. Prerequisites

### Run

| Tool | Service(s) | Installed | Version |
|------|-----------|-----------|---------|
| Node.js | shade-map-web | ❓ | — |
| npm | shade-map-web | ❓ | — |
| Python | foundation-api | ❓ | — |
| pip | foundation-api | ❓ | — |
| Azure Functions Core Tools | foundation-api | ❓ | — |

### Debug

| Tool | Service(s) | Installed | Version |
|------|-----------|-----------|---------|
| Docker | foundation-api | ❓ | — |
| Docker Compose | foundation-api | ❓ | — |
| Chrome | shade-map-web | ✅ | 156.0.8078.47 |
| ms-azuretools.vscode-azurefunctions | foundation-api | ❓ | — |

---

## 6. Design System & UI

**Component Library**: Fluent UI v9
**Style Direction**: Clean, cosmetics-counter feel: warm neutral surfaces so swatches are the most colorful thing on screen, soft 10px corners, light elevation, and scannable product rows with compact shade chips.
**Typography**: Segoe UI Variable, system-ui

### Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `primary` | `#8c3f52` | Search and Plot buttons, active nav, links to product pages |
| `accent` | `#d9a066` | Highlights for the selected shade marker and sand-toned badges |
| `surface` | `#faf6f2` | Page background and the shade-map canvas frame |
| `text` | `#2b2321` | Product names, brand names, hex codes |
| `muted` | `#7a6d68` | Shade counts, ASINs, secondary captions |
| `border` | `#e6dcd5` | Product card borders, shade chip outlines, table dividers |

### Pages

| Page | Route | Purpose | Layout |
|------|-------|---------|--------|
| Search | `/` | Enter a foundation search term and start collecting products from Amazon | `header, nav, hero, form, empty, footer` |
| Products | `/products` | Browse found foundations; expand a product to see its shades with extracted hex swatches | `header, nav, tabs, card-list, loading (skeleton), footer` |
| Shade Map | `/map` | View the generated color-map image with every shade plotted as a marker, plus a legend table | `header, nav, error (inline banner), split(table|main), action-bar, footer` |

> **Layout tokens are layout INTENT, not implementation.** The scaffold agent renders them using `Component Library` primitives. Recognized tokens: `header, nav, sidebar, hero, main, list, card-list, grid, form, table, actions, action-bar, tabs, modal, footer`. Compound tokens: `split(a|b)` (1:2 columns), `two-column(a+b)` (1:1 columns).

### Sample Content

```
Search — recent searches (empty state shown for results):
Search term: "skin foundation" · Max products: 20 · Category: Beauty > Makeup > Foundation
Empty state: "No foundations collected yet" — "Search Amazon to build your first product list."

Products — foundation:
| Product                                            | Brand        | Shades | Status      |
| Double Wear Stay-in-Place Foundation (B0GQVP8RLD)  | Estée Lauder | 42     | Collected   |
| Fit Me Matte + Poreless Foundation                 | Maybelline   | 40     | Collected   |
| Studio Fix Fluid SPF 15 Foundation                 | MAC          | 38     | Extracting  |
| True Match Super-Blendable Foundation              | L'Oréal      | 33     | Collected   |
| Soft Matte Complete Foundation                     | NYX          | 24     | Collected   |
Expanded sublist — Double Wear shades:
| Shade           | Hex      |
| 1N1 Ivory Nude  | #F1D2B5  |
| 2W1 Dawn        | #E6BE98  |
| 3C2 Pebble      | #D7A67F  |
| 4N2 Spiced Sand | #BC8760  |
| 6N2 Truffle     | #7A4A32  |

Shade Map — plotted shades:
| Shade           | Product              | Hex      | Hue (x) | Lightness (y) |
| 1N1 Ivory Nude  | Double Wear          | #F1D2B5  | 28°     | 81%           |
| 220 Natural Beige | Fit Me Matte       | #D9A77E  | 28°     | 65%           |
| N5 Golden       | Studio Fix Fluid     | #C58B58  | 30°     | 55%           |
| W6 Rich Caramel | True Match           | #A56D45  | 26°     | 43%           |
| Espresso        | Soft Matte Complete  | #4B2E22  | 19°     | 21%           |
Error banner: "Couldn't load swatch for 3C2 Pebble" — "The swatch image could not be downloaded; Retry fetches it again."
```

---

## 7. Project Structure

```
pebble/
├── .azure/
│   └── project-plan.md
├── .env.example
├── .gitignore
├── docker-compose.yml                  ← Azurite + PostgreSQL emulators
├── api/                                ← Foundation Collector API (Azure Functions, Python)
│   ├── host.json
│   ├── local.settings.json
│   ├── requirements.txt
│   ├── function_app.py                 ← Function registration
│   ├── src/
│   │   ├── functions/                  ← One handler module per route
│   │   ├── services/
│   │   │   ├── interfaces/             ← ProductSearch, ShadeRepository, BlobStore, ColorExtractor
│   │   │   ├── amazon_paapi.py         ← Amazon Product Advertising API client
│   │   │   ├── color_extractor.py      ← Swatch image → dominant hex (Pillow)
│   │   │   ├── color_map.py            ← Generates map image, hue/lightness → x/y
│   │   │   ├── config.py
│   │   │   └── registry.py
│   │   ├── errors/
│   │   └── models/
│   ├── migrations/
│   └── tests/
│       ├── fixtures/                   ← Recorded Amazon responses, sample swatches
│       ├── mocks/
│       ├── services/
│       └── functions/
└── web/                                ← Shade Map Viewer (React + Vite, TypeScript)
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── api/client.ts               ← Typed API client
        ├── components/                 ← ProductCard, ShadeSublist, ShadeChip, MapCanvas
        ├── pages/                      ← SearchPage, ProductsPage, ShadeMapPage
        └── hooks/
```

---

## 8. Route Definitions

| # | Method | Path | Description | Request Body | Response Body | Status Codes |
|---|--------|------|-------------|-------------|--------------|-------------|
| 1 | GET | `/api/health` | Health check | — | `{ status, services }` | 200, 503 |
| 2 | POST | `/api/searches` | Search Amazon for foundation products, store products and shades, extract hex per shade | `{ query, maxProducts? }` | `{ searchId, products[] }` | 201, 422, 502 |
| 3 | GET | `/api/products` | List collected products with shade counts | — | `{ items: Product[] }` | 200 |
| 4 | GET | `/api/products/{id}` | Get one product | — | `Product` | 200, 404 |
| 5 | GET | `/api/products/{id}/shades` | List shades of a product with hex colors | — | `{ items: Shade[] }` | 200, 404 |
| 6 | POST | `/api/shades/{id}/extract-hex` | Re-download the swatch and re-extract its hex | — | `Shade` | 200, 404, 502 |
| 7 | POST | `/api/color-map` | Generate the color-map image and plot all shades by hex | `{ productIds? }` | `{ imageUrl, width, height, markers[] }` | 201, 404 |
| 8 | GET | `/api/color-map` | Get the latest color-map image metadata and marker positions | — | `{ imageUrl, width, height, markers[] }` | 200, 404 |

---

## 9. Next Steps

1. Run **azure-project-scaffold** to execute this plan
2. Run **azure-project-integrate** to wire the frontend to live data, smoke-test the backend, and create the migrations
3. Run **azure-debug-plan** → **azure-debug-generate** for Docker emulators and VS Code debugging
4. Run the **azure-deploy** agent when ready; it uses **azure-app-onboard** for architecture, cost estimation, IaC generation, provisioning, and health verification
