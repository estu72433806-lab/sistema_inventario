"""
Servicio de Sincronización Híbrida (SQLite Local <-> PostgreSQL Nube).
Permite:
1. Operar 100% desconectado en SQLite.
2. Detección automática del estado (EN_LINEA vs MODO_LOCAL).
3. Conteo de registros locales pendientes de sincronizar.
4. Envío idempotente de ventas, movimientos y maestros mediante UUIDs (sin duplicados).
5. Detección de conflictos basada en fecha de modificación (sin sobreescritura ciega).
6. Descarga de actualizaciones remotas hacia SQLite.
"""
from datetime import datetime
from database.db import get_connection as get_sqlite_conn
from database.pg_db import get_pg_connection, probar_conexion_pg
from database.pg_schema import init_pg_db

class SyncService:
    @staticmethod
    def obtener_estado_conexion() -> tuple[str, str]:
        """
        Retorna ('EN_LINEA', 'Mensaje') o ('MODO_LOCAL', 'Mensaje')
        según la disponibilidad de PostgreSQL.
        """
        ok, msg = probar_conexion_pg()
        if ok:
            return "EN_LINEA", msg
        else:
            return "MODO_LOCAL", msg

    @staticmethod
    def obtener_conteo_pendientes() -> int:
        """Retorna la cantidad total de registros locales pendientes de subir (sincronizado = 0)."""
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        tablas = ["usuarios", "categorias", "proveedores", "productos", "clientes", "movimientos_stock", "ventas", "detalle_ventas"]
        total_pendientes = 0
        try:
            for t in tablas:
                cursor.execute(f"SELECT COUNT(*) FROM {t} WHERE sincronizado = 0;")
                total_pendientes += cursor.fetchone()[0]
        except Exception:
            pass
        finally:
            conn.close()
        return total_pendientes

    @staticmethod
    def obtener_info_ultima_sincronizacion() -> dict:
        """Retorna la fecha y el resultado de la última sincronización registrada."""
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        info = {"ultima_sincronizacion": "Nunca", "estado": "MODO_LOCAL", "detalles": "Sin sincronizaciones previas."}
        try:
            cursor.execute("SELECT ultima_sincronizacion, estado, detalles FROM sincronizacion_info WHERE id = 1;")
            row = cursor.fetchone()
            if row:
                info = {
                    "ultima_sincronizacion": row["ultima_sincronizacion"],
                    "estado": row["estado"],
                    "detalles": row["detalles"]
                }
        except Exception:
            pass
        finally:
            conn.close()
        return info

    @staticmethod
    def sincronizar_todo() -> dict:
        """
        Ejecuta la sincronización completa bidireccional entre SQLite y PostgreSQL:
        - Si no hay conexión, finaliza de forma segura conservando los datos locales.
        - Sube pendientes con control de transacciones y UUIDs.
        - Detecta conflictos y los registra.
        - Descarga novedades remotas a SQLite.
        """
        res = {
            "exito": False,
            "modo": "MODO_LOCAL",
            "subidos": 0,
            "descargados": 0,
            "conflictos": 0,
            "mensaje": ""
        }

        # 1. Probar conexión
        pg_conn, err = get_pg_connection(timeout=3)
        if not pg_conn:
            res["mensaje"] = f"No hay conexión con PostgreSQL en la nube ({err}). Se mantiene el Modo Local."
            SyncService._actualizar_info_sync("MODO_LOCAL", res["mensaje"])
            return res

        # 2. Asegurar que las tablas existen en PostgreSQL
        ok_schema, msg_schema = init_pg_db(pg_conn)
        if not ok_schema:
            pg_conn.close()
            res["mensaje"] = f"Error al inicializar tablas en PostgreSQL: {msg_schema}"
            return res

        sqlite_conn = get_sqlite_conn()
        cursor_sq = sqlite_conn.cursor()
        cursor_pg = pg_conn.cursor()

        try:
            # -------------------------------------------------------------
            # PASO A: Sincronizar Usuarios locales pendientes
            # -------------------------------------------------------------
            cursor_sq.execute("SELECT * FROM usuarios WHERE sincronizado = 0;")
            usuarios_pend = [dict(r) for r in cursor_sq.fetchall()]
            for u in usuarios_pend:
                cursor_pg.execute("SELECT id, fecha_modificacion FROM usuarios WHERE uuid = %s;", (u["uuid"],))
                existe = cursor_pg.fetchone()
                if not existe:
                    cursor_pg.execute("""
                        INSERT INTO usuarios (uuid, username, password_hash, salt, nombre_completo, rol, activo, creado_en, fecha_modificacion)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (uuid) DO NOTHING;
                    """, (u["uuid"], u["username"], u["password_hash"], u["salt"], u["nombre_completo"], u["rol"], u["activo"], u["creado_en"], u["fecha_modificacion"]))
                    res["subidos"] += 1
                cursor_sq.execute("UPDATE usuarios SET sincronizado = 1 WHERE id = ?;", (u["id"],))

            # -------------------------------------------------------------
            # PASO B: Sincronizar Categorías
            # -------------------------------------------------------------
            cursor_sq.execute("SELECT * FROM categorias WHERE sincronizado = 0;")
            cat_pend = [dict(r) for r in cursor_sq.fetchall()]
            for c in cat_pend:
                cursor_pg.execute("SELECT id FROM categorias WHERE uuid = %s;", (c["uuid"],))
                if not cursor_pg.fetchone():
                    cursor_pg.execute("""
                        INSERT INTO categorias (uuid, nombre, descripcion, fecha_modificacion)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (uuid) DO NOTHING;
                    """, (c["uuid"], c["nombre"], c.get("descripcion", ""), c["fecha_modificacion"]))
                    res["subidos"] += 1
                cursor_sq.execute("UPDATE categorias SET sincronizado = 1 WHERE id = ?;", (c["id"],))

            # -------------------------------------------------------------
            # PASO C: Sincronizar Proveedores
            # -------------------------------------------------------------
            cursor_sq.execute("SELECT * FROM proveedores WHERE sincronizado = 0;")
            prov_pend = [dict(r) for r in cursor_sq.fetchall()]
            for p in prov_pend:
                cursor_pg.execute("SELECT id FROM proveedores WHERE uuid = %s;", (p["uuid"],))
                if not cursor_pg.fetchone():
                    cursor_pg.execute("""
                        INSERT INTO proveedores (uuid, ruc_dni, razon_social, contacto, telefono, email, direccion, activo, fecha_modificacion)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (uuid) DO NOTHING;
                    """, (p["uuid"], p["ruc_dni"], p["razon_social"], p.get("contacto", ""), p.get("telefono", ""), p.get("email", ""), p.get("direccion", ""), p["activo"], p["fecha_modificacion"]))
                    res["subidos"] += 1
                cursor_sq.execute("UPDATE proveedores SET sincronizado = 1 WHERE id = ?;", (p["id"],))

            # -------------------------------------------------------------
            # PASO D: Sincronizar Clientes
            # -------------------------------------------------------------
            cursor_sq.execute("SELECT * FROM clientes WHERE sincronizado = 0;")
            cli_pend = [dict(r) for r in cursor_sq.fetchall()]
            for cl in cli_pend:
                cursor_pg.execute("SELECT id, fecha_modificacion FROM clientes WHERE uuid = %s;", (cl["uuid"],))
                ex_cli = cursor_pg.fetchone()
                if not ex_cli:
                    cursor_pg.execute("""
                        INSERT INTO clientes (uuid, tipo_documento, numero_documento, nombre, telefono, email, direccion, activo, fecha_modificacion)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (uuid) DO NOTHING;
                    """, (cl["uuid"], cl["tipo_documento"], cl["numero_documento"], cl["nombre"], cl.get("telefono", ""), cl.get("email", ""), cl.get("direccion", ""), cl["activo"], cl["fecha_modificacion"]))
                    res["subidos"] += 1
                else:
                    # Detectar si ambos cambiaron (conflicto)
                    rem_fecha = str(ex_cli[1]) if ex_cli[1] else ""
                    loc_fecha = str(cl["fecha_modificacion"]) if cl["fecha_modificacion"] else ""
                    if rem_fecha and loc_fecha and rem_fecha > loc_fecha:
                        res["conflictos"] += 1
                        SyncService._registrar_conflicto(cursor_sq, cursor_pg, "clientes", cl["uuid"], "nombre", cl["nombre"], "Modificado en Nube")
                cursor_sq.execute("UPDATE clientes SET sincronizado = 1 WHERE id = ?;", (cl["id"],))

            # -------------------------------------------------------------
            # PASO E: Sincronizar Productos (con detección de conflictos)
            # -------------------------------------------------------------
            cursor_sq.execute("""
                SELECT p.*, c.uuid as cat_uuid, prov.uuid as prov_uuid
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN proveedores prov ON p.proveedor_id = prov.id
                WHERE p.sincronizado = 0;
            """)
            prod_pend = [dict(r) for r in cursor_sq.fetchall()]
            for pr in prod_pend:
                cursor_pg.execute("SELECT id, precio_venta, stock, fecha_modificacion FROM productos WHERE uuid = %s;", (pr["uuid"],))
                rem_prod = cursor_pg.fetchone()
                if not rem_prod:
                    cursor_pg.execute("""
                        INSERT INTO productos (
                            uuid, codigo, nombre, categoria_uuid, proveedor_uuid, marca,
                            precio_compra, precio_venta, stock, stock_minimo, descripcion, activo, fecha_modificacion
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (uuid) DO NOTHING;
                    """, (
                        pr["uuid"], pr["codigo"], pr["nombre"], pr.get("cat_uuid"), pr.get("prov_uuid"),
                        pr.get("marca", ""), float(pr["precio_compra"]), float(pr["precio_venta"]),
                        int(pr["stock"]), int(pr["stock_minimo"]), pr.get("descripcion", ""),
                        int(pr["activo"]), pr["fecha_modificacion"]
                    ))
                    res["subidos"] += 1
                else:
                    # Producto existe en ambos: comprobar conflicto de modificación
                    rem_fecha = str(rem_prod[3]) if rem_prod[3] else ""
                    loc_fecha = str(pr["fecha_modificacion"]) if pr["fecha_modificacion"] else ""
                    if rem_fecha and loc_fecha and rem_fecha > loc_fecha:
                        # Conflicto: se modificó en la nube posteriormente
                        res["conflictos"] += 1
                        SyncService._registrar_conflicto(cursor_sq, cursor_pg, "productos", pr["uuid"], "stock/precio", f"Local: S/ {pr['precio_venta']}, Stock: {pr['stock']}", f"Nube: S/ {rem_prod[1]}, Stock: {rem_prod[2]}")
                    else:
                        # Local es más reciente: actualizar nube
                        cursor_pg.execute("""
                            UPDATE productos
                            SET codigo = %s, nombre = %s, categoria_uuid = %s, proveedor_uuid = %s, marca = %s,
                                precio_compra = %s, precio_venta = %s, stock = %s, stock_minimo = %s, descripcion = %s,
                                activo = %s, fecha_modificacion = %s
                            WHERE uuid = %s;
                        """, (
                            pr["codigo"], pr["nombre"], pr.get("cat_uuid"), pr.get("prov_uuid"),
                            pr.get("marca", ""), float(pr["precio_compra"]), float(pr["precio_venta"]),
                            int(pr["stock"]), int(pr["stock_minimo"]), pr.get("descripcion", ""),
                            int(pr["activo"]), pr["fecha_modificacion"], pr["uuid"]
                        ))
                        res["subidos"] += 1

                cursor_sq.execute("UPDATE productos SET sincronizado = 1 WHERE id = ?;", (pr["id"],))

            # -------------------------------------------------------------
            # PASO F: Sincronizar Ventas locales
            # -------------------------------------------------------------
            cursor_sq.execute("""
                SELECT v.*, cl.uuid as cli_uuid, u.uuid as usr_uuid
                FROM ventas v
                LEFT JOIN clientes cl ON v.cliente_id = cl.id
                LEFT JOIN usuarios u ON v.usuario_id = u.id
                WHERE v.sincronizado = 0;
            """)
            ventas_pend = [dict(r) for r in cursor_sq.fetchall()]
            for v in ventas_pend:
                cursor_pg.execute("SELECT id FROM ventas WHERE uuid = %s;", (v["uuid"],))
                if not cursor_pg.fetchone():
                    cursor_pg.execute("""
                        INSERT INTO ventas (
                            uuid, numero_comprobante, tipo_comprobante, fecha, cliente_uuid, usuario_uuid,
                            subtotal, descuento, impuesto, total, metodo_pago, estado, fecha_modificacion
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (uuid) DO NOTHING;
                    """, (
                        v["uuid"], v["numero_comprobante"], v["tipo_comprobante"], v["fecha"],
                        v.get("cli_uuid"), v.get("usr_uuid"), float(v["subtotal"]), float(v["descuento"]),
                        float(v["impuesto"]), float(v["total"]), v["metodo_pago"], v["estado"], v["fecha_modificacion"]
                    ))
                    res["subidos"] += 1

                cursor_sq.execute("UPDATE ventas SET sincronizado = 1 WHERE id = ?;", (v["id"],))

            # -------------------------------------------------------------
            # PASO G: Sincronizar Detalle de Ventas
            # -------------------------------------------------------------
            cursor_sq.execute("""
                SELECT dv.*, v.uuid as venta_uuid, p.uuid as prod_uuid
                FROM detalle_ventas dv
                JOIN ventas v ON dv.venta_id = v.id
                JOIN productos p ON dv.producto_id = p.id
                WHERE dv.sincronizado = 0;
            """)
            det_pend = [dict(r) for r in cursor_sq.fetchall()]
            for d in det_pend:
                cursor_pg.execute("SELECT id FROM detalle_ventas WHERE uuid = %s;", (d["uuid"],))
                if not cursor_pg.fetchone():
                    cursor_pg.execute("""
                        INSERT INTO detalle_ventas (uuid, venta_uuid, producto_uuid, cantidad, precio_unitario, subtotal, fecha_modificacion)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (uuid) DO NOTHING;
                    """, (
                        d["uuid"], d["venta_uuid"], d["prod_uuid"], int(d["cantidad"]),
                        float(d["precio_unitario"]), float(d["subtotal"]), d["fecha_modificacion"]
                    ))
                    res["subidos"] += 1
                cursor_sq.execute("UPDATE detalle_ventas SET sincronizado = 1 WHERE id = ?;", (d["id"],))

            # -------------------------------------------------------------
            # PASO H: Sincronizar Movimientos de Stock (Kardex)
            # -------------------------------------------------------------
            cursor_sq.execute("""
                SELECT m.*, p.uuid as prod_uuid, u.uuid as usr_uuid, prov.uuid as prov_uuid
                FROM movimientos_stock m
                JOIN productos p ON m.producto_id = p.id
                LEFT JOIN usuarios u ON m.usuario_id = u.id
                LEFT JOIN proveedores prov ON m.proveedor_id = prov.id
                WHERE m.sincronizado = 0;
            """)
            mov_pend = [dict(r) for r in cursor_sq.fetchall()]
            for m in mov_pend:
                cursor_pg.execute("SELECT id FROM movimientos_stock WHERE uuid = %s;", (m["uuid"],))
                if not cursor_pg.fetchone():
                    cursor_pg.execute("""
                        INSERT INTO movimientos_stock (
                            uuid, producto_uuid, tipo_movimiento, cantidad, motivo, referencia, fecha,
                            usuario_uuid, proveedor_uuid, fecha_modificacion
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (uuid) DO NOTHING;
                    """, (
                        m["uuid"], m["prod_uuid"], m["tipo_movimiento"], int(m["cantidad"]),
                        m.get("motivo", ""), m.get("referencia", ""), m["fecha"],
                        m.get("usr_uuid"), m.get("prov_uuid"), m["fecha_modificacion"]
                    ))
                    res["subidos"] += 1
                cursor_sq.execute("UPDATE movimientos_stock SET sincronizado = 1 WHERE id = ?;", (m["id"],))

            # -------------------------------------------------------------
            # PASO I: Descargar novedades remotas desde PostgreSQL a SQLite
            # -------------------------------------------------------------
            # Descargar productos nuevos creados en la nube
            cursor_pg.execute("SELECT uuid, codigo, nombre, marca, precio_compra, precio_venta, stock, stock_minimo, descripcion, activo, fecha_modificacion FROM productos;")
            rem_prods = cursor_pg.fetchall()
            for rp in rem_prods:
                r_uuid, r_cod, r_nom, r_marca, r_pc, r_pv, r_st, r_stmin, r_desc, r_act, r_fec = rp
                cursor_sq.execute("SELECT id FROM productos WHERE uuid = ?;", (r_uuid,))
                loc_p = cursor_sq.fetchone()
                if not loc_p:
                    # Verificar si existe por código para no violar UNIQUE
                    cursor_sq.execute("SELECT id FROM productos WHERE codigo = ?;", (r_cod,))
                    cod_p = cursor_sq.fetchone()
                    if not cod_p:
                        cursor_sq.execute("""
                            INSERT INTO productos (uuid, codigo, nombre, marca, precio_compra, precio_venta, stock, stock_minimo, descripcion, activo, fecha_modificacion, sincronizado)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1);
                        """, (r_uuid, r_cod, r_nom, r_marca or "", float(r_pc), float(r_pv), int(r_st), int(r_stmin), r_desc or "", int(r_act), str(r_fec)))
                        res["descargados"] += 1

            # Confirmar transacciones en ambas bases de datos
            pg_conn.commit()
            sqlite_conn.commit()

            res["exito"] = True
            res["modo"] = "EN_LINEA"
            res["mensaje"] = (
                f"Sincronización completada exitosamente.\n"
                f"• Registros subidos a la nube: {res['subidos']}\n"
                f"• Registros descargados a local: {res['descargados']}\n"
                f"• Conflictos detectados: {res['conflictos']}"
            )
            SyncService._actualizar_info_sync("EN_LINEA", res["mensaje"])

        except Exception as e:
            pg_conn.rollback()
            sqlite_conn.rollback()
            res["exito"] = False
            res["mensaje"] = f"Error transaccional durante la sincronización: {str(e)}. Se preservaron los datos locales."
            SyncService._actualizar_info_sync("ERROR", res["mensaje"])
        finally:
            cursor_sq.close()
            sqlite_conn.close()
            cursor_pg.close()
            pg_conn.close()

        return res

    @staticmethod
    def _registrar_conflicto(cursor_sq, cursor_pg, tabla, reg_uuid, campo, val_loc, val_rem):
        """Registra un conflicto en SQLite y PostgreSQL sin sobreescribir datos automáticamente."""
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor_sq.execute("""
                INSERT INTO conflictos_sincronizacion (tabla, registro_uuid, campo, valor_local, valor_remoto, fecha_conflicto, resuelto)
                VALUES (?, ?, ?, ?, ?, ?, 0);
            """, (tabla, reg_uuid, campo, str(val_loc), str(val_rem), ahora))
        except Exception:
            pass
        try:
            cursor_pg.execute("""
                INSERT INTO conflictos_sincronizacion (tabla, registro_uuid, campo, valor_local, valor_remoto, fecha_conflicto, resuelto)
                VALUES (%s, %s, %s, %s, %s, %s, 0);
            """, (tabla, reg_uuid, campo, str(val_loc), str(val_rem), ahora))
        except Exception:
            pass

    @staticmethod
    def _actualizar_info_sync(estado: str, detalles: str):
        """Actualiza el registro único de estado en SQLite."""
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor.execute("""
                UPDATE sincronizacion_info
                SET ultima_sincronizacion = ?, estado = ?, detalles = ?
                WHERE id = 1;
            """, (ahora, estado, detalles))
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    @staticmethod
    def listar_conflictos() -> list:
        """Retorna la lista de conflictos detectados pendientes de resolución."""
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conflictos_sincronizacion WHERE resuelto = 0 ORDER BY id DESC;")
        filas = cursor.fetchall()
        conn.close()
        return [dict(f) for f in filas]
