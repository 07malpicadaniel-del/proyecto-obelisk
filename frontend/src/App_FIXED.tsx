import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import {
  Search, Server, AlertTriangle, Zap, Activity, Terminal, Users, Globe, Cpu, Copy,
  ShieldAlert, XCircle, MessageSquare, Calendar, TrendingUp, Shield, Layers,
  Clock, Plus, ChevronDown, ChevronUp, Send, Building2, Trash2, BarChart3, ArrowRight,
  X, Briefcase, RefreshCw, Bot, User as UserIcon, Edit3, Save, History, FileText, ChevronLeft,
  ExternalLink, Info, CheckCircle2, Target, Bell, Radio, Radar, Eye, XOctagon,
  ChevronRight, EyeOff, Menu, LogOut
} from 'lucide-react';

const API = 'http://127.0.0.1:8000';

interface Trigger { type: string; description: string; date?: string; }
interface WebData { industry?: string; tech_stack: string[]; competitors: string[]; triggers: Trigger[]; }
interface ParsedAnalysis {
  resumen_ejecutivo: string; pain_points: string[] | string; solucion_hpe_recomendada: string | any;
  speech_opening: string; speech_challenge: string; speech_bridge: string; speech_solution: string;
  speech_approach?: string; speech_resumen: string; referencia_hpe?: string;
  recommendation_status?: string; urgency?: string;
}
interface Recommendation {
  name: string; category: string; url: string; confidence: number;
  need_detected: string[]; competitive_advantage: string; relationship: string; pain_points: string[];
}
interface Account {
  id: number; company_name: string; contact_name: string; contact_role: string;
  industry: string; website: string; context: string; notes: string;
  last_score: number; last_product: string; last_status: string;
  created_at: string; updated_at: string;
}
interface HistoryItem {
  id: number; company_name: string; fit_score: number; hpe_product_recommended: string;
  industry: string; triggers: string; tech_stack: string; competitors: string;
  speech: string; resumen: string; pain_points: string; target_role: string; created_at: string;
}
interface ChatMsg { role: string; content: string; }
interface Alert {
  id: number; account_id: number; company_name: string; alert_level: string;
  summary: string; new_triggers: string; score_change: number; fit_score: number;
  recommended_product: string; is_read: number; created_at: string;
}

const triggerIcon: Record<string, any> = {
  'DATA_CENTER': Server, 'CLOUD_MIGRATION': Layers, 'SECURITY_INCIDENT': Shield,
  'NETWORK_UPGRADE': Activity, 'SERVER_REFRESH': Cpu, 'LEADERSHIP_CHANGE': Users,
  'EXPANSION': TrendingUp, 'DIGITAL_TRANSFORMATION': Zap, 'COMPETITOR_CONTRACT': AlertTriangle,
};
const triggerAccent: Record<string, string> = {
  'DATA_CENTER': '#3B82F6', 'CLOUD_MIGRATION': '#06B6D4', 'SECURITY_INCIDENT': '#EF4444',
  'NETWORK_UPGRADE': '#A855F7', 'SERVER_REFRESH': '#F97316', 'LEADERSHIP_CHANGE': '#EAB308',
  'EXPANSION': '#01A982', 'DIGITAL_TRANSFORMATION': '#6366F1', 'COMPETITOR_CONTRACT': '#EC4899',
};
const alertLevelColor = (l: string) => l === 'HIGH' ? '#EF4444' : l === 'MEDIUM' ? '#FFB900' : '#666';

