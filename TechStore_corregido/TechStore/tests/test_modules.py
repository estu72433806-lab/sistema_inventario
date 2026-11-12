import _path  # noqa: F401  (prepara rutas del proyecto)
"""
Script de pruebas unitarias y de integración para:
1. Productos (crear, consultar, actualizar, desactivar sin borrar historial).
2. Clientes y Proveedores (CRUD y desactivación lógica).
3. Entradas de mercadería vinculadas a proveedores (incremento de stock y registro en Kardex).
4. Ajustes por pérdida o daño (decremento de stock y registro en Kardex).
5. Detección y alerta de stock mínimo.
"""
import sys

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from database.db import get_connection
from database.schema import init_db
from models.producto import ProductoModel
from models.cliente import ClienteModel
from models.proveedor import ProveedorModel
from models.movimiento_stock import MovimientoStockModel

def ejecutar_pruebas_modulos():
    print("=" * 65)
    print("INICIANDO PRUEBAS DE PRODUCTOS, CONTACTOS Y MOVIMIENTOS DE STOCK")
    print("=" * 65)

    init_db()

    import time
    ts = time.time_ns()
    ruc_test = f"20{str(ts)[-9:]}"
    doc_cliente = f"7{str(ts)[-7:]}"
    cod_prod = f"PROD-TEST-{ts}"

    # 1. Pruebas de Proveedores
    print("\n[1] Probando módulo de Proveedores...")
    prov_id, err_p = ProveedorModel.crear_proveedor(
        ruc_dni=ruc_test,
        razon_social="Distribuidora Tech Global S.A.",
        contacto="Ing. Mario Casas",
        telefono="01-9988776",
        email="ventas@techglobal.local",
        direccion="Av. Los Ingenieros 500, Lima"
    )
    assert err_p is None, f"Error al crear proveedor: {err_p}"
    print(f"  [OK] Proveedor registrado con ID: {prov_id}")

    # Consultar
    prov = ProveedorModel.obtener_por_id(prov_id)
    assert prov is not None and prov["ruc_dni"] == ruc_test
    print(f"  [OK] Proveedor consultado: {prov['razon_social']}")

    # Modificar
    ok_upd_prov, err_upd = ProveedorModel.actualizar_proveedor(
        prov_id, ruc_dni=ruc_test, razon_social="Distribuidora Tech Global Modificada S.A.",
        contacto="Ing. Mario Casas", telefono="01-5555555", email="nuevo@techglobal.local", direccion="Nueva Dirección 123"
    )
    assert ok_upd_prov is True, f"Error al actualizar proveedor: {err_upd}"
    print("  [OK] Proveedor modificado exitosamente.")

    # 2. Pruebas de Clientes
    print("\n[2] Probando módulo de Clientes...")
    cli_id, err_c = ClienteModel.crear_cliente(
        tipo_documento="DNI",
        numero_documento=doc_cliente,
        nombre="Lucía Morales Cárdenas",
        telefono="987654321",
        email="lucia.morales@correo.local",
        direccion="Jr. Las Begonias 450, Lince"
    )
    assert err_c is None, f"Error al crear cliente: {err_c}"
    print(f"  [OK] Cliente registrado con ID: {cli_id}")

    cli = ClienteModel.obtener_por_id(cli_id)
    assert cli is not None and cli["nombre"] == "Lucía Morales Cárdenas"
    print(f"  [OK] Cliente consultado: {cli['nombre']} (Doc: {cli['numero_documento']})")

    # Modificar
    ok_upd_cli, _ = ClienteModel.actualizar_cliente(
        cli_id, "DNI", doc_cliente, "Lucía Morales C. Actualizada", "987000111", "lucia@modificado.local", "Nueva Calle 789"
    )
    assert ok_upd_cli is True
    print("  [OK] Cliente modificado exitosamente.")

    # 3. Pruebas de Productos (Registrar, Consultar, Modificar)
    print("\n[3] Probando módulo de Productos...")
    prod_id, err_prod = ProductoModel.crear_producto(
        codigo=cod_prod,
        nombre="Placa Madre MSI MAG B550 TOMAHAWK AM4",
        categoria_id=3,
        marca="MSI",
        precio_compra=520.0,
        precio_venta=680.0,
        stock=5,
        stock_minimo=3,
        descripcion="Chipset AMD B550, DDR4 hasta 4400MHz, Dual M.2 PCIe 4.0",
        proveedor_id=prov_id,
        usuario_id=1
    )
    assert err_prod is None, f"Error al crear producto: {err_prod}"
    print(f"  [OK] Producto registrado con ID {prod_id} y stock inicial de 5 unidades.")

    p_info = ProductoModel.obtener_por_id(prod_id)
    assert p_info is not None and p_info["codigo"] == cod_prod
    assert p_info["stock"] == 5
    print(f"  [OK] Producto consultado: {p_info['nombre']} - Stock: {p_info['stock']}")

    # Modificar producto
    ok_upd_p, _ = ProductoModel.actualizar_producto(
        prod_id, codigo=cod_prod, nombre="Placa Madre MSI MAG B550 TOMAHAWK WIFI AM4",
        categoria_id=3, marca="MSI", precio_compra=530.0, precio_venta=695.0,
        stock=5, stock_minimo=3, descripcion="Versión con WiFi integrada", proveedor_id=prov_id
    )
    assert ok_upd_p is True
    print("  [OK] Producto modificado exitosamente.")

    # 4. Pruebas de Entrada de Mercadería (Indicando Proveedor)
    print("\n[4] Probando Entrada de Mercadería con Proveedor (Incremento de stock)...")
    stock_anterior = p_info["stock"] # 5
    cantidad_ingreso = 10

    mov_entrada_id, err_mov_in = MovimientoStockModel.registrar_entrada_mercaderia(
        producto_id=prod_id,
        cantidad=cantidad_ingreso,
        proveedor_id=prov_id,
        referencia="Factura Compra F001-44321",
        motivo="Recepción de pedido mayorista",
        usuario_id=1
    )
    assert err_mov_in is None, f"Error en entrada de mercadería: {err_mov_in}"

    p_actualizado = ProductoModel.obtener_por_id(prod_id)
    assert p_actualizado["stock"] == stock_anterior + cantidad_ingreso, "El stock no incrementó correctamente!"
    print(f"  [OK] Entrada registrada (ID: {mov_entrada_id}). Stock aumentó de {stock_anterior} a {p_actualizado['stock']}.")

    # 5. Pruebas de Ajuste de Stock por Pérdida o Daño
    print("\n[5] Probando Ajuste de Stock por Daño Físico (Decremento de stock)...")
    stock_antes_ajuste = p_actualizado["stock"] # 15
    cantidad_danio = 2

    mov_ajuste_id, err_mov_aj = MovimientoStockModel.registrar_ajuste_stock(
        producto_id=prod_id,
        cantidad=cantidad_danio,
        motivo="Daño físico en socket durante revisión técnica",
        tipo_movimiento="SALIDA",
        usuario_id=1,
        referencia="Acta de Merma #05"
    )
    assert err_mov_aj is None, f"Error en ajuste: {err_mov_aj}"

    p_despues_ajuste = ProductoModel.obtener_por_id(prod_id)
    assert p_despues_ajuste["stock"] == stock_antes_ajuste - cantidad_danio, "El stock no decrementó correctamente tras el ajuste!"
    print(f"  [OK] Ajuste por daño registrado (ID: {mov_ajuste_id}). Stock ajustado de {stock_antes_ajuste} a {p_despues_ajuste['stock']}.")

    # 6. Verificación de Historial / Kardex del Producto
    print("\n[6] Verificando historial de movimientos del producto...")
    historial = MovimientoStockModel.listar_movimientos(producto_id=prod_id)
    assert len(historial) >= 3 # Apertura + Entrada mercadería + Ajuste daño
    print(f"  [OK] Se recuperaron {len(historial)} movimientos en el historial del producto:")
    for h in historial:
        prov_txt = f"(Proveedor: {h['proveedor_nombre']})" if h['proveedor_nombre'] else ""
        print(f"       -> [{h['fecha']}] {h['tipo_movimiento']} de {h['cantidad']} un. | Motivo: {h['motivo']} {prov_txt}")

    # 7. Detección de Alertas de Stock Mínimo
    print("\n[7] Probando alertas cuando el stock es igual o menor al mínimo...")
    # Provocar stock bajo ajustando la cantidad restante
    stock_actual = p_despues_ajuste["stock"] # 13
    stock_min = p_despues_ajuste["stock_minimo"] # 3
    descuento_para_alerta = stock_actual - 2 # Quedarán 2 unidades (< 3)

    MovimientoStockModel.registrar_ajuste_stock(
        producto_id=prod_id,
        cantidad=descuento_para_alerta,
        motivo="Prueba de umbral de stock bajo",
        tipo_movimiento="SALIDA",
        usuario_id=1
    )

    p_bajo = ProductoModel.obtener_por_id(prod_id)
    assert p_bajo["stock"] == 2 and p_bajo["stock"] <= p_bajo["stock_minimo"]

    lista_bajos = ProductoModel.obtener_productos_bajo_stock()
    ids_bajos = [item["id"] for item in lista_bajos]
    assert prod_id in ids_bajos, "El producto con stock bajo no fue detectado en la alerta!"
    print(f"  [OK] Alerta activada con éxito: Producto con stock {p_bajo['stock']} <= stock mínimo {p_bajo['stock_minimo']}.")

    # 8. Desactivación de Producto (Sin borrar historial)
    print("\n[8] Probando desactivación de producto (Borrado lógico)...")
    ok_desact, _ = ProductoModel.eliminar_producto(prod_id)
    assert ok_desact is True

    # El producto no debe aparecer en listar_productos activos
    prods_activos = ProductoModel.listar_productos()
    assert prod_id not in [p["id"] for p in prods_activos]

    # Pero el historial de movimientos sigue existiendo intacto en SQLite
    historial_post_baja = MovimientoStockModel.listar_movimientos(producto_id=prod_id)
    assert len(historial_post_baja) == len(historial) + 1
    print("  [OK] Producto desactivado del catálogo activo. Todo su historial en movimientos_stock se conserva intacto.")

    # 9. Desactivar Proveedor y Cliente
    print("\n[9] Probando desactivación de Cliente y Proveedor...")
    ok_dcli, _ = ClienteModel.desactivar_cliente(cli_id)
    assert ok_dcli is True
    print("  [OK] Cliente desactivado correctamente (historial conservado).")

    ok_dprov, _ = ProveedorModel.desactivar_proveedor(prov_id)
    assert ok_dprov is True
    print("  [OK] Proveedor desactivado correctamente (historial conservado).")

    print("\n" + "=" * 65)
    print("¡TODAS LAS PRUEBAS DE PRODUCTOS, CONTACTOS Y STOCK PASARON EXITOSAMENTE!")
    print("=" * 65)

if __name__ == "__main__":
    ejecutar_pruebas_modulos()
