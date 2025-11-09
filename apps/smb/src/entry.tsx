import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './styles.css'

import Footer from './components/Footer'
import Header from './components/Header'
import Home from './pages/Home'
import LandingPage from './pages/LandingPage'
import Signup from './pages/Signup'
import Tools from './pages/Tools'
import Verify from './pages/Verify'

function App() {
    return (
        <BrowserRouter>
            <div className="app-root">
                <Header />
                <main className="app-main">
                    <Routes>
                        <Route path="/" element={<LandingPage />} />
                        <Route path="/home" element={<Home />} />
                        <Route path="/signup" element={<Signup />} />
                        <Route path="/verify" element={<Verify />} />
                        <Route path="/tools" element={<Tools />} />
                    </Routes>
                </main>
                <Footer />
            </div>
        </BrowserRouter>
    )
}

createRoot(document.getElementById('root')!).render(<App />)
