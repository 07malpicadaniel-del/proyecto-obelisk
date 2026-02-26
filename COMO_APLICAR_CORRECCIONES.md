# 🔧 APLICAR CORRECCIONES AL APP.TSX

## ⚡ Opción Rápida: Reemplazar Imports (Línea 1-15)

**REEMPLAZA las líneas 1-15 con:**

```typescript
import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import {
  Search, Server, AlertTriangle, Zap, Activity, Terminal, Users, Globe, Cpu, Copy,
  ShieldAlert, XCircle, MessageSquare, Calendar, TrendingUp, Shield, Layers,
  Clock, Plus, ChevronDown, ChevronUp, Send, Building2, Trash2, BarChart3, ArrowRight,
  X, Briefcase, RefreshCw, Bot, User as UserIcon, Edit3, Save, History, FileText, ChevronLeft,
  ExternalLink, Info, CheckCircle2, Target, Bell, Radio, Radar, Eye, XOctagon,
  ChevronRight, EyeOff, Menu, LogOut  // 🔴 AGREGADOS: Menu, LogOut
} from 'lucide-react';
```

---

## 📱 Corrección 1: Estado Mobile (Línea ~110)

**DESPUÉS de la línea:**
```typescript
const [sidebarOpen, setSidebarOpen] = useState(true);
```

**AGREGA:**
```typescript
// 🔴 FIX: Mobile responsive state
const [isMobile, setIsMobile] = useState(false);
```

---

## 📱 Corrección 2: Detectar Mobile (Línea ~140, después de otros useEffect)

**AGREGA este useEffect COMPLETO:**

```typescript
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
```

---

## 🚪 Corrección 3: Función Logout (Línea ~200, después de saveAccountEdit)

**AGREGA esta función COMPLETA:**

```typescript
// 🔴 FIX: Logout function
const logout = () => {
  localStorage.removeItem('hpe_session');
  localStorage.removeItem('hpe_user');
  setAccounts([]);
  setSelectedAccount(null);
  setView('home');
  alert('Sesión cerrada exitosamente');
};
```

---

## 🍔 Corrección 4: Hamburger Menu (Línea ~380, ANTES del sidebar)

**BUSCA:**
```typescript
<div className="flex flex-1 overflow-hidden">
```

**INMEDIATAMENTE DESPUÉS, AGREGA:**

```typescript
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
```

---

## 📱 Corrección 5: Sidebar Responsive (Línea ~390)

**BUSCA:**
```typescript
<aside className={`border-r border-white/[0.08] flex flex-col shrink-0 transition-all duration-200 ${sidebarOpen ? 'w-64' : 'w-16'}`}
```

**REEMPLAZA CON:**

```typescript
<aside className={`
  border-r border-white/[0.08] flex flex-col shrink-0 transition-all duration-200
  ${isMobile ? 'fixed inset-y-0 left-0 z-40' : 'relative'}
  ${isMobile && !sidebarOpen ? '-translate-x-full' : 'translate-x-0'}
  ${isMobile ? 'w-64' : sidebarOpen ? 'w-64' : 'w-16'}
  ${isMobile ? 'bg-[#0D1117]' : ''}
`} style={{ background: '#111820' }}>
```

---

## 📱 Corrección 6: Header del Sidebar (Línea ~395)

**BUSCA:**
```typescript
<div className={`flex items-center ${sidebarOpen ? 'justify-between px-4' : 'justify-center'} py-3`}>
```

**REEMPLAZA CON:**

```typescript
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
```

---

## 🚪 Corrección 7: Botón de Logout en Sidebar (Línea ~550, DESPUÉS del Dashboard button)

**BUSCA:**
```typescript
</div> {/* fin del Dashboard button div */}
```

**INMEDIATAMENTE DESPUÉS, AGREGA:**

```typescript
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
```

---

## 📱 Corrección 8: Backdrop Mobile (Línea ~560, DESPUÉS del sidebar)

**BUSCA:**
```typescript
</aside> {/* fin del sidebar */}
```

**INMEDIATAMENTE DESPUÉS, AGREGA:**

