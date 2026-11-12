"""
Modelo para la gestión de usuarios, autenticación y control de permisos por rol.
"""
import uuid
from datetime import datetime
from database.db import get_connection
from database.schema import hash_password, verificar_password

class UsuarioModel:
    PERMISOS = {
        "administrador": {
            "gestionar_usuarios": True,
            "gestionar_productos": True,
            "eliminar_productos": True,
            "modificar_precio_compra": True,
            "gestionar_proveedores": True,
            "realizar_ventas": True,
            "gestionar_clientes": True,
            "ver_reportes_financieros": True,
            "ajustar_stock_manual": True
        },
        "vendedor": {
            "gestionar_usuarios": False,
            "gestionar_productos": False,       # Solo consulta de catálogo
            "eliminar_productos": False,
            "modificar_precio_compra": False,   # No ve ni modifica costos de compra
            "gestionar_proveedores": False,
            "realizar_ventas": True,
            "gestionar_clientes": True,
            "ver_reportes_financieros": False,
            "ajustar_stock_manual": False
        }
    }

    @classmethod
    def tiene_permiso(cls, rol: str, accion: str) -> bool:
        """Verifica si el rol especificado tiene autorización para realizar una acción."""
        permisos_rol = cls.PERMISOS.get(rol.lower(), {})
        return permisos_rol.get(accion, False)

    @staticmethod
    def autenticar(username: str, password: str):
        """
        Valida las credenciales de inicio de sesión:
        - Retorna (usuario_dict, None) si es exitoso.
        - Retorna (None, mensaje_error) si falla.
        """
        username = username.strip().lower()
        if not username or not password:
            return None, "Ingrese su nombre de usuario y contraseña."

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, password_hash, salt, nombre_completo, rol, activo, creado_en
            FROM usuarios
            WHERE LOWER(username) = ?;
        """, (username,))
        fila = cursor.fetchone()
        conn.close()

        if not fila:
            return None, "El usuario ingresado no existe en el sistema."

        usuario = dict(fila)

        if usuario["activo"] != 1:
            return None, "Esta cuenta de usuario se encuentra desactivada. Contacte al administrador."

        if not verificar_password(password, usuario["password_hash"], usuario["salt"]):
            return None, "Contraseña incorrecta. Verifique sus credenciales."

        sesion = {
            "id": usuario["id"],
            "username": usuario["username"],
            "nombre_completo": usuario["nombre_completo"],
            "rol": usuario["rol"],
            "creado_en": usuario["creado_en"]
        }
        return sesion, None

    @staticmethod
    def crear_usuario(username: str, password: str, nombre_completo: str, rol: str):
        """Registra un nuevo usuario con contraseña protegida por PBKDF2-HMAC-SHA256."""
        username = username.strip().lower()
        nombre_completo = nombre_completo.strip()
        rol = rol.strip().lower()

        if not username or not nombre_completo:
            return None, "El nombre de usuario y el nombre completo son obligatorios."

        if rol not in ("administrador", "vendedor"):
            return None, "El rol debe ser 'administrador' o 'vendedor'."

        if len(password) < 4:
            return None, "La contraseña debe tener al menos 4 caracteres."

        pwd_hash, salt = hash_password(password)
        fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        u_uuid = str(uuid.uuid4())

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO usuarios (uuid, username, password_hash, salt, nombre_completo, rol, activo, creado_en, fecha_modificacion, sincronizado)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, 0);
            """, (u_uuid, username, pwd_hash, salt, nombre_completo, rol, fecha_creacion, fecha_creacion))
            conn.commit()
            nuevo_id = cursor.lastrowid
            return nuevo_id, None
        except Exception as e:
            return None, f"Error al crear usuario (nombre de usuario ya existe): {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def listar_usuarios(solo_activos: bool = True, busqueda: str = None, rol: str = None, orden_columna: str = "id", orden_dir: str = "ASC"):
        """
        Lista usuarios sin exponer contraseñas ni salts.
        Soporta filtrado por estado (solo activos o todos), búsqueda por texto, rol y ordenamiento.
        """
        conn = get_connection()
        cursor = conn.cursor()

        columnas_permitidas = {
            "id": "id",
            "username": "username",
            "nombre": "nombre_completo",
            "nombre_completo": "nombre_completo",
            "rol": "rol",
            "estado": "activo",
            "activo": "activo",
            "fecha": "creado_en",
            "creado_en": "creado_en"
        }
        col = columnas_permitidas.get(orden_columna.lower(), "id")
        dir_sql = "DESC" if orden_dir.upper() == "DESC" else "ASC"

        condiciones = []
        params = []

        if solo_activos is True or solo_activos == "activos":
            condiciones.append("activo = 1")
        elif solo_activos == "inactivos":
            condiciones.append("activo = 0")
        elif solo_activos is False or solo_activos == "todos":
            pass

        if rol and rol.lower() in ("administrador", "vendedor"):
            condiciones.append("LOWER(rol) = ?")
            params.append(rol.lower())

        if busqueda and busqueda.strip():
            patron = f"%{busqueda.strip().lower()}%"
            condiciones.append("(LOWER(username) LIKE ? OR LOWER(nombre_completo) LIKE ?)")
            params.extend([patron, patron])

        where_clause = (" WHERE " + " AND ".join(condiciones)) if condiciones else ""
        query = f"SELECT id, uuid, username, nombre_completo, rol, activo, creado_en FROM usuarios{where_clause} ORDER BY {col} {dir_sql};"

        cursor.execute(query, params)
        filas = cursor.fetchall()
        conn.close()
        return [dict(f) for f in filas]

    @staticmethod
    def desactivar_usuario(usuario_id: int):
        """Desactiva un usuario (evita desactivar al administrador principal ID 1)."""
        if usuario_id == 1:
            return False, "No se puede desactivar al Administrador Principal del sistema."

        conn = get_connection()
        cursor = conn.cursor()
        try:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE usuarios SET activo = 0, fecha_modificacion = ?, sincronizado = 0 WHERE id = ?;", (ahora, usuario_id))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def reactivar_usuario(usuario_id: int):
        """Reactiva una cuenta de usuario previamente desactivada."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE usuarios SET activo = 1, fecha_modificacion = ?, sincronizado = 0 WHERE id = ?;", (ahora, usuario_id))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def actualizar_usuario(usuario_id: int, nombre_completo: str, rol: str):
        """Actualiza el nombre completo y/o rol del usuario."""
        nombre_completo = nombre_completo.strip()
        rol = rol.strip().lower()

        if not nombre_completo:
            return False, "El nombre completo es obligatorio."
        if rol not in ("administrador", "vendedor"):
            return False, "El rol debe ser 'administrador' o 'vendedor'."
        if usuario_id == 1 and rol != "administrador":
            return False, "El Administrador Principal siempre debe conservar el rol de 'administrador'."

        conn = get_connection()
        cursor = conn.cursor()
        try:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                UPDATE usuarios
                SET nombre_completo = ?, rol = ?, fecha_modificacion = ?, sincronizado = 0
                WHERE id = ?;
            """, (nombre_completo, rol, ahora, usuario_id))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def cambiar_password(usuario_id: int, nuevo_password: str):
        """Actualiza la contraseña generando nuevo salt y hash seguro."""
        if len(nuevo_password) < 4:
            return False, "La contraseña debe tener al menos 4 caracteres."

        pwd_hash, salt = hash_password(nuevo_password)
        conn = get_connection()
        cursor = conn.cursor()
        try:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                UPDATE usuarios
                SET password_hash = ?, salt = ?, fecha_modificacion = ?, sincronizado = 0
                WHERE id = ?;
            """, (pwd_hash, salt, ahora, usuario_id))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def sugerir_username(nombre_completo: str) -> str:
        """
        Genera una sugerencia inteligente y automática de nombre de usuario (login) único
        a partir del nombre de la persona (ej: 'Carlos Mendoza' -> 'cmendoza').
        """
        import re
        import unicodedata

        if not nombre_completo or not nombre_completo.strip():
            return "usuario"

        # Remover tildes y caracteres especiales
        texto = unicodedata.normalize('NFKD', nombre_completo).encode('ASCII', 'ignore').decode('utf-8').lower()
        partes = [re.sub(r'[^a-z0-9]', '', p) for p in texto.split() if p]

        if not partes:
            base = "usuario"
        elif len(partes) == 1:
            base = partes[0]
        else:
            base = f"{partes[0][0]}{partes[1]}"

        base = base[:14]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM usuarios;")
        existentes = {fila["username"].lower() for fila in cursor.fetchall()}
        conn.close()

        candidato = base
        contador = 1
        while candidato in existentes:
            candidato = f"{base}{contador}"
            contador += 1

        return candidato

    @staticmethod
    def generar_password_seguro() -> str:
        """Genera una contraseña temporal segura y fácil de recordar para el nuevo usuario."""
        import random
        palabras = ["Tech", "Venta", "Gamer", "Store", "Speed", "Comp"]
        simbolos = ["!", "@", "#", "$", "*"]
        num = random.randint(100, 999)
        return f"{random.choice(palabras)}{num}{random.choice(simbolos)}"
