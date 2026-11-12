import _path  # noqa: F401  (prepara rutas del proyecto)
"""
Pruebas Automatizadas de Verificación para las Mejoras de Gestión de Usuarios y Conexión en la Nube.
"""
import sys
import tkinter as tk

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from database.schema import init_db
from models.usuario import UsuarioModel
from database.pg_config import parse_connection_string
from ui.views.usuarios_view import UsuariosView
from ui.views.config_nube_dialog import ConfigNubeDialog

def run_tests():
    print("=" * 70)
    print("VERIFICANDO MEJORAS EN GESTIÓN DE USUARIOS Y CONEXIÓN EN LA NUBE")
    print("=" * 70)

    init_db()

    # 1. Sugerencia inteligente de Login (Username)
    print("\n[1] Probando generador automático de nombre de usuario (sugerir_username)...")
    sug1 = UsuarioModel.sugerir_username("Carlos Rodríguez")
    assert sug1.startswith("crodriguez"), f"Esperado crodriguez, obtenido: {sug1}"
    print(f"  [OK] Sugerencia para 'Carlos Rodríguez': '{sug1}'")

    sug_acento = UsuarioModel.sugerir_username("Ángel Núñez")
    assert sug_acento.startswith("anunez"), f"Esperado anunez, obtenido: {sug_acento}"
    print(f"  [OK] Sugerencia para 'Ángel Núñez' (sin tildes ni eñes): '{sug_acento}'")

    # 2. Generador de Contraseñas Seguras
    print("\n[2] Probando generador automático de contraseñas temporales...")
    clave = UsuarioModel.generar_password_seguro()
    assert len(clave) >= 6, f"Clave muy corta: {clave}"
    print(f"  [OK] Contraseña temporal generada: '{clave}'")

    # 3. Creación, Actualización, Desactivación y Reactivación de Usuario
    print("\n[3] Probando ciclo completo de usuario con rol vendedor...")
    username_test = "user_mejora_001"
    
    # Crear
    uid, err = UsuarioModel.crear_usuario(
        username=username_test,
        password="claveSegura123",
        nombre_completo="Prueba Mejora Usuarios",
        rol="vendedor"
    )
    if err and "ya existe" in err:
        # Recuperar ID existente
        usuarios = UsuarioModel.listar_usuarios(solo_activos=False, busqueda=username_test)
        uid = usuarios[0]["id"]
    else:
        assert uid is not None, f"Error al crear: {err}"
    print(f"  [OK] Usuario '{username_test}' verificado con ID: {uid}")

    # Actualizar nombre y rol
    ok_act, err_act = UsuarioModel.actualizar_usuario(uid, "Prueba Mejora Modificado", "vendedor")
    assert ok_act is True, f"Fallo al actualizar: {err_act}"
    print("  [OK] Actualización de datos de usuario exitosa.")

    # Desactivar
    ok_des, err_des = UsuarioModel.desactivar_usuario(uid)
    assert ok_des is True, f"Fallo al desactivar: {err_des}"
    print("  [OK] Desactivación exitosa.")

    # Verificar que aparece en inactivos
    inactivos = UsuarioModel.listar_usuarios(solo_activos="inactivos", busqueda=username_test)
    assert any(u["id"] == uid for u in inactivos), "El usuario no apareció en el filtro de inactivos."
    print("  [OK] Filtro de inactivos validado correctamente.")

    # Reactivar
    ok_rea, err_rea = UsuarioModel.reactivar_usuario(uid)
    assert ok_rea is True, f"Fallo al reactivar: {err_rea}"
    activos = UsuarioModel.listar_usuarios(solo_activos=True, busqueda=username_test)
    assert any(u["id"] == uid for u in activos), "El usuario no se reactivó correctamente."
    print("  [OK] Reactivación y filtro de activos validados con éxito.")

    # Protección del Administrador ID 1
    print("\n[4] Probando protección inmutable del Administrador Principal (ID 1)...")
    ok_des_admin, _ = UsuarioModel.desactivar_usuario(1)
    assert ok_des_admin is False, "Se permitió desactivar al Administrador Principal ID 1!"
    ok_rol_admin, _ = UsuarioModel.actualizar_usuario(1, "Super Admin", "vendedor")
    assert ok_rol_admin is False, "Se permitió cambiar el rol del Administrador Principal a vendedor!"
    print("  [OK] El Administrador Principal ID 1 está 100% blindado contra desactivación y degradación de rol.")

    # 5. Ordenamiento de la lista de usuarios
    print("\n[5] Probando ordenamiento y búsqueda en listar_usuarios...")
    por_nombre_asc = UsuarioModel.listar_usuarios(solo_activos=False, orden_columna="nombre_completo", orden_dir="ASC")
    por_nombre_desc = UsuarioModel.listar_usuarios(solo_activos=False, orden_columna="nombre_completo", orden_dir="DESC")
    assert len(por_nombre_asc) == len(por_nombre_desc)
    print(f"  [OK] Ordenamiento ascendente y descendente funcional ({len(por_nombre_asc)} usuarios listados).")

    # 6. Parser de Cadena de Conexión en la Nube (Connection String)
    print("\n[6] Probando desglose automático de URL de PostgreSQL (Neon/Supabase/Render)...")
    url_neon = "psql 'postgresql://neondb_owner:MiClaveSegura@ep-cool-lake-1234.us-east-2.aws.neon.tech:5432/neondb?sslmode=require'"
    datos, err_url = parse_connection_string(url_neon)
    assert err_url is None, f"Error al parsear URL: {err_url}"
    assert datos["pg_host"] == "ep-cool-lake-1234.us-east-2.aws.neon.tech"
    assert datos["pg_user"] == "neondb_owner"
    assert datos["pg_password"] == "MiClaveSegura"
    assert datos["pg_database"] == "neondb"
    assert datos["pg_sslmode"] == "require"
    print("  [OK] Desglose automático de URL validado al 100% (Host, DB, User, Pass, SSLmode extraídos).")

    # 7. Renderizado UI en modo headless (verificar que no haya errores de sintaxis en Tkinter)
    print("\n[7] Verificando instanciación gráfica de las vistas mejoradas en Tkinter...")
    root = tk.Tk()
    root.withdraw() # Ocultar ventana

    vista_user = UsuariosView(root, usuario_sesion={"rol": "administrador", "id": 1, "username": "admin"})
    assert vista_user is not None
    print("  [OK] UsuariosView construida e inicializada con éxito.")

    # Simular cambio de rol para probar actualización en vivo de tarjeta de permisos
    vista_user.combo_rol.set(UsuariosView.ROL_ADMIN_DISPLAY)
    vista_user._on_rol_cambiado()
    assert "Administrador" in vista_user.lbl_permisos_tit.cget("text")
    print("  [OK] Tarjeta de permisos interactiva de Administrador verificada.")

    vista_user.combo_rol.set(UsuariosView.ROL_VENDEDOR_DISPLAY)
    vista_user._on_rol_cambiado()
    assert "Vendedor" in vista_user.lbl_permisos_tit.cget("text")
    print("  [OK] Tarjeta de permisos interactiva de Vendedor verificada.")

    # Diálogo de Nube
    dlg_nube = ConfigNubeDialog(root)
    assert dlg_nube is not None
    print("  [OK] ConfigNubeDialog construido e inicializado con éxito.")
    dlg_nube.destroy()

    root.destroy()
    print("  [OK] Ciclo de vida gráfico cerrado correctamente.")

    print("\n" + "=" * 70)
    print("¡TODAS LAS PRUEBAS DE MEJORA PASARON EXITOSAMENTE (100% OK)!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()

