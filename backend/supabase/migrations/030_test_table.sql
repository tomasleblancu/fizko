-- Migration: Test table creation
-- Description: Tabla de prueba para verificar el sistema de migraciones

CREATE TABLE IF NOT EXISTS tabla_prueba (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE tabla_prueba IS 'Tabla de prueba para verificar migraciones';
COMMENT ON COLUMN tabla_prueba.nombre IS 'Nombre de prueba';
