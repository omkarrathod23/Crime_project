import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Clock, ChevronLeft, Zap, Play, Square, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import SOSModule from './SOSModule';

const SafetyMode = () => {
  const navigate = useNavigate();
  const [isActive, setIsActive] = useState(false);
  const [duration, setDuration] = useState(30); // minutes
  const [timeLeft, setTimeLeft] = useState(0);
  const [showSOS, setShowSOS] = useState(false);
  const [status, setStatus] = useState('idle'); // idle, active, completed

  useEffect(() => {
    let timer;
    if (isActive && timeLeft > 0) {
      timer = setInterval(() => setTimeLeft(prev => prev - 1), 1000);
    } else if (isActive && timeLeft === 0) {
      handleExpire();
    }
    return () => clearInterval(timer);
  }, [isActive, timeLeft]);

  const handleStart = async () => {
    try {
      await api.post('/sos/safety-mode/activate', { duration });
      setTimeLeft(duration * 60);
      setIsActive(true);
      setStatus('active');
    } catch (err) {
      console.error('Failed to activate safety mode');
    }
  };

  const handleCheckIn = async () => {
    try {
      await api.post('/sos/safety-mode/check-in');
      setTimeLeft(duration * 60); // Reset timer
    } catch (err) {
      console.error('Check-in failed');
    }
  };

  const handleDeactivate = async () => {
    try {
      await api.post('/sos/safety-mode/deactivate');
      setIsActive(false);
      setStatus('idle');
    } catch (err) {
      console.error('Deactivation failed');
    }
  };

  const handleExpire = () => {
    setIsActive(false);
    setStatus('completed');
    setShowSOS(true); // Trigger SOS automatically
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-300">
      <header className="p-6 flex items-center gap-4 border-b border-white/5 bg-slate-950/80 sticky top-0 z-30 backdrop-blur-xl">
        <button onClick={() => navigate('/')} className="p-2.5 bg-white/5 rounded-xl text-slate-400">
          <ChevronLeft size={20} />
        </button>
        <div>
          <h2 className="text-xs font-black text-white tracking-[3px] uppercase italic">Guard Protocol</h2>
          <p className="text-[9px] text-cyan-500 font-bold uppercase tracking-widest mt-0.5">Safety Mode Configuration</p>
        </div>
      </header>

      <main className="p-6 space-y-8">
        <section className="glass-card p-8 border-l-4 border-l-cyan-500 relative overflow-hidden text-center">
            <div className="absolute top-0 right-0 p-4 opacity-10">
                <Shield size={120} />
            </div>
            
            <div className={`w-20 h-20 mx-auto rounded-3xl flex items-center justify-center mb-6 border transition-all duration-500 ${isActive ? 'bg-cyan-500/20 border-cyan-500/40 glow-cyan' : 'bg-slate-900 border-white/10'}`}>
                {isActive ? <Zap className="text-cyan-400 animate-pulse" size={40} /> : <Shield className="text-slate-600" size={40} />}
            </div>

            <h3 className="text-xl font-black text-white uppercase italic mb-2">Safety Sentinel</h3>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest max-w-[200px] mx-auto leading-loose">
                Timer-based protection. Failure to check-in will trigger an <span className="text-red-500 font-bold">Automatic SOS</span>.
            </p>
        </section>

        {!isActive ? (
          <section className="space-y-6">
            <div className="space-y-4">
              <label className="text-[10px] text-slate-400 font-black tracking-[4px] uppercase flex justify-between">
                <span>Duration Protocol</span>
                <span className="text-cyan-400">{duration} Minutes</span>
              </label>
              <input 
                type="range" 
                min="5" 
                max="120" 
                step="5"
                value={duration}
                onChange={(e) => setDuration(parseInt(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
              />
              <div className="flex justify-between text-[8px] text-slate-600 font-black uppercase tracking-widest">
                <span>5 MIN</span>
                <span>60 MIN</span>
                <span>120 MIN</span>
              </div>
            </div>

            <button 
                onClick={handleStart}
                className="btn-cyber w-full py-5 !bg-cyan-600 hover:!bg-cyan-500 shadow-[0_10px_30px_rgba(8,145,178,0.3)]"
            >
                Initialize Guard <Play size={20} className="ml-2" />
            </button>
          </section>
        ) : (
          <section className="space-y-8">
            <div className="text-center py-10 glass-card bg-cyan-950/10 border-cyan-500/20">
                <p className="text-[10px] text-cyan-500 font-black tracking-[5px] uppercase mb-4">Countdown in Progress</p>
                <div className="text-6xl font-black text-white font-mono tracking-tighter">
                    {formatTime(timeLeft)}
                </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
                <button 
                    onClick={handleCheckIn}
                    className="glass-card p-6 flex flex-col items-center justify-center gap-3 border-green-500/30 bg-green-500/5 hover:bg-green-500/10 transition-all"
                >
                    <CheckCircle2 className="text-green-500" size={32} />
                    <span className="text-[10px] font-black text-white tracking-[3px] uppercase">I am safe (Reset)</span>
                </button>

                <button 
                    onClick={handleDeactivate}
                    className="glass-card p-6 flex flex-col items-center justify-center gap-3 border-slate-700 bg-slate-800/20 hover:bg-slate-800/40 transition-all"
                >
                    <Square className="text-slate-500" size={32} />
                    <span className="text-[10px] font-black text-white tracking-[3px] uppercase">Terminate Protocol</span>
                </button>
            </div>
          </section>
        )}

        <section className="p-4 bg-white/5 rounded-2xl border border-white/5 flex gap-4 opacity-60">
            <Clock size={20} className="text-slate-500 shrink-0" />
            <p className="text-[9px] text-slate-500 uppercase leading-loose tracking-widest">
                System maintains a persistent link with the <span className="text-cyan-400">Jurisdiction Command</span> while Guard is active.
            </p>
        </section>
      </main>

      <AnimatePresence>
        {showSOS && <SOSModule onClose={() => setShowSOS(false)} />}
      </AnimatePresence>
    </div>
  );
};

export default SafetyMode;
