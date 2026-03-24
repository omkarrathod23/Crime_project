import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, Mail, ArrowRight, UserPlus } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';

const Login = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    const result = await login(email, password);
    if (result.success) {
      navigate('/');
    } else {
      setError(result.message);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-slate-950">
      <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&q=80')] bg-cover bg-center opacity-20 backdrop-blur-sm"></div>
      
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card w-full max-w-md p-8 relative z-10"
      >
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-cyan-500/20 rounded-full flex items-center justify-center mb-4 glow-border">
            <Shield size={32} className="text-cyan-400" />
          </div>
          <h1 className="text-2xl font-black text-white tracking-[2px]">SENTINEL-X</h1>
          <p className="text-cyan-500 text-xs tracking-[4px] uppercase mt-1">Citizen Uplink Portal</p>
        </div>

        {error && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="bg-red-500/10 border border-red-500/30 text-red-500 p-3 rounded-lg text-xs mb-6 text-center"
          >
            {error.toUpperCase()}
          </motion.div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <Mail size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="email"
              placeholder="REGISTERED EMAIL"
              className="input-cyber pl-12"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="relative">
            <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="password"
              placeholder="SECURITY KEYPHRASE"
              className="input-cyber pl-12"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="btn-cyber w-full py-4 mt-6 !bg-cyan-600 hover:!bg-cyan-500"
          >
            {loading ? "AUTHORIZING..." : (
              <>
                ESTABLISH UPLINK <ArrowRight size={20} />
              </>
            )}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-white/5 flex flex-col items-center gap-4">
          <p className="text-slate-500 text-[10px] tracking-widest uppercase text-center">
            NEW OPERATIVE? <Link to="/register" className="text-cyan-400 font-bold ml-2">INITIALIZE ENROLLMENT</Link>
          </p>
          <div className="flex items-center gap-2 text-[10px] text-slate-600 font-bold uppercase tracking-[2px]">
            <Shield size={12} className="text-slate-600" />
            SECURED BY SENTINEL PROTOCOL 4.2B
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
