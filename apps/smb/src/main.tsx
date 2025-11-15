import '@chatscope/chat-ui-kit-styles/dist/default/styles.min.css'
import { MantineProvider, createTheme } from '@mantine/core'
import '@mantine/core/styles.css'
import { Notifications } from '@mantine/notifications'
import '@mantine/notifications/styles.css'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import RequireAuth from './components/RequireAuth'
import { BusinessContextProvider } from './contexts/BusinessContext'
import PlatformLayout from './layouts/PlatformLayout'
import PublicLayout from './layouts/PublicLayout'
import { Achievements } from './pages/Achievements'
import { AdvancedAnalytics } from './pages/AdvancedAnalytics'
import Agents from './pages/Agents'
import { Analytics } from './pages/Analytics'
import CoachV5 from './pages/CoachV5'
import ConnectorsNew from './pages/ConnectorsNew'
import Contact from './pages/Contact'
import Copilot from './pages/Copilot'
import { CustomMetrics } from './pages/CustomMetrics'
import Executor from './pages/Executor'
import { Forecasting } from './pages/Forecasting'
import ForgotPassword from './pages/ForgotPassword'
import Goals from './pages/Goals'
import Home from './pages/Home'
import { Integrations } from './pages/Integrations'
import LandingPage from './pages/LandingPage'
import Login from './pages/Login'
import OAuthCallback from './pages/OAuthCallback'
import Planner from './pages/Planner'
import { Reports } from './pages/Reports'
import Settings from './pages/Settings'
import Signup from './pages/Signup'
import Tools from './pages/Tools'
import Verify from './pages/Verify'
import Welcome from './pages/Welcome'
import './styles.css'

const queryClient = new QueryClient()

