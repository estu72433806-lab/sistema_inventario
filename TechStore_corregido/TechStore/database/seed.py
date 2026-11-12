"""
Datos iniciales de demostración para una instalación nueva.
Solo inserta si las tablas están vacías, así que no duplica datos al reiniciar.
Los registros de demo se marcan como sincronizados para no subirlos a la nube.
"""
import uuid
from datetime import datetime
from database.db import get_connection
from models.usuario import UsuarioModel

# codigo, nombre, categoria_id, proveedor_id, marca, precio_compra, precio_venta, stock, stock_minimo, descripcion
PRODUCTOS_DEMO = [
    ("CPU-INT-001", "Procesador Intel Core i5-13400F 2.5/4.6GHz", 1, 1, "Intel", 720.00, 890.00, 12, 3, "10 núcleos, 16 hilos, LGA1700"),
    ("CPU-AMD-002", "Procesador AMD Ryzen 7 5700X 3.4/4.6GHz", 1, 1, "AMD", 680.00, 830.00, 8, 2, "8 núcleos, 16 hilos, AM4"),
    ("GPU-NV-001", "Tarjeta Gráfica ASUS Dual GeForce RTX 4060 OC 8GB", 2, 2, "ASUS", 1350.00, 1620.00, 5, 2, "GDDR6, DLSS 3, Ray Tracing"),
    ("RAM-KNG-001", "Memoria RAM Kingston Fury Beast 16GB DDR4 3200MHz", 4, 3, "Kingston", 140.00, 185.00, 25, 5, "Disipador negro, CL16"),
    ("SSD-KNG-002", "Disco Sólido SSD M.2 NVMe Kingston NV2 1TB PCIe 4.0", 5, 1, "Kingston", 210.00, 275.00, 15, 4, "Lectura hasta 3500 MB/s"),
    ("PSU-COR-001", "Fuente de Poder Corsair CV650 650W 80 Plus Bronze", 6, 2, "Corsair", 240.00, 310.00, 7, 2, "Certificación 80 Plus Bronze"),
    ("PER-LOG-001", "Mouse Gamer Logitech G502 HERO 25K", 9, 3, "Logitech", 150.00, 219.00, 10, 3, "Sensor HERO 25K, 11 botones"),
    ("PER-RED-002", "Teclado Mecánico Redragon Kumara K552 RGB", 9, 1, "Redragon", 120.00, 169.00, 2, 3, "Switches Outemu Red (Alerta Stock Bajo)"),
]

def insertar_datos_demo():
    """Crea el vendedor de prueba y el catálogo de muestra si faltan."""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'vendedor';")
        if cursor.fetchone()[0] == 0:
            UsuarioModel.crear_usuario(
                username="vendedor",
                password="ven123",
                nombre_completo="Carlos Vendedor",
                rol="vendedor"
            )

        cursor.execute("SELECT COUNT(*) FROM productos;")
        if cursor.fetchone()[0] == 0:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for p in PRODUCTOS_DEMO:
                cursor.execute("""
                    INSERT INTO productos (uuid, codigo, nombre, categoria_id, proveedor_id, marca,
                                           precio_compra, precio_venta, stock, stock_minimo, descripcion,
                                           activo, fecha_modificacion, sincronizado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, 1);
                """, (str(uuid.uuid4()),) + p + (ahora,))
                prod_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO movimientos_stock (uuid, producto_id, tipo_movimiento, cantidad, motivo, referencia,
                                                   fecha, usuario_id, proveedor_id, fecha_modificacion, sincronizado)
                    VALUES (?, ?, 'ENTRADA', ?, 'Inventario inicial de apertura', 'Guía Inicial 001', ?, 1, ?, ?, 1);
                """, (str(uuid.uuid4()), prod_id, p[7], ahora, p[3], ahora))

            conn.commit()
    finally:
        conn.close()
