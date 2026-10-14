"use client";

import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Send,
  Sparkles,
  Database,
  Sliders,
  BookOpen,
  Copy,
  Check,
  RotateCcw,
  Menu,
  X,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  Tag,
  Users,
  Building,
  ShieldCheck,
} from "lucide-react";

interface SourceItem {
  id: string;
  title: string;
  file: string;
  sheet: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceItem[];
  latencyMs?: number;
}

const QUICK_PROMPTS = [
  {
    category: "Pricing & Discounts",
    icon: Tag,
    title: "Hotel Share Discounts",
    prompt: "What discounts were offered on hotel shares in July 2026 and what are the net sales prices?",
  },
  {
    category: "Executive Performance",
    icon: Users,
    title: "September Top Executives",
    prompt: "Who were the top performing sales executives and team leaders in September 2026?",
  },
  {
    category: "Revenue & Target",
    icon: TrendingUp,
    title: "Target vs Achieved Sales",
    prompt: "What was the total company target, achieved sales, and total collection in September 2026?",
  },
  {
    category: "Resort & Investor Rights",
    icon: Building,
    title: "Ownership Benefits & Stays",
    prompt: "What are the investor benefits, annual dividend yields, and complimentary stay privileges for Sunset Kuakata shares?",
  },
  {
    category: "Lead Operations",
    icon: ShieldCheck,
    title: "AI Lead Qualification",
    prompt: "How does AI qualify an investor lead with a budget of 500,000 BDT versus a student inquiry?",
  },
];

