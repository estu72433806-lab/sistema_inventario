-- =====================================================================
-- TechStore - Base de datos completa para MySQL / MariaDB (phpMyAdmin)
-- Crea la base 'techstore' con sus tablas y datos iniciales.
-- Importar en phpMyAdmin: pestaña Importar > elegir este archivo > Continuar.
-- Usuarios demo: admin / admin123 (administrador) y vendedor / ven123 (vendedor).
-- =====================================================================
CREATE DATABASE IF NOT EXISTS techstore CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE techstore;

DROP TABLE IF EXISTS `usuarios`;
CREATE TABLE `usuarios` (
    `id` INT AUTO_INCREMENT,
    `username` VARCHAR(255) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `salt` VARCHAR(255) NOT NULL,
    `nombre_completo` VARCHAR(255) NOT NULL,
    `rol` VARCHAR(255) NOT NULL,
    `activo` INT NOT NULL DEFAULT 1,
    `creado_en` VARCHAR(30) NOT NULL,
    `uuid` VARCHAR(36),
    `sincronizado` INT NOT NULL DEFAULT 1,
    `fecha_modificacion` VARCHAR(30),
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_usuarios_username` (`username`),
    UNIQUE KEY `uq_usuarios_uuid` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `categorias`;
CREATE TABLE `categorias` (
    `id` INT AUTO_INCREMENT,
    `nombre` VARCHAR(255) NOT NULL,
    `descripcion` TEXT,
    `uuid` VARCHAR(36),
    `sincronizado` INT NOT NULL DEFAULT 1,
    `fecha_modificacion` VARCHAR(30),
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_categorias_nombre` (`nombre`),
    UNIQUE KEY `uq_categorias_uuid` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `proveedores`;
CREATE TABLE `proveedores` (
    `id` INT AUTO_INCREMENT,
    `ruc_dni` VARCHAR(255) NOT NULL,
    `razon_social` VARCHAR(255) NOT NULL,
    `contacto` VARCHAR(255),
    `telefono` VARCHAR(255),
    `email` VARCHAR(255),
    `direccion` TEXT,
    `activo` INT NOT NULL DEFAULT 1,
    `uuid` VARCHAR(36),
    `sincronizado` INT NOT NULL DEFAULT 1,
    `fecha_modificacion` VARCHAR(30),
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_proveedores_ruc_dni` (`ruc_dni`),
    UNIQUE KEY `uq_proveedores_uuid` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `productos`;
CREATE TABLE `productos` (
    `id` INT AUTO_INCREMENT,
    `codigo` VARCHAR(255) NOT NULL,
    `nombre` VARCHAR(255) NOT NULL,
    `categoria_id` INT,
    `proveedor_id` INT,
    `marca` VARCHAR(255),
    `precio_compra` DECIMAL(12,2) NOT NULL DEFAULT 0.0,
    `precio_venta` DECIMAL(12,2) NOT NULL DEFAULT 0.0,
    `stock` INT NOT NULL DEFAULT 0,
    `stock_minimo` INT NOT NULL DEFAULT 3,
    `descripcion` TEXT,
    `activo` INT NOT NULL DEFAULT 1,
    `uuid` VARCHAR(36),
    `sincronizado` INT NOT NULL DEFAULT 1,
    `fecha_modificacion` VARCHAR(30),
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_productos_codigo` (`codigo`),
    UNIQUE KEY `uq_productos_uuid` (`uuid`),
    CONSTRAINT `fk_productos_proveedor_id` FOREIGN KEY (`proveedor_id`) REFERENCES `proveedores` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_productos_categoria_id` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `clientes`;
CREATE TABLE `clientes` (
    `id` INT AUTO_INCREMENT,
    `tipo_documento` VARCHAR(255) DEFAULT 'DNI',
    `numero_documento` VARCHAR(255) NOT NULL,
    `nombre` VARCHAR(255) NOT NULL,
    `telefono` VARCHAR(255),
    `email` VARCHAR(255),
    `direccion` TEXT,
    `activo` INT NOT NULL DEFAULT 1,
    `uuid` VARCHAR(36),
    `sincronizado` INT NOT NULL DEFAULT 1,
    `fecha_modificacion` VARCHAR(30),
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_clientes_numero_documento` (`numero_documento`),
    UNIQUE KEY `uq_clientes_uuid` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `movimientos_stock`;
CREATE TABLE `movimientos_stock` (
    `id` INT AUTO_INCREMENT,
    `producto_id` INT NOT NULL,
    `tipo_movimiento` VARCHAR(255) NOT NULL,
    `cantidad` INT NOT NULL,
    `motivo` TEXT,
    `referencia` VARCHAR(255),
    `fecha` VARCHAR(30) NOT NULL,
    `usuario_id` INT,
    `proveedor_id` INT,
    `uuid` VARCHAR(36),
    `sincronizado` INT NOT NULL DEFAULT 1,
    `fecha_modificacion` VARCHAR(30),
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_movimientos_stock_uuid` (`uuid`),
    CONSTRAINT `fk_movimientos_stock_proveedor_id` FOREIGN KEY (`proveedor_id`) REFERENCES `proveedores` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_movimientos_stock_usuario_id` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_movimientos_stock_producto_id` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `ventas`;
CREATE TABLE `ventas` (
    `id` INT AUTO_INCREMENT,
    `numero_comprobante` VARCHAR(255) NOT NULL,
    `tipo_comprobante` VARCHAR(255) NOT NULL DEFAULT 'Boleta',
    `fecha` VARCHAR(30) NOT NULL,
    `cliente_id` INT,
    `usuario_id` INT,
    `subtotal` DECIMAL(12,2) NOT NULL DEFAULT 0.0,
    `descuento` DECIMAL(12,2) NOT NULL DEFAULT 0.0,
    `impuesto` DECIMAL(12,2) NOT NULL DEFAULT 0.0,
    `total` DECIMAL(12,2) NOT NULL DEFAULT 0.0,
    `metodo_pago` VARCHAR(255) NOT NULL DEFAULT 'Efectivo',
    `estado` VARCHAR(255) NOT NULL DEFAULT 'Completada',
    `uuid` VARCHAR(36),
    `sincronizado` INT NOT NULL DEFAULT 1,
    `fecha_modificacion` VARCHAR(30),
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_ventas_numero_comprobante` (`numero_comprobante`),
    UNIQUE KEY `uq_ventas_uuid` (`uuid`),
    CONSTRAINT `fk_ventas_usuario_id` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_ventas_cliente_id` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `detalle_ventas`;
CREATE TABLE `detalle_ventas` (
    `id` INT AUTO_INCREMENT,
    `venta_id` INT NOT NULL,
    `producto_id` INT NOT NULL,
    `cantidad` INT NOT NULL,
    `precio_unitario` DECIMAL(12,2) NOT NULL,
    `subtotal` DECIMAL(12,2) NOT NULL,
    `uuid` VARCHAR(36),
    `sincronizado` INT NOT NULL DEFAULT 1,
    `fecha_modificacion` VARCHAR(30),
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_detalle_ventas_uuid` (`uuid`),
    CONSTRAINT `fk_detalle_ventas_producto_id` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE RESTRICT,
    CONSTRAINT `fk_detalle_ventas_venta_id` FOREIGN KEY (`venta_id`) REFERENCES `ventas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `sincronizacion_info`;
CREATE TABLE `sincronizacion_info` (
    `id` INT AUTO_INCREMENT,
    `ultima_sincronizacion` VARCHAR(30),
    `estado` VARCHAR(255) DEFAULT 'DESCONECTADO',
    `detalles` TEXT,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `conflictos_sincronizacion`;
CREATE TABLE `conflictos_sincronizacion` (
    `id` INT AUTO_INCREMENT,
    `tabla` VARCHAR(255) NOT NULL,
    `registro_uuid` VARCHAR(255) NOT NULL,
    `campo` VARCHAR(255),
    `valor_local` TEXT,
    `valor_remoto` TEXT,
    `fecha_conflicto` VARCHAR(30) NOT NULL,
    `resuelto` INT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 0;

-- usuarios: 2 registros
INSERT INTO `usuarios` (`id`, `username`, `password_hash`, `salt`, `nombre_completo`, `rol`, `activo`, `creado_en`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (1, 'admin', '2ee4e6c61974f6f98a64fe2d644df78d16490afc4327f66fc41617a293b16a06', 'e1bc2e5b7e2b65deed6fbddf542a8f97', 'Administrador del Sistema', 'administrador', 1, '2026-11-10 20:57:28', '17586b6f-f4ff-4d77-9918-814f7f68663c', 1, '2026-11-10 20:57:28');
INSERT INTO `usuarios` (`id`, `username`, `password_hash`, `salt`, `nombre_completo`, `rol`, `activo`, `creado_en`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (2, 'vendedor', '5521645d4ac5469b04e003a6d07d9442b16ce878dbc7f0f8f26a12bdd174ac11', 'd0991618dee463f7446625198b351d2d', 'Carlos Vendedor', 'vendedor', 1, '2026-11-10 20:57:28', '369e6fc4-dad1-4669-b4e5-cd83150af258', 0, '2026-11-10 20:57:28');

-- categorias: 10 registros
INSERT INTO `categorias` (`id`, `nombre`, `descripcion`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (1, 'Procesadores (CPU)', 'Intel Core, AMD Ryzen, etc.', '2c7de5cb-18ce-4298-84ef-d6de9eb5961e', 1, '2026-11-10 20:57:28');
INSERT INTO `categorias` (`id`, `nombre`, `descripcion`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (2, 'Tarjetas Gráficas (GPU)', 'NVIDIA GeForce, AMD Radeon', '7de237a1-1f02-4986-9df8-310144b33661', 1, '2026-11-10 20:57:28');
INSERT INTO `categorias` (`id`, `nombre`, `descripcion`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (3, 'Placas Madre (Motherboard)', 'Sockets AM4, AM5, LGA1700', '685b7ae6-4840-4103-a701-0a55c307d800', 1, '2026-11-10 20:57:28');
INSERT INTO `categorias` (`id`, `nombre`, `descripcion`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (4, 'Memorias RAM', 'DDR4, DDR5 para PC y Laptops', 'e4678bda-6669-4b2e-b5ed-38ac5f6f2b7f', 1, '2026-11-10 20:57:28');
INSERT INTO `categorias` (`id`, `nombre`, `descripcion`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (5, 'Almacenamiento (SSD/HDD)', 'M.2 NVMe, SSD SATA, Discos Duros', '110b057d-6d7b-4cb4-b374-c2e3c6b1f5f7', 1, '2026-11-10 20:57:28');
INSERT INTO `categorias` (`id`, `nombre`, `descripcion`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (6, 'Fuentes de Poder (PSU)', 'Fuentes certificadas 80 Plus', 'ef4fcda7-0fd0-493d-96d9-7e9f184617b6', 1, '2026-11-10 20:57:28');
INSERT INTO `categorias` (`id`, `nombre`, `descripcion`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (7, 'Gabinetes / Cases', 'Mid-Tower, Micro-ATX, Mini-ITX', '5510069f-5a13-4b93-935a-795a5ac349fc', 1, '2026-11-10 20:57:28');
INSERT INTO `categorias` (`id`, `nombre`, `descripcion`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (8, 'Monitores', 'Gaming, Oficina, Profesionales', '2acde5ad-2080-4c9b-b190-5d1ca062a05b', 1, '2026-11-10 20:57:28');
INSERT INTO `categorias` (`id`, `nombre`, `descripcion`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (9, 'Periféricos', 'Teclados, mouse, auriculares, webcams', '890e6259-f5d2-4d2a-baca-0ce58154fd5a', 1, '2026-11-10 20:57:28');
INSERT INTO `categorias` (`id`, `nombre`, `descripcion`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (10, 'Laptops y Equipos', 'Portátiles gamer, ultrabooks, PCs armadas', '7eaf4c48-8d3e-4171-8a61-2026ccddcb73', 1, '2026-11-10 20:57:28');

-- proveedores: 3 registros
INSERT INTO `proveedores` (`id`, `ruc_dni`, `razon_social`, `contacto`, `telefono`, `email`, `direccion`, `activo`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (1, '20100123456', 'Deltron Importaciones S.A.', 'Juan Distribución', '01-4113000', 'ventas@deltron.local', 'Av. Argentina 4050, Lima', 1, '4714a12b-22fa-4247-94fb-c96f31fae8bc', 1, '2026-11-10 20:57:28');
INSERT INTO `proveedores` (`id`, `ruc_dni`, `razon_social`, `contacto`, `telefono`, `email`, `direccion`, `activo`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (2, '20255443322', 'Ingram Micro Perú S.A.C.', 'Área Mayorista', '01-5128000', 'contacto@ingram.local', 'Av. Materiales 3045, Callao', 1, '7d0e5f22-6646-4411-a3ad-04e95f358dc3', 1, '2026-11-10 20:57:28');
INSERT INTO `proveedores` (`id`, `ruc_dni`, `razon_social`, `contacto`, `telefono`, `email`, `direccion`, `activo`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (3, '20334455667', 'TechData Solutions E.I.R.L.', 'Soporte Comercial', '01-6204000', 'pedidos@techdata.local', 'Av. República de Panamá 3500, San Isidro', 1, '24d01964-c8ad-43ad-b6a2-1b5ea070089b', 1, '2026-11-10 20:57:28');

-- productos: 8 registros
INSERT INTO `productos` (`id`, `codigo`, `nombre`, `categoria_id`, `proveedor_id`, `marca`, `precio_compra`, `precio_venta`, `stock`, `stock_minimo`, `descripcion`, `activo`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (1, 'CPU-INT-001', 'Procesador Intel Core i5-13400F 2.5/4.6GHz', 1, 1, 'Intel', 720.0, 890.0, 12, 3, '10 núcleos, 16 hilos, LGA1700', 1, '026efe78-11dd-4d0f-bca7-df5c862b0c76', 1, '2026-11-10 20:57:28');
INSERT INTO `productos` (`id`, `codigo`, `nombre`, `categoria_id`, `proveedor_id`, `marca`, `precio_compra`, `precio_venta`, `stock`, `stock_minimo`, `descripcion`, `activo`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (2, 'CPU-AMD-002', 'Procesador AMD Ryzen 7 5700X 3.4/4.6GHz', 1, 1, 'AMD', 680.0, 830.0, 8, 2, '8 núcleos, 16 hilos, AM4', 1, 'baf9596c-66b2-42b9-8eae-d5fcf9a91e21', 1, '2026-11-10 20:57:28');
INSERT INTO `productos` (`id`, `codigo`, `nombre`, `categoria_id`, `proveedor_id`, `marca`, `precio_compra`, `precio_venta`, `stock`, `stock_minimo`, `descripcion`, `activo`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (3, 'GPU-NV-001', 'Tarjeta Gráfica ASUS Dual GeForce RTX 4060 OC 8GB', 2, 2, 'ASUS', 1350.0, 1620.0, 5, 2, 'GDDR6, DLSS 3, Ray Tracing', 1, 'f5794b78-431c-4415-b3ac-94dae6c41f3a', 1, '2026-11-10 20:57:28');
INSERT INTO `productos` (`id`, `codigo`, `nombre`, `categoria_id`, `proveedor_id`, `marca`, `precio_compra`, `precio_venta`, `stock`, `stock_minimo`, `descripcion`, `activo`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (4, 'RAM-KNG-001', 'Memoria RAM Kingston Fury Beast 16GB DDR4 3200MHz', 4, 3, 'Kingston', 140.0, 185.0, 25, 5, 'Disipador negro, CL16', 1, 'd9de2838-065a-4cd4-9840-26f9aff5b08f', 1, '2026-11-10 20:57:28');
INSERT INTO `productos` (`id`, `codigo`, `nombre`, `categoria_id`, `proveedor_id`, `marca`, `precio_compra`, `precio_venta`, `stock`, `stock_minimo`, `descripcion`, `activo`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (5, 'SSD-KNG-002', 'Disco Sólido SSD M.2 NVMe Kingston NV2 1TB PCIe 4.0', 5, 1, 'Kingston', 210.0, 275.0, 15, 4, 'Lectura hasta 3500 MB/s', 1, 'd3c7577d-b866-473f-adde-be9fcb521b74', 1, '2026-11-10 20:57:28');
INSERT INTO `productos` (`id`, `codigo`, `nombre`, `categoria_id`, `proveedor_id`, `marca`, `precio_compra`, `precio_venta`, `stock`, `stock_minimo`, `descripcion`, `activo`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (6, 'PSU-COR-001', 'Fuente de Poder Corsair CV650 650W 80 Plus Bronze', 6, 2, 'Corsair', 240.0, 310.0, 7, 2, 'Certificación 80 Plus Bronze', 1, '69bf960e-279a-4292-a82f-ae0ff96f2042', 1, '2026-11-10 20:57:28');
INSERT INTO `productos` (`id`, `codigo`, `nombre`, `categoria_id`, `proveedor_id`, `marca`, `precio_compra`, `precio_venta`, `stock`, `stock_minimo`, `descripcion`, `activo`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (7, 'PER-LOG-001', 'Mouse Gamer Logitech G502 HERO 25K', 9, 3, 'Logitech', 150.0, 219.0, 10, 3, 'Sensor HERO 25K, 11 botones', 1, 'b5ed2b1d-fb39-4bcd-a85e-51a111102464', 1, '2026-11-10 20:57:28');
INSERT INTO `productos` (`id`, `codigo`, `nombre`, `categoria_id`, `proveedor_id`, `marca`, `precio_compra`, `precio_venta`, `stock`, `stock_minimo`, `descripcion`, `activo`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (8, 'PER-RED-002', 'Teclado Mecánico Redragon Kumara K552 RGB', 9, 1, 'Redragon', 120.0, 169.0, 2, 3, 'Switches Outemu Red (Alerta Stock Bajo)', 1, '0c8a8f8a-ccdb-4e99-8b64-13bff1cfe530', 1, '2026-11-10 20:57:28');

-- clientes: 1 registros
INSERT INTO `clientes` (`id`, `tipo_documento`, `numero_documento`, `nombre`, `telefono`, `email`, `direccion`, `activo`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (1, 'DNI', '00000000', 'Público General / Venta Rápida', '-', '-', '-', 1, '517e819b-4136-4aa2-8e9c-37df395f73ea', 1, '2026-11-10 20:57:28');

-- movimientos_stock: 8 registros
INSERT INTO `movimientos_stock` (`id`, `producto_id`, `tipo_movimiento`, `cantidad`, `motivo`, `referencia`, `fecha`, `usuario_id`, `proveedor_id`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (1, 1, 'ENTRADA', 12, 'Inventario inicial de apertura', 'Guía Inicial 001', '2026-11-10 20:57:28', 1, 1, '84b46d01-3047-4d63-a41a-6cbb24707d99', 1, '2026-11-10 20:57:28');
INSERT INTO `movimientos_stock` (`id`, `producto_id`, `tipo_movimiento`, `cantidad`, `motivo`, `referencia`, `fecha`, `usuario_id`, `proveedor_id`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (2, 2, 'ENTRADA', 8, 'Inventario inicial de apertura', 'Guía Inicial 001', '2026-11-10 20:57:28', 1, 1, 'e9f4660c-5bfd-45e6-b383-b7af413f5ab8', 1, '2026-11-10 20:57:28');
INSERT INTO `movimientos_stock` (`id`, `producto_id`, `tipo_movimiento`, `cantidad`, `motivo`, `referencia`, `fecha`, `usuario_id`, `proveedor_id`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (3, 3, 'ENTRADA', 5, 'Inventario inicial de apertura', 'Guía Inicial 001', '2026-11-10 20:57:28', 1, 2, '8f9cd32d-d125-4e72-9aa0-e7b0af6423ee', 1, '2026-11-10 20:57:28');
INSERT INTO `movimientos_stock` (`id`, `producto_id`, `tipo_movimiento`, `cantidad`, `motivo`, `referencia`, `fecha`, `usuario_id`, `proveedor_id`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (4, 4, 'ENTRADA', 25, 'Inventario inicial de apertura', 'Guía Inicial 001', '2026-11-10 20:57:28', 1, 3, '711b0086-66e8-4f09-b8be-5c84e687cb1c', 1, '2026-11-10 20:57:28');
INSERT INTO `movimientos_stock` (`id`, `producto_id`, `tipo_movimiento`, `cantidad`, `motivo`, `referencia`, `fecha`, `usuario_id`, `proveedor_id`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (5, 5, 'ENTRADA', 15, 'Inventario inicial de apertura', 'Guía Inicial 001', '2026-11-10 20:57:28', 1, 1, '3430822f-4d33-438c-9d84-c2db7ab620f4', 1, '2026-11-10 20:57:28');
INSERT INTO `movimientos_stock` (`id`, `producto_id`, `tipo_movimiento`, `cantidad`, `motivo`, `referencia`, `fecha`, `usuario_id`, `proveedor_id`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (6, 6, 'ENTRADA', 7, 'Inventario inicial de apertura', 'Guía Inicial 001', '2026-11-10 20:57:28', 1, 2, '6b6cee09-adaa-4099-bea7-d67f64015f91', 1, '2026-11-10 20:57:28');
INSERT INTO `movimientos_stock` (`id`, `producto_id`, `tipo_movimiento`, `cantidad`, `motivo`, `referencia`, `fecha`, `usuario_id`, `proveedor_id`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (7, 7, 'ENTRADA', 10, 'Inventario inicial de apertura', 'Guía Inicial 001', '2026-11-10 20:57:28', 1, 3, 'cab70b14-a2e5-40d0-b138-f9db0b90230c', 1, '2026-11-10 20:57:28');
INSERT INTO `movimientos_stock` (`id`, `producto_id`, `tipo_movimiento`, `cantidad`, `motivo`, `referencia`, `fecha`, `usuario_id`, `proveedor_id`, `uuid`, `sincronizado`, `fecha_modificacion`) VALUES (8, 8, 'ENTRADA', 2, 'Inventario inicial de apertura', 'Guía Inicial 001', '2026-11-10 20:57:28', 1, 1, '37692974-b15a-4887-82ce-5ffa97702feb', 1, '2026-11-10 20:57:28');

-- sincronizacion_info: 1 registros
INSERT INTO `sincronizacion_info` (`id`, `ultima_sincronizacion`, `estado`, `detalles`) VALUES (1, 'Nunca', 'MODO_LOCAL', 'Sistema iniciado en modo local.');

SET FOREIGN_KEY_CHECKS = 1;
