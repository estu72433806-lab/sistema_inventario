"""
Modelo para la gestión de productos, categorías y proveedores.
"""
from database.db import get_connection
import uuid
from datetime import datetime

class ProductoModel:
    @staticmethod
    def listar_categorias():
        """Retorna todas las categorías disponibles."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, descripcion FROM categorias ORDER BY nombre ASC;")
        categorias = cursor.fetchall()
        conn.close()
        return [dict(cat) for cat in categorias]

    @staticmethod
    def listar_productos(busqueda=""):
        """Retorna lista de productos activos filtrados por texto (código, nombre o marca)."""
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT p.id, p.codigo, p.nombre, p.categoria_id, c.nombre as categoria_nombre,
                   p.proveedor_id, prov.razon_social as proveedor_nombre,
                   p.marca, p.precio_compra, p.precio_venta, p.stock, p.stock_minimo, p.descripcion
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            LEFT JOIN proveedores prov ON p.proveedor_id = prov.id
            WHERE p.activo = 1
        """
        params = []
        if busqueda:
            query += " AND (p.codigo LIKE ? OR p.nombre LIKE ? OR p.marca LIKE ?)"
            patron = f"%{busqueda.strip()}%"
            params.extend([patron, patron, patron])
        
        query += " ORDER BY p.nombre ASC;"
        cursor.execute(query, params)
        filas = cursor.fetchall()
        conn.close()
        return [dict(f) for f in filas]

    @staticmethod
    def obtener_por_id(producto_id):
        """Retorna un producto por su ID."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos WHERE id = ? AND activo = 1;", (producto_id,))
        fila = cursor.fetchone()
        conn.close()
        return dict(fila) if fila else None

    @staticmethod
    def obtener_por_codigo(codigo):
        """Retorna un producto por su código único."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos WHERE codigo = ? AND activo = 1;", (codigo.strip(),))
        fila = cursor.fetchone()
        conn.close()
        return dict(fila) if fila else None

    @staticmethod
    def crear_producto(codigo, nombre, categoria_id, marca, precio_compra, precio_venta, stock, stock_minimo, descripcion="", proveedor_id=None, usuario_id=None, prod_uuid=None):
        """Inserta un nuevo producto y registra el movimiento inicial de inventario."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            p_uuid = prod_uuid if prod_uuid else str(uuid.uuid4())
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO productos (uuid, codigo, nombre, categoria_id, proveedor_id, marca, precio_compra, precio_venta, stock, stock_minimo, descripcion, activo, fecha_modificacion, sincronizado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, 0);
            """, (p_uuid, codigo.strip(), nombre.strip(), categoria_id, proveedor_id, marca.strip(), float(precio_compra), float(precio_venta), int(stock), int(stock_minimo), descripcion.strip(), ahora))
            
            nuevo_id = cursor.lastrowid

            # Si se inicia con stock > 0, registrar movimiento de entrada inicial
            if int(stock) > 0:
                mov_uuid = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO movimientos_stock (uuid, producto_id, tipo_movimiento, cantidad, motivo, referencia, fecha, usuario_id, fecha_modificacion, sincronizado)
                    VALUES (?, ?, 'ENTRADA', ?, 'Stock inicial de apertura', 'Registro Inicial', datetime('now', 'localtime'), ?, ?, 0);
                """, (mov_uuid, nuevo_id, int(stock), usuario_id, ahora))

            conn.commit()
            return nuevo_id, None
        except Exception as e:
            conn.rollback()
            return None, str(e)
        finally:
            conn.close()

    @staticmethod
    def actualizar_producto(producto_id, codigo, nombre, categoria_id, marca, precio_compra, precio_venta, stock, stock_minimo, descripcion="", proveedor_id=None):
        """Actualiza un producto existente."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                UPDATE productos
                SET codigo = ?, nombre = ?, categoria_id = ?, proveedor_id = ?, marca = ?, precio_compra = ?,
                    precio_venta = ?, stock = ?, stock_minimo = ?, descripcion = ?,
                    fecha_modificacion = ?, sincronizado = 0
                WHERE id = ?;
            """, (codigo.strip(), nombre.strip(), categoria_id, proveedor_id, marca.strip(), float(precio_compra), float(precio_venta), int(stock), int(stock_minimo), descripcion.strip(), ahora, producto_id))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def eliminar_producto(producto_id):
        """Desactiva un producto (borrado lógico para preservar integridad histórica)."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE productos SET activo = 0, fecha_modificacion = ?, sincronizado = 0 WHERE id = ?;", (ahora, producto_id))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def obtener_productos_bajo_stock():
        """Retorna productos cuyo stock actual sea menor o igual al stock mínimo."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.codigo, p.nombre, c.nombre as categoria_nombre, p.stock, p.stock_minimo, p.precio_venta
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.activo = 1 AND p.stock <= p.stock_minimo
            ORDER BY p.stock ASC;
        """)
        filas = cursor.fetchall()
        conn.close()
        return [dict(f) for f in filas]

    @classmethod
    def normalizar_codigo_categoria(cls, categoria_val):
        """
        Retorna un código nemotécnico de 3 letras en mayúsculas representativo de la categoría.
        Ejemplos:
        - 'Laptops y Equipos' -> 'LAP'
        - 'Procesadores (CPU)' -> 'CPU'
        - 'Tarjetas Gráficas (GPU)' -> 'GPU'
        - 'Placas Madre (Motherboard)' -> 'MBD'
        - 'Memorias RAM' -> 'RAM'
        - 'Almacenamiento (SSD/HDD)' -> 'ALM'
        - 'Fuentes de Poder (PSU)' -> 'PSU'
        - 'Gabinetes / Cases' -> 'CAS'
        - 'Monitores' -> 'MON'
        - 'Periféricos' -> 'PER'
        """
        if not categoria_val:
            return "PRO"

        texto = str(categoria_val).strip()
        if texto.isdigit():
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT nombre FROM categorias WHERE id = ?;", (int(texto),))
            row = cur.fetchone()
            conn.close()
            if row and row[0]:
                texto = row[0]
            else:
                return "PRO"

        import unicodedata
        t_clean = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').lower()

        if "laptop" in t_clean or "notebook" in t_clean:
            return "LAP"
        if "cpu" in t_clean or "procesador" in t_clean:
            return "CPU"
        if "gpu" in t_clean or "grafica" in t_clean or "video" in t_clean:
            return "GPU"
        if "motherboard" in t_clean or "placa" in t_clean:
            return "MBD"
        if "ram" in t_clean or "memoria" in t_clean:
            return "RAM"
        if "almacenamiento" in t_clean or "ssd" in t_clean or "hdd" in t_clean or "disco" in t_clean:
            return "ALM"
        if "psu" in t_clean or "fuente" in t_clean:
            return "PSU"
        if "case" in t_clean or "gabinete" in t_clean:
            return "CAS"
        if "monitor" in t_clean or "pantalla" in t_clean:
            return "MON"
        if "periferico" in t_clean or "teclado" in t_clean or "mouse" in t_clean:
            return "PER"
        if "impresora" in t_clean or "scanner" in t_clean:
            return "IMP"
        if "red" in t_clean or "router" in t_clean:
            return "RED"
        if "accesorio" in t_clean:
            return "ACC"
        if "audio" in t_clean or "audifono" in t_clean:
            return "AUD"

        # Fallback genérico: extraer 3 letras alfanuméricas
        letras = [c for c in t_clean.upper() if c.isalnum()]
        if len(letras) >= 3:
            return "".join(letras[:3])
        elif len(letras) > 0:
            return "".join(letras).ljust(3, "X")
        return "PRO"

    @classmethod
    def normalizar_codigo_marca(cls, marca_val):
        """
        Retorna un prefijo nemotécnico de 3 letras en mayúsculas para la marca.
        Ejemplos:
        - 'Lenovo' -> 'LEN'
        - 'Asus' -> 'ASU'
        - 'Intel' -> 'INT'
        - 'AMD' -> 'AMD'
        - 'MSI' -> 'MSI'
        - 'Corsair' -> 'COR'
        - 'Kingston' -> 'KIN'
        - 'Logitech' -> 'LOG'
        - 'Samsung' -> 'SAM'
        - 'Western Digital' -> 'WDC'
        - 'Redragon' -> 'RED'
        - 'Gigabyte' -> 'GIG'
        - 'HP' -> 'HPX'
        - '' o None -> 'GEN'
        """
        if not marca_val or not str(marca_val).strip():
            return "GEN"

        import unicodedata
        m_clean = unicodedata.normalize('NFKD', str(marca_val)).encode('ASCII', 'ignore').decode('utf-8').upper()

        mapeos = {
            "WESTERN DIGITAL": "WDC",
            "HP": "HPX",
            "LG": "LGX",
            "EVGA": "EVG",
            "SEAGATE": "SEA",
            "CRUCIAL": "CRU",
            "GIGABYTE": "GIG",
            "REDRAGON": "RED",
            "LOGITECH": "LOG",
            "KINGSTON": "KIN",
            "CORSAIR": "COR",
            "SAMSUNG": "SAM",
            "LENOVO": "LEN",
            "INTEL": "INT",
            "ASUS": "ASU",
            "MSI": "MSI",
            "AMD": "AMD"
        }
        m_stripped = m_clean.strip()
        if m_stripped in mapeos:
            return mapeos[m_stripped]

        chars = [c for c in m_stripped if c.isalnum()]
        if len(chars) >= 3:
            return "".join(chars[:3])
        elif len(chars) > 0:
            return "".join(chars).ljust(3, "X")
        return "GEN"

    @staticmethod
    def es_codigo_disponible(codigo, excluir_producto_id=None):
        """
        Verifica en SQLite si un código SKU está libre o ya se encuentra asignado.
        Retorna True si está disponible, False si ya existe (evitando duplicados).
        """
        if not codigo or not str(codigo).strip():
            return False

        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT id FROM productos WHERE UPPER(TRIM(codigo)) = UPPER(TRIM(?))"
        params = [str(codigo).strip()]
        if excluir_producto_id:
            query += " AND id != ?"
            params.append(excluir_producto_id)
        query += " LIMIT 1;"

        cursor.execute(query, params)
        existe = cursor.fetchone() is not None
        conn.close()
        return not existe

    @classmethod
    def generar_sku_sugerido(cls, categoria_id=None, marca=None, categoria_nombre=None):
        """
        Genera un código SKU inteligente sugerido correlativo único según categoría y marca.
        Formato: [CAT]-[MAR]-[001] (ej: LAP-LEN-001, CPU-AMD-001, PER-RED-001).
        Garantiza que el código no esté repetido en la base de datos.
        """
        cat_val = categoria_nombre if categoria_nombre else categoria_id
        cod_cat = cls.normalizar_codigo_categoria(cat_val)
        cod_mar = cls.normalizar_codigo_marca(marca)

        prefijo = f"{cod_cat}-{cod_mar}"

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT codigo FROM productos WHERE codigo LIKE ?;", (f"{prefijo}-%",))
        filas = cursor.fetchall()
        conn.close()

        import re
        max_correlativo = 0
        patron = re.compile(rf"^{re.escape(prefijo)}-(\d+)$", re.IGNORECASE)

        for f in filas:
            c = str(f[0]).strip()
            m = patron.match(c)
            if m:
                try:
                    num = int(m.group(1))
                    if num > max_correlativo:
                        max_correlativo = num
                except ValueError:
                    pass

        # Generar el siguiente correlativo y verificar contra colisiones
        siguiente = max_correlativo + 1
        while True:
            candidato = f"{prefijo}-{str(siguiente).zfill(3)}"
            if cls.es_codigo_disponible(candidato):
                return candidato
            siguiente += 1

    @staticmethod
    def obtener_sugerencias_reposicion(dias_analisis=30, dias_cobertura_deseada=30, solo_requieren_reposicion=True):
        """
        Obtiene las recomendaciones inteligentes del Asistente de Reposición.
        """
        from services.reposicion_service import ReposicionService
        return ReposicionService.analizar_reposicion(
            dias_analisis=dias_analisis,
            dias_cobertura_deseada=dias_cobertura_deseada,
            solo_requieren_reposicion=solo_requieren_reposicion
        )
