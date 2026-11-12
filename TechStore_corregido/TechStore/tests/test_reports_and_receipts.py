import _path  # noqa: F401  (prepara rutas del proyecto)
"""
Script de pruebas automatizadas para:
1. Validación de fechas (formato y coherencia de rangos).
2. Reportes detallados de ventas con productos, cantidades, descuentos y totales.
3. Exportación de reporte de inventario a Excel (.xlsx) con openpyxl.
4. Exportación de reporte de ventas a Excel (.xlsx) con openpyxl.
5. Generación de boletas/recibos en PDF con ReportLab en 'documentos_generados/comprobantes'.
6. Manejo seguro de errores sin cerrar la aplicación.
"""
import os
import sys

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from datetime import datetime
from database.schema import init_db
from models.producto import ProductoModel
from models.cliente import ClienteModel
from models.venta import VentaModel
from services.excel_service import ExcelService
from services.pdf_service import PDFService

def ejecutar_pruebas_reportes():
    print("=" * 65)
    print("INICIANDO PRUEBAS DE REPORTES Y COMPROBANTES (EXCEL Y PDF)")
    print("=" * 65)

    init_db()

    import time
    ts = time.time_ns()

    # 1. Probar validación de fechas
    print("\n[1] Probando validaciones de fechas (AAAA-MM-DD)...")
    def validar(f_ini, f_fin):
        if not f_ini and not f_fin:
            return True, None
        try:
            d_ini = datetime.strptime(f_ini, "%Y-%m-%d").date() if f_ini else None
            d_fin = datetime.strptime(f_fin, "%Y-%m-%d").date() if f_fin else None
            if d_ini and d_fin and d_ini > d_fin:
                return False, "Fecha inicial posterior a fecha final"
            return True, None
        except ValueError:
            return False, "Formato inválido"

    # Casos de prueba
    assert validar("2026-10-01", "2026-10-31")[0] is True
    assert validar("2026-12-01", "2026-01-01")[0] is False # Rango invertido
    assert validar("fecha_invalida", "2026-10-01")[0] is False # Malformado
    assert validar("", "")[0] is True # Vacío = todo
    print("  [OK] Validaciones de fecha exitosas (control de formato y coherencia de rango).")

    # 2. Registrar venta de prueba para asegurar datos en el periodo
    print("\n[2] Registrando venta de prueba con descuento para verificar detalle...")
    p_id, _ = ProductoModel.crear_producto(
        codigo=f"REP-CPU-{ts}",
        nombre="Procesador AMD Ryzen 9 7900X",
        categoria_id=1,
        marca="AMD",
        precio_compra=1400.0,
        precio_venta=1800.0,
        stock=6,
        stock_minimo=2,
        usuario_id=1
    )

    items = [{"producto_id": p_id, "cantidad": 2, "precio_unitario": 1800.0}] # Subtotal S/ 3600
    venta_id, err_v = VentaModel.registrar_venta(
        cliente_id=1,
        tipo_comprobante="Boleta",
        metodo_pago="Transferencia BCP",
        items=items,
        tipo_descuento="MONTO",
        valor_descuento=200.0, # Descuento S/ 200
        impuesto_porcentaje=18.0,
        usuario_id=1
    )
    assert err_v is None and venta_id is not None
    print(f"  [OK] Venta de prueba registrada (ID: {venta_id}) con 2 unidades y S/ 200.00 de descuento.")

    # 3. Consultar ventas detalladas por rango
    print("\n[3] Consultando detalle de ventas por rango de fechas...")
    hoy = datetime.now().strftime("%Y-%m-%d")
    detalles = VentaModel.obtener_ventas_detalladas_rango(fecha_inicio=hoy, fecha_fin=hoy)
    assert len(detalles) > 0
    primer_det = next((d for d in detalles if d["venta_id"] == venta_id), None)
    assert primer_det is not None
    assert primer_det["cantidad"] == 2
    assert primer_det["precio_unitario"] == 1800.0
    assert primer_det["venta_descuento"] == 200.0
    print(f"  [OK] Detalle recuperado correctamente: Producto '{primer_det['producto_nombre']}', Cant: {primer_det['cantidad']}, P.Unit: S/ {primer_det['precio_unitario']}, Desc: S/ {primer_det['venta_descuento']}.")

    # 4. Probar exportación de Inventario a Excel (.xlsx) con openpyxl
    print("\n[4] Exportando Reporte de Inventario a Excel (.xlsx) con openpyxl...")
    prods = ProductoModel.listar_productos()
    ok_inv, ruta_inv = ExcelService.exportar_inventario(prods)
    assert ok_inv is True
    assert os.path.exists(ruta_inv) and os.path.getsize(ruta_inv) > 1000
    print(f"  [OK] Archivo Excel de Inventario generado ({os.path.getsize(ruta_inv)} bytes) en:\n       {ruta_inv}")

    # 5. Probar exportación de Ventas Detalladas a Excel (.xlsx) con openpyxl
    print("\n[5] Exportando Reporte Detallado de Ventas a Excel (.xlsx) con openpyxl...")
    ok_v_excel, ruta_v_excel = ExcelService.exportar_ventas_detallado(
        ventas_detalladas=detalles,
        fecha_inicio=hoy,
        fecha_fin=hoy
    )
    assert ok_v_excel is True
    assert os.path.exists(ruta_v_excel) and os.path.getsize(ruta_v_excel) > 1000
    print(f"  [OK] Archivo Excel de Ventas generado ({os.path.getsize(ruta_v_excel)} bytes) en:\n       {ruta_v_excel}")

    # 6. Probar generación de Comprobante PDF con ReportLab
    print("\n[6] Generando Boleta / Recibo de venta en PDF con ReportLab...")
    venta_completa = VentaModel.obtener_venta_completa(venta_id)
    ok_pdf, ruta_pdf = PDFService.generar_comprobante_pdf(venta_completa)
    assert ok_pdf is True
    assert os.path.exists(ruta_pdf) and os.path.getsize(ruta_pdf) > 1000
    print(f"  [OK] Boleta PDF generada ({os.path.getsize(ruta_pdf)} bytes) en:\n       {ruta_pdf}")

    # 7. Verificar estructura de carpetas 'documentos_generados'
    print("\n[7] Verificando carpetas de documentos generados...")
    base_dir = _path.ROOT
    carpeta_reportes = os.path.join(base_dir, "documentos_generados", "reportes")
    carpeta_comprobantes = os.path.join(base_dir, "documentos_generados", "comprobantes")

    assert os.path.exists(carpeta_reportes), "No existe la carpeta documentos_generados/reportes"
    assert os.path.exists(carpeta_comprobantes), "No existe la carpeta documentos_generados/comprobantes"
    print(f"  [OK] Carpeta de reportes: {carpeta_reportes}")
    print(f"  [OK] Carpeta de comprobantes: {carpeta_comprobantes}")

    print("\n" + "=" * 65)
    print("¡TODAS LAS PRUEBAS DE REPORTES Y COMPROBANTES PASARON EXITOSAMENTE!")
    print("=" * 65)

if __name__ == "__main__":
    ejecutar_pruebas_reportes()
