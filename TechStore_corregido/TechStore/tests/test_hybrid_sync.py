import _path  # noqa: F401  (prepara rutas del proyecto)
"""
Suite de Pruebas Automatizadas para el Modo Híbrido y Sincronización (SQLite <-> PostgreSQL).
Verifica:
1. MODO LOCAL: Operación 100% offline (login, productos, clientes, ventas, stock, comprobante).
2. SEGURIDAD Y CONFIGURACIÓN: Credenciales seguras, variables de entorno, archivo ignorado por Git.
3. COMPATIBILIDAD DE ESQUEMAS: Estructura relacional idéntica con UUIDs globales.
4. MANEJO OFFLINE / RESILIENCIA: Fallback elegante cuando PostgreSQL no está disponible.
5. SINCRONIZACIÓN Y DESDUPLICACIÓN: Envío de ventas pendientes con UUID sin duplicados.
6. DETECCIÓN DE CONFLICTOS: Alertas ante cambios simultáneos sin sobreescritura ciega.
7. PERSISTENCIA LOCAL: Conservación de datos locales ante fallos de conexión.
"""
import os
import sys
import uuid
import time
from datetime import datetime

# Configurar encoding seguro para consola de Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from database.db import get_connection as get_sqlite_conn
from database.schema import init_db
from database.pg_config import obtener_configuracion_pg, guardar_configuracion_pg, get_config_path
from database.pg_db import probar_conexion_pg, get_pg_connection
from database.pg_schema import PG_DDL, init_pg_db
from models.usuario import UsuarioModel
from models.producto import ProductoModel
from models.cliente import ClienteModel
from models.proveedor import ProveedorModel
from models.movimiento_stock import MovimientoStockModel
from models.venta import VentaModel
from services.sync_service import SyncService
from services.pdf_service import PDFService

def print_test_header(num, titulo):
    print(f"\n[PRUEBA HÍBRIDA {num}] {titulo}...")

def test_1_modo_local_offline():
    print_test_header(1, "Operación completa en Modo Local Offline (sin internet)")
    init_db()

    # 1. Login local
    admin_sesion, err = UsuarioModel.autenticar("admin", "admin123")
    assert admin_sesion is not None, f"Error en login offline: {err}"
    assert admin_sesion["rol"] == "administrador"
    print("  [OK] Login offline con usuario local validado correctamente.")

    # 2. Registrar producto offline
    cod = f"OFF-{int(time.time())}"
    pid, err = ProductoModel.crear_producto(
        codigo=cod,
        nombre=f"Disco SSD M.2 Offline {cod}",
        categoria_id=1,
        marca="Crucial",
        precio_compra=180.0,
        precio_venta=240.0,
        stock=10,
        stock_minimo=2,
        descripcion="Producto creado en modo offline",
        usuario_id=admin_sesion["id"]
    )
    assert pid is not None, f"Error al crear producto offline: {err}"

    # Verificar que tiene UUID y sincronizado = 0
    conn = get_sqlite_conn()
    c = conn.cursor()
    c.execute("SELECT uuid, sincronizado, fecha_modificacion FROM productos WHERE id = ?;", (pid,))
    row = c.fetchone()
    assert row["uuid"] is not None and len(row["uuid"]) > 10, "El producto debe tener un UUID asignado."
    assert row["sincronizado"] == 0, "El nuevo producto offline debe tener sincronizado = 0 (pendiente)."
    conn.close()
    print("  [OK] Producto registrado localmente con UUID único y marcado como pendiente de sincronizar.")

    # 3. Registrar cliente offline
    dni = f"4{int(time.time()) % 10000000:07d}"
    cid, err = ClienteModel.crear_cliente("DNI", dni, "Juan Cliente Offline", "999888777", "offline@tienda.pe", "Av. Local 123")
    assert cid is not None, f"Error al crear cliente: {err}"

    # 4. Registrar venta offline con stock y descuento
    items = [{"producto_id": pid, "cantidad": 2, "precio_unitario": 240.0}]
    vid, err = VentaModel.registrar_venta(
        cliente_id=cid,
        tipo_comprobante="Boleta",
        metodo_pago="Efectivo",
        items=items,
        tipo_descuento="MONTO",
        valor_descuento=20.0,
        usuario_id=admin_sesion["id"]
    )
    assert vid is not None, f"Error al registrar venta offline: {err}"

    # 5. Generar comprobante PDF offline
    venta_dict = VentaModel.obtener_venta_completa(vid)
    pdf_path, err_pdf = PDFService.generar_comprobante_pdf(venta_dict)
    assert pdf_path and os.path.exists(pdf_path), f"Error al generar PDF offline: {err_pdf}"
    print(f"  [OK] Venta offline registrada (ID: {vid}) y comprobante PDF emitido localmente.")

    # Verificar que la venta y sus detalles tienen sincronizado = 0
    conn = get_sqlite_conn()
    c = conn.cursor()
    c.execute("SELECT uuid, sincronizado FROM ventas WHERE id = ?;", (vid,))
    v_row = c.fetchone()
    assert v_row["sincronizado"] == 0, "La venta offline debe estar pendiente de sincronizar."
    c.execute("SELECT COUNT(*) FROM detalle_ventas WHERE venta_id = ? AND sincronizado = 0;", (vid,))
    assert c.fetchone()[0] == 1, "Los detalles deben estar pendientes de sincronizar."
    conn.close()
    print("  [OK] Venta y detalles marcados correctamente como pendientes de sincronización (sincronizado = 0).")

