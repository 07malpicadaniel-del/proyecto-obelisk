import { useState } from 'react';
import axios from 'axios';
import { 
  Search, Server, AlertTriangle, CheckCircle, Zap, ArrowRight, 
  Activity, Terminal, Users, Globe, Cpu, TrendingUp, Mail, Copy 
} from 'lucide-react';

// --- TIPOS DE DATOS (Lo que el Backend nos manda) ---
interface Trigger {
  type: string;
  description: string;
  sentiment?: string;
}

interface WebData {
  industry?: string;
  tech_stack: string[];
  competitors: string[];
  triggers: Trigger[];
  fit_score_reasoning?: string;
}

interface ParsedAnalysis {
  resumen_ejecutivo: string;
  pain_points: string[] | string;
  solucion_hpe_recomendada: string | any;
  speech_ventas: string;
}

function App() {
  // --- ESTADOS ---
  const [company, setCompany] = useState('');
  const [role, setRole] = useState('CEO');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Datos de la IA
  const [analysis, setAnalysis] = useState<ParsedAnalysis | null>(null);
  const [webData, setWebData] = useState<WebData | null>(null);
  const [sources, setSources] = useState<string[]>([]);
  
  // Estado para el Modal de Email
  const [showEmailModal, setShowEmailModal] = useState(false);

  // --- LÓGICA DE SCORE (Simulada para la Demo) ---
  const calculateScore = () => {
    if (!webData) return 0;
    let score = 60; // Base
    score += (webData.triggers?.length || 0) * 10;
    score += (webData.tech_stack?.length || 0) * 5;
    if (analysis?.solucion_hpe_recomendada) score += 10;
    return Math.min(score, 98); // Tope en 98
  };

  const score = calculateScore();

  // --- FUNCIÓN PRINCIPAL ---
  const handleAnalyze = async () => {
    if (!company) return;
    
    setLoading(true);
    setError('');
    setAnalysis(null);
    setWebData(null);
    setSources([]);
    setShowEmailModal(false);

    try {
      console.log(`📡 Analizando: ${company} (${role})`);

      const response = await axios.post('http://127.0.0.1:8000/analyze', {
        company_name: company,
        url: "http://ignore.me",
        target_role: role 
      });

      // 1. Guardar metadatos
      setSources(response.data.sources || []);
      setWebData(response.data.web_data || { tech_stack: [], triggers: [], competitors: [] });

      // 2. Limpiar el JSON del Speech
      const rawJson = response.data.analysis_json;
      let cleanData: ParsedAnalysis | null = null;

      if (typeof rawJson === 'object') {
        cleanData = rawJson;
      } else if (typeof rawJson === 'string') {
        try {
          cleanData = JSON.parse(rawJson);
        } catch (e) {
          // Intento de rescate con Regex
          const jsonMatch = rawJson.match(/\{[\s\S]*\}/);
          if (jsonMatch) cleanData = JSON.parse(jsonMatch[0]);
        }
      }

      if (cleanData) {
        // Normalizar campos que a veces llegan como objetos
        if (typeof cleanData.solucion_hpe_recomendada === 'object') {
             cleanData.solucion_hpe_recomendada = JSON.stringify(cleanData.solucion_hpe_recomendada);
        }
        setAnalysis(cleanData);
      } else {
        setError("La IA respondió, pero el formato no fue perfecto.");
      }

    } catch (err) {
      console.error("🔥 Error:", err);
      setError('Error de conexión. Asegúrate que el Backend esté corriendo.');
    } finally {
      setLoading(false);
    }
  };

  // Renderizar un Trigger con color según tipo
  const renderTrigger = (t: Trigger, i: number) => {
    let icon = <Activity className="w-4 h-4 text-blue-400" />;
    let colorClass = "border-blue-500/30 bg-blue-500/10 text-blue-200";

    if (t.type.includes("EXPANSION")) {
      icon = <TrendingUp className="w-4 h-4 text-emerald-400" />;
      colorClass = "border-emerald-500/30 bg-emerald-500/10 text-emerald-200";
    } else if (t.type.includes("TECNOLOGIA") || t.type.includes("TECH")) {
      icon = <Cpu className="w-4 h-4 text-purple-400" />;
      colorClass = "border-purple-500/30 bg-purple-500/10 text-purple-200";
    }

    return (
      <div key={i} className={`flex items-start gap-3 p-3 rounded-lg border ${colorClass} mb-2`}>
        <div className="mt-1">{icon}</div>
        <div>
          <p className="text-xs font-bold opacity-70 uppercase">{t.type}</p>
          <p className="text-sm font-medium">{t.description}</p>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen font-sans text-slate-100 selection:bg-emerald-500 selection:text-white pb-20 bg-[#0f172a]">
      
      {/* HEADER */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-[#01A982] p-1.5 rounded-sm">
              <Server className="text-white w-5 h-5" />
            </div>
            <h1 className="text-lg font-bold tracking-tight">HPE <span className="font-light text-emerald-400">Sales Guardian</span></h1>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-emerald-500 bg-emerald-950/30 px-3 py-1 rounded-full border border-emerald-900">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            SYSTEM ONLINE
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 mt-12">
        
        {/* BUSCADOR */}
        <div className="max-w-4xl mx-auto mb-12">
          <div className="text-center mb-8">
            <h2 className="text-4xl font-extrabold tracking-tight text-white mb-2">
              Radar de Oportunidades
            </h2>
            <p className="text-slate-400">
              Detecta Triggers Operacionales y genera estrategias de venta en tiempo real.
            </p>
          </div>
          
          <div className="flex flex-col md:flex-row bg-slate-900 rounded-lg p-2 border border-slate-700 shadow-2xl gap-2 relative z-10">
            <div className="relative md:w-1/3 border-b md:border-b-0 md:border-r border-slate-700">
              <Users className="absolute left-3 top-3.5 h-5 w-5 text-emerald-500" />
              <select 
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full h-12 bg-transparent text-white pl-10 pr-8 rounded-md outline-none appearance-none cursor-pointer font-medium hover:bg-slate-800 transition-colors"
              >
                <option value="CEO">Estrategia (CEO)</option>
                <option value="CTO">Técnico (CTO)</option>
                <option value="Vendedor">Ventas (Express)</option>
              </select>
            </div>
            <input 
              type="text" 
              placeholder="Ej: Cemex, Walmart, Tesla..."
              className="flex-1 bg-transparent outline-none px-4 text-white placeholder-slate-500 h-12 text-lg"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
            />
            <button 
              onClick={handleAnalyze}
              disabled={loading || !company}
              className="bg-[#01A982] hover:bg-emerald-600 text-white px-8 h-12 rounded-md font-bold transition-all flex items-center gap-2 disabled:opacity-50 shadow-[0_0_15px_rgba(1,169,130,0.4)]"
            >
              {loading ? <Activity className="animate-spin" /> : <Search />}
              {loading ? 'Analizando...' : 'Escanear'}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-950/30 border border-red-900/50 text-red-200 rounded-lg mb-8 text-center animate-in fade-in">
            <AlertTriangle className="inline w-5 h-5 mr-2" /> {error}
          </div>
        )}

        {/* --- RESULTADOS DEL DASHBOARD --- */}
        {analysis && webData && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-700">
            
            {/* 1. BARRA SUPERIOR: SCORE + TECH STACK */}
            <div className="grid md:grid-cols-3 gap-6">
              
              {/* Tarjeta de Score */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10">
                  <Activity className="w-24 h-24 text-emerald-500" />
                </div>
                <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-2">HPE Opportunity Index</h3>
                <div className="flex items-end gap-3">
                  <span className={`text-6xl font-black ${score > 80 ? 'text-[#01A982]' : 'text-yellow-500'}`}>
                    {score}
                  </span>
                  <span className="text-xl text-slate-500 mb-2">/100</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full mt-4 overflow-hidden">
                  <div 
                    className={`h-full ${score > 80 ? 'bg-[#01A982]' : 'bg-yellow-500'} transition-all duration-1000`} 
                    style={{ width: `${score}%` }}
                  ></div>
                </div>
                <p className="text-slate-400 text-sm mt-3">
                  {webData.triggers?.length > 0 ? "Detectados eventos de expansión de alto valor." : "Oportunidad basada en alineación tecnológica."}
                </p>
              </div>

              {/* Tarjeta de Tech Stack */}
              <div className="md:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
                <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-4 flex items-center gap-2">
                  <Cpu className="w-4 h-4" /> Tech Stack Detectado
                </h3>
                {webData.tech_stack?.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {webData.tech_stack.map((tech, i) => (
                      <span key={i} className="px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-slate-200 text-sm font-medium flex items-center gap-2">
                        <Terminal className="w-3 h-3 text-emerald-500" /> {tech}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 italic text-sm">No se detectó stack público específico.</p>
                )}
                
                {/* Competidores (Si hay) */}
                {webData.competitors?.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-slate-800">
                    <h4 className="text-xs text-red-400 font-bold mb-2">COMPETENCIA DETECTADA</h4>
                    <div className="flex gap-2">
                      {webData.competitors.map((comp, i) => (
                        <span key={i} className="text-xs px-2 py-1 bg-red-950/30 text-red-200 border border-red-900/50 rounded">
                          {comp}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* 2. ZONA CENTRAL: TRIGGERS + ESTRATEGIA */}
            <div className="grid md:grid-cols-12 gap-6">
              
              {/* Columna Izquierda: Triggers (3 cols) */}
              <div className="md:col-span-4 space-y-4">
                <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 h-full">
                  <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-4 flex items-center gap-2">
                    <Zap className="w-4 h-4 text-yellow-500" /> Triggers Operacionales
                  </h3>
                  {webData.triggers?.length > 0 ? (
                    <div className="space-y-2">
                      {webData.triggers.map((t, i) => renderTrigger(t, i))}
                    </div>
                  ) : (
                    <p className="text-slate-500 text-sm italic">No se detectaron eventos recientes en noticias públicas.</p>
                  )}
                </div>
              </div>

              {/* Columna Derecha: Estrategia (8 cols) */}
              <div className="md:col-span-8 space-y-6">
                
                {/* Tarjeta Principal de Solución */}
                <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-xl p-8 relative overflow-hidden group">
                  <div className="relative z-10">
                    <div className="flex items-center gap-3 mb-4">
                      <span className="bg-[#01A982]/20 text-[#01A982] px-3 py-1 rounded-full text-xs font-bold border border-[#01A982]/30 uppercase">
                        RECOMENDACIÓN
                      </span>
                      <h2 className="text-2xl font-bold text-white">
                        {String(analysis.solucion_hpe_recomendada).replace(/["{}]/g, '')}
                      </h2>
                    </div>
                    
                    <p className="text-slate-300 leading-relaxed mb-6">
                      {analysis.resumen_ejecutivo}
                    </p>

                    <div className="bg-black/30 rounded-lg p-5 border-l-4 border-[#01A982]">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="text-slate-500 text-xs uppercase font-bold tracking-widest">
                          Speech Sugerido ({role})
                        </h4>
                        <button 
                          onClick={() => setShowEmailModal(true)}
                          className="text-xs bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1 rounded flex items-center gap-1 transition-colors"
                        >
                          <Mail className="w-3 h-3" /> Generar Email
                        </button>
                      </div>
                      <p className="text-emerald-50 italic text-sm md:text-base leading-relaxed">
                        "{analysis.speech_ventas}"
                      </p>
                    </div>
                  </div>
                </div>

                {/* Pain Points */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                   <h3 className="text-red-400 text-xs font-bold uppercase tracking-widest mb-3 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" /> Puntos de Dolor
                  </h3>
                  <div className="grid md:grid-cols-2 gap-3">
                    {Array.isArray(analysis.pain_points) ? analysis.pain_points.map((p, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm text-slate-300">
                        <span className="text-red-500">•</span> {p}
                      </div>
                    )) : <p className="text-slate-400 text-sm">{String(analysis.pain_points)}</p>}
                  </div>
                </div>

              </div>
            </div>

            {/* Fuentes */}
            <div className="flex justify-center gap-3 text-xs text-slate-500 pb-8">
              <span>Fuentes:</span>
              {sources.map((s, i) => (
                <span key={i} className="flex items-center gap-1 bg-slate-800 px-2 py-0.5 rounded text-slate-300">
                  <Globe className="w-3 h-3" /> {s}
                </span>
              ))}
            </div>

          </div>
        )}
      </main>

      {/* --- MODAL DE EMAIL --- */}
      {showEmailModal && analysis && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-2xl w-full shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Mail className="w-5 h-5 text-emerald-500" /> Borrador de Correo
              </h3>
              <button onClick={() => setShowEmailModal(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>
            <div className="p-6 space-y-4">
              <div className="space-y-1">
                <label className="text-xs text-slate-500 uppercase font-bold">Asunto Sugerido</label>
                <input 
                  type="text" 
                  defaultValue={`Oportunidad estratégica para ${company} - Solución HPE`}
                  className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-slate-200 text-sm"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-slate-500 uppercase font-bold">Cuerpo del Correo</label>
                <textarea 
                  rows={8}
                  className="w-full bg-slate-950 border border-slate-700 rounded p-3 text-slate-200 text-sm leading-relaxed"
                  defaultValue={`Hola [Nombre],\n\n${analysis.speech_ventas}\n\nQuedo atento para agendar una breve llamada.\n\nSaludos,\n[Tu Nombre]`}
                />
              </div>
            </div>
            <div className="p-4 border-t border-slate-800 flex justify-end gap-3 bg-slate-900/50 rounded-b-xl">
              <button 
                onClick={() => setShowEmailModal(false)}
                className="px-4 py-2 text-sm text-slate-300 hover:text-white"
              >
                Cancelar
              </button>
              <button className="bg-[#01A982] hover:bg-emerald-600 text-white px-4 py-2 rounded text-sm font-medium flex items-center gap-2">
                <Copy className="w-4 h-4" /> Copiar y Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;