export default function ChatbotPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [knowledgeOpen, setKnowledgeOpen] = useState(false);

  // Settings
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("openai/gpt-oss-120b");
  const [temperature, setTemperature] = useState(0.2);

  // Knowledge browser chunks
  const [allChunks, setAllChunks] = useState<any[]>([]);
  const [chunkSearch, setChunkSearch] = useState("");
  const [selectedChunk, setSelectedChunk] = useState<any | null>(null);

  // Copy feedback state
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load API key from localStorage or pre-filled env
  useEffect(() => {
    const savedKey = localStorage.getItem("groq_api_key");
    if (savedKey) {
      setApiKey(savedKey);
    }

    // Fetch knowledge chunks for the explorer
    fetch("/api/chunks")
      .then((res) => res.json())
      .then((data) => {
        if (data.chunks) setAllChunks(data.chunks);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSaveSettings = () => {
    if (apiKey) {
      localStorage.setItem("groq_api_key", apiKey);
    }
    setSettingsOpen(false);
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSend = async (customPrompt?: string) => {
    const textToSend = customPrompt || input.trim();
    if (!textToSend || isLoading) return;

    const userMessage: Message = {
      id: "u-" + Date.now(),
      role: "user",
      content: textToSend,
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);

    const startTime = performance.now();

    const assistantPlaceholderId = "a-" + Date.now();
    const assistantMessage: Message = {
      id: assistantPlaceholderId,
      role: "assistant",
      content: "",
      sources: [],
    };

    setMessages([...newMessages, assistantMessage]);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: newMessages.map((m) => ({ role: m.role, content: m.content })),
          apiKey: apiKey || undefined,
          model,
          temperature,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to generate response.");
      }

      if (!response.body) {
        throw new Error("No response stream available.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let streamedContent = "";
      let retrievedSources: SourceItem[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunkText = decoder.decode(value);
        const lines = chunkText.split("\n");

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data: ")) {
            const jsonStr = trimmed.slice(6);
            if (jsonStr === "[DONE]") continue;

            try {
              const data = JSON.parse(jsonStr);
              if (data.sources) {
                retrievedSources = data.sources;
              }
              if (data.text) {
                streamedContent += data.text;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantPlaceholderId
                      ? {
                          ...m,
                          content: streamedContent,
                          sources: retrievedSources,
                        }
                      : m
                  )
                );
              }
            } catch {
              // Ignore parse errors on split packets
            }
          }
        }
      }

      const duration = Math.round(performance.now() - startTime);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantPlaceholderId
            ? {
                ...m,
                content: streamedContent,
                sources: retrievedSources,
                latencyMs: duration,
              }
            : m
        )
      );
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantPlaceholderId
            ? {
                ...m,
                content: `⚠️ **Request Error:** ${err.message || "Failed to contact Groq API."}\n\n*Tip: Check that your Groq API Key is configured in the Chat Settings (top-right gear icon) or Vercel Environment Variables.*`,
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
      textareaRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const filteredChunks = allChunks.filter(
    (c) =>
      c.title.toLowerCase().includes(chunkSearch.toLowerCase()) ||
      c.content.toLowerCase().includes(chunkSearch.toLowerCase()) ||
      c.category.toLowerCase().includes(chunkSearch.toLowerCase())
  );

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-header">
          <div className="brand-badge">
            <div className="logo-icon">SK</div>
            <div>
              <div className="brand-title">Sunset Kuakata</div>
              <div className="brand-sub">RAG Operations Chatbot</div>
            </div>
          </div>
          <button
            className="btn-icon"
            onClick={() => setSidebarOpen(false)}
            style={{ display: "none" }}
            aria-label="Close sidebar"
          >
            <X size={16} />
          </button>
        </div>

        <div className="sidebar-content">
          <div>
            <div className="sidebar-section-title">
              <Sparkles size={14} /> Sample Questions
            </div>
            {QUICK_PROMPTS.map((qp, idx) => {
              const Icon = qp.icon;
              return (
                <button
                  key={idx}
                  className="prompt-chip"
                  onClick={() => {
                    handleSend(qp.prompt);
                    setSidebarOpen(false);
                  }}
                >
                  <Icon size={14} style={{ color: "#38bdf8", flexShrink: 0, marginTop: 2 }} />
                  <div>
                    <div style={{ fontWeight: 600, color: "#fff", fontSize: "0.78rem" }}>
                      {qp.title}
                    </div>
                    <div style={{ fontSize: "0.72rem", color: "#94a3b8" }}>{qp.category}</div>
                  </div>
                </button>
              );
            })}
          </div>

          <div>
            <div className="sidebar-section-title">
              <Database size={14} /> Operations Corpus
            </div>
            <div className="stats-box">
              <div className="stat-item">
                <span className="stat-label">Source Documents:</span>
                <span className="stat-val">8 Excel Spreadsheets</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Indexed Knowledge:</span>
                <span className="stat-val">13 Verified Chunks</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Sales Deals Audited:</span>
                <span className="stat-val">115 Transactions</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Management Budget:</span>
                <span className="stat-val">46,500,000 BDT</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">LLM Inference:</span>
                <span className="stat-val" style={{ color: "#10b981" }}>Groq Cloud (Sub-second)</span>
              </div>
            </div>
          </div>

          <button
            className="prompt-chip"
            style={{ background: "rgba(56, 189, 248, 0.08)", borderColor: "rgba(56, 189, 248, 0.25)" }}
            onClick={() => setKnowledgeOpen(true)}
          >
            <BookOpen size={14} style={{ color: "#38bdf8" }} />
            <span style={{ fontWeight: 600, color: "#38bdf8" }}>Open Knowledge Explorer</span>
          </button>
        </div>

        <div className="sidebar-footer">
          <div className="db-pill">
            <span className="status-dot"></span>
            Supabase DB Ready
          </div>
          <button
            className="btn-icon"
            onClick={() => setMessages([])}
            title="Reset Conversation"
          >
            <RotateCcw size={15} />
          </button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="chat-arena">
        {/* Top Navbar */}
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="btn-icon"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label="Toggle menu"
            >
              <Menu size={18} />
            </button>
            <div style={{ display: "flex", flexDirection: "column" }}>
              <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "#fff" }}>
                AI Sales Operations & Investment Advisor
              </span>
              <span style={{ fontSize: "0.72rem", color: "#64748b" }}>
                Sunset Kuakata Hotel & Resort Ltd. • Grounded RAG
              </span>
            </div>
          </div>

          <div className="topbar-right">
            <div className="model-badge">
              <Sparkles size={13} style={{ color: "#818cf8" }} />
              {model.replace("-versatile", "").replace("-instant", "")}
            </div>
            <button
              className="btn-icon"
              onClick={() => setSettingsOpen(true)}
              title="Groq & Model Settings"
            >
              <Sliders size={16} />
            </button>
          </div>
        </header>

        {/* Message Feed */}
        <section className="messages-wrapper" aria-label="Conversation messages">
          {messages.length === 0 ? (
            <div className="welcome-hero">
              <div className="logo-icon" style={{ width: 52, height: 52, fontSize: "1.4rem" }}>
                SK
              </div>
              <h1 className="welcome-title">AI Sales Operations Assistant</h1>
              <p className="welcome-desc">
                Ask questions regarding Sunset Kuakata hotel share pricing, approved discounts,
                executive sales quotas, revenue collections, and investor ownership rights.
                Answers are grounded with verifiable source citations from official Excel files.
              </p>

              <div className="welcome-grid">
                {QUICK_PROMPTS.slice(0, 4).map((qp, i) => (
                  <div
                    key={i}
                    className="welcome-card"
                    onClick={() => handleSend(qp.prompt)}
                  >
                    <div className="welcome-card-title">
                      <qp.icon size={15} style={{ color: "#38bdf8" }} />
                      {qp.title}
                    </div>
                    <div className="welcome-card-desc">{qp.prompt}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m) => (
              <div key={m.id} className={`message-row ${m.role}`}>
                {m.role === "assistant" && (
                  <div className="message-avatar bot">SK</div>
                )}
                <div className="message-bubble">
                  {m.role === "user" ? (
                    <div>{m.content}</div>
                  ) : (
                    <div className="markdown-content">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {m.content || "..."}
                      </ReactMarkdown>

                      {/* Source Citations */}
                      {m.sources && m.sources.length > 0 && (
                        <div className="citations-box">
                          <div className="citations-label">
                            <BookOpen size={12} /> Verified Sources Used:
                          </div>
                          <div className="sources-chips">
                            {m.sources.map((src, idx) => (
                              <button
                                key={idx}
                                className="source-pill"
                                onClick={() => {
                                  const found = allChunks.find((c) => c.id === src.id);
                                  if (found) {
                                    setSelectedChunk(found);
                                    setKnowledgeOpen(true);
                                  }
                                }}
                                title={`${src.file} -> ${src.sheet}`}
                              >
                                {src.file}: {src.sheet}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Message Footer Info */}
                      {m.content && (
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            marginTop: 10,
                            paddingTop: 8,
                            fontSize: "0.72rem",
                            color: "#64748b",
                          }}
                        >
                          <span>
                            {m.latencyMs ? `⚡ ${m.latencyMs}ms on Groq Cloud` : "Grounded via RAG"}
                          </span>
                          <button
                            onClick={() => handleCopy(m.content, m.id)}
                            style={{
                              background: "none",
                              border: "none",
                              color: copiedId === m.id ? "#10b981" : "#94a3b8",
                              cursor: "pointer",
                              display: "flex",
                              alignItems: "center",
                              gap: 4,
                              fontSize: "0.72rem",
                            }}
                          >
                            {copiedId === m.id ? (
                              <>
                                <Check size={12} /> Copied
                              </>
                            ) : (
                              <>
                                <Copy size={12} /> Copy
                              </>
                            )}
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                {m.role === "user" && <div className="message-avatar user">You</div>}
              </div>
            ))
          )}

          {isLoading && messages[messages.length - 1]?.role !== "assistant" && (
            <div className="message-row assistant">
              <div className="message-avatar bot">SK</div>
              <div className="message-bubble">
                <div className="typing-dots">
                  <span className="typing-dot"></span>
                  <span className="typing-dot"></span>
                  <span className="typing-dot"></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </section>

        {/* Input Console */}
        <footer className="input-console">
          <div className="input-box">
            <textarea
              ref={textareaRef}
              className="chat-textarea"
              placeholder="Ask anything about resort shares, discounts, executive performance, or lead rules..."
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button
              className="btn-send"
              disabled={!input.trim() || isLoading}
              onClick={() => handleSend()}
              aria-label="Send message"
            >
              <Send size={15} />
            </button>
          </div>
          <div className="input-footer">
            <span>Powered by Groq Cloud • High-speed LLaMA 3.3 Inference</span>
            <span>Press Enter to send, Shift + Enter for new line</span>
          </div>
        </footer>
      </main>

      {/* Settings Modal */}
      {settingsOpen && (
        <div className="modal-backdrop" onClick={() => setSettingsOpen(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Model & API Configuration</h2>
              <button className="btn-icon" onClick={() => setSettingsOpen(false)}>
                <X size={16} />
              </button>
            </div>

            <div className="form-field">
              <label className="form-label">Groq Cloud API Key</label>
              <input
                type="password"
                className="form-input"
                placeholder="gsk_..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
              <span style={{ fontSize: "0.72rem", color: "#64748b", marginTop: 4, display: "block" }}>
                Stored locally in your browser. Leave blank to use server environment variable (GROQ_API_KEY).
              </span>
            </div>

            <div className="form-field">
              <label className="form-label">Groq Model</label>
              <select
                className="form-input"
                value={model}
                onChange={(e) => setModel(e.target.value)}
              >
                <option value="openai/gpt-oss-120b">GPT-OSS 120B (High Precision & Reasoning)</option>
                <option value="openai/gpt-oss-20b">GPT-OSS 20B (Ultra Fast)</option>
                <option value="qwen/qwen3.8-27b">Qwen 3.8 27B (Multilingual)</option>
              </select>
            </div>

            <div className="form-field">
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <label className="form-label">Temperature (Hallucination Control)</label>
                <span style={{ fontSize: "0.78rem", color: "#38bdf8", fontWeight: 700 }}>
                  {temperature}
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="0.8"
                step="0.05"
                style={{ width: "100%", accentColor: "#38bdf8" }}
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
              />
              <span style={{ fontSize: "0.72rem", color: "#64748b", marginTop: 4, display: "block" }}>
                Lower values (0.1 - 0.2) ensure answers stick strictly to verified spreadsheet facts.
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 20 }}>
              <button
                className="prompt-chip"
                style={{ width: "auto", padding: "8px 16px" }}
                onClick={() => setSettingsOpen(false)}
              >
                Cancel
              </button>
              <button
                className="btn-send"
                style={{ width: "auto", padding: "0 20px", borderRadius: 8, fontWeight: 600 }}
                onClick={handleSaveSettings}
              >
                Save Settings
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Knowledge Explorer Modal */}
      {knowledgeOpen && (
        <div className="modal-backdrop" onClick={() => setKnowledgeOpen(false)}>
          <div
            className="modal-card"
            style={{ maxWidth: 760, maxHeight: "85vh", display: "flex", flexDirection: "column" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <div>
                <h2 className="modal-title">Operations Knowledge Corpus</h2>
                <p style={{ fontSize: "0.75rem", color: "#64748b" }}>
                  Extracted from 8 official Excel spreadsheets and company operating manuals
                </p>
              </div>
              <button className="btn-icon" onClick={() => setKnowledgeOpen(false)}>
                <X size={16} />
              </button>
            </div>

            <input
              type="text"
              className="form-input"
              placeholder="Search knowledge by keyword, title, sheet, or figure (e.g. 250000, dues)..."
              value={chunkSearch}
              onChange={(e) => setChunkSearch(e.target.value)}
              style={{ marginBottom: 16 }}
            />

            <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 12 }}>
              {selectedChunk ? (
                <div style={{ background: "rgba(255,255,255,0.03)", padding: 18, borderRadius: 10 }}>
                  <button
                    onClick={() => setSelectedChunk(null)}
                    style={{
                      background: "none",
                      border: "none",
                      color: "#38bdf8",
                      cursor: "pointer",
                      fontSize: "0.8rem",
                      marginBottom: 10,
                      display: "flex",
                      alignItems: "center",
                      gap: 4,
                    }}
                  >
                    ← Back to All Documents
                  </button>
                  <h3 style={{ color: "#fff", fontSize: "1.05rem", marginBottom: 6 }}>
                    {selectedChunk.title}
                  </h3>
                  <div style={{ fontSize: "0.75rem", color: "#64748b", marginBottom: 14 }}>
                    File: <strong>{selectedChunk.source_file}</strong> | Sheet:{" "}
                    <strong>{selectedChunk.source_sheet}</strong> | Category:{" "}
                    <strong>{selectedChunk.category}</strong>
                  </div>
                  <pre
                    style={{
                      whiteSpace: "pre-wrap",
                      fontFamily: "inherit",
                      fontSize: "0.825rem",
                      lineHeight: 1.6,
                      color: "#cbd5e1",
                    }}
                  >
                    {selectedChunk.content}
                  </pre>
                </div>
              ) : (
                filteredChunks.map((chunk) => (
                  <div
                    key={chunk.id}
                    onClick={() => setSelectedChunk(chunk)}
                    style={{
                      background: "rgba(255, 255, 255, 0.02)",
                      border: "1px solid rgba(255, 255, 255, 0.06)",
                      borderRadius: 8,
                      padding: "12px 16px",
                      cursor: "pointer",
                      transition: "all 0.2s",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontWeight: 700, color: "#fff", fontSize: "0.85rem" }}>
                        {chunk.title}
                      </span>
                      <span
                        style={{
                          fontSize: "0.7rem",
                          background: "rgba(56, 189, 248, 0.1)",
                          color: "#38bdf8",
                          padding: "2px 8px",
                          borderRadius: 4,
                        }}
                      >
                        {chunk.category}
                      </span>
                    </div>
                    <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: 4 }}>
                      {chunk.source_file} • {chunk.source_sheet}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
