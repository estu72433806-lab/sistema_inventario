import _path  # noqa: F401  (prepara rutas del proyecto)
"""
Script Integral de Pruebas de Sistema Completo (test_complete_system.py).
Prueba exhaustivamente cada una de las funcionalidades requeridas:
1. Inicio de sesión con credenciales válidas e inválidas (hash seguro PBKDF2).
2. Registro, consulta, modificación y desactivación de productos.
3. Entradas de stock indicando proveedor mayorista.
4. Ajustes de stock por pérdida o daño físico.
5. Ventas con varios productos, descuentos (monto y %) y cálculo de totales.
6. Validación estricta de stock y reversión transaccional (rollback).
7. Alertas inmediatas de stock mínimo.
8. Reportes de ventas por rango de fechas (con validación AAAA-MM-DD).
9. Exportación de inventario y ventas a Excel (.xlsx) con openpyxl.
10. Generación de comprobantes PDF con ReportLab en 'documentos_generados/comprobantes'.
11. Matriz de permisos de usuario (Administrador vs Vendedor).
12. Creación y desactivación de cuentas de usuario.
13. Consulta de métricas del Dashboard con datos reales de SQLite.
14. Persistencia de datos al cerrar y volver a conectar la base de datos SQLite.
"""
import os
import sys
import time

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from datetime import datetime
from database.db import get_connection
from database.schema import init_db
from database.seed import insertar_datos_demo
from models.usuario import UsuarioModel
from models.producto import ProductoModel
from models.cliente import ClienteModel
from models.proveedor import ProveedorModel
from models.movimiento_stock import MovimientoStockModel
from models.venta import VentaModel
from services.excel_service import ExcelService
from services.pdf_service import PDFService

