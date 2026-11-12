import _path  # noqa: F401  (prepara rutas del proyecto)
"""
Script de verificación y pruebas automatizadas:
- Creación de las 8 tablas en SQLite.
- Verificación del hash seguro (PBKDF2-HMAC-SHA256) sin contraseñas en texto plano.
- Creación automática del primer administrador sin duplicados al reiniciar.
- Validación de inicio de sesión (credenciales correctas e incorrectas).
- Comprobación de roles y permisos básicos (administrador vs vendedor).
- Registro de movimientos de stock en SQLite.
"""
import sys

# Configurar salida segura para consolas Windows estándar
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from database.db import get_connection
from database.schema import init_db
from models.usuario import UsuarioModel
from models.movimiento_stock import MovimientoStockModel
from models.producto import ProductoModel

def ejecutar_pruebas():
    print("=" * 60)
    print("INICIANDO PRUEBAS DE BASE DE DATOS Y AUTENTICACION SQLITE")
    print("=" * 60)

    # 1. Inicializar base de datos
    print("\n[1] Inicializando base de datos SQLite...")
    init_db()
    print("  [OK] Base de datos inicializada correctamente.")

    # 2. Verificar existencia de las 8 tablas requeridas
    print("\n[2] Verificando existencia de las 8 tablas en SQLite...")
    tablas_esperadas = [
        "usuarios", "categorias", "proveedores", "productos",
        "clientes", "movimientos_stock", "ventas", "detalle_ventas"
    ]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas_existentes = [fila["name"] for fila in cursor.fetchall()]
    conn.close()

    for tabla in tablas_esperadas:
        assert tabla in tablas_existentes, f"Falta la tabla obligatoria '{tabla}'"
        print(f"  [OK] Tabla '{tabla}' encontrada.")

    # 3. Verificar el usuario administrador y seguridad de contraseña
    print("\n[3] Verificando creacion del administrador y proteccion de contrasena...")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, salt, rol, nombre_completo FROM usuarios WHERE username = 'admin';")
    admin = cursor.fetchone()
    conn.close()

    assert admin is not None, "El usuario 'admin' no fue creado automaticamente."
    assert admin["rol"] == "administrador", f"Rol incorrecto: {admin['rol']}"
    assert admin["password_hash"] != "admin123", "ERROR CRITICO: La contrasena esta en texto plano!"
    assert len(admin["password_hash"]) == 64, "El hash SHA256 debe tener 64 caracteres hexadecimales."
    assert len(admin["salt"]) == 32, "El salt debe tener 32 caracteres hexadecimales."

    print(f"  [OK] Administrador creado: {admin['nombre_completo']} (ID: {admin['id']})")
    print(f"  [OK] Hash seguro verificado: {admin['password_hash'][:16]}... (Salt: {admin['salt'][:8]}...)")
    print("  [OK] Contrasena NO guardada en texto plano.")

    # 4. Probar mecanismo anti-duplicacion al reiniciar
    print("\n[4] Probando mecanismo de no duplicacion al reiniciar init_db()...")
    init_db() # Segunda llamada simulando reinicio del programa
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin';")
    count_admin = cursor.fetchone()[0]
    conn.close()
    assert count_admin == 1, f"Se duplico el usuario admin! Count = {count_admin}"
    print("  [OK] Se confirmo que no se duplica el administrador al reiniciar la aplicacion.")

    # 5. Probar autenticacion con credenciales correctas
    print("\n[5] Probando inicio de sesion con credenciales validas (admin / admin123)...")
    sesion, err = UsuarioModel.autenticar("admin", "admin123")
    assert err is None, f"Error inesperado en login: {err}"
    assert sesion is not None and sesion["username"] == "admin"
    print(f"  [OK] Inicio de sesion exitoso para: {sesion['nombre_completo']} con rol [{sesion['rol']}].")

    # 6. Probar rechazo con contrasena incorrecta
    print("\n[6] Probando inicio de sesion con contrasena incorrecta (admin / clave_errada)...")
    sesion_fail, err_fail = UsuarioModel.autenticar("admin", "clave_errada")
    assert sesion_fail is None, "El sistema permitio acceso con contrasena erronea!"
    print(f"  [OK] Acceso rechazado correctamente: '{err_fail}'")

    # 7. Probar rechazo con usuario inexistente
    print("\n[7] Probando inicio de sesion con usuario inexistente...")
    sesion_no_user, err_no_user = UsuarioModel.autenticar("usuario_fantasma", "123456")
    assert sesion_no_user is None
    print(f"  [OK] Acceso rechazado correctamente: '{err_no_user}'")

    # 8. Crear y probar usuario con rol vendedor
    print("\n[8] Creando usuario con rol 'vendedor'...")
    nuevo_vendedor_id, err_crear = UsuarioModel.crear_usuario(
        username="vendedor_test",
        password="ven_secret_123",
        nombre_completo="Vendedor de Pruebas",
        rol="vendedor"
    )
    if not err_crear:
        print(f"  [OK] Vendedor creado con ID {nuevo_vendedor_id}.")
    else:
        print("  [INFO] El vendedor ya existia de pruebas previas.")

    sesion_ven, err_ven = UsuarioModel.autenticar("vendedor_test", "ven_secret_123")
    assert err_ven is None
    assert sesion_ven["rol"] == "vendedor"
    print(f"  [OK] Inicio de sesion de vendedor exitoso: {sesion_ven['nombre_completo']} [{sesion_ven['rol']}].")

    # 9. Probar control de permisos segun el rol
    print("\n[9] Comprobando matriz de permisos por rol...")
    # Admin
    assert UsuarioModel.tiene_permiso("administrador", "eliminar_productos") is True
    assert UsuarioModel.tiene_permiso("administrador", "modificar_precio_compra") is True
    assert UsuarioModel.tiene_permiso("administrador", "realizar_ventas") is True
    # Vendedor
    assert UsuarioModel.tiene_permiso("vendedor", "eliminar_productos") is False
    assert UsuarioModel.tiene_permiso("vendedor", "modificar_precio_compra") is False
    assert UsuarioModel.tiene_permiso("vendedor", "realizar_ventas") is True
    print("  [OK] Permisos del Administrador validados (Control total).")
    print("  [OK] Permisos del Vendedor validados (Ventas permitidas, eliminacion y costo de compra restringidos).")

    # 10. Probar insercion en movimientos_stock
    print("\n[10] Probando registro en movimientos_stock...")
    prod_id, _ = ProductoModel.crear_producto(
        codigo="TEST-RAM-001",
        nombre="Memoria RAM Test 8GB",
        categoria_id=4,
        marca="TestBrand",
        precio_compra=80.0,
        precio_venta=110.0,
        stock=10,
        stock_minimo=2,
        descripcion="Producto de prueba",
        usuario_id=admin["id"]
    )
    
    mov_id, err_mov = MovimientoStockModel.registrar_movimiento(
        producto_id=prod_id or 1,
        tipo_movimiento="ENTRADA",
        cantidad=5,
        motivo="Ingreso por compra a proveedor",
        usuario_id=admin["id"],
        referencia="Factura F001-987"
    )
    assert err_mov is None, f"Error al registrar movimiento: {err_mov}"
    print(f"  [OK] Movimiento de stock registrado con exito (ID: {mov_id}).")

    print("\n" + "=" * 60)
    print("TODAS LAS PRUEBAS FINALIZARON EXITOSAMENTE EN SQLITE!")
    print("=" * 60)

if __name__ == "__main__":
    ejecutar_pruebas()
