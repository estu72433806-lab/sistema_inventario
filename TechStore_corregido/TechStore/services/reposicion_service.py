"""
Servicio Inteligente de Asistente de Reposición e Inventario.
Analiza existencias actuales, rotación y ventas históricas en SQLite,
calculando la demanda diaria promedio, autonomía de stock y recomendando
compras optimizadas por producto y por proveedor mayorista.
"""
import math
from datetime import datetime, timedelta
from database.db import get_connection

class ReposicionService:
    @staticmethod
    def analizar_reposicion(dias_analisis=30, dias_cobertura_deseada=30, solo_requieren_reposicion=False):
        """
        Analiza todos los productos activos y genera recomendaciones inteligentes de compra.
        
        Parámetros:
        - dias_analisis: Días hacia atrás para medir las ventas y la demanda habitual (ej: 30).
        - dias_cobertura_deseada: Días de inventario que se desea abastecer con el nuevo pedido (ej: 30).
        - solo_requieren_reposicion: Si es True, filtra únicamente aquellos que requieren compra.
        
        Retorna un dict con:
        - 'resumen': Métricas globales (críticos, unidades a pedir, inversión estimada, etc.).
        - 'sugerencias': Lista de productos analizados con métricas y justificación detallada.
        - 'proveedores': Agrupación por proveedor mayorista con montos y unidades.
        """
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Obtener catálogo activo con categorías y proveedores
        cursor.execute("""
            SELECT p.id, p.codigo, p.nombre, p.marca, p.precio_compra, p.precio_venta,
                   p.stock, p.stock_minimo, p.descripcion,
                   c.id as categoria_id, c.nombre as categoria_nombre,
                   prov.id as proveedor_id, prov.razon_social as proveedor_nombre,
                   prov.ruc_dni as proveedor_ruc, prov.telefono as proveedor_telefono,
                   prov.email as proveedor_email, prov.contacto as proveedor_contacto
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            LEFT JOIN proveedores prov ON p.proveedor_id = prov.id
            WHERE p.activo = 1
            ORDER BY p.stock ASC, p.nombre ASC;
        """)
        productos = [dict(r) for r in cursor.fetchall()]

        # 2. Obtener historial de ventas en la ventana de análisis
        fecha_limite = (datetime.now() - timedelta(days=dias_analisis)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            SELECT dv.producto_id,
                   SUM(dv.cantidad) as total_vendido,
                   SUM(dv.subtotal) as total_monto,
                   COUNT(DISTINCT v.id) as transacciones_count
            FROM detalle_ventas dv
            JOIN ventas v ON dv.venta_id = v.id
            WHERE v.estado != 'Cancelada' AND v.fecha >= ?
            GROUP BY dv.producto_id;
        """, (fecha_limite,))
        ventas_map = {row["producto_id"]: dict(row) for row in cursor.fetchall()}
        conn.close()

        sugerencias = []
        tot_criticos = 0
        tot_urgentes = 0
        tot_alertas = 0
        tot_preventivos = 0
        tot_unidades_sugeridas = 0
        tot_inversion_estimada = 0.0

        proveedores_agrupados = {}

        for p in productos:
            pid = p["id"]
            stock_actual = int(p["stock"])
            stock_minimo = int(p["stock_minimo"])
            precio_compra = float(p["precio_compra"] or 0.0)

            v_info = ventas_map.get(pid, {"total_vendido": 0, "total_monto": 0.0, "transacciones_count": 0})
            unidades_vendidas = int(v_info["total_vendido"] or 0)
            ventas_monto = float(v_info["total_monto"] or 0.0)
            transacciones = int(v_info["transacciones_count"] or 0)

            demanda_diaria = round(unidades_vendidas / float(dias_analisis), 2)
            demanda_mensual_estimada = round(demanda_diaria * 30.0, 1)

            if demanda_diaria > 0:
                dias_autonomia = round(stock_actual / demanda_diaria, 1)
            else:
                dias_autonomia = None

            # Determinar nivel de urgencia
            requiere_reposicion = False
            if stock_actual <= 0:
                nivel_urgencia = "CRITICO"
                urgencia_label = "🔴 Crítico (Agotado)"
                urgencia_orden = 1
                requiere_reposicion = True
                tot_criticos += 1
            elif stock_actual <= max(1, stock_minimo // 2) or (dias_autonomia is not None and dias_autonomia <= 3.0):
                nivel_urgencia = "URGENTE"
                urgencia_label = "🟠 Urgente (< Mitad Mín.)"
                urgencia_orden = 2
                requiere_reposicion = True
                tot_urgentes += 1
            elif stock_actual <= stock_minimo:
                nivel_urgencia = "ALERTA"
                urgencia_label = "🟡 Mínimo Alcanzado"
                urgencia_orden = 3
                requiere_reposicion = True
                tot_alertas += 1
            elif dias_autonomia is not None and dias_autonomia <= 7.0:
                nivel_urgencia = "PREVENTIVO"
                urgencia_label = "🔵 Preventivo (Alta Rotación)"
                urgencia_orden = 4
                requiere_reposicion = True
                tot_preventivos += 1
            else:
                nivel_urgencia = "OPTIMO"
                urgencia_label = "🟢 Óptimo"
                urgencia_orden = 5

            # Cálculo inteligente de cantidad sugerida
            if requiere_reposicion:
                if demanda_diaria > 0:
                    demanda_cobertura = math.ceil(demanda_diaria * dias_cobertura_deseada)
                    stock_objetivo = stock_minimo + demanda_cobertura
                    cantidad_sugerida = max(stock_objetivo - stock_actual, stock_minimo)
                    
                    autonomia_txt = f"~{dias_autonomia} día(s)" if dias_autonomia is not None else "0 días"
                    justificacion = (
                        f"Stock actual de {stock_actual} un. con ventas de {unidades_vendidas} un. "
                        f"en los últimos {dias_analisis} días (ritmo de {demanda_diaria:.2f} un/día, autonomía {autonomia_txt}). "
                        f"Se recomienda adquirir {cantidad_sugerida} un. para asegurar una cobertura de {dias_cobertura_deseada} días "
                        f"y salvaguardar el stock de seguridad mínimo ({stock_minimo} un.)."
                    )
                else:
                    # Sin ventas registradas en el período: reponer hasta un nivel de seguridad
                    cantidad_sugerida = max((stock_minimo * 2) - stock_actual, stock_minimo, 1)
                    justificacion = (
                        f"Stock actual ({stock_actual} un.) igual o menor al mínimo ({stock_minimo} un.), "
                        f"sin ventas registradas en los últimos {dias_analisis} días. "
                        f"Se sugiere reposición prudente de {cantidad_sugerida} un. para restablecer "
                        f"el inventario de reserva óptimo."
                    )
            else:
                cantidad_sugerida = 0
                autonomia_txt = f"~{dias_autonomia} días" if dias_autonomia is not None else "Sin demanda reciente"
                justificacion = f"Stock en nivel suficiente ({stock_actual} un. disponibles, autonomía estimada {autonomia_txt}). No requiere reposición inmediata."

            costo_reposicion = round(cantidad_sugerida * precio_compra, 2)

            item = {
                "id": pid,
                "codigo": p["codigo"],
                "nombre": p["nombre"],
                "marca": p["marca"] or "-",
                "categoria_id": p["categoria_id"],
                "categoria_nombre": p["categoria_nombre"] or "Sin Categoría",
                "proveedor_id": p["proveedor_id"],
                "proveedor_nombre": p["proveedor_nombre"] or "(Sin proveedor asignado)",
                "proveedor_telefono": p["proveedor_telefono"] or "-",
                "proveedor_email": p["proveedor_email"] or "-",
                "proveedor_contacto": p["proveedor_contacto"] or "-",
                "stock_actual": stock_actual,
                "stock_minimo": stock_minimo,
                "precio_compra": precio_compra,
                "precio_venta": float(p["precio_venta"] or 0.0),
                "unidades_vendidas_periodo": unidades_vendidas,
                "ventas_monto_periodo": ventas_monto,
                "transacciones_periodo": transacciones,
                "demanda_diaria": demanda_diaria,
                "demanda_mensual_estimada": demanda_mensual_estimada,
                "dias_autonomia": dias_autonomia,
                "nivel_urgencia": nivel_urgencia,
                "urgencia_label": urgencia_label,
                "urgencia_orden": urgencia_orden,
                "requiere_reposicion": requiere_reposicion,
                "cantidad_sugerida": cantidad_sugerida,
                "costo_estimado": costo_reposicion,
                "justificacion": justificacion
            }

            if requiere_reposicion:
                tot_unidades_sugeridas += cantidad_sugerida
                tot_inversion_estimada += costo_reposicion

                # Agrupación por proveedor
                p_key = p["proveedor_nombre"] or "Sin Proveedor Asignado"
                if p_key not in proveedores_agrupados:
                    proveedores_agrupados[p_key] = {
                        "proveedor_id": p["proveedor_id"],
                        "proveedor_nombre": p_key,
                        "telefono": p["proveedor_telefono"] or "-",
                        "email": p["proveedor_email"] or "-",
                        "contacto": p["proveedor_contacto"] or "-",
                        "total_items": 0,
                        "unidades_totales": 0,
                        "monto_total": 0.0,
                        "productos": []
                    }
                proveedores_agrupados[p_key]["total_items"] += 1
                proveedores_agrupados[p_key]["unidades_totales"] += cantidad_sugerida
                proveedores_agrupados[p_key]["monto_total"] += costo_reposicion
                proveedores_agrupados[p_key]["productos"].append(item)

            if not solo_requieren_reposicion or requiere_reposicion:
                sugerencias.append(item)

        # Ordenar por urgencia (1 a 5), y luego por autonomía ascendente
        sugerencias.sort(key=lambda x: (x["urgencia_orden"], x["dias_autonomia"] if x["dias_autonomia"] is not None else 9999, x["stock_actual"]))

        resumen = {
            "dias_analisis": dias_analisis,
            "dias_cobertura_deseada": dias_cobertura_deseada,
            "total_catalogo": len(productos),
            "total_criticos": tot_criticos,
            "total_urgentes": tot_urgentes,
            "total_alertas": tot_alertas,
            "total_preventivos": tot_preventivos,
            "total_por_reponer": tot_criticos + tot_urgentes + tot_alertas + tot_preventivos,
            "unidades_totales_sugeridas": tot_unidades_sugeridas,
            "inversion_total_estimada": round(tot_inversion_estimada, 2),
            "total_proveedores_involucrados": len(proveedores_agrupados)
        }

        return {
            "resumen": resumen,
            "sugerencias": sugerencias,
            "proveedores": list(proveedores_agrupados.values())
        }