// Modern SaaS Design System - Refined & Professional
const theme = createTheme({
    primaryColor: 'brand',
    fontFamily: '"Inter var", Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    fontFamilyMonospace: '"JetBrains Mono", "Fira Code", Consolas, Monaco, "Courier New", monospace',
    headings: {
        fontFamily: '"Inter var", Inter, -apple-system, BlinkMacSystemFont, sans-serif',
        fontWeight: '700',
        sizes: {
            h1: { fontSize: '2.75rem', lineHeight: '1.2', fontWeight: '800' },
            h2: { fontSize: '2rem', lineHeight: '1.3', fontWeight: '700' },
            h3: { fontSize: '1.5rem', lineHeight: '1.4', fontWeight: '600' },
            h4: { fontSize: '1.25rem', lineHeight: '1.4', fontWeight: '600' },
            h5: { fontSize: '1.125rem', lineHeight: '1.5', fontWeight: '600' },
            h6: { fontSize: '1rem', lineHeight: '1.5', fontWeight: '600' },
        },
    },
    colors: {
        // Premium indigo brand - more vibrant and professional
        brand: [
            '#F0F1FF',  // 50
            '#E0E2FF',  // 100
            '#C7CBFF',  // 200
            '#A5ABFF',  // 300
            '#8188FF',  // 400
            '#6366F1',  // 500 - Primary
            '#5558E3',  // 600
            '#4A4DD1',  // 700
            '#3E41B8',  // 800
            '#31349A',  // 900
        ],
        // Sophisticated neutrals - better contrast
        dark: [
            '#F8F9FA',  // 50
            '#F1F3F5',  // 100
            '#E9ECEF',  // 200
            '#DEE2E6',  // 300
            '#CED4DA',  // 400
            '#ADB5BD',  // 500
            '#868E96',  // 600
            '#495057',  // 700
            '#343A40',  // 800
            '#212529',  // 900
        ],
        // Success green - more trustworthy
        green: [
            '#ECFDF5',
            '#D1FAE5',
            '#A7F3D0',
            '#6EE7B7',
            '#34D399',
            '#10B981',  // Primary
            '#059669',
            '#047857',
            '#065F46',
            '#064E3B',
        ],
        // Alert states - balanced
        yellow: [
            '#FFFBEB',
            '#FEF3C7',
            '#FDE68A',
            '#FCD34D',
            '#FBBF24',
            '#F59E0B',  // Primary
            '#D97706',
            '#B45309',
            '#92400E',
            '#78350F',
        ],
        red: [
            '#FEF2F2',
            '#FEE2E2',
            '#FECACA',
            '#FCA5A5',
            '#F87171',
            '#EF4444',  // Primary
            '#DC2626',
            '#B91C1C',
            '#991B1B',
            '#7F1D1D',
        ],
        // Accent colors
        violet: [
            '#F5F3FF',
            '#EDE9FE',
            '#DDD6FE',
            '#C4B5FD',
            '#A78BFA',
            '#8B5CF6',  // Primary
            '#7C3AED',
            '#6D28D9',
            '#5B21B6',
            '#4C1D95',
        ],
        teal: [
            '#F0FDFA',
            '#CCFBF1',
            '#99F6E4',
            '#5EEAD4',
            '#2DD4BF',
            '#14B8A6',  // Primary
            '#0D9488',
            '#0F766E',
            '#115E59',
            '#134E4A',
        ],
    },
    defaultRadius: 'md',
    radius: {
        xs: '0.375rem',   // 6px
        sm: '0.5rem',     // 8px
        md: '0.75rem',    // 12px
        lg: '1rem',       // 16px
        xl: '1.5rem',     // 24px
    },
    spacing: {
        xs: '0.625rem',   // 10px
        sm: '0.75rem',    // 12px
        md: '1rem',       // 16px
        lg: '1.25rem',    // 20px
        xl: '1.5rem',     // 24px
    },
    shadows: {
        xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        sm: '0 2px 8px 0 rgba(0, 0, 0, 0.08), 0 1px 3px 0 rgba(0, 0, 0, 0.04)',
        md: '0 4px 16px 0 rgba(0, 0, 0, 0.12), 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
        lg: '0 12px 32px 0 rgba(0, 0, 0, 0.15), 0 4px 8px 0 rgba(0, 0, 0, 0.08)',
        xl: '0 24px 48px 0 rgba(0, 0, 0, 0.18), 0 8px 16px 0 rgba(0, 0, 0, 0.10)',
    },
    white: '#FFFFFF',
    black: '#0A0A0A',
    other: {
        // Custom design tokens
        borderRadius: {
            card: '1rem',
            button: '0.75rem',
            input: '0.625rem',
            modal: '1.25rem',
        },
        transition: {
            fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
            base: '250ms cubic-bezier(0.4, 0, 0.2, 1)',
            slow: '350ms cubic-bezier(0.4, 0, 0.2, 1)',
        },
    },
    components: {
        Button: {
            defaultProps: {
                radius: 'md',
            },
            styles: {
                root: {
                    fontWeight: 600,
                    transition: 'all 200ms cubic-bezier(0.4, 0, 0.2, 1)',
                    '&:hover': {
                        transform: 'translateY(-1px)',
                    },
                    '&:active': {
                        transform: 'translateY(0)',
                    },
                },
            },
        },
        Card: {
            defaultProps: {
                radius: 'lg',
                withBorder: true,
            },
            styles: {
                root: {
                    transition: 'all 200ms ease',
                },
            },
        },
        Input: {
            defaultProps: {
                radius: 'md',
            },
            styles: {
                input: {
                    fontSize: '0.9375rem',
                    '&:focus': {
                        borderColor: '#6366F1',
                    },
                },
            },
        },
        Modal: {
            defaultProps: {
                radius: 'xl',
                overlayProps: { opacity: 0.55, blur: 3 },
            },
        },
        Badge: {
            defaultProps: {
                radius: 'sm',
            },
            styles: {
                root: {
                    fontWeight: 600,
                    textTransform: 'none',
                },
            },
        },
    },
})

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <MantineProvider theme={theme} defaultColorScheme="light">
                <Notifications position="top-right" />
                <BusinessContextProvider>
                    <BrowserRouter future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
                        <Routes>
                            {/* Public Routes - Anonymous Access */}
                            <Route
                                path="/"
                                element={
                                    <PublicLayout>
                                        <LandingPage />
                                    </PublicLayout>
                                }
                            />
                            <Route
                                path="/signup"
                                element={
                                    <PublicLayout showNav={false}>
                                        <Signup />
                                    </PublicLayout>
                                }
                            />
                            <Route
                                path="/login"
                                element={
                                    <PublicLayout showNav={false}>
                                        <Login />
                                    </PublicLayout>
                                }
                            />
                            <Route
                                path="/forgot-password"
                                element={
                                    <PublicLayout showNav={false}>
                                        <ForgotPassword />
                                    </PublicLayout>
                                }
                            />
                            <Route
                                path="/verify"
                                element={
                                    <PublicLayout showNav={false}>
                                        <Verify />
                                    </PublicLayout>
                                }
                            />
                            <Route
                                path="/auth/:provider/callback"
                                element={
                                    <PublicLayout showNav={false}>
                                        <OAuthCallback />
                                    </PublicLayout>
                                }
                            />
                            <Route
                                path="/contact"
                                element={
                                    <PublicLayout>
                                        <Contact />
                                    </PublicLayout>
                                }
                            />
                            <Route
                                path="/tools"
                                element={
                                    <PublicLayout>
                                        <Tools />
                                    </PublicLayout>
                                }
                            />

                            {/* Platform Routes - Authenticated Access */}
                            <Route
                                path="/welcome"
                                element={
                                    <RequireAuth>
                                        <PublicLayout showNav={false}>
                                            <Welcome />
                                        </PublicLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/home"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <Home />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/copilot"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <Copilot />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/planner"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <Planner />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/connectors"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <ConnectorsNew />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            {/* Legacy redirect - marketplace now unified with connectors */}
                            <Route
                                path="/marketplace"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <ConnectorsNew />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/agents"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <Agents />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/goals"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <Goals />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/executor"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <Executor />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/settings"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <Settings />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/coach"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <CoachV5 />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/coach/:chatId"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <CoachV5 />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/coach-v5"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <CoachV5 />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/analytics"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <Analytics />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/advanced-analytics"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <AdvancedAnalytics />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/reports"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <Reports />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/custom-metrics"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <CustomMetrics />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/forecasting"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <Forecasting />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/integrations"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <Integrations />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                            <Route
                                path="/achievements"
                                element={
                                    <RequireAuth>
                                        <PlatformLayout>
                                            <Achievements />
                                        </PlatformLayout>
                                    </RequireAuth>
                                }
                            />
                        </Routes>
                    </BrowserRouter>
                </BusinessContextProvider>
            </MantineProvider>
        </QueryClientProvider>
    )
}

createRoot(document.getElementById('root')!).render(<App />)
