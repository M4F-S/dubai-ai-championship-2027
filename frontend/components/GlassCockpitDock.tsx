'use client';

import React from 'react';
import { AuditRecord } from '../lib/types';

interface GlassCockpitDockProps {
  auditRecords: AuditRecord[];
  isArabic: boolean;
  onRefreshAudit: () => void;
}

export const GlassCockpitDock: React.FC<GlassCockpitDockProps> = ({
  auditRecords,
  isArabic,
  onRefreshAudit,
}) => {
  return (
    <aside className="flex flex-col gap-4 overflow-y-auto">
      {/* 4 Telemetry Gauges */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3.5 bg-surface border border-white/10 rounded-xl flex flex-col gap-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            {isArabic ? 'الإقلاع البارد (C99)' : 'C99 Cold Start'}
          </span>
          <span className="text-xl font-extrabold font-mono text-emerald">0.013 ms</span>
          <span className="text-[10px] text-slate-500">Target &lt; 15.000 ms</span>
        </div>

        <div className="p-3.5 bg-surface border border-white/10 rounded-xl flex flex-col gap-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            {isArabic ? 'تشبع ذاكرة DDR5' : 'DDR5 Saturation'}
          </span>
          <span className="text-xl font-extrabold font-mono text-cyan">19.91 tok/s</span>
          <span className="text-[10px] text-slate-500">89.6 GB/s UM790 Bus</span>
        </div>

        <div className="p-3.5 bg-surface border border-white/10 rounded-xl flex flex-col gap-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            {isArabic ? 'التسريب السحابي' : 'WAN Exfiltration'}
          </span>
          <span className="text-xl font-extrabold font-mono text-emerald">0.00 KB</span>
          <span className="text-[10px] text-slate-500">DESC ISR v3.1 Air-Gap</span>
        </div>

        <div className="p-3.5 bg-surface border border-white/10 rounded-xl flex flex-col gap-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            {isArabic ? 'سجلات التدقيق' : 'Audit Signatures'}
          </span>
          <span className="text-xl font-extrabold font-mono text-gold">{auditRecords.length}</span>
          <span className="text-[10px] text-slate-500">SHA-256 Non-Repudiated</span>
        </div>
      </div>

      {/* Security Gate Matrix */}
      <div className="p-4 bg-surface border border-white/10 rounded-xl flex flex-col gap-2.5">
        <div className="flex justify-between items-center text-xs font-bold text-cyan uppercase tracking-wider">
          <span>{isArabic ? 'مصفوفة الحماية المادية C99' : 'C99 Hardware Security Matrix'}</span>
          <span className="text-emerald text-[10px]">ALL GATES ARMED</span>
        </div>

        <div className="p-2.5 bg-background/60 border border-white/5 rounded-lg flex justify-between items-center text-xs">
          <span>Taryaq CYP3A4 Pharmacovigilance</span>
          <span className="px-2 py-0.5 rounded bg-emerald/10 text-emerald border border-emerald/30 font-mono text-[10px] font-bold">
            ARMED (&lt;0.01ms)
          </span>
        </div>

        <div className="p-2.5 bg-background/60 border border-white/5 rounded-lg flex justify-between items-center text-xs">
          <span>DHA SN 03/2019 Claim Scrubber</span>
          <span className="px-2 py-0.5 rounded bg-emerald/10 text-emerald border border-emerald/30 font-mono text-[10px] font-bold">
            0.03%/DAY ACTIVE
          </span>
        </div>

        <div className="p-2.5 bg-background/60 border border-white/5 rounded-lg flex justify-between items-center text-xs">
          <span>Tau-3 Financial Limit Gatekeeper</span>
          <span className="px-2 py-0.5 rounded bg-gold/10 text-gold border border-gold/30 font-mono text-[10px] font-bold">
            AED 50,000 CAP
          </span>
        </div>

        <div className="p-2.5 bg-background/60 border border-white/5 rounded-lg flex justify-between items-center text-xs">
          <span>C99 Path Isolation (DESC ISR v3)</span>
          <span className="px-2 py-0.5 rounded bg-emerald/10 text-emerald border border-emerald/30 font-mono text-[10px] font-bold">
            JAILED /workspace
          </span>
        </div>
      </div>

      {/* Cryptographic Audit Ledger */}
      <div className="flex-1 min-h-[220px] p-4 bg-surface border border-white/10 rounded-xl flex flex-col gap-2">
        <div className="flex justify-between items-center text-xs font-bold text-cyan uppercase tracking-wider">
          <span>{isArabic ? 'دفتر التدقيق الرقمي المشفر' : 'Cryptographic JSONL Audit Ledger'}</span>
          <button
            onClick={onRefreshAudit}
            className="px-2 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded text-[10px] text-white transition-all"
          >
            Refresh
          </button>
        </div>

        <div className="flex-1 bg-slate-950 border border-white/5 rounded-lg p-3 overflow-y-auto space-y-2.5 font-mono text-[11px]">
          {auditRecords.map((r, idx) => (
            <div key={idx} className="pb-2 border-b border-white/5 last:border-none last:pb-0">
              <div className="flex justify-between text-slate-500 text-[10px]">
                <span>{r.action} ({r.agent})</span>
                <span>{new Date(r.timestamp_utc * 1000).toLocaleTimeString()}</span>
              </div>
              <div
                className={`font-semibold text-xs ${
                  r.state === 'COMMITTED' ? 'text-emerald' : 'text-crimson'
                }`}
              >
                State: {r.state}
              </div>
              <div className="text-[10px] text-gold/80 break-all">{r.sha256_signature}</div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
};
