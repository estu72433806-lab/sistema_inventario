"""
Definición de tablas e inicialización de datos para la tienda de computadoras.
Incluye soporte para usuarios con contraseñas hasheadas (PBKDF2-HMAC-SHA256),
roles (administrador, vendedor), inventario, proveedores y movimientos de stock.
"""
import os
import secrets
import hashlib
from datetime import datetime
from database.db import get_connection

DDL_STATEMENTS = """
-- 1. Tabla de Usuarios del Sistema
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    nombre_completo TEXT NOT NULL,
    rol TEXT NOT NULL CHECK(rol IN ('administrador', 'vendedor')),
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL
);

-- 2. Tabla de Categorías de Hardware / Cómputo
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT
);

-- 3. Tabla de Proveedores de Tecnología
CREATE TABLE IF NOT EXISTS proveedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ruc_dni TEXT NOT NULL UNIQUE,
    razon_social TEXT NOT NULL,
    contacto TEXT,
    telefono TEXT,
    email TEXT,
    direccion TEXT,
    activo INTEGER NOT NULL DEFAULT 1
);

-- 4. Tabla de Productos y Componentes
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    categoria_id INTEGER,
    proveedor_id INTEGER,
    marca TEXT,
    precio_compra REAL NOT NULL DEFAULT 0.0,
    precio_venta REAL NOT NULL DEFAULT 0.0,
    stock INTEGER NOT NULL DEFAULT 0,
    stock_minimo INTEGER NOT NULL DEFAULT 3,
    descripcion TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL,
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id) ON DELETE SET NULL
);

-- 5. Tabla de Clientes
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_documento TEXT DEFAULT 'DNI',
    numero_documento TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    telefono TEXT,
    email TEXT,
    direccion TEXT,
    activo INTEGER NOT NULL DEFAULT 1
);

-- 6. Tabla de Movimientos de Stock (Kardex / Auditoría)
CREATE TABLE IF NOT EXISTS movimientos_stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    tipo_movimiento TEXT NOT NULL CHECK(tipo_movimiento IN ('ENTRADA', 'SALIDA', 'AJUSTE')),
    cantidad INTEGER NOT NULL,
    motivo TEXT,
    referencia TEXT,
    fecha TEXT NOT NULL,
    usuario_id INTEGER,
    proveedor_id INTEGER,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id) ON DELETE SET NULL
);

-- 7. Tabla de Ventas
CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_comprobante TEXT NOT NULL UNIQUE,
    tipo_comprobante TEXT NOT NULL DEFAULT 'Boleta',
    fecha TEXT NOT NULL,
    cliente_id INTEGER,
    usuario_id INTEGER,
    subtotal REAL NOT NULL DEFAULT 0.0,
    descuento REAL NOT NULL DEFAULT 0.0,
    impuesto REAL NOT NULL DEFAULT 0.0,
    total REAL NOT NULL DEFAULT 0.0,
    metodo_pago TEXT NOT NULL DEFAULT 'Efectivo',
    estado TEXT NOT NULL DEFAULT 'Completada',
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
);

-- 8. Tabla de Detalle de Venta
CREATE TABLE IF NOT EXISTS detalle_ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,
    subtotal REAL NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);
"""

DEFAULT_CATEGORIAS = [
    ("Procesadores (CPU)", "Intel Core, AMD Ryzen, etc."),
    ("Tarjetas Gráficas (GPU)", "NVIDIA GeForce, AMD Radeon"),
    ("Placas Madre (Motherboard)", "Sockets AM4, AM5, LGA1700"),
    ("Memorias RAM", "DDR4, DDR5 para PC y Laptops"),
    ("Almacenamiento (SSD/HDD)", "M.2 NVMe, SSD SATA, Discos Duros"),
    ("Fuentes de Poder (PSU)", "Fuentes certificadas 80 Plus"),
    ("Gabinetes / Cases", "Mid-Tower, Micro-ATX, Mini-ITX"),
    ("Monitores", "Gaming, Oficina, Profesionales"),
    ("Periféricos", "Teclados, mouse, auriculares, webcams"),
    ("Laptops y Equipos", "Portátiles gamer, ultrabooks, PCs armadas")
]

DEFAULT_PROVEEDORES = [
    ("20100123456", "Deltron Importaciones S.A.", "Juan Distribución", "01-4113000", "ventas@deltron.local", "Av. Argentina 4050, Lima"),
    ("20255443322", "Ingram Micro Perú S.A.C.", "Área Mayorista", "01-5128000", "contacto@ingram.local", "Av. Materiales 3045, Callao"),
    ("20334455667", "TechData Solutions E.I.R.L.", "Soporte Comercial", "01-6204000", "pedidos@techdata.local", "Av. República de Panamá 3500, San Isidro")
]

def hash_password(password: str, salt: str = None):
    if salt is None:
        salt = secrets.token_hex(16)
    pwd_bytes = password.encode('utf-8')
    salt_bytes = bytes.fromhex(salt)
    key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
    return key.hex(), salt

def verificar_password(password: str, password_hash: str, salt: str) -> bool:
    try:
        nuevo_hash, _ = hash_password(password, salt)
        return secrets.compare_digest(nuevo_hash, password_hash)
    except Exception:
        return False

