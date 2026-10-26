import { Caption1, Divider, Subtitle1, Tab, TabList, Toolbar, ToolbarButton, makeStyles, tokens } from '@fluentui/react-components';
import {
  ChartMultipleRegular,
  GridRegular,
  SearchRegular,
  WeatherMoonRegular,
  WeatherSunnyRegular,
} from '@fluentui/react-icons';
import { motion, useReducedMotion } from 'framer-motion';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAppTheme } from '../theme/ThemeProvider';
import { PreviewStateSwitcher } from './PreviewStateSwitcher';

const useStyles = makeStyles({
  root: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
  },
  header: {
    position: 'sticky',
    top: 0,
    zIndex: 10,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: `${tokens.spacingVerticalS} ${tokens.spacingHorizontalXXL}`,
    backgroundColor: tokens.colorNeutralBackground1,
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    boxShadow: tokens.shadow4,
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalM,
  },
  logo: {
    display: 'grid',
    placeItems: 'center',
    width: '28px',
    height: '28px',
    borderRadius: tokens.borderRadiusMedium,
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
    fontSize: tokens.fontSizeBase200,
    fontWeight: tokens.fontWeightBold,
  },
  nav: {
    padding: `${tokens.spacingVerticalXS} ${tokens.spacingHorizontalXXL}`,
    backgroundColor: tokens.colorNeutralBackground2,
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
  },
  main: {
    flex: 1,
    width: '100%',
    maxWidth: '1180px',
    margin: '0 auto',
    padding: `${tokens.spacingVerticalXXL} ${tokens.spacingHorizontalXXL}`,
    boxSizing: 'border-box',
  },
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: `${tokens.spacingVerticalM} ${tokens.spacingHorizontalXXL}`,
    color: tokens.colorNeutralForeground3,
  },
});

const ROUTES = [
  { path: '/', label: 'Search', icon: <SearchRegular /> },
  { path: '/products', label: 'Products', icon: <GridRegular /> },
  { path: '/map', label: 'Shade Map', icon: <ChartMultipleRegular /> },
];

export function AppShell() {
  const styles = useStyles();
  const location = useLocation();
  const navigate = useNavigate();
  const { resolved, toggle } = useAppTheme();
  const reduceMotion = useReducedMotion();

  return (
    <div className={styles.root}>
      <header className={styles.header}>
        <div className={styles.brand}>
          <span className={styles.logo} aria-hidden="true">
            SM
          </span>
          <Subtitle1>Shade Map</Subtitle1>
        </div>
        <Toolbar aria-label="App actions">
          <ToolbarButton
            appearance="subtle"
            aria-label={resolved === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
            icon={resolved === 'dark' ? <WeatherSunnyRegular /> : <WeatherMoonRegular />}
            onClick={toggle}
          />
        </Toolbar>
      </header>
      <nav className={styles.nav} aria-label="Primary">
        <TabList
          selectedValue={location.pathname}
          onTabSelect={(_event, data) => navigate(String(data.value))}
        >
          {ROUTES.map((route) => (
            <Tab key={route.path} value={route.path} icon={route.icon}>
              {route.label}
            </Tab>
          ))}
        </TabList>
      </nav>
      <motion.main
        key={location.pathname}
        className={styles.main}
        initial={reduceMotion ? false : { opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.22, ease: [0.4, 0, 0.2, 1] }}
      >
        <Outlet />
      </motion.main>
      <Divider />
      <footer className={styles.footer}>
        <Caption1>© Shade Map</Caption1>
        <Caption1>v0.1.0</Caption1>
      </footer>
      <PreviewStateSwitcher />
    </div>
  );
}
