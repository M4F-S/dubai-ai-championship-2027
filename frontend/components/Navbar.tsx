'use client';

import React from 'react';
import { AgentType } from '../lib/types';

interface NavbarProps {
  currentAgent: AgentType;
  onSelectAgent: (agent: AgentType) => void;
  isArabic: boolean;
  onToggleLanguage: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentAgent,
  onSelectAgent,
  isArabic,
  onToggleLanguage,
}) => {
  return (
    <header className="h-16 px-6 flex items-center justify-between bg-surface/90 backdrop-blur-xl border-b border-white/10 z-50">
      <div className="flex items-center gap-4">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-gold to-amber-600 flex items-center justify-center font-extrabold text-background text-lg shadow-lg shadow-gold/20">
          D
        </div>
        <div>
          <div className="text-sm font-bold tracking-wide text-white">
            {isArabic ? 'بطولة دبي للذكاء الاصطناعي ٢٠٢٧' : 'DUBAI AI AGENTS CHAMPIONSHIP 2027'}
          </div>
          <div className="text-[11px] text-slate-400 font-mono tracking-wider uppercase">
            {isArabic ? 'قمرة القيادة السيادية لنواة C99 البرمجية' : 'Bare-Metal C99 Sovereign Agent Cockpit'}
          </div>
        </div>
      </div>

      <nav className="flex bg-background/80 border border-white/10 rounded-xl p-1 gap-1">
        <button
          onClick={() => onSelectAgent('taryaq')}
          className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
            currentAgent === 'taryaq'
              ? 'bg-elevated text-white border border-gold/40 shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-emerald shadow-[0_0_8px_#10b981]" />
          {isArabic ? 'الـتِـرْيـاق (الصحي)' : 'TARYAQ (Societal)'}
        </button>

        <button
          onClick={() => onSelectAgent('qala')}
          className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
            currentAgent === 'qala'
              ? 'bg-elevated text-white border border-gold/40 shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-cyan shadow-[0_0_8px_#06b6d4]" />
          {isArabic ? 'الـقَـلْـعَـة (الأعمال)' : 'QALA (Business)'}
        </button>

        <button
          onClick={() => onSelectAgent('nibras')}
          className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
            currentAgent === 'nibras'
              ? 'bg-elevated text-white border border-gold/40 shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-purple-500 shadow-[0_0_8px_#8b5cf6]" />
          {isArabic ? 'الـنِّـبْـراس (الشخصي)' : 'NIBRAS (Personal)'}
        </button>
      </nav>

      <div className="flex items-center gap-3">
        <span className="px-2.5 py-1 rounded bg-emerald/10 text-emerald border border-emerald/30 font-mono text-[11px] font-bold flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald animate-pulse" />
          C99 SHIELD: &lt;0.02ms
        </span>
        <span className="px-2.5 py-1 rounded bg-cyan/10 text-cyan border border-cyan/30 font-mono text-[11px] font-bold">
          AIR-GAP: 0 B
        </span>
        <button
          onClick={onToggleLanguage}
          className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-semibold text-white transition-all hover:border-gold"
        >
          {isArabic ? '🌐 English (LTR)' : '🌐 العربية (RTL)'}
        </button>
      </div>
    </header>
  );
};