import uuid
from datetime import datetime
from database.db import get_connection

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript(DDL_STATEMENTS)

    # Migración segura: agregar columnas si la base de datos ya existía previamente
    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN proveedor_id INTEGER REFERENCES proveedores(id);")
    except Exception:
        pass # Columna ya existe

    try:
        cursor.execute("ALTER TABLE movimientos_stock ADD COLUMN proveedor_id INTEGER REFERENCES proveedores(id);")
    except Exception:
        pass # Columna ya existe

    try:
        cursor.execute("ALTER TABLE ventas ADD COLUMN usuario_id INTEGER REFERENCES usuarios(id);")
    except Exception:
        pass # Columna ya existe

    try:
        cursor.execute("ALTER TABLE ventas ADD COLUMN descuento REAL NOT NULL DEFAULT 0.0;")
    except Exception:
        pass # Columna ya existe

    # Tablas auxiliares para modo híbrido y sincronización con PostgreSQL
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sincronizacion_info (
            id INTEGER PRIMARY KEY,
            ultima_sincronizacion TEXT,
            estado TEXT DEFAULT 'DESCONECTADO',
            detalles TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conflictos_sincronizacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tabla TEXT NOT NULL,
            registro_uuid TEXT NOT NULL,
            campo TEXT,
            valor_local TEXT,
            valor_remoto TEXT,
            fecha_conflicto TEXT NOT NULL,
            resuelto INTEGER NOT NULL DEFAULT 0
        );
    """)

    # Inicializar registro único de estado si no existe
    cursor.execute("SELECT COUNT(*) FROM sincronizacion_info WHERE id = 1;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO sincronizacion_info (id, ultima_sincronizacion, estado, detalles)
            VALUES (1, 'Nunca', 'MODO_LOCAL', 'Sistema iniciado en modo local.');
        """)

    # Migración híbrida: agregar campos uuid, sincronizado y fecha_modificacion a todas las entidades
    tablas_sync = [
        "usuarios", "categorias", "proveedores", "productos",
        "clientes", "movimientos_stock", "ventas", "detalle_ventas"
    ]
    for tabla in tablas_sync:
        try:
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN uuid TEXT;")
        except Exception:
            pass
        try:
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN sincronizado INTEGER NOT NULL DEFAULT 1;")
        except Exception:
            pass
        try:
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN fecha_modificacion TEXT;")
        except Exception:
            pass

        # Generar UUID único y fecha para registros existentes que no lo tengan
        cursor.execute(f"SELECT id FROM {tabla} WHERE uuid IS NULL OR uuid = '';")
        filas = cursor.fetchall()
        for f in filas:
            row_id = f[0]
            gen_uuid = str(uuid.uuid4())
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                f"UPDATE {tabla} SET uuid = ?, fecha_modificacion = COALESCE(fecha_modificacion, ?) WHERE id = ?;",
                (gen_uuid, ahora, row_id)
            )

    # 1. Crear el primer administrador si no existe
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'administrador';")
    if cursor.fetchone()[0] == 0:
        pwd_hash, salt = hash_password("admin123")
        fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        admin_uuid = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO usuarios (uuid, username, password_hash, salt, nombre_completo, rol, activo, creado_en, fecha_modificacion, sincronizado)
            VALUES (?, ?, ?, ?, ?, 'administrador', 1, ?, ?, 1);
        """, (admin_uuid, "admin", pwd_hash, salt, "Administrador del Sistema", fecha_creacion, fecha_creacion))

    # 2. Insertar categorías de cómputo por defecto si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM categorias;")
    if cursor.fetchone()[0] == 0:
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for cat in DEFAULT_CATEGORIAS:
            cursor.execute(
                "INSERT INTO categorias (uuid, nombre, descripcion, fecha_modificacion, sincronizado) VALUES (?, ?, ?, ?, 1);",
                (str(uuid.uuid4()), cat[0], cat[1], ahora)
            )

    # 3. Proveedores iniciales si está vacía
    cursor.execute("SELECT COUNT(*) FROM proveedores;")
    if cursor.fetchone()[0] == 0:
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for prov in DEFAULT_PROVEEDORES:
            cursor.execute("""
                INSERT INTO proveedores (uuid, ruc_dni, razon_social, contacto, telefono, email, direccion, activo, fecha_modificacion, sincronizado)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 1);
            """, (str(uuid.uuid4()), prov[0], prov[1], prov[2], prov[3], prov[4], prov[5], ahora))

    # 4. Cliente genérico para venta rápida / público en general
    cursor.execute("SELECT COUNT(*) FROM clientes WHERE numero_documento = '00000000';")
    if cursor.fetchone()[0] == 0:
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO clientes (uuid, tipo_documento, numero_documento, nombre, telefono, email, direccion, activo, fecha_modificacion, sincronizado)
            VALUES (?, 'DNI', '00000000', 'Público General / Venta Rápida', '-', '-', '-', 1, ?, 1);
        """, (str(uuid.uuid4()), ahora))

    conn.commit()
    conn.close()
