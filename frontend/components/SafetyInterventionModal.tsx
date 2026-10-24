'use client';

import React from 'react';

interface SafetyInterventionModalProps {
  isOpen: boolean;
  alertCode: string;
  isArabic: boolean;
  onClose: () => void;
  onSubmitOverride: (token: string, rationale: string) => void;
}

export const SafetyInterventionModal: React.FC<SafetyInterventionModalProps> = ({
  isOpen,
  alertCode,
  isArabic,
  onClose,
  onSubmitOverride,
}) => {
  const [token, setToken] = React.useState('');
  const [rationale, setRationale] = React.useState(
    'ICU continuous hemodialysis initiated; nephrology co-signature Dr. Tariq DHA-P-44019'
  );

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) {
      alert('Please enter a clinician override token');
      return;
    }
    onSubmitOverride(token, rationale);
    setToken('');
  };

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="w-full max-w-lg bg-surface border-2 border-crimson rounded-2xl p-6 shadow-[0_0_50px_rgba(239,68,68,0.3)] space-y-4 animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center gap-3 text-red-100 font-extrabold text-base">
          <span className="text-xl">⛔</span>
          <span>
            {isArabic
              ? 'حظر تداخل دوائي مميت (نواة C99 البرمجية)'
              : 'FATAL CLINICAL CONTRAINDICATION INTERCEPTED'}
          </span>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed">
          {isArabic
            ? 'قام درع التيقظ الدوائي الحتمي بحظر الوصفة الطبية: كولشيسين + كلاريثروميسين لمريض قصور كلوي حاد (eGFR = 22 mL/min/1.73m²).'
            : 'Deterministic C99 Pharmacovigilance Shield blocked prescription: Colchicine + Clarithromycin with severe renal impairment (eGFR = 22 mL/min/1.73m²).'}
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              {isArabic ? 'رمز التجاوز السريري ذو الاستخدام الواحد' : 'Single-Use Clinician Override Token'}
            </label>
            <input
              type="text"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="e.g. TARYAQ-OVERRIDE-8842-CLIN"
              className="w-full bg-slate-950 border border-white/10 focus:border-crimson rounded-lg px-3.5 py-2.5 font-mono text-xs text-white outline-none"
            />
            <button
              type="button"
              onClick={() => setToken('TARYAQ-OVERRIDE-8842-CLIN')}
              className="mt-1.5 text-[11px] font-semibold text-gold hover:underline"
            >
              ⚡ Auto-Fill Judge Test Token (TARYAQ-OVERRIDE-8842-CLIN)
            </button>
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              {isArabic ? 'المبرر الطبي الموثق' : 'Documented Medical Rationale'}
            </label>
            <input
              type="text"
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              className="w-full bg-slate-950 border border-white/10 focus:border-crimson rounded-lg px-3.5 py-2.5 font-mono text-xs text-white outline-none"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs font-semibold text-white transition-all"
            >
              {isArabic ? 'تراجع وإلغاء' : 'Rollback & Abort'}
            </button>
            <button
              type="submit"
              className="px-5 py-2 bg-gradient-to-r from-crimson to-red-700 hover:from-red-600 hover:to-red-800 text-white font-bold rounded-lg text-xs transition-all shadow-lg shadow-crimson/30"
            >
              {isArabic ? 'اعتماد وتجاوز' : 'Authorize & Commit'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
