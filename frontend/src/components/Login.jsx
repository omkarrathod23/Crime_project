import React, { useState } from 'react';
import './Login.css';

const Login = ({ onBack, onLoginSuccess, initialRole = 'citizen' }) => {
    const [role, setRole] = useState(initialRole);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleLogin = (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        
        // Simulate API call
        setTimeout(() => {
            setLoading(false);
            if (email && password) {
                onLoginSuccess(role);
            } else {
                setError('Invalid credentials. Please try again.');
            }
        }, 1500);
    };

    return (
        <div className="login-wrapper">
            <div className="mesh-gradient"></div>
            
            <button className="glass-back-btn" onClick={onBack}>
                <span className="arrow">←</span> Back
            </button>

            <div className="login-card-container">
                <div className="login-glass-card">
                    <div className="login-header">
                        <div className="brand-logo">🛡️</div>
                        <h1>{role.charAt(0).toUpperCase() + role.slice(1)} Login</h1>
                        <p>Enter your credentials to access the secure portal</p>
                    </div>

                    <div className="role-selector-wrapper">
                        <div className={`role-slider active-${role}`}></div>
                        <button 
                            className={`role-tab ${role === 'citizen' ? 'active' : ''}`}
                            onClick={() => setRole('citizen')}
                        >Citizen</button>
                        <button 
                            className={`role-tab ${role === 'police' ? 'active' : ''}`}
                            onClick={() => setRole('police')}
                        >Police</button>
                        <button 
                            className={`role-tab ${role === 'admin' ? 'active' : ''}`}
                            onClick={() => setRole('admin')}
                        >Admin</button>
                    </div>

                    <form className="login-form" onSubmit={handleLogin}>
                        <div className="input-group-premium">
                            <input 
                                type="email" 
                                required 
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder=" "
                            />
                            <label>Email Address</label>
                            <div className="input-line"></div>
                        </div>

                        <div className="input-group-premium">
                            <input 
                                type="password" 
                                required 
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder=" "
                            />
                            <label>Password</label>
                            <div className="input-line"></div>
                        </div>

                        {error && <div className="error-message-glass">{error}</div>}

                        <button className={`login-submit-btn ${role}`} disabled={loading}>
                            {loading ? (
                                <div className="loader-dots">
                                    <span></span><span></span><span></span>
                                </div>
                            ) : (
                                `Access ${role.charAt(0).toUpperCase() + role.slice(1)} Portal`
                            )}
                        </button>
                    </form>

                    <div className="login-footer">
                        {role === 'citizen' && (
                            <p>New here? <a href="#register">Create an account</a></p>
                        )}
                        <p><a href="#forgot">Forgot password?</a></p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
