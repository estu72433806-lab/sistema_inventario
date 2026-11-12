-- TechStore: base de datos completa (esquema + datos iniciales), SQLite
-- Crear la base y cargarla:  sqlite3 inventario_tienda.db < inventario_tienda.sql
-- Usuarios demo: admin / admin123 (administrador), vendedor / ven123 (vendedor). Cambiar las contraseñas en uso real.
BEGIN TRANSACTION;
CREATE TABLE categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT
, uuid TEXT, sincronizado INTEGER NOT NULL DEFAULT 1, fecha_modificacion TEXT);
INSERT INTO "categorias" VALUES(1,'Procesadores (CPU)','Intel Core, AMD Ryzen, etc.','9150cb13-6b7d-406e-99b8-f79f6a273ba8',1,'2026-11-10 20:55:46');
INSERT INTO "categorias" VALUES(2,'Tarjetas Gráficas (GPU)','NVIDIA GeForce, AMD Radeon','2a16d4c9-8b22-47a7-9f43-46a7e95c5b94',1,'2026-11-10 20:55:46');
INSERT INTO "categorias" VALUES(3,'Placas Madre (Motherboard)','Sockets AM4, AM5, LGA1700','5cf68ca3-299e-4add-8ff2-41695cf15409',1,'2026-11-10 20:55:46');
INSERT INTO "categorias" VALUES(4,'Memorias RAM','DDR4, DDR5 para PC y Laptops','c331ea63-2542-4d08-913b-9b7484598152',1,'2026-11-10 20:55:46');
INSERT INTO "categorias" VALUES(5,'Almacenamiento (SSD/HDD)','M.2 NVMe, SSD SATA, Discos Duros','aa8570cd-cd70-428d-9af3-6a81e7e41a66',1,'2026-11-10 20:55:46');
INSERT INTO "categorias" VALUES(6,'Fuentes de Poder (PSU)','Fuentes certificadas 80 Plus','a62ea836-539a-41b2-a322-4a5dd0a0c8e1',1,'2026-11-10 20:55:46');
INSERT INTO "categorias" VALUES(7,'Gabinetes / Cases','Mid-Tower, Micro-ATX, Mini-ITX','eda6f052-48ef-45bf-851d-8d05873dd362',1,'2026-11-10 20:55:46');
INSERT INTO "categorias" VALUES(8,'Monitores','Gaming, Oficina, Profesionales','d61eff92-797d-45f7-ae69-1e311594b4a2',1,'2026-11-10 20:55:46');
INSERT INTO "categorias" VALUES(9,'Periféricos','Teclados, mouse, auriculares, webcams','cde13648-bf5b-4a66-a272-1cc3513f3733',1,'2026-11-10 20:55:46');
INSERT INTO "categorias" VALUES(10,'Laptops y Equipos','Portátiles gamer, ultrabooks, PCs armadas','abd4fed0-33bb-44b9-82fa-fc219b25afb2',1,'2026-11-10 20:55:46');
CREATE TABLE clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_documento TEXT DEFAULT 'DNI',
    numero_documento TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    telefono TEXT,
    email TEXT,
    direccion TEXT,
    activo INTEGER NOT NULL DEFAULT 1
, uuid TEXT, sincronizado INTEGER NOT NULL DEFAULT 1, fecha_modificacion TEXT);
INSERT INTO "clientes" VALUES(1,'DNI','00000000','Público General / Venta Rápida','-','-','-',1,'59e59055-6774-4150-8c71-b499f5f2f6ff',1,'2026-11-10 20:55:46');
CREATE TABLE conflictos_sincronizacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tabla TEXT NOT NULL,
            registro_uuid TEXT NOT NULL,
            campo TEXT,
            valor_local TEXT,
            valor_remoto TEXT,
            fecha_conflicto TEXT NOT NULL,
            resuelto INTEGER NOT NULL DEFAULT 0
        );
CREATE TABLE detalle_ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,
    subtotal REAL NOT NULL, uuid TEXT, sincronizado INTEGER NOT NULL DEFAULT 1, fecha_modificacion TEXT,
    FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);
