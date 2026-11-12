import _path  # noqa: F401  (prepara rutas del proyecto)
"""
Script de pruebas automatizadas para el módulo de ventas:
1. Venta múltiple de productos.
2. Descuento en monto fijo (S/) y en porcentaje (%).
3. Validación estricta de límites de descuento.
4. Rechazo de venta si falta stock y reversión transaccional completa (rollback).
5. Descuento automático de stock e inserción de movimientos de salida en Kardex.
6. Generación del comprobante PDF con ReportLab.
"""
import os
import sys

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from database.db import get_connection
from database.schema import init_db
from models.producto import ProductoModel
from models.cliente import ClienteModel
from models.venta import VentaModel
from models.movimiento_stock import MovimientoStockModel
from services.pdf_service import PDFService

def ejecutar_pruebas_ventas():
    print("=" * 65)
    print("INICIANDO PRUEBAS DEL MÓDULO DE VENTAS (POS)")
    print("=" * 65)

    init_db()

    import time
    ts = time.time_ns()

    # 1. Crear productos específicos para las pruebas
    print("\n[1] Creando productos de prueba con stock conocido...")
    p1_id, _ = ProductoModel.crear_producto(
        codigo=f"CPU-TEST-{ts}",
        nombre="CPU Ryzen 5 5600X",
        categoria_id=1,
        marca="AMD",
        precio_compra=500.0,
        precio_venta=700.0,
        stock=10,
        stock_minimo=2,
        usuario_id=1
    )
    p2_id, _ = ProductoModel.crear_producto(
        codigo=f"GPU-TEST-{ts}",
        nombre="GPU GeForce RTX 3060",
        categoria_id=2,
        marca="NVIDIA",
        precio_compra=1100.0,
        precio_venta=1400.0,
        stock=4,
        stock_minimo=1,
        usuario_id=1
    )
    assert p1_id and p2_id
    print(f"  [OK] Producto 1 (Stock: 10, P.Venta: S/ 700.00)")
    print(f"  [OK] Producto 2 (Stock: 4, P.Venta: S/ 1400.00)")

    # 2. Probar rechazo cuando falta stock (Rollback transaccional)
    print("\n[2] Probando intento de venta con STOCK INSUFICIENTE...")
    items_insuficientes = [
        {"producto_id": p1_id, "cantidad": 2, "precio_unitario": 700.0},
        {"producto_id": p2_id, "cantidad": 10, "precio_unitario": 1400.0} # Pide 10 habiendo solo 4!
    ]
    venta_fail_id, err_stock = VentaModel.registrar_venta(
        cliente_id=1,
        tipo_comprobante="Boleta",
        metodo_pago="Efectivo",
        items=items_insuficientes,
        tipo_descuento="NINGUNO",
        valor_descuento=0.0,
        impuesto_porcentaje=18.0,
        usuario_id=1
    )
    assert venta_fail_id is None, "La venta debió rechazarse por falta de stock!"
    assert "Stock insuficiente" in err_stock, f"Mensaje incorrecto: {err_stock}"
    print(f"  [OK] Venta rechazada correctamente:\n       \"{err_stock.splitlines()[0]}\"")

    # Verificar que el stock de p1 no se descontó (Rollback verificado)
    p1_check = ProductoModel.obtener_por_id(p1_id)
    assert p1_check["stock"] == 10, f"Error: El stock de p1 se modificó a pesar del fallo! ({p1_check['stock']})"
    print("  [OK] Transacción revertida (Rollback): El stock de todos los productos permanece intacto.")

    # 3. Probar validación de límites de descuento
    print("\n[3] Probando validaciones de límites de descuento...")
    items_validos = [
        {"producto_id": p1_id, "cantidad": 2, "precio_unitario": 700.0}, # S/ 1400
        {"producto_id": p2_id, "cantidad": 1, "precio_unitario": 1400.0}  # S/ 1400 -> Total Bruto: S/ 2800
    ]

    # Descuento mayor a subtotal en monto
    v_desc_excede, err_desc1 = VentaModel.registrar_venta(
        cliente_id=1, tipo_comprobante="Boleta", metodo_pago="Efectivo",
        items=items_validos, tipo_descuento="MONTO", valor_descuento=3500.0,
        usuario_id=1
    )
    assert v_desc_excede is None and "no puede superar el subtotal" in err_desc1
    print("  [OK] Rechazado descuento en monto superior al subtotal.")

    # Descuento en porcentaje mayor al 100%
    v_pct_excede, err_desc2 = VentaModel.registrar_venta(
        cliente_id=1, tipo_comprobante="Boleta", metodo_pago="Efectivo",
        items=items_validos, tipo_descuento="PORCENTAJE", valor_descuento=110.0,
        usuario_id=1
    )
    assert v_pct_excede is None and "100%" in err_desc2
    print("  [OK] Rechazado descuento en porcentaje mayor al 100%.")

    # 4. Probar venta exitosa con descuento en monto y descuento automático de stock
    print("\n[4] Procesando venta múltiple válida con descuento de S/ 300.00...")
    # Subtotal bruto: 2*700 + 1*1400 = S/ 2800
    # Descuento: S/ 300 -> Subtotal neto: S/ 2500
    # IGV 18%: S/ 450 -> Total: S/ 2950
    venta_ok_id, err_ok = VentaModel.registrar_venta(
        cliente_id=1,
        tipo_comprobante="Boleta",
        metodo_pago="Tarjeta de Crédito",
        items=items_validos,
        tipo_descuento="MONTO",
        valor_descuento=300.0,
        impuesto_porcentaje=18.0,
        usuario_id=1
    )
    assert err_ok is None, f"Error al procesar venta: {err_ok}"
    assert venta_ok_id is not None
    print(f"  [OK] Venta registrada con ID: {venta_ok_id}")

    # Consultar venta confirmada
    v_conf = VentaModel.obtener_venta_completa(venta_ok_id)
    assert v_conf["subtotal"] == 2800.0
    assert v_conf["descuento"] == 300.0
    assert v_conf["impuesto"] == 450.0
    assert v_conf["total"] == 2950.0
    assert len(v_conf["detalles"]) == 2
    print(f"  [OK] Comprobante: {v_conf['numero_comprobante']}")
    print(f"  [OK] Montos calculados: Subtotal: S/ {v_conf['subtotal']} | Descuento: -S/ {v_conf['descuento']} | IGV: S/ {v_conf['impuesto']} | Total: S/ {v_conf['total']}")

    # 5. Verificar descuento de stock y Kardex
    print("\n[5] Verificando descuento de stock y trazabilidad en Kardex...")
    p1_post = ProductoModel.obtener_por_id(p1_id)
    p2_post = ProductoModel.obtener_por_id(p2_id)
    assert p1_post["stock"] == 10 - 2, f"Stock p1 incorrecto: {p1_post['stock']}" # 8
    assert p2_post["stock"] == 4 - 1, f"Stock p2 incorrecto: {p2_post['stock']}"   # 3
    print(f"  [OK] Stock actualizado correctamente: p1 (10 -> {p1_post['stock']}), p2 (4 -> {p2_post['stock']})")

    # Kardex en movimientos_stock
    kardex_p1 = MovimientoStockModel.listar_movimientos(producto_id=p1_id)
    mov_salida = next((m for m in kardex_p1 if m["referencia"] == v_conf["numero_comprobante"]), None)
    assert mov_salida is not None
    assert mov_salida["tipo_movimiento"] == "SALIDA" and mov_salida["cantidad"] == 2
    print(f"  [OK] Movimiento de salida registrado en Kardex para {v_conf['numero_comprobante']}.")

    # 6. Probar generación de comprobante PDF con ReportLab
    print("\n[6] Generando comprobante PDF con ReportLab...")
    base_dir = _path.ROOT
    comprobantes_dir = os.path.join(base_dir, "comprobantes")
    os.makedirs(comprobantes_dir, exist_ok=True)
    pdf_test_path = os.path.join(comprobantes_dir, f"Test_{v_conf['numero_comprobante']}.pdf")

    ok_pdf, ruta = PDFService.generar_comprobante_pdf(v_conf, pdf_test_path)
    assert ok_pdf is True
    assert os.path.exists(ruta) and os.path.getsize(ruta) > 1000
    print(f"  [OK] Comprobante PDF generado exitosamente ({os.path.getsize(ruta)} bytes) en:\n       {ruta}")

    print("\n" + "=" * 65)
    print("¡TODAS LAS PRUEBAS DEL MÓDULO DE VENTAS PASARON CON ÉXITO!")
    print("=" * 65)

if __name__ == "__main__":
    ejecutar_pruebas_ventas()
