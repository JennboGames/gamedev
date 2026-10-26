import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { ProductsPage } from './pages/ProductsPage';
import { SearchPage } from './pages/SearchPage';
import { ShadeMapPage } from './pages/ShadeMapPage';

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<SearchPage />} />
        <Route path="products" element={<ProductsPage />} />
        <Route path="map" element={<ShadeMapPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