CREATE TABLE movimientos_stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    tipo_movimiento TEXT NOT NULL CHECK(tipo_movimiento IN ('ENTRADA', 'SALIDA', 'AJUSTE')),
    cantidad INTEGER NOT NULL,
    motivo TEXT,
    referencia TEXT,
    fecha TEXT NOT NULL,
    usuario_id INTEGER,
    proveedor_id INTEGER, uuid TEXT, sincronizado INTEGER NOT NULL DEFAULT 1, fecha_modificacion TEXT,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id) ON DELETE SET NULL
);
INSERT INTO "movimientos_stock" VALUES(1,1,'ENTRADA',12,'Inventario inicial de apertura','Guía Inicial 001','2026-11-10 20:55:46',1,1,'4d41f717-441c-4714-9c2e-abd5dc537397',1,'2026-11-10 20:55:46');
INSERT INTO "movimientos_stock" VALUES(2,2,'ENTRADA',8,'Inventario inicial de apertura','Guía Inicial 001','2026-11-10 20:55:46',1,1,'75103ecc-f4ea-4bfe-bb19-f84dbbcfa666',1,'2026-11-10 20:55:46');
INSERT INTO "movimientos_stock" VALUES(3,3,'ENTRADA',5,'Inventario inicial de apertura','Guía Inicial 001','2026-11-10 20:55:46',1,2,'90f66c70-6359-43f5-b6fc-9c961b370f4a',1,'2026-11-10 20:55:46');
INSERT INTO "movimientos_stock" VALUES(4,4,'ENTRADA',25,'Inventario inicial de apertura','Guía Inicial 001','2026-11-10 20:55:46',1,3,'4822d52e-1308-4dac-8c41-5b8030ed652d',1,'2026-11-10 20:55:46');
INSERT INTO "movimientos_stock" VALUES(5,5,'ENTRADA',15,'Inventario inicial de apertura','Guía Inicial 001','2026-11-10 20:55:46',1,1,'f6dd169b-b7bb-4686-b15d-11077799f954',1,'2026-11-10 20:55:46');
INSERT INTO "movimientos_stock" VALUES(6,6,'ENTRADA',7,'Inventario inicial de apertura','Guía Inicial 001','2026-11-10 20:55:46',1,2,'0901ad56-8aa2-4900-9487-a0b1646e921b',1,'2026-11-10 20:55:46');
INSERT INTO "movimientos_stock" VALUES(7,7,'ENTRADA',10,'Inventario inicial de apertura','Guía Inicial 001','2026-11-10 20:55:46',1,3,'4b11a29d-bcf9-4dbd-8286-2ca21353e5cd',1,'2026-11-10 20:55:46');
INSERT INTO "movimientos_stock" VALUES(8,8,'ENTRADA',2,'Inventario inicial de apertura','Guía Inicial 001','2026-11-10 20:55:46',1,1,'1103965a-4094-4106-ab8b-a9150253e279',1,'2026-11-10 20:55:46');
CREATE TABLE productos (
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
    activo INTEGER NOT NULL DEFAULT 1, uuid TEXT, sincronizado INTEGER NOT NULL DEFAULT 1, fecha_modificacion TEXT,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL,
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id) ON DELETE SET NULL
);
INSERT INTO "productos" VALUES(1,'CPU-INT-001','Procesador Intel Core i5-13400F 2.5/4.6GHz',1,1,'Intel',720.0,890.0,12,3,'10 núcleos, 16 hilos, LGA1700',1,'8723eb6a-8cee-4a6e-b541-defdce38d5db',1,'2026-11-10 20:55:46');
INSERT INTO "productos" VALUES(2,'CPU-AMD-002','Procesador AMD Ryzen 7 5700X 3.4/4.6GHz',1,1,'AMD',680.0,830.0,8,2,'8 núcleos, 16 hilos, AM4',1,'dc1c0dd5-b84e-40d3-949f-09f0dee43d67',1,'2026-11-10 20:55:46');
INSERT INTO "productos" VALUES(3,'GPU-NV-001','Tarjeta Gráfica ASUS Dual GeForce RTX 4060 OC 8GB',2,2,'ASUS',1350.0,1620.0,5,2,'GDDR6, DLSS 3, Ray Tracing',1,'a7bc8865-571d-45cd-9f78-1274d0f7f115',1,'2026-11-10 20:55:46');
INSERT INTO "productos" VALUES(4,'RAM-KNG-001','Memoria RAM Kingston Fury Beast 16GB DDR4 3200MHz',4,3,'Kingston',140.0,185.0,25,5,'Disipador negro, CL16',1,'10853bc3-223a-4307-ad9c-97366afb33ff',1,'2026-11-10 20:55:46');
INSERT INTO "productos" VALUES(5,'SSD-KNG-002','Disco Sólido SSD M.2 NVMe Kingston NV2 1TB PCIe 4.0',5,1,'Kingston',210.0,275.0,15,4,'Lectura hasta 3500 MB/s',1,'0199f5a9-eea4-4e48-bdd6-59b8da33fd7b',1,'2026-11-10 20:55:46');
INSERT INTO "productos" VALUES(6,'PSU-COR-001','Fuente de Poder Corsair CV650 650W 80 Plus Bronze',6,2,'Corsair',240.0,310.0,7,2,'Certificación 80 Plus Bronze',1,'ba3180dc-9d02-4876-9f2d-eaf308a6aa00',1,'2026-11-10 20:55:46');
INSERT INTO "productos" VALUES(7,'PER-LOG-001','Mouse Gamer Logitech G502 HERO 25K',9,3,'Logitech',150.0,219.0,10,3,'Sensor HERO 25K, 11 botones',1,'b62d7ad9-b33c-4055-959c-3a1133eaaf82',1,'2026-11-10 20:55:46');
INSERT INTO "productos" VALUES(8,'PER-RED-002','Teclado Mecánico Redragon Kumara K552 RGB',9,1,'Redragon',120.0,169.0,2,3,'Switches Outemu Red (Alerta Stock Bajo)',1,'438b221e-01bc-49f6-8cec-96ad3b4ab840',1,'2026-11-10 20:55:46');
CREATE TABLE proveedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ruc_dni TEXT NOT NULL UNIQUE,
    razon_social TEXT NOT NULL,
    contacto TEXT,
    telefono TEXT,
    email TEXT,
    direccion TEXT,
    activo INTEGER NOT NULL DEFAULT 1
