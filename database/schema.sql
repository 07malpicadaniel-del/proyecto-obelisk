-- ============================================
-- HPE SALES GUARDIAN - SUPABASE SCHEMA
-- Solo tablas esenciales para la competencia
-- ============================================

-- 1. CATÁLOGO DE PRODUCTOS HPE (CRÍTICO - 20% del score)
CREATE TABLE IF NOT EXISTS hpe_products (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    categoria VARCHAR(100),
    descripcion TEXT,
    trigger_keywords TEXT[],
    casos_uso TEXT[],
    ventaja_vs_competencia JSONB,
    speech_hook TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índice para búsquedas por keywords
CREATE INDEX idx_hpe_trigger_keywords ON hpe_products USING GIN(trigger_keywords);

-- 2. ANÁLISIS DE EMPRESAS (Historial)
CREATE TABLE IF NOT EXISTS company_analysis (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(200) NOT NULL,
    industry VARCHAR(100),
    fit_score INTEGER CHECK (fit_score >= 0 AND fit_score <= 100),
    tech_stack JSONB,
    triggers JSONB,
    competitors_detected JSONB,
    hpe_solution_recommended VARCHAR(200),
    speech_generated TEXT,
    target_role VARCHAR(50),
    sources JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_analysis_date ON company_analysis(created_at DESC);
CREATE INDEX idx_analysis_score ON company_analysis(fit_score DESC);
CREATE INDEX idx_analysis_company ON company_analysis(company_name);

-- ============================================
-- SEED DATA - Productos HPE
-- ============================================
INSERT INTO hpe_products (product_id, nombre, categoria, descripcion, trigger_keywords, speech_hook, ventaja_vs_competencia) VALUES
('greenlake', 'HPE GreenLake', 'Hybrid Cloud', 'Plataforma as-a-service edge-to-cloud', 
 ARRAY['expansion', 'data center', 'capex reduction', 'cloud migration', 'hybrid cloud'],
 '¿Y si pudieran tener la agilidad de AWS pero con control total de sus datos críticos?',
 '{"Dell APEX": "Modelo financiero más flexible", "AWS Outposts": "Control total on-prem", "Azure Stack": "Mejor TCO"}'::jsonb),

('aruba', 'HPE Aruba Networking', 'Networking', 'Red empresarial edge-to-cloud con IA', 
 ARRAY['network modernization', 'wifi upgrade', 'zero trust', 'remote work', 'ciberseguridad'],
 '¿Sabían que el 80% de los ataques ransomware entran por redes mal segmentadas?',
 '{"Cisco Meraki": "30% menor TCO", "Juniper Mist": "Más simple de gestionar"}'::jsonb),

('alletra', 'HPE Alletra Storage', 'Storage', 'Almacenamiento inteligente con IA predictiva', 
 ARRAY['data growth', 'storage consolidation', 'ransomware protection', 'backup modernization'],
 '¿Cuánto les costaría perder acceso a su base de datos por 48 horas?',
 '{"Dell EMC": "AI-driven operations 80% menos admin", "Pure Storage": "Mejor price/performance"}'::jsonb),

('proliant', 'HPE ProLiant Gen11', 'Compute', 'Servidores con Silicon Root of Trust', 
 ARRAY['server refresh', 'virtualization', 'data center expansion', 'EOL servers'],
 '¿Sabían que servidores +5 años consumen 3x más energía?',
 '{"Dell PowerEdge": "Mejor gestión con iLO 6", "Lenovo": "15% más eficiente"}'::jsonb),

('simplivity', 'HPE SimpliVity', 'HCI', 'Infraestructura hiperconvergida simplificada', 
 ARRAY['hyperconverged', 'HCI', 'VDI', 'ROBO', 'remote office'],
 '¿Y si pudieran gestionar 1,000 sitios remotos como si fueran uno solo?',
 '{"Nutanix": "Deduplicación global", "VMware vSAN": "Mejor TCO en ROBO"}'::jsonb)

ON CONFLICT (product_id) DO NOTHING;

-- ============================================
-- VIEWS ÚTILES
-- ============================================

-- Top oportunidades recientes
CREATE OR REPLACE VIEW high_score_analysis AS
SELECT 
    id,
    company_name,
    fit_score,
    hpe_solution_recommended,
    target_role,
    created_at
FROM company_analysis
WHERE fit_score >= 70
ORDER BY created_at DESC
LIMIT 20;

COMMENT ON TABLE hpe_products IS 'Catálogo de soluciones HPE con keywords para trigger matching';
COMMENT ON TABLE company_analysis IS 'Historial de análisis con scores y recomendaciones';