```typescript
{/* 🔴 FIX: Backdrop para cerrar sidebar en móvil */}
{isMobile && sidebarOpen && (
  <div
    className="fixed inset-0 bg-black/50 z-30"
    onClick={() => setSidebarOpen(false)}
  />
)}
```

---

## 📱 Corrección 9: Main Content Responsive (Línea ~565)

**BUSCA:**
```typescript
<main className="flex-1 overflow-y-auto"
```

**REEMPLAZA CON:**

```typescript
<main className={`flex-1 overflow-y-auto ${isMobile && sidebarOpen ? 'hidden' : 'block'}`}
```

---

## 📱 Corrección 10: Search Bar Responsive (Línea ~575)

**BUSCA:**
```typescript
<div className="flex items-center gap-3 mb-8">
```

**REEMPLAZA CON:**

```typescript
<div className="flex flex-col md:flex-row items-center gap-3 mb-8">
```

**Y en el botón de Role:**

**BUSCA:**
```typescript
<div className="relative">
  <button onClick={() => setRoleOpen(!roleOpen)} className="h-12 px-5
```

**REEMPLAZA CON:**

```typescript
<div className="relative w-full md:w-auto">
  <button onClick={() => setRoleOpen(!roleOpen)} className="w-full md:w-auto h-12 px-5
```

**Y en el input de búsqueda:**

**BUSCA:**
```typescript
<div className="flex-1 flex items-center h-12
```

**REEMPLAZA CON:**

```typescript
<div className="flex-1 w-full flex items-center h-12
```

**Y en el botón de Analyze:**

**BUSCA:**
```typescript
<button onClick={handleAnalyze} disabled={loading || !company}
  className="h-12 px-7 rounded-xl font-bold text-base transition-all flex items-center gap-2.5 disabled:opacity-30 text-white shrink-0
```

**REEMPLAZA CON:**

```typescript
<button onClick={handleAnalyze} disabled={loading || !company}
  className="w-full md:w-auto h-12 px-7 rounded-xl font-bold text-base transition-all flex items-center justify-center gap-2.5 disabled:opacity-30 text-white shrink-0
```

---

## 📭 Corrección 11: Empty State Home (Línea ~680)

**BUSCA el código que dice:**
```typescript
if (ranked.length === 0) return (
  <div className="rounded-2xl border border-dashed
```

**REEMPLAZA ESE BLOQUE COMPLETO CON:**

```typescript
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
```

---

## 📭 Corrección 12: Empty State Triggers (BUSCA en Analysis view, línea ~900+)

**BUSCA donde renderiza los triggers:**

**AGREGA esta lógica ANTES de mapear triggers:**

```typescript
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
  // ... código existente de triggers
)}
```

---

## ✅ RESUMEN DE CAMBIOS

1. ✅ **Imports:** Agregar `Menu`, `LogOut`
2. ✅ **Estado:** `isMobile`
3. ✅ **useEffect:** Detectar mobile
4. ✅ **Función:** `logout()`
5. ✅ **Hamburger menu:** Botón flotante en móvil
6. ✅ **Sidebar:** Responsive con translate
7. ✅ **Botón cerrar:** En header del sidebar (móvil)
8. ✅ **Logout button:** Al final del sidebar
9. ✅ **Backdrop:** Para cerrar sidebar (móvil)
10. ✅ **Main content:** Ocultar cuando sidebar abierto (móvil)
11. ✅ **Search bar:** Responsive flex-col en móvil
12. ✅ **Empty states:** Home y Triggers mejorados

---

## 🧪 TESTING

Después de aplicar los cambios:

```bash
# En el frontend
cd frontend
npm run dev
```

Abre Chrome DevTools (F12) → Toggle Device Toolbar

**Probar en:**
- iPhone 12/13 Pro (390px)
- iPad (768px)
- Desktop (1920px)

**Validar:**
- [ ] Sidebar oculto por defecto en móvil
- [ ] Hamburger menu visible y funcional
- [ ] Backdrop cierra sidebar
- [ ] Botón de logout funciona
- [ ] Empty states se ven bien
- [ ] Responsive en todos los breakpoints

---

_Tiempo estimado: 20-30 minutos_  
_Nivel: Intermedio_
