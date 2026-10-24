'use client';

import React from 'react';
import { Navbar } from '../components/Navbar';
import { ChatWorkspace } from '../components/ChatWorkspace';
import { GlassCockpitDock } from '../components/GlassCockpitDock';
import { SafetyInterventionModal } from '../components/SafetyInterventionModal';
import { AgentType, AuditRecord, ChatMessage, Scenario } from '../lib/types';

export default function Home() {
  const [currentAgent, setCurrentAgent] = React.useState<AgentType>('taryaq');
  const [isArabic, setIsArabic] = React.useState(false);
  const [scenarios, setScenarios] = React.useState<Scenario[]>([]);
  const [auditRecords, setAuditRecords] = React.useState<AuditRecord[]>([]);
  const [messages, setMessages] = React.useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'agent',
      content:
        'Welcome to the Sovereign Championship Cockpit. Select a judge demo scenario above or enter a clinical/business query. All model proposals are deterministically checked in local C99 code in microseconds before execution.',
    },
  ]);
  const [isModalOpen, setIsModalOpen] = React.useState(false);
  const [activeAlertCode, setActiveAlertCode] = React.useState('');
  const [lastPrompt, setLastPrompt] = React.useState('');

  React.useEffect(() => {
    fetchScenarios();
    fetchAudit();
  }, []);

  const fetchScenarios = async () => {
    try {
      const res = await fetch('/api/scenarios');
      if (res.ok) {
        const data = await res.json();
        setScenarios(data.scenarios || []);
      }
    } catch (e) {
      console.warn('Scenarios fetch error:', e);
    }
  };

  const fetchAudit = async () => {
    try {
      const res = await fetch('/api/audit');
      if (res.ok) {
        const data = await res.json();
        setAuditRecords(data.records || []);
      }
    } catch (e) {
      console.warn('Audit fetch error:', e);
    }
  };

  const handleToggleLanguage = () => {
    const nextAr = !isArabic;
    setIsArabic(nextAr);
    document.documentElement.setAttribute('dir', nextAr ? 'rtl' : 'ltr');
    document.documentElement.setAttribute('lang', nextAr ? 'ar' : 'en');
  };

  const handleSelectScenario = (s: Scenario) => {
    setCurrentAgent(s.agent);
    handleSendMessage(s.prompt);
  };

  const handleSendMessage = async (
    text: string,
    overrideToken?: string,
    overrideRationale?: string
  ) => {
    setLastPrompt(text);
    if (!overrideToken) {
      const userMsg: ChatMessage = {
        id: String(Date.now()),
        role: 'user',
        content: text,
      };
      setMessages((prev) => [...prev, userMsg]);
    }

    const agentMsgId = String(Date.now() + 1);
    const agentMsg: ChatMessage = {
      id: agentMsgId,
      role: 'agent',
      content: '',
      toolCalls: [],
    };
    setMessages((prev) => [...prev, agentMsg]);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          agent: currentAgent,
          override_token: overrideToken,
          override_rationale: overrideRationale,
        }),
      });

      if (!response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const raw = line.slice(6).trim();
            if (raw === '[DONE]') break;
            try {
              const event = JSON.parse(raw);
              updateAgentMessage(agentMsgId, event);
            } catch (err) {
              console.error(err);
            }
          }
        }
      }
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === agentMsgId
            ? { ...m, content: `Error communicating with bridge: ${err.message}` }
            : m
        )
      );
    }

    fetchAudit();
  };

  const updateAgentMessage = (msgId: string, event: any) => {
    setMessages((prev) =>
      prev.map((m) => {
        if (m.id !== msgId) return m;

        if (event.type === 'pii_scrubbed') {
          return { ...m, piiRedactedBytes: event.bytes_redacted };
        } else if (event.type === 'tool_call') {
          const tc = {
            name: event.tool,
            args: event.args,
          };
          return { ...m, toolCalls: [...(m.toolCalls || []), tc] };
        } else if (event.type === 'c99_execution') {
          const updatedTCs = (m.toolCalls || []).map((t) =>
            t.name === event.tool
              ? {
                  ...t,
                  result: event.result,
                  executionTimeMs: event.result?.execution_time_ms,
                  isBlocked: event.result?.is_blocked,
                }
              : t
          );
          return { ...m, toolCalls: updatedTCs };
        } else if (event.type === 'security_block') {
          setActiveAlertCode(event.alert_code);
          return {
            ...m,
            isBlocked: true,
            alertCode: event.alert_code,
            content: event.rationale,
          };
        } else if (event.type === 'token') {
          return { ...m, content: m.content + event.content };
        } else if (event.type === 'audit_committed') {
          return { ...m, signature: event.signature };
        }
        return m;
      })
    );
  };

  const handleOpenOverride = (alertCode: string) => {
    setActiveAlertCode(alertCode);
    setIsModalOpen(true);
  };

  const handleSubmitOverride = (token: string, rationale: string) => {
    setIsModalOpen(false);
    handleSendMessage(lastPrompt, token, rationale);
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden">
      <Navbar
        currentAgent={currentAgent}
        onSelectAgent={setCurrentAgent}
        isArabic={isArabic}
        onToggleLanguage={handleToggleLanguage}
      />

      <main className="flex-1 grid grid-cols-[62%_38%] gap-4 p-4 min-h-0">
        <ChatWorkspace
          currentAgent={currentAgent}
          messages={messages}
          scenarios={scenarios}
          isArabic={isArabic}
          onSelectScenario={handleSelectScenario}
          onSendMessage={(t) => handleSendMessage(t)}
          onOpenOverride={handleOpenOverride}
        />

        <GlassCockpitDock
          auditRecords={auditRecords}
          isArabic={isArabic}
          onRefreshAudit={fetchAudit}
        />
      </main>

      <SafetyInterventionModal
        isOpen={isModalOpen}
        alertCode={activeAlertCode}
        isArabic={isArabic}
        onClose={() => setIsModalOpen(false)}
        onSubmitOverride={handleSubmitOverride}
      />
    </div>
  );
}
