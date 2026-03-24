import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Calendar, 
  ShieldCheck, 
  ChevronLeft,
  Camera,
  Edit3,
  LogOut,
  Building2
} from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

const Profile = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-950 pb-20 text-slate-300">
      <header className="p-6 flex items-center gap-4 border-b border-white/5 bg-slate-950/80 sticky top-0 z-30 backdrop-blur-xl">
        <button onClick={() => navigate('/')} className="p-2.5 bg-white/5 rounded-xl text-slate-400 active:bg-cyan-500 active:text-white transition-all">
          <ChevronLeft size={20} />
        </button>
        <div>
          <h2 className="text-xs font-black text-white tracking-[3px] uppercase italic">Operative Profile</h2>
          <p className="text-[9px] text-cyan-500 font-bold uppercase tracking-widest mt-0.5">Citizen Identity Node</p>
        </div>
      </header>

      <main className="p-6 space-y-6">
        {/* Profile Card */}
        <section className="glass-card p-8 border-l-4 border-l-cyan-500 relative overflow-hidden group">
          <div className="flex flex-col items-center">
            <div className="relative mb-4">
              <div className="w-24 h-24 rounded-full bg-slate-900 border-2 border-cyan-500/30 flex items-center justify-center overflow-hidden">
                {user?.face_image ? (
                  <img src={user.face_image} alt="Profile" className="w-full h-full object-cover" />
                ) : (
                  <User size={48} className="text-slate-700" />
                )}
              </div>
              <button className="absolute bottom-0 right-0 p-2 bg-cyan-500 rounded-full border-4 border-slate-950 hover:bg-cyan-400 transition-colors">
                <Camera size={14} className="text-white" />
              </button>
            </div>
            <h3 className="text-xl font-black text-white uppercase italic">{user?.name}</h3>
            <div className="flex items-center gap-2 mt-2">
              <ShieldCheck size={14} className="text-green-500" />
              <span className="text-[10px] text-green-500 font-black uppercase tracking-widest">Verified Citizen</span>
            </div>
          </div>
        </section>

        {/* Data Points */}
        <section className="space-y-3">
          <h4 className="text-[10px] text-slate-500 font-black tracking-[4px] uppercase ml-1">Identity Metrics</h4>
          
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center gap-4">
              <div className="p-2.5 bg-slate-900 rounded-lg text-slate-500">
                <Mail size={18} />
              </div>
              <div>
                <p className="text-[8px] text-slate-500 font-black uppercase tracking-widest">Uplink Identifier</p>
                <p className="text-sm font-bold text-white">{user?.email}</p>
              </div>
            </div>

            <div className="flex items-center gap-4 border-t border-white/5 pt-4">
              <div className="p-2.5 bg-slate-900 rounded-lg text-slate-500">
                <Phone size={18} />
              </div>
              <div>
                <p className="text-[8px] text-slate-500 font-black uppercase tracking-widest">Emergency Contact</p>
                <p className="text-sm font-bold text-white">{user?.phone || 'NOT LINKED'}</p>
              </div>
            </div>

            <div className="flex items-center gap-4 border-t border-white/5 pt-4">
              <div className="p-2.5 bg-slate-900 rounded-lg text-slate-500">
                <MapPin size={18} />
              </div>
              <div>
                <p className="text-[8px] text-slate-500 font-black uppercase tracking-widest">Sector / District</p>
                <p className="text-sm font-bold text-white uppercase">{user?.district || 'UNCLASSIFIED'}</p>
              </div>
            </div>

            <div className="flex items-center gap-4 border-t border-white/5 pt-4">
              <div className="p-2.5 bg-slate-900 rounded-lg text-slate-500">
                <Building2 size={18} />
              </div>
              <div>
                <p className="text-[8px] text-slate-500 font-black uppercase tracking-widest">Jurisdiction</p>
                <p className="text-sm font-bold text-white uppercase">{user?.police_station || 'AUTO-SCANNING'}</p>
              </div>
            </div>
          </div>
        </section>

        {/* Action Zone */}
        <div className="grid grid-cols-1 gap-4">
          <motion.button 
            whileTap={{ scale: 0.98 }}
            className="btn-cyber w-full py-4 !bg-slate-800 hover:!bg-slate-700 flex items-center justify-center gap-3"
          >
            <Edit3 size={18} />
            <span className="text-[10px] font-black tracking-[2px] uppercase">Update Identity Data</span>
          </motion.button>

          <motion.button 
            whileTap={{ scale: 0.98 }}
            onClick={logout}
            className="btn-cyber w-full py-4 !bg-red-950/20 border-red-900/40 text-red-500 hover:!bg-red-500/20 flex items-center justify-center gap-3"
          >
            <LogOut size={18} />
            <span className="text-[10px] font-black tracking-[2px] uppercase">Terminate Uplink Session</span>
          </motion.button>
        </div>
      </main>

      <div className="p-10 text-center opacity-20 italic">
        <p className="text-[9px] uppercase tracking-widest font-bold">Protocol v4.2.8-stable</p>
      </div>
    </div>
  );
};

export default Profile;