, uuid TEXT, sincronizado INTEGER NOT NULL DEFAULT 1, fecha_modificacion TEXT);
INSERT INTO "proveedores" VALUES(1,'20100123456','Deltron Importaciones S.A.','Juan Distribución','01-4113000','ventas@deltron.local','Av. Argentina 4050, Lima',1,'7adb0ba9-1e25-4e92-bd93-10b9529c0689',1,'2026-11-10 20:55:46');
INSERT INTO "proveedores" VALUES(2,'20255443322','Ingram Micro Perú S.A.C.','Área Mayorista','01-5128000','contacto@ingram.local','Av. Materiales 3045, Callao',1,'7e81200e-8aca-4e30-a681-87d17c2bea73',1,'2026-11-10 20:55:46');
INSERT INTO "proveedores" VALUES(3,'20334455667','TechData Solutions E.I.R.L.','Soporte Comercial','01-6204000','pedidos@techdata.local','Av. República de Panamá 3500, San Isidro',1,'434fa576-c545-44c3-b28c-3bf75f8243ce',1,'2026-11-10 20:55:46');
CREATE TABLE sincronizacion_info (
            id INTEGER PRIMARY KEY,
            ultima_sincronizacion TEXT,
            estado TEXT DEFAULT 'DESCONECTADO',
            detalles TEXT
        );
INSERT INTO "sincronizacion_info" VALUES(1,'Nunca','MODO_LOCAL','Sistema iniciado en modo local.');
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    nombre_completo TEXT NOT NULL,
    rol TEXT NOT NULL CHECK(rol IN ('administrador', 'vendedor')),
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL
, uuid TEXT, sincronizado INTEGER NOT NULL DEFAULT 1, fecha_modificacion TEXT);
INSERT INTO "usuarios" VALUES(1,'admin','11fe083cb72a35c5e853043765f21183961f6b4b7fc4979b38a0f352464d22f0','464b344beaac13588877389226fe8f47','Administrador del Sistema','administrador',1,'2026-11-10 20:55:46','8e2661cd-c913-4cf8-be29-7dd230e82270',1,'2026-11-10 20:55:46');
INSERT INTO "usuarios" VALUES(2,'vendedor','54a2756d237ec4aee302c8c867e05b0dff5b5de3b53f7de9bc9667b5321d9482','d0e0ec74271e948643baac45766d75dc','Carlos Vendedor','vendedor',1,'2026-11-10 20:55:46','ab4fb6da-16bb-4ba6-b97e-1c7337dcf4f8',0,'2026-11-10 20:55:46');
CREATE TABLE ventas (
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
    estado TEXT NOT NULL DEFAULT 'Completada', uuid TEXT, sincronizado INTEGER NOT NULL DEFAULT 1, fecha_modificacion TEXT,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('usuarios',2);
INSERT INTO "sqlite_sequence" VALUES('categorias',10);
INSERT INTO "sqlite_sequence" VALUES('proveedores',3);
INSERT INTO "sqlite_sequence" VALUES('clientes',1);
INSERT INTO "sqlite_sequence" VALUES('productos',8);
INSERT INTO "sqlite_sequence" VALUES('movimientos_stock',8);
COMMIT;