function App() {
  const [company, setCompany] = useState('');
  const [role, setRole] = useState('CEO');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysis, setAnalysis] = useState<ParsedAnalysis | null>(null);
  const [webData, setWebData] = useState<WebData | null>(null);
  const [sources, setSources] = useState<string[]>([]);
  const [fitScore, setFitScore] = useState(0);
  const [hasOpportunity, setHasOpportunity] = useState(true);
  const [isCompetitor, setIsCompetitor] = useState(false);
  const [copied, setCopied] = useState('');
  const [analyzedCompany, setAnalyzedCompany] = useState('');
  const [top3, setTop3] = useState<Recommendation[]>([]);

  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newAcc, setNewAcc] = useState({ name: '', website: '' });
  const [showAbout, setShowAbout] = useState(false);
  const [roleOpen, setRoleOpen] = useState(false);
  const [accountHistory, setAccountHistory] = useState<HistoryItem[]>([]);
  const [editingAccount, setEditingAccount] = useState(false);
  const [editFields, setEditFields] = useState({ contact_name: '', contact_role: '', industry: '', website: '', context: '', notes: '' });
  const [view, setView] = useState<'home' | 'analysis' | 'account'>('home');
  const [homeChatInput, setHomeChatInput] = useState('');
  const [homeChatMessages, setHomeChatMessages] = useState<ChatMsg[]>([]);
  const [homeChatLoading, setHomeChatLoading] = useState(false);
  const homeChatEndRef = useRef<HTMLDivElement>(null);
  const [expandedHistory, setExpandedHistory] = useState<number | null>(null);

  const [chatOpen, setChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMsg[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Alerts & Scanner
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [alertsOpen, setAlertsOpen] = useState(false);
  const [scannerStatus, setScannerStatus] = useState<any>(null);
  const [scanning, setScanning] = useState(false);

  // Collapsible sections
  const [showSignals, setShowSignals] = useState(true);
  const [showDetails, setShowDetails] = useState(true);
  const [showBrief, setShowBrief] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [showSalesContext, setShowSalesContext] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // 🔴 FIX: Mobile responsive state
  const [isMobile, setIsMobile] = useState(false);

  // Max history items to display
  const MAX_HISTORY = 7;

  // Top 5 trigger details for Home view
  const [topTriggers, setTopTriggers] = useState<Record<number, { type: string; description: string }[]>>({});

  useEffect(() => { fetchAccounts(); fetchAlerts(); fetchScannerStatus(); }, []);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [chatMessages]);
  useEffect(() => { homeChatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [homeChatMessages]);
  useEffect(() => {
    const interval = setInterval(() => { fetchAlerts(); fetchScannerStatus(); }, 30000);
    return () => clearInterval(interval);
  }, []);

  // 🔴 FIX: Detect mobile on mount and resize
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) setSidebarOpen(false);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Fetch latest triggers for Top 5 accounts
  useEffect(() => {
    const top5 = accounts.filter(a => a.last_score > 0).sort((a, b) => b.last_score - a.last_score).slice(0, 5);
    if (top5.length === 0) return;
    const fetchTriggers = async () => {
      const result: Record<number, { type: string; description: string }[]> = {};
      await Promise.all(top5.map(async (acc) => {
        try {
          const r = await axios.get(`${API}/accounts/${acc.id}/history`);
          const history = r.data.history || [];
          if (history.length > 0) {
            const latest = history[0];
            const triggers = JSON.parse(latest.triggers || '[]');
            result[acc.id] = triggers;
          }
        } catch {}
      }));
      setTopTriggers(result);
    };
    fetchTriggers();
  }, [accounts]);

  const fetchAccounts = async () => { try { const r = await axios.get(`${API}/accounts`); setAccounts(r.data.accounts || []); } catch {} };
  const fetchAlerts = async () => {
    try { const r = await axios.get(`${API}/alerts`); setAlerts(r.data.alerts || []); setUnreadCount(r.data.unread_count || 0); } catch {}
  };
  const fetchScannerStatus = async () => { try { const r = await axios.get(`${API}/scanner/status`); setScannerStatus(r.data); } catch {} };

  const markAllRead = async () => { try { await axios.post(`${API}/alerts/read-all`); fetchAlerts(); } catch {} };
  const dismissAlert = async (id: number) => { try { await axios.post(`${API}/alerts/${id}/dismiss`); fetchAlerts(); } catch {} };
  const runScanNow = async () => {
    setScanning(true);
    try { await axios.post(`${API}/scanner/run-now`); fetchAlerts(); fetchAccounts(); fetchScannerStatus(); } catch {}
    finally { setScanning(false); }
  };

  const addAccount = async () => {
    if (!newAcc.name.trim() && !newAcc.website.trim()) return;
    try {
      await axios.post(`${API}/accounts`, { company_name: newAcc.name, website: newAcc.website });
      setNewAcc({ name: '', website: '' });
      setShowAddModal(false); fetchAccounts();
    } catch (e: any) { alert(e.response?.data?.detail || 'Error'); }
  };

  const deleteAccount = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Delete this account and its chat history?')) return;
    try { await axios.delete(`${API}/accounts/${id}`); fetchAccounts(); if (selectedAccount?.id === id) { setSelectedAccount(null); setView('home'); } } catch {}
  };

  const selectAccount = async (acc: Account) => {
    setSelectedAccount(acc); setCompany(acc.company_name); setView('account');
    setEditingAccount(false); setAnalysis(null);
    setEditFields({ contact_name: acc.contact_name||'', contact_role: acc.contact_role||'', industry: acc.industry||'', website: acc.website||'', context: acc.context||'', notes: acc.notes||'' });
    try { const r = await axios.get(`${API}/accounts/${acc.id}/history`); setAccountHistory(r.data.history || []); } catch { setAccountHistory([]); }
    try { const r = await axios.get(`${API}/chat/${acc.id}/messages`); setChatMessages(r.data.messages || []); } catch { setChatMessages([]); }
  };

  const saveAccountEdit = async () => {
    if (!selectedAccount) return;
    try { const r = await axios.patch(`${API}/accounts/${selectedAccount.id}`, editFields); setSelectedAccount(r.data); setEditingAccount(false); fetchAccounts(); } catch {}
  };

  // 🔴 FIX: Logout function
  const logout = () => {
    localStorage.removeItem('hpe_session');
    localStorage.removeItem('hpe_user');
    setAccounts([]);
    setSelectedAccount(null);
    setView('home');
    alert('Sesión cerrada exitosamente');
  };

  const handleAnalyze = async () => {
    if (!company) return;
    setLoading(true); setError(''); setAnalysis(null); setWebData(null); setTop3([]);
    setHasOpportunity(true); setIsCompetitor(false); setView('analysis');
    try {
      const response = await axios.post(`${API}/analyze`, {
        company_name: company, url: "", target_role: role,
        account_context: selectedAccount?.context || '', contact_name: selectedAccount?.contact_name || '',
      });
      const data = response.data;
      setSources(data.sources || []); setWebData(data.web_data || { tech_stack: [], triggers: [], competitors: [] });
      setFitScore(data.fit_score || 0); setHasOpportunity(data.has_opportunity ?? true);
      setIsCompetitor(data.is_competitor ?? false); setAnalyzedCompany(company); setTop3(data.top3_recommendations || []);
      let cleanData: ParsedAnalysis | null = null;
      const rawJson = data.analysis_json;
      if (typeof rawJson === 'object') cleanData = rawJson;
      else if (typeof rawJson === 'string') { try { cleanData = JSON.parse(rawJson); } catch { const m = rawJson.match(/\{[\s\S]*\}/); if (m) cleanData = JSON.parse(m[0]); } }
      if (cleanData) { if (typeof cleanData.solucion_hpe_recomendada === 'object') cleanData.solucion_hpe_recomendada = JSON.stringify(cleanData.solucion_hpe_recomendada); setAnalysis(cleanData); }
      else setError("Unexpected AI format.");
      fetchAccounts();
      if (selectedAccount) { try { const r = await axios.get(`${API}/accounts/${selectedAccount.id}/history`); setAccountHistory(r.data.history || []); } catch {} }
    } catch { setError('Connection error. Check backend on port 8000.'); }
    finally { setLoading(false); }
  };

  const sendChat = async () => {
    if (!chatInput.trim()) return; const msg = chatInput.trim(); setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: msg }]); setChatLoading(true);
    try { const r = await axios.post(`${API}/chat`, { message: msg, account_id: selectedAccount?.id || null, company_context: analyzedCompany || company || '' });
      setChatMessages(prev => [...prev, { role: 'assistant', content: r.data.reply }]);
    } catch { setChatMessages(prev => [...prev, { role: 'assistant', content: 'Error. Try again.' }]); }
    finally { setChatLoading(false); }
  };

  const sendHomeChat = async () => {
    if (!homeChatInput.trim()) return; const msg = homeChatInput.trim(); setHomeChatInput('');
    setHomeChatMessages(prev => [...prev, { role: 'user', content: msg }]); setHomeChatLoading(true);
    try { const r = await axios.post(`${API}/chat`, { message: msg, account_id: null, company_context: '' });
      setHomeChatMessages(prev => [...prev, { role: 'assistant', content: r.data.reply }]);
    } catch { setHomeChatMessages(prev => [...prev, { role: 'assistant', content: 'Error. Try again.' }]); }
    finally { setHomeChatLoading(false); }
  };

  const copyText = (text: string, id: string) => { navigator.clipboard.writeText(text); setCopied(id); setTimeout(() => setCopied(''), 2000); };
  const fullSpeech = analysis ? `${analysis.speech_opening||''}\n\n${analysis.speech_challenge||''}\n\n${analysis.speech_bridge||''}\n\n${analysis.speech_solution||''}`.trim() : '';
  const scoreColor = fitScore >= 75 ? '#01A982' : fitScore >= 50 ? '#FFB900' : fitScore >= 25 ? '#FF8300' : '#FF4C4C';
  const scoreLabel = fitScore >= 80 ? 'CRITICAL' : fitScore >= 60 ? 'HIGH' : fitScore >= 40 ? 'MODERATE' : fitScore >= 20 ? 'LOW' : 'MINIMAL';
  const urgencyColor = (u: string) => u === 'HIGH' ? '#EF4444' : u === 'MEDIUM' ? '#FFB900' : '#01A982';
  const roles = [{ value: 'CEO', label: 'CEO' }, { value: 'CTO', label: 'CTO' }, { value: 'Vendedor', label: 'Sales Rep' }];
  const statusColor = (s: string) => s === 'ANALYZED' ? '#01A982' : s === 'NEW' ? '#666' : '#FFB900';
  const parseJSON = (s: string) => { try { return JSON.parse(s); } catch { return []; } };
  const fmtDate = (d: string) => { try { return new Date(d).toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' }); } catch { return d; } };
  const fmtTime = (d: string) => { try { const dt = new Date(d); return `${dt.toLocaleDateString('en-US',{month:'short',day:'numeric'})} ${dt.toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit'})}`; } catch { return d; } };

  // Collapsible section header component
  const SectionToggle = ({ label, icon: Icon, color, open, onToggle, count, extra }: { label: string; icon: any; color: string; open: boolean; onToggle: () => void; count?: number; extra?: React.ReactNode }) => (
    <button onClick={onToggle} className="w-full flex items-center justify-between group mb-3">
      <p className="text-xs uppercase tracking-[0.15em] font-bold flex items-center gap-2" style={{ color }}>
        <Icon className="w-4 h-4" /> {label} {count !== undefined && <span className="text-white/30">({count})</span>}
      </p>
      <div className="flex items-center gap-2">
        {extra}
        <div className="w-6 h-6 rounded-md flex items-center justify-center bg-white/[0.04] group-hover:bg-white/[0.08] transition-colors">
          {open ? <ChevronUp className="w-3.5 h-3.5 text-white/40" /> : <ChevronDown className="w-3.5 h-3.5 text-white/40" />}
        </div>
      </div>
    </button>
  );

  // Markdown renderer for chat messages
  const ChatMarkdown = ({ content }: { content: string }) => (
    <ReactMarkdown
      components={{
        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
        strong: ({ children }) => <strong className="font-bold text-white/80">{children}</strong>,
        em: ({ children }) => <em className="italic text-white/70">{children}</em>,
        h1: ({ children }) => <h1 className="text-lg font-bold text-white/90 mb-2 mt-3 first:mt-0">{children}</h1>,
        h2: ({ children }) => <h2 className="text-base font-bold text-white/85 mb-1.5 mt-2.5 first:mt-0">{children}</h2>,
        h3: ({ children }) => <h3 className="text-sm font-bold text-white/80 mb-1 mt-2 first:mt-0">{children}</h3>,
        ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-2 ml-1">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mb-2 ml-1">{children}</ol>,
        li: ({ children }) => <li className="text-white/60">{children}</li>,
        code: ({ className, children }) => {
          const isBlock = className?.includes('language-');
          return isBlock
            ? <pre className="bg-black/30 border border-white/[0.08] rounded-lg p-3 my-2 overflow-x-auto"><code className="text-xs text-green-400/80 font-mono">{children}</code></pre>
            : <code className="bg-white/[0.08] text-[#01A982] px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>;
        },
        a: ({ href, children }) => <a href={href} target="_blank" rel="noopener noreferrer" className="text-[#01A982] underline underline-offset-2 hover:text-[#01A982]/80">{children}</a>,
        blockquote: ({ children }) => <blockquote className="border-l-2 border-[#01A982]/40 pl-3 my-2 text-white/50 italic">{children}</blockquote>,
        hr: () => <hr className="border-white/[0.08] my-3" />,
        table: ({ children }) => <div className="overflow-x-auto my-2"><table className="text-xs border-collapse w-full">{children}</table></div>,
        th: ({ children }) => <th className="border border-white/[0.1] bg-white/[0.05] px-3 py-1.5 text-left font-bold text-white/60">{children}</th>,
        td: ({ children }) => <td className="border border-white/[0.08] px-3 py-1.5 text-white/50">{children}</td>,
      }}
    >{content}</ReactMarkdown>
  );

  return (
    <div className="h-screen flex flex-col font-sans text-white overflow-hidden" style={{ background: '#0D1117' }}>

      {/* ═══ TOP BAR ═══ */}
      <header className="h-14 flex items-center justify-between px-6 border-b border-white/[0.08] shrink-0" style={{ background: '#161B22' }}>
        <button onClick={() => { setSelectedAccount(null); setAnalysis(null); setView('home'); }} className="flex items-center gap-3 hover:opacity-80 transition-opacity">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: '#01A982' }}>
            <Server className="w-4 h-4 text-white" />
          </div>
          <span className="text-base font-bold tracking-wide">HPE</span>
          <span className="text-sm text-white/40 font-light">Sales Guardian</span>
        </button>
        <div className="flex items-center gap-5">
          {/* Scanner Status */}
          <div className="flex items-center gap-2 text-xs text-white/40">
            <Radar className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} style={{ color: scannerStatus?.enabled ? '#01A982' : '#666' }} />
            <span>Radar {scannerStatus?.enabled ? 'ON' : 'OFF'}</span>
            {scannerStatus?.last_scan_at && <span className="text-white/25">· {fmtTime(scannerStatus.last_scan_at)}</span>}
          </div>
          {/* Scan Now */}
          <button onClick={runScanNow} disabled={scanning}
            className="text-xs px-3 py-1.5 rounded-lg border border-white/[0.1] hover:border-white/[0.2] flex items-center gap-2 transition-colors disabled:opacity-30"
            style={{ color: '#01A982' }}>
            <RefreshCw className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} /> {scanning ? 'Scanning...' : 'Scan Now'}
          </button>
          {/* Alerts Bell */}
          <div className="relative">
            <button onClick={() => { setAlertsOpen(!alertsOpen); if (!alertsOpen) markAllRead(); }}
              className="relative w-9 h-9 rounded-lg flex items-center justify-center hover:bg-white/[0.08] transition-colors">
              <Bell className="w-5 h-5 text-white/50" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-5 h-5 rounded-full text-[10px] font-bold flex items-center justify-center text-white animate-pulse" style={{ background: '#EF4444' }}>
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>
            {/* Alerts Panel */}
            {alertsOpen && (
              <div className="absolute top-full right-0 mt-2 w-[420px] rounded-2xl border border-white/[0.1] shadow-2xl overflow-hidden z-50" style={{ background: '#1C2128' }}>
                <div className="px-5 py-3.5 border-b border-white/[0.08] flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Radar className="w-4.5 h-4.5" style={{ color: '#01A982' }} />
                    <span className="text-sm font-bold text-white">Account Radar</span>
                  </div>
                  <button onClick={() => setAlertsOpen(false)} className="text-white/40 hover:text-white"><X className="w-4 h-4" /></button>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {alerts.length === 0 ? (
                    <div className="py-12 text-center">
                      <Radar className="w-10 h-10 text-white/15 mx-auto mb-3" />
                      <p className="text-sm text-white/30">No alerts yet</p>
                      <p className="text-xs text-white/20 mt-1">Monitoring {scannerStatus?.accounts_monitored || 0} accounts every {scannerStatus?.interval_hours || 6}h</p>
                    </div>
                  ) : alerts.map(a => {
                    const triggers = parseJSON(a.new_triggers || '[]');
                    return (
                      <div key={a.id} className={`px-5 py-3.5 border-b border-white/[0.06] hover:bg-white/[0.03] transition-colors ${!a.is_read ? 'bg-white/[0.03]' : ''}`}>
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-start gap-3 flex-1 min-w-0">
                            <div className="w-2.5 h-2.5 rounded-full mt-1.5 shrink-0" style={{ background: alertLevelColor(a.alert_level) }} />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-sm font-bold text-white/80 truncate cursor-pointer hover:text-white"
                                  onClick={() => { const acc = accounts.find(ac => ac.id === a.account_id); if (acc) { selectAccount(acc); setAlertsOpen(false); } }}>
                                  {a.company_name}
                                </span>
                                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded" style={{ color: alertLevelColor(a.alert_level), background: `${alertLevelColor(a.alert_level)}15` }}>
                                  {a.alert_level}
                                </span>
                              </div>
                              <p className="text-xs text-white/45 leading-relaxed">{a.summary}</p>
                              {a.score_change !== 0 && (
                                <span className="text-xs font-bold" style={{ color: a.score_change > 0 ? '#01A982' : '#EF4444' }}>
                                  Score: {a.fit_score} ({a.score_change > 0 ? '+' : ''}{a.score_change})
                                </span>
                              )}
                              {triggers.length > 0 && (
                                <div className="flex flex-wrap gap-1.5 mt-1.5">
                                  {triggers.slice(0, 3).map((t: any, i: number) => (
                                    <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-yellow-500/10 text-yellow-500/60">{t.type?.replace(/_/g,' ')}</span>
                                  ))}
                                </div>
                              )}
                              <p className="text-[10px] text-white/20 mt-1.5">{fmtTime(a.created_at)}</p>
                            </div>
                          </div>
                          <button onClick={() => dismissAlert(a.id)} className="p-1.5 hover:bg-white/[0.08] rounded shrink-0" title="Dismiss">
                            <X className="w-3.5 h-3.5 text-white/25" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="px-5 py-3 border-t border-white/[0.08] flex items-center justify-between">
                  <span className="text-xs text-white/25">{scannerStatus?.accounts_monitored || 0} accounts · every {scannerStatus?.interval_hours || 6}h</span>
                  <button onClick={runScanNow} disabled={scanning} className="text-xs font-medium flex items-center gap-1.5 disabled:opacity-30" style={{ color: '#01A982' }}>
                    <RefreshCw className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} /> {scanning ? 'Scanning...' : 'Scan All Now'}
                  </button>
                </div>
              </div>
            )}
          </div>
          {/* Version */}
          <div className="flex items-center gap-2 text-xs font-mono tracking-widest" style={{ color: '#01A982' }}>
            <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: '#01A982' }} />
            v8.1
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">

        {/* 🔴 FIX: Hamburger Menu (solo móvil) */}
        {isMobile && !sidebarOpen && (
          <button
            onClick={() => setSidebarOpen(true)}
            className="fixed top-4 left-4 z-50 p-2 rounded-lg border border-white/[0.1] shadow-lg"
            style={{ background: '#1C2128' }}
          >
            <Menu className="w-5 h-5 text-white" />
          </button>
        )}

        {/* ═══ LEFT SIDEBAR (RESPONSIVE) ═══ */}
        <aside className={`
          border-r border-white/[0.08] flex flex-col shrink-0 transition-all duration-200
          ${isMobile ? 'fixed inset-y-0 left-0 z-40' : 'relative'}
          ${isMobile && !sidebarOpen ? '-translate-x-full' : 'translate-x-0'}
          ${isMobile ? 'w-64' : sidebarOpen ? 'w-64' : 'w-16'}
          ${isMobile ? 'bg-[#0D1117]' : ''}
        `} style={{ background: '#111820' }}>
          {/* Header */}
          <div className={`flex items-center ${sidebarOpen ? 'justify-between px-4' : 'justify-center'} py-3 border-b border-white/[0.08]`}>
            {sidebarOpen && <span className="text-[11px] uppercase tracking-[0.15em] text-white/35 font-semibold">Accounts</span>}
            <div className="flex items-center gap-1">
              {sidebarOpen && (
                <button onClick={() => setShowAddModal(true)} className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-white/10 transition-colors" style={{ background: 'rgba(1,169,130,0.15)' }}>
                  <Plus className="w-3.5 h-3.5" style={{ color: '#01A982' }} />
                </button>
              )}
              {/* 🔴 FIX: Botón de cerrar en móvil */}
              {isMobile && sidebarOpen ? (
                <button onClick={() => setSidebarOpen(false)} className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-white/[0.08] transition-colors">
                  <X className="w-3.5 h-3.5 text-white/35" />
                </button>
              ) : !isMobile && (
                <button onClick={() => setSidebarOpen(!sidebarOpen)} className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-white/[0.08] transition-colors" title={sidebarOpen ? 'Collapse' : 'Expand'}>
                  {sidebarOpen ? <ChevronLeft className="w-3.5 h-3.5 text-white/35" /> : <ChevronRight className="w-3.5 h-3.5 text-white/35" />}
                </button>
              )}
            </div>
          </div>

          {/* Account List */}
          <div className="flex-1 overflow-y-auto px-1.5 space-y-0.5 pb-2">
            {!sidebarOpen && (
              <button onClick={() => setShowAddModal(true)} className="w-full flex items-center justify-center py-2 mb-1">
                <div className="w-9 h-9 rounded-lg flex items-center justify-center hover:bg-white/[0.08] transition-colors" style={{ background: 'rgba(1,169,130,0.15)' }}>
                  <Plus className="w-3.5 h-3.5" style={{ color: '#01A982' }} />
                </div>
              </button>
            )}
            {accounts.length === 0 && sidebarOpen ? (
              <div className="px-3 py-8 text-center"><Building2 className="w-8 h-8 text-white/10 mx-auto mb-2" /><p className="text-xs text-white/25">No accounts</p></div>
            ) : accounts.map(acc => {
              const hasAlert = alerts.some(a => a.account_id === acc.id && !a.is_read);
              const isActive = selectedAccount?.id === acc.id;
              return (
                <button key={acc.id} onClick={() => selectAccount(acc)} title={!sidebarOpen ? acc.company_name : undefined}
                  className={`w-full text-left rounded-lg transition-all group flex items-center ${sidebarOpen ? 'px-3 py-2.5 gap-2.5' : 'justify-center py-2 px-0'} ${isActive ? 'bg-white/[0.08]' : 'hover:bg-white/[0.04]'}`}>
                  <div className="relative shrink-0">
                    <div className={`${sidebarOpen ? 'w-8 h-8 text-xs' : 'w-9 h-9 text-sm'} rounded-lg flex items-center justify-center font-bold`}
                      style={{ background: `${statusColor(acc.last_status)}15`, color: statusColor(acc.last_status) }}>
                      {acc.company_name.charAt(0).toUpperCase()}
                    </div>
                    {hasAlert && <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full animate-pulse" style={{ background: '#EF4444', border: '2px solid #111820' }} />}
                  </div>
                  {sidebarOpen && (
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-medium text-white/80 truncate">{acc.company_name}</p>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        {acc.last_score > 0 && <span className="text-[11px] font-bold" style={{ color: acc.last_score >= 70 ? '#01A982' : '#FFB900' }}>{acc.last_score}</span>}
                        <span className="text-[11px] text-white/25 truncate">{acc.contact_name || acc.industry || acc.last_status}</span>
                      </div>
                    </div>
                  )}
                  {sidebarOpen && (
                    <button onClick={(e) => deleteAccount(acc.id, e)} className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded transition-all">
                      <Trash2 className="w-3 h-3 text-red-400/60" />
                    </button>
                  )}
                </button>
              );
            })}
          </div>

          {/* Dashboard Button */}
          <div className="border-t border-white/[0.06] p-2">
            <button onClick={() => { setSelectedAccount(null); setAnalysis(null); setView('home'); }}
              title={!sidebarOpen ? 'Dashboard' : undefined}
              className={`w-full flex items-center ${sidebarOpen ? 'gap-2.5 px-3 py-2.5' : 'justify-center py-2.5'} rounded-lg transition-all ${
                view === 'home' ? 'bg-[#01A982]/12' : 'hover:bg-white/[0.04]'
              }`}>
              <BarChart3 className="w-4.5 h-4.5 shrink-0" style={{ color: view === 'home' ? '#01A982' : 'rgba(255,255,255,0.3)' }} />
              {sidebarOpen && <span className={`text-[13px] font-medium ${view === 'home' ? 'text-white/90' : 'text-white/45'}`}>Dashboard</span>}
            </button>
          </div>

          {/* 🔴 FIX: Botón de Logout */}
          <div className="border-t border-white/[0.06] p-2">
            <button
              onClick={logout}
              title={!sidebarOpen ? 'Cerrar Sesión' : undefined}
              className={`w-full flex items-center ${sidebarOpen ? 'gap-2.5 px-3 py-2.5' : 'justify-center py-2.5'} rounded-lg transition-all hover:bg-red-500/10`}
            >
              <LogOut className="w-4 h-4 shrink-0 text-red-400/60" />
              {sidebarOpen && <span className="text-[13px] font-medium text-red-400/60">Cerrar Sesión</span>}
            </button>
          </div>
        </aside>

        {/* 🔴 FIX: Backdrop para cerrar sidebar en móvil */}
        {isMobile && sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-30"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* ═══ MAIN ═══ */}
        <main className={`flex-1 overflow-y-auto ${isMobile && sidebarOpen ? 'hidden' : 'block'}`} style={{ paddingBottom: view === 'home' ? '20px' : chatOpen ? '340px' : '60px' }}>
          <div className="max-w-5xl mx-auto px-8 py-8">

            {/* Search Bar */}
            <div className="flex flex-col md:flex-row items-center gap-3 mb-8">
              <div className="relative w-full md:w-auto">
                <button onClick={() => setRoleOpen(!roleOpen)} className="w-full md:w-auto h-12 px-5 rounded-xl flex items-center gap-2.5 text-sm font-semibold transition-colors border border-white/[0.1] hover:border-white/[0.2]" style={{ background: 'rgba(255,255,255,0.05)' }}>
                  <Briefcase className="w-4 h-4 text-white/50" /><span className="text-white/80">{roles.find(r => r.value === role)?.label}</span><ChevronDown className="w-3.5 h-3.5 text-white/40" />
                </button>
                {roleOpen && (
                  <div className="absolute top-full mt-1.5 left-0 rounded-xl border border-white/[0.12] py-1 z-50 shadow-2xl min-w-[150px]" style={{ background: '#1C2128' }}>
                    {roles.map(r => (<button key={r.value} onClick={() => { setRole(r.value); setRoleOpen(false); }} className={`w-full text-left px-4 py-2.5 text-sm hover:bg-white/[0.08] transition-colors ${role === r.value ? 'text-white font-semibold' : 'text-white/60'}`}>{r.label}</button>))}
                  </div>
                )}
              </div>
              <div className="flex-1 w-full flex items-center h-12 rounded-xl border border-white/[0.1] px-5 gap-3 focus-within:border-[#01A982]/50 transition-colors" style={{ background: 'rgba(255,255,255,0.04)' }}>
                <Search className="w-5 h-5 text-white/30 shrink-0" />
                <input type="text" placeholder="Enter company name..." className="flex-1 bg-transparent outline-none text-white text-base placeholder-white/30"
                  value={company} onChange={e => setCompany(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleAnalyze()} />
                <span className="text-xs text-white/25 flex items-center gap-1.5 shrink-0"><Clock className="w-3.5 h-3.5" /> 3 months</span>
              </div>
              <button onClick={handleAnalyze} disabled={loading || !company}
                className="w-full md:w-auto h-12 px-7 rounded-xl font-bold text-base transition-all flex items-center justify-center gap-2.5 disabled:opacity-30 text-white shrink-0 hover:brightness-110"
                style={{ background: loading ? '#333' : '#01A982' }}>
                {loading ? <RefreshCw className="animate-spin w-5 h-5" /> : <ArrowRight className="w-5 h-5" />}
                {loading ? 'Scanning...' : 'Analyze'}
              </button>
            </div>

            {error && <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-300 rounded-xl mb-6 text-sm flex items-center gap-2"><AlertTriangle className="w-5 h-5 shrink-0" /> {error}</div>}

            {/* ═══ HOME VIEW (con Empty States mejorados) ═══ */}
            {view === 'home' && !loading && (
              <div className="space-y-8">
                {/* Top 5 Hero */}
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h1 className="text-3xl font-black text-white tracking-tight">Priority Accounts</h1>
                      <p className="text-sm text-white/35 mt-1">Top opportunities ranked by buying signal strength</p>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-white/30">
                      <Radar className="w-4 h-4" style={{ color: '#01A982' }} />
                      <span>Auto-scans every {scannerStatus?.interval_hours || 6}h</span>
                    </div>
                  </div>

                  {(() => {
                    const ranked = accounts.filter(a => a.last_score > 0).sort((a, b) => b.last_score - a.last_score).slice(0, 5);
                    
                    // 🔴 FIX: Empty State mejorado para Home
                    if (ranked.length === 0) return (
                      <div className="rounded-xl border border-white/[0.1] p-12 text-center">
                        <div className="w-20 h-20 rounded-full mx-auto mb-6 flex items-center justify-center" style={{ background: 'rgba(1,169,130,0.08)' }}>
                          <Target className="w-10 h-10" style={{ color: '#01A982' }} />
                        </div>
                        <h3 className="text-xl font-bold text-white mb-3">No Accounts Yet</h3>
                        <p className="text-white/40 mb-6 max-w-md mx-auto">
                          Start adding accounts to monitor buying signals and get AI-powered sales intelligence.
                        </p>
                        <button
                          onClick={() => setShowAddModal(true)}
                          className="inline-flex items-center gap-2 px-6 py-3 rounded-lg font-semibold text-white"
                          style={{ background: '#01A982' }}
                        >
                          <Plus className="w-5 h-5" />
                          Add Your First Account
                        </button>
                      </div>
                    );
                    
                    return (
                      <div className="space-y-3">
                        {ranked.map((acc, i) => {
                          const sc = acc.last_score >= 80 ? '#01A982' : acc.last_score >= 60 ? '#FFB900' : acc.last_score >= 40 ? '#FF8300' : '#FF4C4C';
                          const lbl = acc.last_score >= 80 ? 'CRITICAL' : acc.last_score >= 60 ? 'HIGH' : acc.last_score >= 40 ? 'MODERATE' : 'LOW';
                          const accAlerts = alerts.filter(a => a.account_id === acc.id && !a.is_read);
                          return (
                            <div key={acc.id}
                              onClick={() => selectAccount(acc)}
                              className={`rounded-2xl border cursor-pointer transition-all hover:scale-[1.005] hover:shadow-lg group ${
                                i === 0 ? 'border-[#01A982]/25' : 'border-white/[0.08] hover:border-white/[0.15]'
                              }`}
                              style={{
                                background: i === 0
                                  ? 'linear-gradient(135deg, rgba(1,169,130,0.08) 0%, rgba(1,169,130,0.02) 100%)'
                                  : 'rgba(255,255,255,0.025)'
                              }}>
                              <div className="flex items-center gap-5 px-6 py-5">
                                {/* Rank */}
                                <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 text-lg font-black ${
                                  i === 0 ? 'text-white' : ''
                                }`} style={{
                                  background: i === 0 ? '#01A982' : i < 3 ? 'rgba(1,169,130,0.15)' : 'rgba(255,255,255,0.06)',
                                  color: i === 0 ? 'white' : i < 3 ? '#01A982' : '#666'
                                }}>
                                  #{i + 1}
                                </div>

                                {/* Company Info */}
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-3">
                                    <h3 className={`font-bold truncate ${i === 0 ? 'text-xl text-white' : 'text-lg text-white/80'}`}>{acc.company_name}</h3>
                                    {accAlerts.length > 0 && (
                                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full animate-pulse" style={{ background: 'rgba(239,68,68,0.15)', color: '#EF4444' }}>
                                        {accAlerts.length} alert{accAlerts.length > 1 ? 's' : ''}
                                      </span>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-3 mt-1">
                                    {acc.industry && <span className="text-xs text-white/35 bg-white/[0.05] px-2.5 py-0.5 rounded-md">{acc.industry}</span>}
                                    {acc.last_product && acc.last_product !== 'None' && (
                                      <span className="text-xs font-medium" style={{ color: '#01A982' }}>{acc.last_product}</span>
                                    )}
                                    {acc.contact_name && <span className="text-xs text-white/30">{acc.contact_name}{acc.contact_role ? ` · ${acc.contact_role}` : ''}</span>}
                                  </div>
                                  {/* Why Now? — top trigger */}
                                  {topTriggers[acc.id] && topTriggers[acc.id].length > 0 && (() => {
                                    const t = topTriggers[acc.id][0];
                                    const IC = triggerIcon[t.type] || Zap;
                                    const ac = triggerAccent[t.type] || '#888';
                                    return (
                                      <div className="flex items-center gap-2 mt-2">
                                        <span className="text-[10px] font-bold uppercase tracking-wider text-yellow-500/70 shrink-0">Why now?</span>
                                        <div className="flex items-center gap-1.5 min-w-0">
                                          <IC className="w-3 h-3 shrink-0" style={{ color: ac }} />
                                          <span className="text-xs text-white/45 truncate">{t.type?.replace(/_/g, ' ')}: {t.description?.substring(0, 80)}{(t.description?.length || 0) > 80 ? '...' : ''}</span>
                                        </div>
                                        {topTriggers[acc.id].length > 1 && (
                                          <span className="text-[10px] text-white/25 shrink-0">+{topTriggers[acc.id].length - 1} more</span>
                                        )}
                                      </div>
                                    );
                                  })()}
                                </div>

                                {/* Score */}
                                <div className="text-right shrink-0">
                                  <div className="flex items-baseline gap-1 justify-end">
                                    <span className={`font-black ${i === 0 ? 'text-4xl' : 'text-3xl'}`} style={{ color: sc }}>{acc.last_score}</span>
                                    <span className="text-xs text-white/20">/100</span>
                                  </div>
                                  <p className="text-[10px] uppercase tracking-[0.15em] font-bold mt-0.5" style={{ color: sc }}>{lbl}</p>
                                  <div className="w-20 h-1.5 rounded-full bg-white/[0.08] mt-2 ml-auto overflow-hidden">
                                    <div className="h-full rounded-full" style={{ width: `${acc.last_score}%`, background: sc }} />
                                  </div>
                                </div>

                                {/* Arrow */}
                                <ArrowRight className="w-5 h-5 text-white/20 group-hover:text-white/50 transition-colors shrink-0" />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    );
                  })()}
                </div>

                {/* Inline Chat on Home */}
                <div className="rounded-2xl border border-white/[0.08] overflow-hidden" style={{ background: 'rgba(255,255,255,0.02)' }}>
                  <div className="px-6 py-4 border-b border-white/[0.08] flex items-center gap-3" style={{ background: 'rgba(22,27,34,0.6)' }}>
                    <Bot className="w-5 h-5" style={{ color: '#01A982' }} />
                    <span className="text-sm font-semibold text-white/60">AI Assistant</span>
                    <span className="text-xs text-white/25">— Ask about HPE products, accounts, or sales strategies</span>
                  </div>
                  <div className="h-[280px] overflow-y-auto px-6 py-4 space-y-4">
                    {homeChatMessages.length === 0 && (
                      <div className="text-center py-8">
                        <Bot className="w-10 h-10 text-white/10 mx-auto mb-3" />
                        <p className="text-sm text-white/25 mb-4">Ask anything about HPE solutions, sales strategies, or account research.</p>
                        <div className="flex gap-2 justify-center flex-wrap">
                          {['Which HPE products fit hybrid cloud?', 'How to pitch HPE GreenLake?', 'Search latest IT spending trends', 'Compare HPE vs Dell for storage'].map((s, i) => (
                            <button key={i} onClick={() => setHomeChatInput(s)} className="text-xs text-white/35 bg-white/[0.04] px-4 py-2 rounded-full border border-white/[0.07] hover:bg-white/[0.08] transition-colors">{s}</button>
                          ))}
                        </div>
                      </div>
                    )}
                    {homeChatMessages.map((m, i) => (
                      <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : ''}`}>
                        {m.role === 'assistant' && <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5" style={{ background:'rgba(1,169,130,0.18)' }}><Bot className="w-3.5 h-3.5" style={{ color:'#01A982' }} /></div>}
                        <div className={`max-w-[70%] rounded-xl px-4 py-3 text-sm leading-relaxed ${m.role === 'user' ? 'bg-white/[0.1] text-white/80' : 'text-white/60'}`} style={m.role === 'assistant' ? { background:'rgba(1,169,130,0.05)' } : {}}>
                          {m.role === 'assistant' ? <ChatMarkdown content={m.content} /> : <p className="whitespace-pre-line">{m.content}</p>}
                        </div>
                        {m.role === 'user' && <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 bg-white/[0.1]"><UserIcon className="w-3.5 h-3.5 text-white/50" /></div>}
                      </div>
                    ))}
                    {homeChatLoading && <div className="flex gap-3"><div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background:'rgba(1,169,130,0.18)' }}><Bot className="w-3.5 h-3.5 animate-pulse" style={{ color:'#01A982' }} /></div><div className="text-sm text-white/40 py-2.5">Thinking...</div></div>}
                    <div ref={homeChatEndRef} />
                  </div>
                  <div className="px-6 py-3.5 border-t border-white/[0.08]" style={{ background: 'rgba(22,27,34,0.4)' }}>
                    <div className="flex items-center gap-3">
                      <input type="text" placeholder="Ask anything... (use 'search' for web lookup)"
                        className="flex-1 bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-3 text-sm text-white placeholder-white/30 outline-none focus:border-[#01A982]/50"
                        value={homeChatInput} onChange={e => setHomeChatInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendHomeChat()} />
                      <button onClick={sendHomeChat} disabled={homeChatLoading || !homeChatInput.trim()}
                        className="w-10 h-10 rounded-xl flex items-center justify-center disabled:opacity-20 hover:brightness-110 transition-all" style={{ background: '#01A982' }}>
                        <Send className="w-4 h-4 text-white" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {loading && (
              <div className="flex flex-col items-center justify-center py-24">
                <RefreshCw className="w-10 h-10 animate-spin mb-5" style={{ color: '#01A982' }} />
                <p className="text-base text-white/50">Analyzing <span className="text-white/70 font-semibold">{company}</span>...</p>
                <p className="text-sm text-white/30 mt-2">Scanning news, financials, tech stack</p>
              </div>
            )}

            {/* ... resto del código igual ... (Account view, Analysis view con Empty States mejorados en triggers/tech) */}

            {analysis && view === 'analysis' && webData?.triggers && (
              <div>
                {/* 🔴 FIX: Empty State mejorado para Triggers */}
                {webData.triggers.length === 0 ? (
                  <div className="rounded-xl border border-white/[0.06] p-8 text-center" style={{ background: 'rgba(255,255,255,0.02)' }}>
                    <div className="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center" style={{ background: 'rgba(1,169,130,0.1)' }}>
                      <Radar className="w-8 h-8 text-[#01A982]/50" />
                    </div>
                    <h4 className="text-white font-semibold mb-2">No Active Signals</h4>
                    <p className="text-white/40 text-sm mb-4">
                      No recent infrastructure buying signals detected for {analyzedCompany}.
                    </p>
                    <p className="text-white/30 text-xs mb-4">
                      This company might be in a stable operations phase, or recent news hasn't captured IT-related activities.
                    </p>
                    <button
                      onClick={() => setChatOpen(true)}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium"
                      style={{ background: 'rgba(1,169,130,0.15)', color: '#01A982' }}
                    >
                      <MessageSquare className="w-4 h-4" />
                      Ask AI about this sector
                    </button>
                  </div>
                ) : (
                  <div>
                    <SectionToggle label="Buying Signals" icon={Zap} color="#EAB308" open={showSignals} onToggle={() => setShowSignals(!showSignals)} count={webData.triggers.length} />
                    {showSignals && (
                      <div className="grid md:grid-cols-2 gap-4">
                        {webData.triggers.map((t, i) => {
                          const IC = triggerIcon[t.type] || Zap; const ac = triggerAccent[t.type] || '#888';
                          return (
                            <div key={i} className="rounded-xl p-5 border border-white/[0.06] hover:border-white/[0.1] transition-colors" style={{ background: `linear-gradient(135deg, ${ac}08 0%, transparent 100%)` }}>
                              <div className="flex items-start gap-3">
                                <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" style={{ background: `${ac}15` }}><IC className="w-4.5 h-4.5" style={{ color: ac }} /></div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2.5 mb-1.5">
                                    <span className="text-xs font-bold uppercase tracking-wider" style={{ color: ac }}>{t.type.replace(/_/g, ' ')}</span>
                                    {t.date && <span className="text-xs text-white/30 flex items-center gap-1"><Calendar className="w-3 h-3" /> {t.date}</span>}
                                  </div>
                                  <p className="text-sm text-white/55 leading-relaxed">{t.description}</p>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Aquí iría el resto del código de Analysis y Account views que ya existe... */}
            {/* Por brevedad no lo repito, pero DEBE incluirse tal como estaba */}

          </div>
        </main>
      </div>

      {/* Resto de modales y chat drawer igual... */}

      {roleOpen && <div className="fixed inset-0 z-40" onClick={() => setRoleOpen(false)} />}
      {alertsOpen && <div className="fixed inset-0 z-40" onClick={() => setAlertsOpen(false)} />}
    </div>
  );
}

export default App;
