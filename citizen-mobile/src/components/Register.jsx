import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { UserPlus, Mail, Lock, User, MapPin, Building2, ArrowRight, Calendar, Home, Phone } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { useNavigate, Link } from 'react-router-dom';

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    phone: '',
    district: '',
    station: '',
    dob: '',
    address: ''
  });
  const [stations, setStations] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();

  useEffect(() => {
    const fetchStations = async () => {
      try {
        const response = await api.get('/api/police/stations');
        setStations(response.data);
      } catch (err) {
        console.error('Failed to fetch stations:', err);
      }
    };
    fetchStations();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    const result = await register({
      name: formData.name,
      email: formData.email,
      password: formData.password,
      phone: formData.phone,
      district: formData.district,
      policeStation: formData.station,
      dob: formData.dob,
      address: formData.address
    });

    if (result.success) {
      navigate('/login');
    } else {
      setError(result.message);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-slate-950">
      <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80')] bg-cover bg-center opacity-10"></div>
      
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card w-full max-w-md p-8 relative z-10"
      >
        <div className="flex flex-col items-center mb-6">
          <div className="w-14 h-14 bg-cyan-500/20 rounded-full flex items-center justify-center mb-3 glow-border">
            <UserPlus size={28} className="text-cyan-400" />
          </div>
          <h1 className="text-xl font-black text-white tracking-widest">CITIZEN ENROLLMENT</h1>
          <p className="text-cyan-500 text-[10px] tracking-[4px] uppercase mt-1">Biometric Uplink Protocol</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-500 p-3 rounded-lg text-xs mb-4 text-center">
            {error.toUpperCase()}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            <div className="relative">
              <User size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="FULL LEGAL NAME"
                className="input-cyber pl-12 py-3"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
              />
            </div>

            <div className="relative">
              <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="email"
                placeholder="SECURE EMAIL"
                className="input-cyber pl-12 py-3"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="relative">
                <Phone size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="text"
                  placeholder="PHONE"
                  className="input-cyber pl-11 py-3"
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  required
                />
              </div>
              <div className="relative">
                <Calendar size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="date"
                  className="input-cyber pl-11 py-3 text-slate-400"
                  value={formData.dob}
                  onChange={(e) => setFormData({...formData, dob: e.target.value})}
                  required
                />
              </div>
            </div>

            <div className="relative">
              <MapPin size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="DISTRICT"
                className="input-cyber pl-12 py-3"
                value={formData.district}
                onChange={(e) => setFormData({...formData, district: e.target.value})}
                required
              />
            </div>

            <div className="relative">
              <Building2 size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
              <select
                className="input-cyber pl-12 py-3 appearance-none"
                value={formData.station}
                onChange={(e) => setFormData({...formData, station: e.target.value})}
                required
              >
                <option value="">HOME POLICE STATION</option>
                {stations.map(s => (
                  <option key={s.id} value={s.name} className="bg-slate-900">
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="relative">
              <Home size={16} className="absolute left-4 top-4 text-slate-500" />
              <textarea
                placeholder="RESIDENTIAL ADDRESS"
                className="input-cyber pl-12 py-3 min-h-[80px]"
                value={formData.address}
                onChange={(e) => setFormData({...formData, address: e.target.value})}
                required
              ></textarea>
            </div>

            <div className="relative">
              <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="password"
                placeholder="SECURITY KEYPHRASE"
                className="input-cyber pl-12 py-3"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
              />
            </div>
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="btn-cyber w-full py-4 mt-4 !bg-cyan-600 hover:!bg-cyan-500"
          >
            {loading ? "PROCESSING..." : (
              <>
                ESTABLISH CITIZEN IDENTITY <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        <p className="text-center text-slate-500 text-[10px] mt-6 tracking-widest">
          ALREADY ENROLLED? <Link to="/login" className="text-cyan-400 font-bold">AUTHORIZE UPLINK</Link>
        </p>
      </motion.div>
    </div>
  );
};

export default Register;
