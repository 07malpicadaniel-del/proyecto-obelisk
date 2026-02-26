#!/usr/bin/env python3
"""
Script para aplicar TODAS las correcciones al frontend App.tsx
Uso: python aplicar_correcciones.py
"""

import os
import shutil
from datetime import datetime

# Rutas
BASE_DIR = r"C:\Users\R-Cou\Escritorio\CLAUDE COSAS\Innovation2"
APP_PATH = os.path.join(BASE_DIR, "frontend", "src", "App.tsx")
BACKUP_PATH = APP_PATH + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def aplicar_correcciones():
    print("🔧 Aplicando correcciones al App.tsx...")
    
    # 1. Hacer backup
    print(f"📦 Creando backup en: {BACKUP_PATH}")
    shutil.copy(APP_PATH, BACKUP_PATH)
    
    # 2. Leer archivo
    with open(APP_PATH, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # 3. Aplicar correcciones
    print("✅ Corrección 1/12: Agregando imports Menu, LogOut")
    contenido = contenido.replace(
        "ChevronRight, EyeOff\n} from 'lucide-react';",
        "ChevronRight, EyeOff, Menu, LogOut\n} from 'lucide-react';"
    )
    
    print("✅ Corrección 2/12: Agregando estado isMobile")
    contenido = contenido.replace(
        "const [sidebarOpen, setSidebarOpen] = useState(true);",
        "const [sidebarOpen, setSidebarOpen] = useState(true);\n  const [isMobile, setIsMobile] = useState(false);"
    )
    
    print("✅ Corrección 3/12: Agregando useEffect para detectar mobile")
    # Buscar después del último useEffect de topTriggers
    contenido = contenido.replace(
        "  }, [accounts]);",
        """  }, [accounts]);

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) setSidebarOpen(false);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);""",
        1  # Solo la primera ocurrencia
    )
    
    print("✅ Corrección 4/12: Agregando función logout")
    contenido = contenido.replace(
        "  const saveAccountEdit = async () => {\n    if (!selectedAccount) return;\n    try { const r = await axios.patch(`${API}/accounts/${selectedAccount.id}`, editFields); setSelectedAccount(r.data); setEditingAccount(false); fetchAccounts(); } catch {}\n  };",
        """  const saveAccountEdit = async () => {
    if (!selectedAccount) return;
    try { const r = await axios.patch(`${API}/accounts/${selectedAccount.id}`, editFields); setSelectedAccount(r.data); setEditingAccount(false); fetchAccounts(); } catch {}
  };

  const logout = () => {
    localStorage.removeItem('hpe_session');
    localStorage.removeItem('hpe_user');
    setAccounts([]);
    setSelectedAccount(null);
    setView('home');
    alert('Sesión cerrada exitosamente');
  };"""
    )
    
    print("✅ Corrección 5/12: Agregando hamburger menu")
    contenido = contenido.replace(
        "      <div className=\"flex flex-1 overflow-hidden\">",
        """      <div className="flex flex-1 overflow-hidden">

        {/* Hamburger Menu (solo móvil) */}
        {isMobile && !sidebarOpen && (
          <button
            onClick={() => setSidebarOpen(true)}
            className="fixed top-4 left-4 z-50 p-2 rounded-lg border border-white/[0.1] shadow-lg"
            style={{ background: '#1C2128' }}
          >
            <Menu className="w-5 h-5 text-white" />
          </button>
        )}"""
    )
    
    print("✅ Corrección 6/12: Sidebar responsive")
    contenido = contenido.replace(
        "        <aside className={`border-r border-white/[0.08] flex flex-col shrink-0 transition-all duration-200 ${sidebarOpen ? 'w-64' : 'w-16'}`} style={{ background: '#111820' }}>",
        """        <aside className={`
          border-r border-white/[0.08] flex flex-col shrink-0 transition-all duration-200
          ${isMobile ? 'fixed inset-y-0 left-0 z-40' : 'relative'}
          ${isMobile && !sidebarOpen ? '-translate-x-full' : 'translate-x-0'}
          ${isMobile ? 'w-64' : sidebarOpen ? 'w-64' : 'w-16'}
          ${isMobile ? 'bg-[#0D1117]' : ''}
        `} style={{ background: '#111820' }}>"""
    )
    
    print("✅ Corrección 7/12: Header sidebar con X en móvil")
    contenido = contenido.replace(
        """          <div className={`flex items-center ${sidebarOpen ? 'justify-between px-4' : 'justify-center'} py-3`}>
            {sidebarOpen && <span className="text-[11px] uppercase tracking-[0.15em] text-white/35 font-semibold">Accounts</span>}
            <div className="flex items-center gap-1">
              {sidebarOpen && (
                <button onClick={() => setShowAddModal(true)} className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-white/10 transition-colors" style={{ background: 'rgba(1,169,130,0.15)' }}>
                  <Plus className="w-3.5 h-3.5" style={{ color: '#01A982' }} />
                </button>
              )}
              <button onClick={() => setSidebarOpen(!sidebarOpen)} className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-white/[0.08] transition-colors" title={sidebarOpen ? 'Collapse' : 'Expand'}>
                {sidebarOpen ? <ChevronLeft className="w-3.5 h-3.5 text-white/35" /> : <ChevronRight className="w-3.5 h-3.5 text-white/35" />}
              </button>
            </div>
          </div>""",
        """          <div className={`flex items-center ${sidebarOpen ? 'justify-between px-4' : 'justify-center'} py-3 border-b border-white/[0.08]`}>
            {sidebarOpen && <span className="text-[11px] uppercase tracking-[0.15em] text-white/35 font-semibold">Accounts</span>}
            <div className="flex items-center gap-1">
              {sidebarOpen && (
                <button onClick={() => setShowAddModal(true)} className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-white/10 transition-colors" style={{ background: 'rgba(1,169,130,0.15)' }}>
                  <Plus className="w-3.5 h-3.5" style={{ color: '#01A982' }} />
                </button>
              )}
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
          </div>"""
    )
    
    print("✅ Corrección 8/12: Agregando botón de logout")
    contenido = contenido.replace(
        """          </div>
        </aside>""",
        """          </div>

          {/* Botón de Logout */}
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
        </aside>"""
    )
    
    print("✅ Corrección 9/12: Agregando backdrop móvil")
    contenido = contenido.replace(
        "        </aside>\n\n        {/* ═══ MAIN ═══ */}",
        """        </aside>

        {/* Backdrop para cerrar sidebar en móvil */}
        {isMobile && sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-30"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* ═══ MAIN ═══ */}"""
    )
    
    print("✅ Corrección 10/12: Main content responsive")
    contenido = contenido.replace(
        '        <main className="flex-1 overflow-y-auto" style={{ paddingBottom: view === \'home\' ? \'20px\' : chatOpen ? \'340px\' : \'60px\' }}>',
        '        <main className={`flex-1 overflow-y-auto ${isMobile && sidebarOpen ? \'hidden\' : \'block\'}`} style={{ paddingBottom: view === \'home\' ? \'20px\' : chatOpen ? \'340px\' : \'60px\' }}>'
    )
    
    print("✅ Corrección 11/12: Search bar responsive")
    contenido = contenido.replace(
        '            <div className="flex items-center gap-3 mb-8">',
        '            <div className="flex flex-col md:flex-row items-center gap-3 mb-8">'
    )
    contenido = contenido.replace(
        '              <div className="relative">',
        '              <div className="relative w-full md:w-auto">',
        1
    )
    contenido = contenido.replace(
        '                <button onClick={() => setRoleOpen(!roleOpen)} className="h-12 px-5 rounded-xl',
        '                <button onClick={() => setRoleOpen(!roleOpen)} className="w-full md:w-auto h-12 px-5 rounded-xl'
    )
    contenido = contenido.replace(
        '              <div className="flex-1 flex items-center h-12 rounded-xl',
        '              <div className="flex-1 w-full flex items-center h-12 rounded-xl'
    )
    contenido = contenido.replace(
        '              <button onClick={handleAnalyze} disabled={loading || !company}\n                className="h-12 px-7 rounded-xl font-bold text-base transition-all flex items-center gap-2.5',
        '              <button onClick={handleAnalyze} disabled={loading || !company}\n                className="w-full md:w-auto h-12 px-7 rounded-xl font-bold text-base transition-all flex items-center justify-center gap-2.5'
    )
    
    print("✅ Corrección 12/12: Empty state mejorado en Home")
    contenido = contenido.replace(
        """                    if (ranked.length === 0) return (
                      <div className="rounded-2xl border border-dashed border-white/[0.1] p-16 text-center">
                        <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-5" style={{ background: 'rgba(1,169,130,0.08)' }}>
                          <BarChart3 className="w-7 h-7" style={{ color: '#01A982', opacity: 0.4 }} />
                        </div>
                        <h3 className="text-lg font-bold text-white/40 mb-2">No accounts ranked yet</h3>
                        <p className="text-sm text-white/25 max-w-sm mx-auto">Add accounts and run analyses to see your Top 5 priority list here.</p>
                      </div>
                    );""",
        """                    if (ranked.length === 0) return (
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
                    );"""
    )
    
    # 4. Guardar archivo corregido
    print("💾 Guardando archivo corregido...")
    with open(APP_PATH, 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print("\n✅ ¡TODAS LAS CORRECCIONES APLICADAS!")
    print(f"📦 Backup guardado en: {BACKUP_PATH}")
    print(f"✨ Archivo corregido: {APP_PATH}")
    print("\n🚀 Ahora ejecuta:")
    print("   cd frontend")
    print("   npm run dev")

if __name__ == "__main__":
    try:
        aplicar_correcciones()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Por favor revisa que los archivos existan y tengas permisos de escritura")