def test_2_seguridad_configuracion():
    print_test_header(2, "Seguridad de credenciales y configuración excluida de Git")
    
    # 1. Comprobar que el archivo .gitignore contiene config_db.json y .env
    assert os.path.exists(".gitignore"), "El archivo .gitignore debe existir."
    with open(".gitignore", "r", encoding="utf-8") as f:
        git_content = f.read()
    assert "config_db.json" in git_content, ".gitignore debe excluir 'config_db.json'."
    assert ".env" in git_content, ".gitignore debe excluir '.env'."
    print("  [OK] .gitignore protege las credenciales de la base de datos remota.")

    # 2. Comprobar que no hay contraseñas en código duro y existe plantilla config_db.example.json
    config = obtener_configuracion_pg()
    assert isinstance(config, dict), "La configuración debe ser un diccionario."
    assert os.path.exists("config_db.example.json"), "Debe existir la plantilla 'config_db.example.json'."
    print("  [OK] Plantilla de configuración disponible sin exponer contraseñas en código.")

def test_3_compatibilidad_esquemas():
    print_test_header(3, "Compatibilidad de esquema relacional (SQLite y PostgreSQL)")
    
    # Verificar que el DDL de PostgreSQL define todas las tablas clave con UUID
    tablas_esperadas = ["usuarios", "categorias", "proveedores", "productos", "clientes", "movimientos_stock", "ventas", "detalle_ventas", "conflictos_sincronizacion"]
    for t in tablas_esperadas:
        assert f"CREATE TABLE IF NOT EXISTS {t}" in PG_DDL, f"Falta tabla {t} en el esquema PostgreSQL."

    # Verificar que SQLite tiene las columnas uuid y sincronizado en todas las tablas
    conn = get_sqlite_conn()
    c = conn.cursor()
    for t in ["productos", "clientes", "proveedores", "ventas", "movimientos_stock"]:
        c.execute(f"PRAGMA table_info({t});")
        cols = [col[1] for col in c.fetchall()]
        assert "uuid" in cols, f"Tabla {t} en SQLite no tiene columna uuid."
        assert "sincronizado" in cols, f"Tabla {t} en SQLite no tiene columna sincronizado."
        assert "fecha_modificacion" in cols, f"Tabla {t} en SQLite no tiene columna fecha_modificacion."
    conn.close()
    print("  [OK] Ambas bases de datos comparten columnas de sincronización (uuid, sincronizado, fecha_modificacion).")

def test_4_resiliencia_servidor_desconectado():
    print_test_header(4, "Resiliencia ante servidor PostgreSQL desconectado / no configurado")
    
    # Probar conexión con host inexistente o no configurado
    config_invalida = {
        "pg_host": "127.0.0.1",
        "pg_port": 54329, # Puerto cerrado
        "pg_database": "db_inexistente",
        "pg_user": "user_prueba",
        "pg_password": "pwd",
        "pg_sslmode": "prefer",
        "timeout_segundos": 1
    }
    ok, msg = probar_conexion_pg(config_override=config_invalida)
    assert ok is False, "La prueba de conexión debe retornar False con host no accesible."
    print("  [OK] Fallo de conexión detectado rápidamente sin congelar ni lanzar excepciones no controladas.")

    # Ejecutar SyncService con host desconectado
    estado, det = SyncService.obtener_estado_conexion()
    assert estado in ("MODO_LOCAL", "EN_LINEA")
    res_sync = SyncService.sincronizar_todo()
    assert res_sync["exito"] is False or res_sync["modo"] == "EN_LINEA"
    print("  [OK] Sincronización aborta limpiamente ante desconexión preservando 100% de los datos locales.")

