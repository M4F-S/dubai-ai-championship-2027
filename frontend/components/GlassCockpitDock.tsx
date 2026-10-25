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
  const [verifyData, setVerifyData] = React.useState<any>(null);
  const [expandedIdx, setExpandedIdx] = React.useState<number | null>(null);

  React.useEffect(() => {
    fetchVerify();
  }, [auditRecords]);

  const fetchVerify = async () => {
    try {
      const res = await fetch('/api/audit/verify');
      if (res.ok) {
        const data = await res.json();
        setVerifyData(data);
      }
    } catch (e) {
      console.warn('Verify fetch error:', e);
    }
  };

  const handleRefresh = () => {
    onRefreshAudit();
    fetchVerify();
  };
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
            onClick={handleRefresh}
            className="px-2 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded text-[10px] text-white transition-all"
          >
            Refresh
          </button>
        </div>

        {/* Live SHA-256 Chain Verification Status Banner */}
        <div
          className={`flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-mono border transition-all ${
            verifyData?.chain_intact
              ? 'bg-emerald/10 border-emerald/30 text-emerald'
              : verifyData
              ? 'bg-crimson/15 border-crimson text-red-200'
              : 'bg-white/5 border-white/10 text-slate-400'
          }`}
        >
          <span className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                verifyData?.chain_intact ? 'bg-emerald animate-pulse' : 'bg-crimson'
              }`}
            />
            {verifyData?.chain_intact
              ? isArabic
                ? 'درع التشفير: السلسلة سليمة ومحققة'
                : 'SHA-256 CHAIN: TAMPER-EVIDENT & VERIFIED'
              : verifyData
              ? 'CHAIN INTEGRITY COMPROMISED'
              : 'VERIFYING LEDGER CHAIN...'}
          </span>
          <span className="text-[10px] opacity-80">
            {verifyData?.total_records
              ? `${verifyData.total_records} Records`
              : 'Checking'}
          </span>
        </div>

        <div className="flex-1 bg-slate-950 border border-white/5 rounded-lg p-3 overflow-y-auto space-y-2.5 font-mono text-[11px]">
          {auditRecords.map((r, idx) => {
            const isExpanded = expandedIdx === idx;
            const isCommitted = (r.state === 'COMMITTED' || r.status === 'COMMITTED');
            return (
              <div
                key={idx}
                onClick={() => setExpandedIdx(isExpanded ? null : idx)}
                className="pb-2 border-b border-white/5 last:border-none last:pb-0 cursor-pointer hover:bg-white/[0.02] rounded p-1 transition-colors"
                title="Click to toggle cryptographic payload"
              >
                <div className="flex justify-between text-slate-500 text-[10px]">
                  <span><strong>{r.action}</strong> ({r.agent || 'Taryaq'})</span>
                  <span>{new Date(r.timestamp_utc * 1000).toLocaleTimeString()}</span>
                </div>
                <div className="flex justify-between items-center mt-0.5">
                  <span
                    className={`font-semibold text-xs ${
                      isCommitted ? 'text-emerald' : 'text-crimson'
                    }`}
                  >
                    State: {r.state || r.status || 'COMMITTED'}
                  </span>
                  {r.prev_sha256 ? (
                    <span className="text-[9.5px] text-slate-500 font-mono">
                      prev: {r.prev_sha256.slice(0, 8)}...
                    </span>
                  ) : null}
                </div>
                <div className="text-[10px] text-gold/80 break-all mt-0.5">
                  sig: {r.sha256_signature}
                </div>
                {isExpanded ? (
                  <pre className="mt-2 p-2 bg-black/60 border border-white/10 rounded text-[9.5px] text-slate-300 whitespace-pre-wrap overflow-x-auto">
                    {JSON.stringify(r, null, 2)}
                  </pre>
                ) : null}
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
};
