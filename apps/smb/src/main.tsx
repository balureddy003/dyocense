import { MantineProvider, createTheme } from '@mantine/core'
import '@mantine/core/styles.css'
import { Notifications } from '@mantine/notifications'
import '@mantine/notifications/styles.css'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import RequireAuth from './components/RequireAuth'
import PlatformLayout from './layouts/PlatformLayout'
import PublicLayout from './layouts/PublicLayout'
import Agents from './pages/Agents'
import Connectors from './pages/Connectors'
import Contact from './pages/Contact'
import Copilot from './pages/Copilot'
import Executor from './pages/Executor'
import Goals from './pages/Goals'
import Home from './pages/Home'
import LandingPage from './pages/LandingPage'
import Planner from './pages/Planner'
import Signup from './pages/Signup'
import Tools from './pages/Tools'
import Verify from './pages/Verify'
import './styles.css'

const queryClient = new QueryClient()

// Professional SaaS theme
const theme = createTheme({
    primaryColor: 'brand',
    fontFamily: 'Inter var, Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif',
    headings: {
        fontFamily: 'Inter var, Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif',
        fontWeight: 600,
        sizes: {
            h1: { fontSize: '3.5rem', fontWeight: 700 },
            h2: { fontSize: '2.5rem', fontWeight: 700 },
            h3: { fontSize: '1.75rem', fontWeight: 600 },
        },
    },
    colors: {
        brand: ['#EEF2FF', '#E0E7FF', '#C7D2FE', '#A5B4FC', '#818CF8', '#6366F1', '#4F46E5', '#4338CA', '#3730A3', '#312E81'],
        night: ['#EDF1F6', '#D7DEEA', '#BCC8DA', '#9FB1CA', '#839AB9', '#687EA1', '#4D6288', '#394B6B', '#26344E', '#101522'],
        neutral: ['#F9FAFB', '#F3F4F6', '#E5E7EB', '#D1D5DB', '#9CA3AF', '#6B7280', '#4B5563', '#374151', '#1F2937', '#0F172A'],
    },
    defaultRadius: 'lg',
    shadows: {
        xs: '0 1px 2px 0 rgba(15, 18, 27, 0.05)',
        sm: '0 4px 6px rgba(15, 18, 27, 0.08)',
        md: '0 10px 20px rgba(15, 18, 27, 0.12)',
        lg: '0 25px 40px rgba(15, 18, 27, 0.15)',
        xl: '0 35px 60px rgba(15, 18, 27, 0.2)',
    },
    white: '#FFFFFF',
    black: '#050A16',
})

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <MantineProvider theme={theme} defaultColorScheme="light">
                <Notifications position="top-right" />
                <BrowserRouter future={{ v7_relativesplatPath: true, v7_startTransition: true }}>
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
                            path="/verify"
                            element={
                                <PublicLayout showNav={false}>
                                    <Verify />
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
                                        <Connectors />
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
                    </Routes>
                </BrowserRouter>
            </MantineProvider>
        </QueryClientProvider>
    )
}

createRoot(document.getElementById('root')!).render(<App />)