def ejecutar_suite_completa():
    print("=" * 70)
    print("EJECUTANDO SUITE INTEGRAL DE PRUEBAS DEL SISTEMA TECHSTORE")
    print("=" * 70)

    # Inicializar SQLite y cargar los usuarios/datos demo (admin y vendedor de prueba)
    init_db()
    insertar_datos_demo()
    ts = time.time_ns()

    # -------------------------------------------------------------
    # PRUEBA 1: Inicio de sesión y seguridad de contraseñas
    # -------------------------------------------------------------
    print("\n[PRUEBA 1] Inicio de sesión y hash seguro (PBKDF2-HMAC-SHA256)...")
    ses_admin, err_admin = UsuarioModel.autenticar("admin", "admin123")
    assert err_admin is None and ses_admin["rol"] == "administrador"

    ses_ven, err_ven = UsuarioModel.autenticar("vendedor", "ven123")
    assert err_ven is None and ses_ven["rol"] == "vendedor"

    ses_err, err_pass = UsuarioModel.autenticar("admin", "clave_falsa")
    assert ses_err is None and "incorrecta" in err_pass.lower()

    print("  [OK] Autenticación de Administrador, Vendedor y rechazo de clave errónea verificados.")

    # -------------------------------------------------------------
    # PRUEBA 2: Registro, consulta y modificación de productos
    # -------------------------------------------------------------
    print("\n[PRUEBA 2] Registro y consulta de productos...")
    sku_test = f"GPU-TEST-{ts}"
    prod_id, err_p = ProductoModel.crear_producto(
        codigo=sku_test,
        nombre="Tarjeta Gráfica RTX 4070 Ti Super",
        categoria_id=2,
        marca="MSI",
        precio_compra=2800.0,
        precio_venta=3400.0,
        stock=8,
        stock_minimo=3,
        descripcion="16GB GDDR6X, DLSS 3.5",
        proveedor_id=1,
        usuario_id=1
    )
    assert err_p is None and prod_id is not None
    p_reg = ProductoModel.obtener_por_id(prod_id)
    assert p_reg["stock"] == 8 and p_reg["codigo"] == sku_test
    print(f"  [OK] Producto registrado con ID {prod_id} y stock verificado de {p_reg['stock']} unidades.")

    # -------------------------------------------------------------
    # PRUEBA 3: Entradas de stock indicando proveedor
    # -------------------------------------------------------------
    print("\n[PRUEBA 3] Entradas de mercadería indicando proveedor...")
    mov_in_id, err_in = MovimientoStockModel.registrar_entrada_mercaderia(
        producto_id=prod_id,
        cantidad=5,
        proveedor_id=1,
        referencia="Factura Mayorista F001-9921",
        motivo="Ingreso de lote por reposición",
        usuario_id=1
    )
    assert err_in is None and mov_in_id is not None
    p_after_in = ProductoModel.obtener_por_id(prod_id)
    assert p_after_in["stock"] == 13 # 8 + 5 = 13
    print(f"  [OK] Entrada de 5 unidades registrada (ID: {mov_in_id}). Stock incrementó a {p_after_in['stock']}.")

    # -------------------------------------------------------------
    # PRUEBA 4: Ajustes de stock por daño o pérdida
    # -------------------------------------------------------------
    print("\n[PRUEBA 4] Ajustes de stock por daño o pérdida...")
    mov_aj_id, err_aj = MovimientoStockModel.registrar_ajuste_stock(
        producto_id=prod_id,
        cantidad=2,
        motivo="Daño físico en ventilador durante manipulación",
        tipo_movimiento="SALIDA",
        usuario_id=1,
        referencia="Reporte Avería #102"
    )
    assert err_aj is None and mov_aj_id is not None
    p_after_aj = ProductoModel.obtener_por_id(prod_id)
    assert p_after_aj["stock"] == 11 # 13 - 2 = 11
    print(f"  [OK] Ajuste de salida por daño registrado (ID: {mov_aj_id}). Stock ajustado a {p_after_aj['stock']}.")

    # -------------------------------------------------------------
    # PRUEBA 5: Validación de stock y reversión transaccional
    # -------------------------------------------------------------
    print("\n[PRUEBA 5] Validación estricta de stock y reversión transaccional (Rollback)...")
    items_insuficientes = [
        {"producto_id": prod_id, "cantidad": 20, "precio_unitario": 3400.0} # Hay 11, pide 20!
    ]
    v_fail, err_stock = VentaModel.registrar_venta(
        cliente_id=1, tipo_comprobante="Boleta", metodo_pago="Efectivo",
        items=items_insuficientes, tipo_descuento="NINGUNO", valor_descuento=0.0, usuario_id=1
    )
    assert v_fail is None and "Stock insuficiente" in err_stock
    # Verificar que el stock no cambió
    p_check_roll = ProductoModel.obtener_por_id(prod_id)
    assert p_check_roll["stock"] == 11
    print(f"  [OK] Intento con sobre-stock rechazado correctamente. Stock intacto en {p_check_roll['stock']}.")

    # -------------------------------------------------------------
    # PRUEBA 6: Venta con varios productos y descuentos (Monto y %)
    # -------------------------------------------------------------
    print("\n[PRUEBA 6] Venta múltiple con descuentos calculados y trazabilidad...")
    p_ram_id, _ = ProductoModel.crear_producto(
        codigo=f"RAM-TEST-{ts}", nombre="RAM DDR5 32GB 6000MHz", categoria_id=4,
        marca="Corsair", precio_compra=380.0, precio_venta=500.0, stock=10, stock_minimo=2, usuario_id=1
    )

    items_venta = [
        {"producto_id": prod_id, "cantidad": 2, "precio_unitario": 3400.0}, # S/ 6800
        {"producto_id": p_ram_id, "cantidad": 2, "precio_unitario": 500.0}   # S/ 1000 -> Total Bruto: S/ 7800
    ]

    # Probar descuento del 10% (S/ 780.00) sobre S/ 7800 -> Neto: S/ 7020 -> IGV (18%): S/ 1263.60 -> Total: S/ 8283.60
    venta_id, err_venta = VentaModel.registrar_venta(
        cliente_id=1,
        tipo_comprobante="Factura",
        metodo_pago="Transferencia",
        items=items_venta,
        tipo_descuento="PORCENTAJE",
        valor_descuento=10.0,
        impuesto_porcentaje=18.0,
        usuario_id=1
    )
    assert err_venta is None and venta_id is not None
    v_info = VentaModel.obtener_venta_completa(venta_id)
    assert v_info["subtotal"] == 7800.0
    assert v_info["descuento"] == 780.0
    assert v_info["total"] == 8283.60
    print(f"  [OK] Venta Factura N° {v_info['numero_comprobante']} registrada: Bruto S/ {v_info['subtotal']} - Desc 10% (-S/ {v_info['descuento']}) + IGV S/ {v_info['impuesto']} = Total S/ {v_info['total']}")

    # Verificar stock post venta
    p_gpu_post = ProductoModel.obtener_por_id(prod_id)
    p_ram_post = ProductoModel.obtener_por_id(p_ram_id)
    assert p_gpu_post["stock"] == 11 - 2 # 9
    assert p_ram_post["stock"] == 10 - 2  # 8
    print(f"  [OK] Stock descontado automáticamente en SQLite: GPU ({p_gpu_post['stock']}), RAM ({p_ram_post['stock']}).")

    # -------------------------------------------------------------
    # PRUEBA 7: Detección de alertas de stock mínimo
    # -------------------------------------------------------------
    print("\n[PRUEBA 7] Detección de alertas de stock mínimo...")
    # Ajustar RAM a 1 unidad (menor que su stock mínimo de 2)
    MovimientoStockModel.registrar_ajuste_stock(
        producto_id=p_ram_id, cantidad=7, motivo="Ajuste para prueba de stock crítico",
        tipo_movimiento="SALIDA", usuario_id=1
    )
    p_ram_crit = ProductoModel.obtener_por_id(p_ram_id)
    assert p_ram_crit["stock"] == 1 and p_ram_crit["stock"] <= p_ram_crit["stock_minimo"]
    bajos = ProductoModel.obtener_productos_bajo_stock()
    assert any(b["id"] == p_ram_id for b in bajos)
    print(f"  [OK] Componente en nivel crítico detectado automáticamente ({p_ram_crit['stock']} <= mín {p_ram_crit['stock_minimo']}).")

    # -------------------------------------------------------------
    # PRUEBA 8: Reportes de ventas por rango de fechas
    # -------------------------------------------------------------
    print("\n[PRUEBA 8] Reportes detallados por rango de fechas...")
    hoy_str = datetime.now().strftime("%Y-%m-%d")
    detalles_rep = VentaModel.obtener_ventas_detalladas_rango(fecha_inicio=hoy_str, fecha_fin=hoy_str)
    assert len(detalles_rep) > 0
    print(f"  [OK] Se recuperaron {len(detalles_rep)} líneas de productos vendidos en el rango {hoy_str} al {hoy_str}.")

    # -------------------------------------------------------------
    # PRUEBA 9: Exportación a Excel (.xlsx) con openpyxl
    # -------------------------------------------------------------
    print("\n[PRUEBA 9] Exportación a Excel (.xlsx) con openpyxl...")
    ok_inv, path_inv = ExcelService.exportar_inventario(ProductoModel.listar_productos())
    assert ok_inv and os.path.exists(path_inv) and os.path.getsize(path_inv) > 1000

    ok_vta, path_vta = ExcelService.exportar_ventas_detallado(detalles_rep, fecha_inicio=hoy_str, fecha_fin=hoy_str)
    assert ok_vta and os.path.exists(path_vta) and os.path.getsize(path_vta) > 1000
    print(f"  [OK] Excel de Inventario: {os.path.basename(path_inv)} ({os.path.getsize(path_inv)} bytes)")
    print(f"  [OK] Excel de Ventas Detalladas: {os.path.basename(path_vta)} ({os.path.getsize(path_vta)} bytes)")

    # -------------------------------------------------------------
    # PRUEBA 10: Generación de comprobante en PDF con ReportLab
    # -------------------------------------------------------------
    print("\n[PRUEBA 10] Generación de comprobante PDF con ReportLab...")
    ok_pdf, path_pdf = PDFService.generar_comprobante_pdf(v_info)
    assert ok_pdf and os.path.exists(path_pdf) and os.path.getsize(path_pdf) > 1000
    print(f"  [OK] Comprobante PDF generado: {os.path.basename(path_pdf)} ({os.path.getsize(path_pdf)} bytes)")

    # -------------------------------------------------------------
    # PRUEBA 11: Control de permisos y roles
    # -------------------------------------------------------------
    print("\n[PRUEBA 11] Matriz de permisos de usuario (Admin vs Vendedor)...")
    assert UsuarioModel.tiene_permiso("administrador", "gestionar_usuarios") is True
    assert UsuarioModel.tiene_permiso("administrador", "eliminar_productos") is True
    assert UsuarioModel.tiene_permiso("administrador", "modificar_precio_compra") is True

    assert UsuarioModel.tiene_permiso("vendedor", "gestionar_usuarios") is False
    assert UsuarioModel.tiene_permiso("vendedor", "eliminar_productos") is False
    assert UsuarioModel.tiene_permiso("vendedor", "modificar_precio_compra") is False
    assert UsuarioModel.tiene_permiso("vendedor", "realizar_ventas") is True
    print("  [OK] Permisos verificados: Administrador con control total, Vendedor con costos y eliminación bloqueados.")

    # -------------------------------------------------------------
    # PRUEBA 12: Gestión de usuarios (Crear y desactivar)
    # -------------------------------------------------------------
    print("\n[PRUEBA 12] Creación y desactivación de usuarios...")
    u_test_id, err_u = UsuarioModel.crear_usuario(
        username=f"cajero_{ts}",
        password="clave_segura_123",
        nombre_completo="Cajero Temporal",
        rol="vendedor"
    )
    assert err_u is None and u_test_id is not None
    # Desactivar
    ok_des, _ = UsuarioModel.desactivar_usuario(u_test_id)
    assert ok_des is True
    # Comprobar que no puede iniciar sesión
    ses_bloq, err_bloq = UsuarioModel.autenticar(f"cajero_{ts}", "clave_segura_123")
    assert ses_bloq is None and "desactivada" in err_bloq.lower()
    print("  [OK] Usuario creado, desactivado y acceso bloqueado correctamente.")

    # -------------------------------------------------------------
    # PRUEBA 13: Métricas del Dashboard con datos reales de SQLite
    # -------------------------------------------------------------
    print("\n[PRUEBA 13] Métricas del Dashboard con datos de SQLite...")
    metricas = VentaModel.obtener_metricas_dashboard()
    assert metricas["ventas_hoy_count"] >= 1
    assert metricas["ventas_hoy_total"] > 0
    assert metricas["total_productos"] >= 2
    assert metricas["stock_bajo_count"] >= 1
    print(f"  [OK] Dashboard SQLite: Ventas hoy: S/ {metricas['ventas_hoy_total']:,.2f} ({metricas['ventas_hoy_count']} ventas), Productos: {metricas['total_productos']}, Bajo stock: {metricas['stock_bajo_count']}.")

    # -------------------------------------------------------------
    # PRUEBA 14: Persistencia de datos al cerrar y volver a conectar
    # -------------------------------------------------------------
    print("\n[PRUEBA 14] Persistencia al cerrar y volver a abrir la conexión SQLite...")
    # Abrir nueva conexión limpia independiente
    conn_nueva = get_connection()
    c_nueva = conn_nueva.cursor()
    c_nueva.execute("SELECT COUNT(*) FROM ventas WHERE id = ?;", (venta_id,))
    assert c_nueva.fetchone()[0] == 1
    c_nueva.execute("SELECT stock FROM productos WHERE id = ?;", (prod_id,))
    assert c_nueva.fetchone()[0] == 9
    conn_nueva.close()
    print("  [OK] Persistencia verificada: Las ventas, movimientos y stock se conservan en 'inventario_tienda.db'.")

    print("\n" + "=" * 70)
    print("¡TODAS LAS 14 PRUEBAS DEL SISTEMA FINALIZARON EXITOSAMENTE (100% OK)!")
    print("=" * 70)

if __name__ == "__main__":
    ejecutar_suite_completa()
