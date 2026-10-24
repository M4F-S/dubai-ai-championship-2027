'use client';

import React from 'react';
import { AgentType, ChatMessage, Scenario } from '../lib/types';

interface ChatWorkspaceProps {
  currentAgent: AgentType;
  messages: ChatMessage[];
  scenarios: Scenario[];
  isArabic: boolean;
  onSelectScenario: (scenario: Scenario) => void;
  onSendMessage: (text: string) => void;
  onOpenOverride: (alertCode: string) => void;
}

export const ChatWorkspace: React.FC<ChatWorkspaceProps> = ({
  currentAgent,
  messages,
  scenarios,
  isArabic,
  onSelectScenario,
  onSendMessage,
  onOpenOverride,
}) => {
  const [inputValue, setInputValue] = React.useState('');
  const scrollRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;
    onSendMessage(inputValue);
    setInputValue('');
  };

  return (
    <section className="flex flex-col bg-surface border border-white/10 rounded-2xl overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="px-5 py-3.5 bg-panel/70 border-b border-white/10 flex items-center justify-between">
        <div className="text-xs font-bold text-gold uppercase tracking-wider flex items-center gap-2">
          <span>⚡</span>
          <span>{isArabic ? 'مسار التنفيذ التفاعلي للوكيل السيادي' : 'Interactive Agent Execution Stream'}</span>
        </div>
        <div className="text-[11px] font-mono text-slate-400">
          Model: Qwen 2.5 7B (UM790 Edge Parity)
        </div>
      </div>

      {/* Preset Chips */}
      <div className="px-5 py-2.5 bg-background/50 border-b border-white/10 flex gap-2 overflow-x-auto scrollbar-none">
        {scenarios.map((s) => (
          <button
            key={s.id}
            onClick={() => onSelectScenario(s)}
            className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-elevated border border-white/10 hover:border-cyan text-slate-300 hover:text-white text-[11px] font-semibold whitespace-nowrap transition-all flex items-center gap-1.5"
          >
            <span className="text-cyan">✦</span>
            <span>{isArabic ? s.title_ar : s.title_en}</span>
          </button>
        ))}
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 p-5 overflow-y-auto space-y-4">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`max-w-[88%] p-4 rounded-xl text-[13.5px] leading-relaxed ${
              m.role === 'user'
                ? 'ml-auto bg-gradient-to-br from-slate-800 to-slate-900 border border-white/15 text-white'
                : 'mr-auto bg-panel border border-white/10 text-slate-200'
            }`}
          >
            {/* PII Redacted Card */}
            {m.piiRedactedBytes && m.piiRedactedBytes > 0 ? (
              <div className="mb-2 p-2 bg-emerald/10 border border-dashed border-emerald/40 rounded-lg text-emerald text-xs flex justify-between items-center font-mono">
                <span>🛡️ DESC ISR v3.1 PII Scrubber: {m.piiRedactedBytes} B redacted</span>
                <span>0.009 ms</span>
              </div>
            ) : null}

            {/* Tool Calls */}
            {m.toolCalls?.map((tc, idx) => (
              <div
                key={idx}
                className="my-2 p-3 bg-slate-950/70 border border-cyan/30 border-l-4 border-l-cyan rounded-lg font-mono text-xs"
              >
                <div className="flex justify-between items-center text-cyan font-bold mb-1">
                  <span>⚙️ C99 Proposal: {tc.name}</span>
                  <span className="text-emerald text-[11px]">
                    {tc.executionTimeMs ? `${tc.executionTimeMs} ms` : 'Running'}
                  </span>
                </div>
                <pre className="text-slate-300 text-[11px] whitespace-pre-wrap">
                  {JSON.stringify(tc.args, null, 2)}
                </pre>
              </div>
            ))}

            {/* Block Alert */}
            {m.isBlocked ? (
              <div className="my-3 p-3 bg-crimson/15 border border-crimson rounded-lg text-red-200">
                <div className="font-bold text-sm text-red-100 flex items-center gap-1.5">
                  <span>⛔</span>
                  <span>SECURITY BARRIER TRIGGERED: {m.alertCode}</span>
                </div>
                <div className="mt-1 text-xs">{m.content}</div>
                <button
                  onClick={() => onOpenOverride(m.alertCode || 'CLINICAL_CONTRAINDICATION')}
                  className="mt-3 px-3 py-1.5 bg-crimson hover:bg-red-700 text-white rounded-lg text-xs font-bold transition-all shadow-lg shadow-crimson/30"
                >
                  ⚠️ Clinician Override Required
                </button>
              </div>
            ) : (
              <div className="whitespace-pre-wrap">{m.content}</div>
            )}

            {/* SHA Signature */}
            {m.signature ? (
              <div className="mt-3 p-2 bg-gold/10 border border-gold/30 rounded-lg font-mono text-[11px]">
                <span className="text-gold font-bold">✍️ Cryptographic Ledger Signature (SHA-256):</span>
                <div className="text-slate-300 text-[10px] break-all">{m.signature}</div>
              </div>
            ) : null}
          </div>
        ))}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 bg-panel border-t border-white/10 flex gap-3">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={
            isArabic
              ? 'اكتب وصفة طبية، أو استفساراً تأمينياً، أو أمراً تنفيذياً...'
              : 'Type clinical prescription, claim inquiry, or business directive...'
          }
          className="flex-1 bg-background/90 border border-white/10 focus:border-gold rounded-xl px-4 py-3 text-sm text-white outline-none transition-colors"
        />
        <button
          type="submit"
          className="px-6 py-3 bg-gradient-to-r from-gold to-amber-600 hover:from-amber-500 hover:to-amber-700 text-background font-bold rounded-xl text-sm transition-all shadow-lg shadow-gold/20"
        >
          {isArabic ? 'تنفيذ الوكيل' : 'Execute Agent'}
        </button>
      </form>
    </section>
  );
};
