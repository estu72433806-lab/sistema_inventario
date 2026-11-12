"""
Diálogo / Ventana del Asistente Inteligente de Reposición y Compras.
Muestra recomendaciones automáticas de compra basadas en existencias actuales,
ventas históricas recientes y ritmo de demanda habitual.
Permite exportar informes a Excel y enlazar directamente con el registro de entradas de mercadería.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from services.reposicion_service import ReposicionService
from services.excel_service import ExcelService
from ui.theme import Color

class AsistenteReposicionDialog(tk.Toplevel):
    def __init__(self, parent, on_registrar_entrada=None, producto_id_foco=None):
        super().__init__(parent)
        self.parent = parent
        self.on_registrar_entrada = on_registrar_entrada
        self.producto_id_foco = producto_id_foco
        
        self.title("💡 Asistente Inteligente de Reposición y Compras - TechStore")
        self.geometry("1180x720")
        self.minsize(980, 600)
        self.transient(parent)
        self.grab_set()

        self.datos_analisis = None
        self.sugerencias_filtradas = []
        self.item_seleccionado = None

        self._construir_ui()
        self.ejecutar_analisis()

    def _construir_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # 1. Cabecera Informativa
        frame_header = tk.Frame(self, bg=Color.OSCURO, padx=16, pady=12)
        frame_header.grid(row=0, column=0, sticky="ew")

        lbl_icono = tk.Label(frame_header, text="💡", font=("Segoe UI Emoji", 18), bg=Color.OSCURO, fg=Color.ACENTO_CLARO)
        lbl_icono.pack(side="left", padx=(0, 10))

        frame_header_text = tk.Frame(frame_header, bg=Color.OSCURO)
        frame_header_text.pack(side="left")

        lbl_tit = tk.Label(
            frame_header_text,
            text="Asistente de Reposición Inteligente de Inventario",
            font=("Segoe UI", 13, "bold"),
            fg=Color.FONDO,
            bg=Color.OSCURO
        )
        lbl_tit.pack(anchor="w")

        lbl_sub = tk.Label(
            frame_header_text,
            text="Recomendaciones automáticas de reabastecimiento calculadas según stock actual, ventas recientes y demanda proyectada.",
            font=("Segoe UI", 9),
            fg=Color.GRIS,
            bg=Color.OSCURO
        )
        lbl_sub.pack(anchor="w")

        # 2. Tarjetas KPI Superiores
        frame_kpis = ttk.Frame(self, padding=(12, 10, 12, 6))
        frame_kpis.grid(row=1, column=0, sticky="ew")
        for i in range(4):
            frame_kpis.columnconfigure(i, weight=1)

        self.kpi_criticos = self._crear_tarjeta_kpi(frame_kpis, 0, "PRODUCTOS EN ALERTA", "0", "Nivel crítico o stock mínimo", Color.PELIGRO_OSCURO)
        self.kpi_unidades = self._crear_tarjeta_kpi(frame_kpis, 1, "UNIDADES SUGERIDAS", "0 un.", "Total recomendado a comprar", Color.ACENTO_OSCURO)
        self.kpi_inversion = self._crear_tarjeta_kpi(frame_kpis, 2, "INVERSIÓN ESTIMADA", "S/ 0.00", "Presupuesto estimado de reposición", "#047857")
        self.kpi_proveedores = self._crear_tarjeta_kpi(frame_kpis, 3, "PROVEEDORES MAYORISTAS", "0", "Mayoristas a contactar", Color.TEXTO_SUAVE)

        # 3. Contenedor Central: Filtros + Tabla Principal
        frame_central = ttk.Frame(self, padding=(12, 6, 12, 6))
        frame_central.grid(row=2, column=0, sticky="nsew")
        frame_central.rowconfigure(1, weight=1)
        frame_central.columnconfigure(0, weight=1)

        # Barra de Filtros y Configuración del Modelo
        frame_filtros = ttk.LabelFrame(frame_central, text=" Filtros y Parámetros de Demanda ", padding=8)
        frame_filtros.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        # Filtro de Urgencia
        ttk.Label(frame_filtros, text="Urgencia:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(4, 4))
        self.combo_urgencia = ttk.Combobox(
            frame_filtros,
            values=[
                "Todos los que requieren compra (Recomendado)",
                "Solo Críticos (Agotados)",
                "Urgentes (< Mitad del Mínimo)",
                "Mínimo Alcanzado (<= Mínimo)",
                "Preventivos (Alta Rotación)",
                "Ver Catálogo Completo"
            ],
            state="readonly",
            width=36
        )
        self.combo_urgencia.current(0)
        self.combo_urgencia.pack(side="left", padx=(0, 12))
        self.combo_urgencia.bind("<<ComboboxSelected>>", lambda e: self._aplicar_filtros())

        # Horizonte de Cobertura
        ttk.Label(frame_filtros, text="Cobertura Deseada:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(4, 4))
        self.combo_cobertura = ttk.Combobox(
            frame_filtros,
            values=["15 días", "30 días (Recomendado)", "45 días", "60 días"],
            state="readonly",
            width=22
        )
        self.combo_cobertura.current(1)
        self.combo_cobertura.pack(side="left", padx=(0, 12))
        self.combo_cobertura.bind("<<ComboboxSelected>>", lambda e: self.ejecutar_analisis())

        # Filtro de Proveedor
        ttk.Label(frame_filtros, text="Proveedor:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(4, 4))
        self.combo_proveedor = ttk.Combobox(frame_filtros, state="readonly", width=24)
        self.combo_proveedor.pack(side="left", padx=(0, 12))
        self.combo_proveedor.bind("<<ComboboxSelected>>", lambda e: self._aplicar_filtros())

        # Búsqueda por texto
        ttk.Label(frame_filtros, text="Buscar:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(4, 4))
        self.entry_buscar = ttk.Entry(frame_filtros, width=20)
        self.entry_buscar.pack(side="left", padx=(0, 10))
        self.entry_buscar.bind("<KeyRelease>", lambda e: self._aplicar_filtros())

        btn_recalcular = ttk.Button(frame_filtros, text="🔄 Recalcular", command=self.ejecutar_analisis)
        btn_recalcular.pack(side="right", padx=4)

        # Tabla Principal (Treeview)
        frame_tabla = ttk.Frame(frame_central)
        frame_tabla.grid(row=1, column=0, sticky="nsew")
        frame_tabla.rowconfigure(0, weight=1)
        frame_tabla.columnconfigure(0, weight=1)

        columnas = (
            "id", "urgencia", "codigo", "nombre", "categoria", "marca",
            "stock", "stock_min", "ventas", "demanda", "autonomia",
            "sugerido", "pcompra", "inversion", "proveedor"
        )
        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("urgencia", text="Nivel Urgencia")
        self.tree.heading("codigo", text="Código SKU")
        self.tree.heading("nombre", text="Producto / Componente")
        self.tree.heading("categoria", text="Categoría")
        self.tree.heading("marca", text="Marca")
        self.tree.heading("stock", text="Stock")
        self.tree.heading("stock_min", text="Mín.")
        self.tree.heading("ventas", text="Ventas (30d)")
        self.tree.heading("demanda", text="Demanda/Día")
        self.tree.heading("autonomia", text="Autonomía")
        self.tree.heading("sugerido", text="Sugerido")
        self.tree.heading("pcompra", text="P. Compra")
        self.tree.heading("inversion", text="Inversión Est.")
        self.tree.heading("proveedor", text="Proveedor Sugerido")

        self.tree.column("id", width=35, anchor="center")
        self.tree.column("urgencia", width=155, anchor="w")
        self.tree.column("codigo", width=95, anchor="center")
        self.tree.column("nombre", width=220, anchor="w")
        self.tree.column("categoria", width=120, anchor="w")
        self.tree.column("marca", width=80, anchor="w")
        self.tree.column("stock", width=50, anchor="center")
        self.tree.column("stock_min", width=45, anchor="center")
        self.tree.column("ventas", width=75, anchor="center")
        self.tree.column("demanda", width=85, anchor="e")
        self.tree.column("autonomia", width=80, anchor="center")
        self.tree.column("sugerido", width=65, anchor="center")
        self.tree.column("pcompra", width=75, anchor="e")
        self.tree.column("inversion", width=85, anchor="e")
        self.tree.column("proveedor", width=160, anchor="w")

        scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self._on_producto_seleccionado)

        # Configuración de tags de color para filas
        self.tree.tag_configure("CRITICO", background=Color.PELIGRO_PALIDO, foreground=Color.PELIGRO_MUY_OSCURO)
        self.tree.tag_configure("URGENTE", background=Color.NARANJA_PALIDO, foreground=Color.NARANJA_OSCURO)
        self.tree.tag_configure("ALERTA", background=Color.AMBAR_PALIDO, foreground=Color.AMBAR_TEXTO)
        self.tree.tag_configure("PREVENTIVO", background=Color.ACENTO_PALIDO, foreground=Color.ACENTO_OSCURO)
        self.tree.tag_configure("OPTIMO", background=Color.FONDO, foreground=Color.GRIS_PIZARRA)

        # 4. Panel Inferior de Detalle y Acciones
        frame_inferior = ttk.LabelFrame(self, text=" Justificación de la Recomendación y Datos de Contacto del Proveedor ", padding=10)
        frame_inferior.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 10))
        frame_inferior.columnconfigure(0, weight=1)

        self.lbl_justificacion = tk.Label(
            frame_inferior,
            text="Seleccione un producto en la tabla para ver la justificación detallada del cálculo y los datos de compra.",
            font=("Segoe UI", 9),
            fg=Color.GRIS_PIZARRA,
            bg=Color.FONDO,
            anchor="w",
            justify="left",
            wraplength=920
        )
        self.lbl_justificacion.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self.lbl_contacto_proveedor = tk.Label(
            frame_inferior,
            text="",
            font=("Segoe UI", 9, "bold"),
            fg=Color.TEAL,
            bg=Color.FONDO,
            anchor="w"
        )
        self.lbl_contacto_proveedor.grid(row=1, column=0, sticky="ew")

        # Barra de Botones de Acción
        frame_acciones = ttk.Frame(frame_inferior)
        frame_acciones.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        self.btn_orden_compra = ttk.Button(
            frame_acciones,
            text="📥 Registrar Entrada de Mercadería (Kardex)",
            command=self._registrar_entrada_directa,
            state="disabled"
        )
        self.btn_orden_compra.pack(side="left", padx=(0, 10))

        self.btn_exportar_excel = ttk.Button(
            frame_acciones,
            text="📊 Exportar Sugerencias a Excel (.xlsx)",
            command=self._exportar_excel
        )
        self.btn_exportar_excel.pack(side="left", padx=(0, 10))

        btn_cerrar = ttk.Button(frame_acciones, text="Cerrar", command=self.destroy)
        btn_cerrar.pack(side="right")

    def _crear_tarjeta_kpi(self, parent, col, titulo, valor_inicial, subtitulo, color_fondo):
        card = tk.Frame(parent, bg=color_fondo, padx=14, pady=10, relief="flat")
        card.grid(row=0, column=col, sticky="nsew", padx=4)

        lbl_tit = tk.Label(card, text=titulo, font=("Segoe UI", 8, "bold"), fg=Color.BORDE, bg=color_fondo)
        lbl_tit.pack(anchor="w")

        lbl_val = tk.Label(card, text=valor_inicial, font=("Segoe UI", 16, "bold"), fg=Color.BLANCO, bg=color_fondo)
        lbl_val.pack(anchor="w", pady=(2, 0))

        lbl_sub = tk.Label(card, text=subtitulo, font=("Segoe UI", 8), fg=Color.GRIS_CLARO, bg=color_fondo)
        lbl_sub.pack(anchor="w", pady=(2, 0))

        return {"valor": lbl_val, "sub": lbl_sub}

    def _obtener_cobertura_seleccionada(self):
        txt = self.combo_cobertura.get()
        if "15" in txt:
            return 15
        elif "45" in txt:
            return 45
        elif "60" in txt:
            return 60
        return 30

    def ejecutar_analisis(self):
        """Ejecuta el análisis inteligente a través de ReposicionService."""
        cobertura = self._obtener_cobertura_seleccionada()
        self.datos_analisis = ReposicionService.analizar_reposicion(
            dias_analisis=30,
            dias_cobertura_deseada=cobertura,
            solo_requieren_reposicion=False
        )

        resumen = self.datos_analisis["resumen"]

        # Actualizar KPIs
        self.kpi_criticos["valor"].config(text=str(resumen["total_por_reponer"]))
        self.kpi_criticos["sub"].config(text=f"{resumen['total_criticos']} agotados | {resumen['total_urgentes']} urgentes")

        self.kpi_unidades["valor"].config(text=f"{resumen['unidades_totales_sugeridas']} un.")
        self.kpi_unidades["sub"].config(text=f"Para {cobertura} días de demanda estimada")

        self.kpi_inversion["valor"].config(text=f"S/ {resumen['inversion_total_estimada']:,.2f}")
        self.kpi_inversion["sub"].config(text="Costo estimado a precio de compra")

        self.kpi_proveedores["valor"].config(text=str(resumen["total_proveedores_involucrados"]))
        self.kpi_proveedores["sub"].config(text="Distribuidores mayoristas")

        # Cargar lista de proveedores en selector
        provs = ["(Todos los Proveedores)"] + sorted(list({
            s["proveedor_nombre"] for s in self.datos_analisis["sugerencias"] if s.get("proveedor_nombre")
        }))
        self.combo_proveedor["values"] = provs
        if not self.combo_proveedor.get():
            self.combo_proveedor.current(0)

        self._aplicar_filtros()

    def _aplicar_filtros(self):
        """Filtra la lista de recomendaciones según los criterios seleccionados."""
        if not self.datos_analisis:
            return

        for it in self.tree.get_children():
            self.tree.delete(it)

        filtro_urg = self.combo_urgencia.get()
        filtro_prov = self.combo_proveedor.get()
        busqueda = self.entry_buscar.get().strip().lower()

        todas = self.datos_analisis["sugerencias"]
        filtradas = []

        for s in todas:
            # Filtro Urgencia
            if "Todos los que requieren" in filtro_urg and not s["requiere_reposicion"]:
                continue
            elif "Solo Críticos" in filtro_urg and s["nivel_urgencia"] != "CRITICO":
                continue
            elif "Urgentes" in filtro_urg and s["nivel_urgencia"] != "URGENTE":
                continue
            elif "Mínimo Alcanzado" in filtro_urg and s["nivel_urgencia"] != "ALERTA":
                continue
            elif "Preventivos" in filtro_urg and s["nivel_urgencia"] != "PREVENTIVO":
                continue

            # Filtro Proveedor
            if filtro_prov and filtro_prov != "(Todos los Proveedores)":
                if s["proveedor_nombre"] != filtro_prov:
                    continue

            # Filtro Búsqueda
            if busqueda:
                campos_texto = f"{s['codigo']} {s['nombre']} {s['marca']} {s['categoria_nombre']}".lower()
                if busqueda not in campos_texto:
                    continue

            filtradas.append(s)

        self.sugerencias_filtradas = filtradas

        foco_item_id = None
        for s in filtradas:
            autonomia_txt = f"{s['dias_autonomia']:.1f} d" if s['dias_autonomia'] is not None else "-"
            valores = (
                s["id"],
                s["urgencia_label"],
                s["codigo"],
                s["nombre"],
                s["categoria_nombre"],
                s["marca"],
                s["stock_actual"],
                s["stock_minimo"],
                s["unidades_vendidas_periodo"],
                f"{s['demanda_diaria']:.2f} /d",
                autonomia_txt,
                f"+{s['cantidad_sugerida']}" if s['cantidad_sugerida'] > 0 else "0",
                f"S/ {s['precio_compra']:.2f}",
                f"S/ {s['costo_estimado']:.2f}",
                s["proveedor_nombre"]
            )
            item_id = self.tree.insert("", "end", values=valores, tags=(s["nivel_urgencia"],))
            if self.producto_id_foco and s["id"] == self.producto_id_foco:
                foco_item_id = item_id

        if foco_item_id:
            self.tree.selection_set(foco_item_id)
            self.tree.see(foco_item_id)
            self._on_producto_seleccionado()

    def _on_producto_seleccionado(self, event=None):
        seleccion = self.tree.selection()
        if not seleccion:
            self.item_seleccionado = None
            self.btn_orden_compra.config(state="disabled")
            return

        item_row = self.tree.item(seleccion[0])
        prod_id = item_row["values"][0]

        # Buscar el objeto completo
        for s in self.sugerencias_filtradas:
            if s["id"] == prod_id:
                self.item_seleccionado = s
                break

        if not self.item_seleccionado:
            return

        s = self.item_seleccionado
        self.lbl_justificacion.config(
            text=f"📋 Análisis de Reposición para [{s['codigo']}] {s['nombre']}:\n{s['justificacion']}"
        )

        p_nom = s["proveedor_nombre"]
        p_tel = s["proveedor_telefono"]
        p_em = s["proveedor_email"]
        p_cont = s["proveedor_contacto"]

        if p_nom and p_nom != "(Sin proveedor asignado)":
            self.lbl_contacto_proveedor.config(
                text=f"🏢 Proveedor Sugerido: {p_nom} | Contacto: {p_cont} | 📞 Tel: {p_tel} | ✉ Email: {p_em}"
            )
        else:
            self.lbl_contacto_proveedor.config(
                text="⚠ Este producto no tiene un proveedor preferido asignado en el catálogo. Puede asignarlo desde Inventario."
            )

        if s["cantidad_sugerida"] > 0:
            self.btn_orden_compra.config(state="normal")
        else:
            self.btn_orden_compra.config(state="disabled")

    def _registrar_entrada_directa(self):
        """Inicia el registro de entrada de mercadería con los datos sugeridos."""
        if not self.item_seleccionado:
            return

        s = self.item_seleccionado
        if self.on_registrar_entrada:
            self.destroy()
            self.on_registrar_entrada(
                producto_id=s["id"],
                cantidad=s["cantidad_sugerida"],
                proveedor_id=s["proveedor_id"]
            )
        else:
            messagebox.showinfo(
                "Sugerencia de Reposición",
                f"Se recomienda adquirir {s['cantidad_sugerida']} unidad(es) de [{s['codigo']}] {s['nombre']}\n"
                f"al proveedor {s['proveedor_nombre']}.\n"
                f"Puede ingresar al módulo 'Movimientos de Stock' para registrar la entrada física de mercadería.",
                parent=self
            )

    def _exportar_excel(self):
        """Exporta las sugerencias mostradas a Excel."""
        if not self.datos_analisis or not self.sugerencias_filtradas:
            messagebox.showwarning("Atención", "No hay datos para exportar en este momento.", parent=self)
            return

        datos_export = {
            "resumen": self.datos_analisis["resumen"],
            "sugerencias": self.sugerencias_filtradas
        }

        try:
            ok, ruta = ExcelService.exportar_asistente_reposicion(datos_export)
            if ok:
                msg = f"Reporte de reposición generado con éxito:\n\n{ruta}\n\n¿Desea abrir la carpeta contenedora?"
                resp = messagebox.askyesno("Exportación Exitosa", msg, parent=self)
                if resp:
                    import os
                    os.startfile(os.path.dirname(ruta))
        except Exception as e:
            messagebox.showerror("Error al Exportar", f"No se pudo generar el archivo Excel:\n{e}", parent=self)