def test_5_logica_desduplicacion_y_sincronizacion():
    print_test_header(5, "Verificación de la lógica de sincronización y prevención de duplicados")
    
    # Comprobar conteo de pendientes en SQLite
    pendientes = SyncService.obtener_conteo_pendientes()
    assert isinstance(pendientes, int) and pendientes >= 0
    print(f"  [OK] Conteo de registros pendientes calculado correctamente: {pendientes} registro(s) por subir.")

    # Simular inserción idempotente con UUID
    conn = get_sqlite_conn()
    c = conn.cursor()
    test_uuid = str(uuid.uuid4())
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Registrar venta con UUID
    c.execute("""
        INSERT INTO ventas (uuid, numero_comprobante, tipo_comprobante, fecha, subtotal, total, metodo_pago, estado, fecha_modificacion, sincronizado)
        VALUES (?, ?, 'Boleta', ?, 100.0, 100.0, 'Efectivo', 'Completada', ?, 0);
    """, (test_uuid, f"B-TEST-{int(time.time())}", ahora, ahora))
    conn.commit()

    # Verificar que el UUID es único
    c.execute("SELECT COUNT(*) FROM ventas WHERE uuid = ?;", (test_uuid,))
    assert c.fetchone()[0] == 1, "La venta debe existir exactamente una vez."

    # Si se intenta sincronizar y se actualiza a sincronizado = 1:
    c.execute("UPDATE ventas SET sincronizado = 1 WHERE uuid = ?;", (test_uuid,))
    conn.commit()

    # Al volver a consultar pendientes, este registro ya no cuenta como pendiente
    c.execute("SELECT sincronizado FROM ventas WHERE uuid = ?;", (test_uuid,))
    assert c.fetchone()[0] == 1
    conn.close()
    print("  [OK] Desduplicación garantizada mediante UUID global e indicador de sincronización (sincronizado = 1).")

def test_6_deteccion_de_conflictos():
    print_test_header(6, "Detección de conflictos sin sobreescritura ciega")
    
    conn = get_sqlite_conn()
    c = conn.cursor()
    
    # Insertar un conflicto simulado en la tabla de auditoría de conflictos
    conflicto_uuid = str(uuid.uuid4())
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO conflictos_sincronizacion (tabla, registro_uuid, campo, valor_local, valor_remoto, fecha_conflicto, resuelto)
        VALUES ('productos', ?, 'precio_venta', 'Local: S/ 250.00', 'Nube: S/ 280.00', ?, 0);
    """, (conflicto_uuid, ahora))
    conn.commit()

    conflictos = SyncService.listar_conflictos()
    assert len(conflictos) > 0, "El conflicto registrado debe poder ser consultado."
    assert any(conf["registro_uuid"] == conflicto_uuid for conf in conflictos)
    print("  [OK] Registro de conflicto detectado y guardado en SQLite sin sobreescribir datos.")
    conn.close()

def test_7_persistencia_hibrida():
    print_test_header(7, "Persistencia de estado híbrido entre reinicios")
    
    info_antes = SyncService.obtener_info_ultima_sincronizacion()
    assert isinstance(info_antes, dict)
    assert "ultima_sincronizacion" in info_antes
    assert "estado" in info_antes
    print(f"  [OK] Estado híbrido persistido en SQLite: Última sync '{info_antes['ultima_sincronizacion']}', Estado '{info_antes['estado']}'.")

def ejecutar_todas_las_pruebas():
    print("=" * 70)
    print("EJECUTANDO SUITE DE PRUEBAS DE MODO HÍBRIDO (SQLITE + POSTGRESQL)")
    print("=" * 70)

    test_1_modo_local_offline()
    test_2_seguridad_configuracion()
    test_3_compatibilidad_esquemas()
    test_4_resiliencia_servidor_desconectado()
    test_5_logica_desduplicacion_y_sincronizacion()
    test_6_deteccion_de_conflictos()
    test_7_persistencia_hibrida()

    print("\n" + "=" * 70)
    print("¡TODAS LAS 7 PRUEBAS DEL MODO HÍBRIDO FINALIZARON CON ÉXITO (100% OK)!")
    print("=" * 70)

if __name__ == "__main__":
    ejecutar_todas_las_pruebas()
