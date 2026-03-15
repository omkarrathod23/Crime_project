import { useState } from 'react'
import './App.css'
import Login from './components/Login'

function App() {
  const [view, setView] = useState('landing') // landing, login, citizen, police, admin
  const [loginRole, setLoginRole] = useState('citizen')
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  const handlePortalSelect = (portal) => {
    setLoginRole(portal)
    setView('login')
  }

  const handleLoginSuccess = (role) => {
    setView(role)
    setIsLoggedIn(true)
  }

  const handleBack = () => {
    setView('landing')
  }

  if (view === 'landing') {
    return (
      <div className="landing-page">
        <header className="hero-section glass">
          <div className="logo-badge">🛡️</div>
          <h1 className="hero-title">Crime Management System</h1>
          <p className="hero-subtitle">Comprehensive crime reporting, analysis, and management platform</p>
        </header>

        <main className="portal-container">
          <div className="welcome-text">
            <h2>Welcome to the Crime Management System</h2>
            <p className="text-secondary">Choose your portal to access the system</p>
          </div>

          <div className="portal-grid">
            {/* Citizen Portal */}
            <div className="portal-card glass" onClick={() => handlePortalSelect('citizen')}>
              <div className="portal-icon citizen">👤</div>
              <h3>Citizen Portal</h3>
              <p>Report crimes, track FIR status, and access safety information.</p>
              <div className="portal-actions">
                <button className="premium-btn portal-btn citizen">Login</button>
                <button className="outline-btn">Register</button>
              </div>
            </div>

            {/* Police Portal */}
            <div className="portal-card glass" onClick={() => handlePortalSelect('police')}>
              <div className="portal-icon police">👮</div>
              <h3>Police Portal</h3>
              <p>Manage FIRs, update case status, and view department analytics.</p>
              <div className="portal-actions">
                <button className="premium-btn portal-btn police">Login</button>
              </div>
            </div>

            {/* Admin Portal */}
            <div className="portal-card glass" onClick={() => handlePortalSelect('admin')}>
              <div className="portal-icon admin">🛡️</div>
              <h3>Admin Portal</h3>
              <p>Verify locations, assign cases, and manage system operations.</p>
              <div className="portal-actions">
                <button className="premium-btn portal-btn admin">Login</button>
              </div>
            </div>
          </div>
        </main>

        <footer className="footer-simple">
          &copy; 2024 Crime Management System. All rights reserved.
        </footer>
      </div>
    )
  }

  if (view === 'login') {
    return (
      <Login 
        initialRole={loginRole} 
        onBack={handleBack} 
        onLoginSuccess={handleLoginSuccess} 
      />
    )
  }

  // Dashboard View (Placeholder for now)
  return (
    <div className="dashboard-container">
      <button className="back-btn" onClick={handleBack}>← Back to Portals</button>
      <div className="layout">
        {/* Previous dashboard implementation here, or just a simple view */}
        <aside className="sidebar glass">
          <div className="logo-container">
            <div className="logo-icon">🛡️</div>
            <h2>{view.charAt(0).toUpperCase() + view.slice(1)} Portal</h2>
          </div>
          <nav className="nav-menu">
            <button className="nav-item active">Dashboard</button>
            <button className="nav-item">Reports</button>
            <button className="nav-item">Profile</button>
          </nav>
        </aside>

        <main className="main-content">
          <h1 className="gradient-text">{view.charAt(0).toUpperCase() + view.slice(1)} Dashboard</h1>
          <div className="card glass">
            <h3>Welcome, {view}</h3>
            <p>This is your personalized command center. Features are being synchronized from the backend.</p>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
