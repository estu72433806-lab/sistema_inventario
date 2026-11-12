"""
Definición de Esquema y Migración para PostgreSQL (Nube / Servidor Central).
Crea tablas compatibles con el modelo SQLite, vinculadas por identificadores globales UUID
para permitir sincronización bidireccional sin conflictos de claves autoincrementales.
"""
from datetime import datetime

PG_DDL = """
-- 1. Usuarios del sistema
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    nombre_completo VARCHAR(150) NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK(rol IN ('administrador', 'vendedor')),
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Categorías de cómputo
CREATE TABLE IF NOT EXISTS categorias (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Proveedores de hardware
CREATE TABLE IF NOT EXISTS proveedores (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    ruc_dni VARCHAR(20) NOT NULL UNIQUE,
    razon_social VARCHAR(150) NOT NULL,
    contacto VARCHAR(100),
    telefono VARCHAR(50),
    email VARCHAR(100),
    direccion TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. Productos
CREATE TABLE IF NOT EXISTS productos (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nombre VARCHAR(200) NOT NULL,
    categoria_uuid VARCHAR(36),
    proveedor_uuid VARCHAR(36),
    marca VARCHAR(100),
    precio_compra NUMERIC(10,2) NOT NULL DEFAULT 0.0,
    precio_venta NUMERIC(10,2) NOT NULL DEFAULT 0.0,
    stock INTEGER NOT NULL DEFAULT 0,
    stock_minimo INTEGER NOT NULL DEFAULT 3,
    descripcion TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5. Clientes
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    tipo_documento VARCHAR(20) DEFAULT 'DNI',
    numero_documento VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    telefono VARCHAR(50),
    email VARCHAR(100),
    direccion TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 6. Movimientos de Stock (Kardex global)
CREATE TABLE IF NOT EXISTS movimientos_stock (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    producto_uuid VARCHAR(36) NOT NULL,
    tipo_movimiento VARCHAR(20) NOT NULL CHECK(tipo_movimiento IN ('ENTRADA', 'SALIDA', 'AJUSTE')),
    cantidad INTEGER NOT NULL,
    motivo TEXT,
    referencia VARCHAR(100),
    fecha TIMESTAMP NOT NULL,
    usuario_uuid VARCHAR(36),
    proveedor_uuid VARCHAR(36),
    fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 7. Ventas
CREATE TABLE IF NOT EXISTS ventas (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    numero_comprobante VARCHAR(50) NOT NULL UNIQUE,
    tipo_comprobante VARCHAR(30) NOT NULL DEFAULT 'Boleta',
    fecha TIMESTAMP NOT NULL,
    cliente_uuid VARCHAR(36),
    usuario_uuid VARCHAR(36),
    subtotal NUMERIC(10,2) NOT NULL DEFAULT 0.0,
    descuento NUMERIC(10,2) NOT NULL DEFAULT 0.0,
    impuesto NUMERIC(10,2) NOT NULL DEFAULT 0.0,
    total NUMERIC(10,2) NOT NULL DEFAULT 0.0,
    metodo_pago VARCHAR(50) NOT NULL DEFAULT 'Efectivo',
    estado VARCHAR(30) NOT NULL DEFAULT 'Completada',
    fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 8. Detalle de Ventas
CREATE TABLE IF NOT EXISTS detalle_ventas (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    venta_uuid VARCHAR(36) NOT NULL,
    producto_uuid VARCHAR(36) NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario NUMERIC(10,2) NOT NULL,
    subtotal NUMERIC(10,2) NOT NULL,
    fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 9. Registro de Conflictos de Sincronización
CREATE TABLE IF NOT EXISTS conflictos_sincronizacion (
    id SERIAL PRIMARY KEY,
    tabla VARCHAR(50) NOT NULL,
    registro_uuid VARCHAR(36) NOT NULL,
    campo VARCHAR(50),
    valor_local TEXT,
    valor_remoto TEXT,
    fecha_conflicto TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resuelto INTEGER NOT NULL DEFAULT 0
);
"""

def init_pg_db(conn) -> tuple[bool, str]:
    """Crea las tablas en PostgreSQL si aún no existen."""
    try:
        with conn.cursor() as cur:
            cur.execute(PG_DDL)
        conn.commit()
        return True, "Esquema PostgreSQL inicializado con éxito."
    except Exception as e:
        conn.rollback()
        return False, f"Error al inicializar esquema PostgreSQL: {str(e)}"
