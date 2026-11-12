import _path  # noqa: F401  (prepara rutas del proyecto)
"""
Suite de Pruebas Unitarias e Integrales para:
1. Código SKU Inteligente (Generación nemotécnica, correlativos correlativos y control de duplicados).
2. Asistente Inteligente de Reposición (Detección de stock mínimo, demanda habitual, cálculo de compras y exportación Excel).
"""
import os
import sys
import time

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from datetime import datetime, timedelta
from database.db import get_connection
from database.schema import init_db
from models.producto import ProductoModel
from models.venta import VentaModel
from models.cliente import ClienteModel
from models.movimiento_stock import MovimientoStockModel
from services.reposicion_service import ReposicionService
from services.excel_service import ExcelService

def ejecutar_pruebas():
    print("=" * 75)
    print("EJECUTANDO PRUEBAS DE CÓDIGO SKU INTELIGENTE Y ASISTENTE DE REPOSICIÓN")
    print("=" * 75)

    init_db()
    ts = time.time_ns()

    # =========================================================================
    # PARTE 1: CÓDIGO SKU INTELIGENTE
    # =========================================================================
    print("\n--- [PARTE 1] VALIDACIÓN DE CÓDIGO SKU INTELIGENTE ---")

    # 1.1 Generación según categoría y marca
    print("\n[1.1] Generación nemotécnica según categoría y marca...")
    sku_lap_len = ProductoModel.generar_sku_sugerido(categoria_nombre="Laptops y Equipos", marca="Lenovo")
    print(f"  -> Laptops + Lenovo: '{sku_lap_len}'")
    assert sku_lap_len.startswith("LAP-LEN-"), f"Esperado prefijo LAP-LEN-, obtenido: {sku_lap_len}"

    sku_cpu_amd = ProductoModel.generar_sku_sugerido(categoria_nombre="Procesadores (CPU)", marca="AMD")
    print(f"  -> Procesadores + AMD: '{sku_cpu_amd}'")
    assert sku_cpu_amd.startswith("CPU-AMD-"), f"Esperado prefijo CPU-AMD-, obtenido: {sku_cpu_amd}"

    sku_gpu_msi = ProductoModel.generar_sku_sugerido(categoria_nombre="Tarjetas Gráficas (GPU)", marca="MSI")
    print(f"  -> Tarjetas Gráficas + MSI: '{sku_gpu_msi}'")
    assert sku_gpu_msi.startswith("GPU-MSI-"), f"Esperado prefijo GPU-MSI-, obtenido: {sku_gpu_msi}"

    sku_mon_sam = ProductoModel.generar_sku_sugerido(categoria_nombre="Monitores", marca="Samsung")
    print(f"  -> Monitores + Samsung: '{sku_mon_sam}'")
    assert sku_mon_sam.startswith("MON-SAM-"), f"Esperado prefijo MON-SAM-, obtenido: {sku_mon_sam}"

    # Marca corta (ej: HP) con padding
    sku_lap_hp = ProductoModel.generar_sku_sugerido(categoria_nombre="Laptops y Equipos", marca="HP")
    print(f"  -> Laptops + HP: '{sku_lap_hp}'")
    assert sku_lap_hp.startswith("LAP-HPX-"), f"Esperado prefijo LAP-HPX-, obtenido: {sku_lap_hp}"

    # Marca vacía o genérica
    sku_gen = ProductoModel.generar_sku_sugerido(categoria_nombre="Periféricos", marca="")
    print(f"  -> Periféricos + (Vacío): '{sku_gen}'")
    assert sku_gen.startswith("PER-GEN-"), f"Esperado prefijo PER-GEN-, obtenido: {sku_gen}"
    print("  [OK] Códigos nemotécnicos generados correctamente.")

    # 1.2 Secuencia de correlativos e incremento automático
    print("\n[1.2] Verificación del incremento de correlativo numérico...")
    # Crear un producto con el SKU sugerido actual
    sku_base = ProductoModel.generar_sku_sugerido(categoria_nombre="Laptops y Equipos", marca="Asus")
    prefijo_asus = "LAP-ASU"
    assert sku_base.startswith(f"{prefijo_asus}-")
    correlativo_1 = int(sku_base.split("-")[-1])

    # Guardar producto en la base de datos con ese código
    pid_1, err_1 = ProductoModel.crear_producto(
        codigo=sku_base,
        nombre="Laptop Gamer Asus ROG Strix",
        categoria_id=10,
        marca="Asus",
        precio_compra=4500.0,
        precio_venta=5200.0,
        stock=5,
        stock_minimo=2,
        descripcion="i7 13va Gen, RTX 4060",
        proveedor_id=1
    )
    assert err_1 is None and pid_1 is not None

    # Generar el siguiente: debe ser correlativo_1 + 1
    sku_siguiente = ProductoModel.generar_sku_sugerido(categoria_nombre="Laptops y Equipos", marca="Asus")
    correlativo_2 = int(sku_siguiente.split("-")[-1])
    assert correlativo_2 == correlativo_1 + 1, f"Esperado correlativo {correlativo_1 + 1}, obtenido: {correlativo_2}"
    print(f"  [OK] Correlativo consecutivo verificado: {sku_base} -> {sku_siguiente}")

    # 1.3 Verificación y validación de código no duplicado
    print("\n[1.3] Control estricto de códigos no repetidos...")
    # El código recién registrado debe figurar como no disponible
    disp_ocupado = ProductoModel.es_codigo_disponible(sku_base)
    assert disp_ocupado is False, f"El código {sku_base} debería estar ocupado"

    # Si se excluye el producto ID propio (en caso de edición), debe figurar como disponible para sí mismo
    disp_propio = ProductoModel.es_codigo_disponible(sku_base, excluir_producto_id=pid_1)
    assert disp_propio is True, "El código propio debe ser válido para el mismo producto al editar"

    # Un código no registrado debe figurar como disponible
    sku_inventado = f"LAP-ASU-{correlativo_1 + 999:03d}"
    disp_libre = ProductoModel.es_codigo_disponible(sku_inventado)
    assert disp_libre is True, f"El código {sku_inventado} debería estar disponible"

    # Intento de inserción directa de código repetido: debe ser rechazado
    pid_dup, err_dup = ProductoModel.crear_producto(
        codigo=sku_base,
        nombre="Laptop Clon Repetido",
        categoria_id=10,
        marca="Asus",
        precio_compra=3000.0,
        precio_venta=3500.0,
        stock=2,
        stock_minimo=1
    )
    assert pid_dup is None and err_dup is not None, "El sistema debe rechazar la creación de producto con SKU repetido"
    print(f"  [OK] Inserción duplicada bloqueada correctamente: {err_dup}")


    # =========================================================================
    # PARTE 2: ASISTENTE INTELIGENTE DE REPOSICIÓN
    # =========================================================================
    print("\n--- [PARTE 2] ASISTENTE INTELIGENTE DE REPOSICIÓN ---")

    # 2.1 Crear productos con diferentes escenarios de inventario
    print("\n[2.1] Preparando productos de prueba para escenarios de reposición...")
    
    # Escenario A: Producto Crítico (Agotado, Stock = 0, con ventas registradas)
    sku_critico = f"LAP-TEST-CRIT-{ts}"
    pid_critico, _ = ProductoModel.crear_producto(
        codigo=sku_critico,
        nombre="Laptop Ultrabook ZenBook Pro",
        categoria_id=10,
        marca="Asus",
        precio_compra=3500.0,
        precio_venta=4200.0,
        stock=0, # AGOTADO
        stock_minimo=3,
        descripcion="Test Agotado",
        proveedor_id=1
    )

    # Escenario B: Producto en Stock Mínimo (Stock = 2 <= Mínimo 4)
    sku_alerta = f"MBD-TEST-ALER-{ts}"
    pid_alerta, _ = ProductoModel.crear_producto(
        codigo=sku_alerta,
        nombre="Placa Madre ASUS TUF B650-PLUS WIFI",
        categoria_id=3,
        marca="Asus",
        precio_compra=650.0,
        precio_venta=820.0,
        stock=2, # <= Mínimo
        stock_minimo=4,
        descripcion="Test Nivel Alerta",
        proveedor_id=2
    )

    # Escenario C: Producto con stock óptimo y sin necesidad de reposición
    sku_optimo = f"CPU-TEST-OPT-{ts}"
    pid_optimo, _ = ProductoModel.crear_producto(
        codigo=sku_optimo,
        nombre="Procesador Intel Core i5 13400F",
        categoria_id=1,
        marca="Intel",
        precio_compra=600.0,
        precio_venta=750.0,
        stock=20, # Muy por encima del mínimo
        stock_minimo=3,
        descripcion="Test Nivel Óptimo",
        proveedor_id=3
    )

    print(f"  -> Creado producto crítico ID {pid_critico} (Stock: 0, Mín: 3)")
    print(f"  -> Creado producto alerta ID {pid_alerta} (Stock: 2, Mín: 4)")
    print(f"  -> Creado producto óptimo ID {pid_optimo} (Stock: 20, Mín: 3)")

    # 2.2 Registrar ventas para probar el cálculo de demanda habitual
    print("\n[2.2] Registrando ventas para simular demanda histórica habitual...")
    # Aseguramos cliente
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM clientes WHERE numero_documento = '00000000';")
    cli_id = c.fetchone()[0]
    
    # Temporalmente añadimos stock para realizar la venta de prueba del producto crítico
    c.execute("UPDATE productos SET stock = 10 WHERE id = ?;", (pid_critico,))
    conn.commit()
    conn.close()

    # Venta de 6 unidades en el producto crítico
    items_venta = [{"producto_id": pid_critico, "cantidad": 6, "precio_unitario": 4200.0}]
    v_id, v_err = VentaModel.registrar_venta(
        cliente_id=cli_id,
        tipo_comprobante="Boleta",
        metodo_pago="Efectivo",
        items=items_venta
    )
    assert v_err is None and v_id is not None
    
    # Dejamos el stock en 0 como correspondía
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE productos SET stock = 0 WHERE id = ?;", (pid_critico,))
    conn.commit()
    conn.close()

    print(f"  [OK] Venta registrada (ID {v_id}) con 6 unidades vendidas del producto crítico.")

    # 2.3 Ejecución del análisis del Asistente de Reposición
    print("\n[2.3] Ejecutando análisis del Asistente de Reposición (30 días de demanda y cobertura)...")
    resultado = ReposicionService.analizar_reposicion(dias_analisis=30, dias_cobertura_deseada=30)
    resumen = resultado["resumen"]
    sugerencias = resultado["sugerencias"]

    print(f"  -> Total catálogo evaluado: {resumen['total_catalogo']}")
    print(f"  -> Productos que requieren reposición: {resumen['total_por_reponer']}")
    print(f"  -> Total unidades recomendadas a comprar: {resumen['unidades_totales_sugeridas']} un.")
    print(f"  -> Presupuesto total estimado: S/ {resumen['inversion_total_estimada']:,.2f}")
    print(f"  -> Proveedores mayoristas involucrados: {resumen['total_proveedores_involucrados']}")

    assert resumen["total_por_reponer"] > 0
    assert resumen["unidades_totales_sugeridas"] > 0

    # 2.4 Verificación de las métricas específicas de los productos probados
    print("\n[2.4] Verificación de cálculos individuales...")
    mapa_sug = {s["id"]: s for s in sugerencias}

    # Validar producto crítico (pid_critico)
    s_crit = mapa_sug.get(pid_critico)
    assert s_crit is not None, "El producto crítico debe estar en el reporte de reposición"
    assert s_crit["nivel_urgencia"] == "CRITICO", f"Esperado CRITICO, obtenido {s_crit['nivel_urgencia']}"
    assert s_crit["stock_actual"] == 0
    assert s_crit["unidades_vendidas_periodo"] >= 6
    # Demanda diaria = 6 / 30 = 0.2 un/día. Cobertura 30 días = 6 un. Stock objetivo = 3 (mín) + 6 = 9 un.
    assert s_crit["cantidad_sugerida"] >= 9, f"Cantidad sugerida insuficiente: {s_crit['cantidad_sugerida']}"
    assert s_crit["costo_estimado"] == round(s_crit["cantidad_sugerida"] * s_crit["precio_compra"], 2)
    assert s_crit["proveedor_id"] == 1
    print(f"  [OK] Producto Crítico verificado:")
    print(f"       SKU: {s_crit['codigo']} | Stock: {s_crit['stock_actual']} | Ventas: {s_crit['unidades_vendidas_periodo']}")
    print(f"       Demanda Diaria: {s_crit['demanda_diaria']} un/d | Sugerido a Comprar: {s_crit['cantidad_sugerida']} un.")
    print(f"       Inversión Est.: S/ {s_crit['costo_estimado']:,.2f} | Justificación: {s_crit['justificacion'][:80]}...")

    # Validar producto en stock mínimo sin ventas (pid_alerta)
    s_alert = mapa_sug.get(pid_alerta)
    assert s_alert is not None, "El producto en alerta debe estar en el reporte"
    assert s_alert["requiere_reposicion"] is True
    assert s_alert["stock_actual"] == 2 and s_alert["stock_minimo"] == 4
    # Recomendación para producto sin ventas: max(stock_minimo*2 - stock, stock_minimo) = max(8-2, 4) = 6 un.
    assert s_alert["cantidad_sugerida"] >= 4
    print(f"  [OK] Producto en Alerta verificado:")
    print(f"       SKU: {s_alert['codigo']} | Stock: {s_alert['stock_actual']} (Mín {s_alert['stock_minimo']})")
    print(f"       Sugerido a Comprar: {s_alert['cantidad_sugerida']} un. | Proveedor: {s_alert['proveedor_nombre']}")

    # Validar producto óptimo (pid_optimo): No debe requerir reposición
    s_opt = mapa_sug.get(pid_optimo)
    assert s_opt is not None
    assert s_opt["requiere_reposicion"] is False
    assert s_opt["cantidad_sugerida"] == 0
    print(f"  [OK] Producto Óptimo verificado: Stock {s_opt['stock_actual']} no requiere reposición.")

    # 2.5 Exportación de recomendaciones a Microsoft Excel (.xlsx)
    print("\n[2.5] Exportación del informe del Asistente a Microsoft Excel (.xlsx)...")
    ok_xlsx, ruta_xlsx = ExcelService.exportar_asistente_reposicion(resultado)
    assert ok_xlsx is True and os.path.exists(ruta_xlsx)
    tam_xlsx = os.path.getsize(ruta_xlsx)
    assert tam_xlsx > 1000
    print(f"  [OK] Archivo Excel generado exitosamente: {os.path.basename(ruta_xlsx)} ({tam_xlsx} bytes)")

    # 2.6 Limpieza de registros de prueba
    print("\n[2.6] Limpieza de productos de prueba...")
    ProductoModel.eliminar_producto(pid_1)
    ProductoModel.eliminar_producto(pid_critico)
    ProductoModel.eliminar_producto(pid_alerta)
    ProductoModel.eliminar_producto(pid_optimo)
    print("  [OK] Productos de prueba desactivados preservando historial.")

    print("\n" + "=" * 75)
    print("¡TODAS LAS PRUEBAS DE SKU INTELIGENTE Y ASISTENTE DE REPOSICIÓN PASARON (100% OK)!")
    print("=" * 75)

if __name__ == "__main__":
    ejecutar_pruebas()

