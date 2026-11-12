"""
Vista de Gestión de Productos e Inventario con restricciones por rol de usuario.
Permite registrar, consultar, modificar y desactivar productos sin borrar el historial relacionado.
Muestra alertas cuando el stock es igual o menor al stock mínimo y permite consultar el historial (Kardex).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from models.producto import ProductoModel
from models.proveedor import ProveedorModel
from models.movimiento_stock import MovimientoStockModel
from models.usuario import UsuarioModel
from ui.theme import Color, FUENTE
from ui.widgets import Formulario

class ProductosView(ttk.Frame):
    def __init__(self, parent, usuario_sesion=None, on_registrar_entrada=None):
        super().__init__(parent)
        self.usuario_sesion = usuario_sesion or {"rol": "administrador", "id": 1}
        self.on_registrar_entrada = on_registrar_entrada
        self.producto_seleccionado_id = None
        self.categorias_cache = []
        self.proveedores_cache = []
        self._construir_ui()
        self._aplicar_permisos_rol()
        self.cargar_selectores()
        self.cargar_productos()

    def _construir_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Panel izquierdo: formulario de registro / edición
        form = Formulario(self, "Datos del Producto")
        form.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)

        form.seccion("Identificación")
        frame_sku = ttk.Frame(form)
        self.btn_sugerir_sku = ttk.Button(frame_sku, text="Sugerir SKU", command=self.sugerir_sku, width=13)
        entry_codigo = ttk.Entry(frame_sku, width=18)
        entry_codigo.pack(side="left", fill="x", expand=True)
        self.btn_sugerir_sku.pack(side="left", padx=(6, 0))
        form.campo("entry_codigo", "Código / SKU", frame_sku, requerido=True)
        form.campo("entry_nombre", "Nombre del producto", ttk.Entry(form, width=28), requerido=True)
        form.campo("combo_categoria", "Categoría", ttk.Combobox(form, state="readonly", width=26), requerido=True)
        form.campo("entry_marca", "Marca / fabricante", ttk.Entry(form, width=28))
        form.campo("combo_proveedor", "Proveedor preferido", ttk.Combobox(form, state="readonly", width=26))

        form.seccion("Precios")
        form.campo("entry_pcompra", "Precio de compra (S/)", ttk.Entry(form, width=28), requerido=True)
        form.campo("entry_pventa", "Precio de venta (S/)", ttk.Entry(form, width=28), requerido=True)

        form.seccion("Inventario")
        form.campo("entry_stock", "Stock actual", ttk.Entry(form, width=28), requerido=True)
        form.campo("entry_stock_min", "Stock mínimo (alerta)", ttk.Entry(form, width=28), requerido=True)

        form.seccion("Detalle")
        form.campo("entry_desc", "Descripción", tk.Text(form, width=28, height=3, font=(FUENTE, 9)))

        self.widgets = form.campos
        self.widgets["entry_codigo"] = entry_codigo

        # Auto-sugerencia de SKU al seleccionar categoría o salir del campo marca
        self.widgets["combo_categoria"].bind("<<ComboboxSelected>>", self._on_cambio_categoria_o_marca)
        self.widgets["entry_marca"].bind("<FocusOut>", self._on_cambio_categoria_o_marca)

        botones = form.acciones([
            ("guardar", "Guardar nuevo producto", self.guardar_producto, "primario"),
            ("actualizar", "Actualizar producto", self.actualizar_producto, "secundario"),
            ("desactivar", "Desactivar producto (baja)", self.desactivar_producto, "peligro"),
            ("historial", "Ver historial de movimientos", self.abrir_historial_producto, "secundario"),
            ("limpiar", "Limpiar campos", self.limpiar_formulario, "neutro"),
        ])
        self.btn_guardar = botones["guardar"]
        self.btn_actualizar = botones["actualizar"]
        self.btn_desactivar = botones["desactivar"]
        self.btn_historial = botones["historial"]
        self.btn_limpiar = botones["limpiar"]

        # Panel derecho: Filtros, Alerta de Stock y Tabla
        frame_tabla = ttk.Frame(self, padding=10)
        frame_tabla.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        frame_tabla.rowconfigure(2, weight=1)
        frame_tabla.columnconfigure(0, weight=1)

        frame_top = ttk.Frame(frame_tabla)
        frame_top.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(frame_top, text="Buscar producto:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 5))
        self.entry_buscar = ttk.Entry(frame_top, width=24)
        self.entry_buscar.pack(side="left", padx=5)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.cargar_productos())

        btn_buscar = ttk.Button(frame_top, text="Buscar", command=self.cargar_productos)
        btn_buscar.pack(side="left", padx=5)

        btn_mostrar_todo = ttk.Button(frame_top, text="Ver Todos", command=self._restablecer_busqueda)
        btn_mostrar_todo.pack(side="left", padx=5)

        self.btn_asistente_reposicion = ttk.Button(
            frame_top,
            text="💡 Asistente de Reposición",
            command=self.abrir_asistente_reposicion
        )
        self.btn_asistente_reposicion.pack(side="right", padx=(8, 0))

        self.lbl_alerta_stock = ttk.Label(
            frame_top,
            text="",
            foreground=Color.PELIGRO_OSCURO,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2"
        )
        self.lbl_alerta_stock.pack(side="right", padx=5)
        self.lbl_alerta_stock.bind("<Button-1>", lambda e: self.abrir_asistente_reposicion())

        # Configuración de columnas
        rol = self.usuario_sesion.get("rol", "administrador")
        es_admin = (rol == "administrador")

        if es_admin:
            columnas = ("id", "codigo", "nombre", "categoria", "marca", "proveedor", "pcompra", "pventa", "stock", "stock_min")
        else:
            columnas = ("id", "codigo", "nombre", "categoria", "marca", "proveedor", "pventa", "stock", "stock_min")

        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("codigo", text="Código SKU")
        self.tree.heading("nombre", text="Nombre / Modelo")
        self.tree.heading("categoria", text="Categoría")
        self.tree.heading("marca", text="Marca")
        self.tree.heading("proveedor", text="Proveedor")
        if es_admin:
            self.tree.heading("pcompra", text="P. Compra")
        self.tree.heading("pventa", text="P. Venta")
        self.tree.heading("stock", text="Stock")
        self.tree.heading("stock_min", text="Stock Mín.")

        self.tree.column("id", width=35, anchor="center")
        self.tree.column("codigo", width=85, anchor="center")
        self.tree.column("nombre", width=220, anchor="w")
        self.tree.column("categoria", width=130, anchor="w")
        self.tree.column("marca", width=85, anchor="w")
        self.tree.column("proveedor", width=140, anchor="w")
        if es_admin:
            self.tree.column("pcompra", width=75, anchor="e")
        self.tree.column("pventa", width=75, anchor="e")
        self.tree.column("stock", width=55, anchor="center")
        self.tree.column("stock_min", width=65, anchor="center")

        scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=2, column=0, sticky="nsew")
        scroll_y.grid(row=2, column=1, sticky="ns")
        scroll_x.grid(row=3, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self.seleccionar_producto)
        self.tree.tag_configure("stock_bajo", background=Color.PELIGRO_PALIDO, foreground=Color.PELIGRO_MUY_OSCURO)

    def _aplicar_permisos_rol(self):
        rol = self.usuario_sesion.get("rol", "administrador")
        if not UsuarioModel.tiene_permiso(rol, "eliminar_productos"):
            self.btn_desactivar.config(state="disabled")

        if not UsuarioModel.tiene_permiso(rol, "modificar_precio_compra"):
            self.widgets["entry_pcompra"].config(state="disabled")

    def cargar_selectores(self):
        # 1. Categorías
        self.categorias_cache = ProductoModel.listar_categorias()
        nombres_cat = [c["nombre"] for c in self.categorias_cache]
        self.widgets["combo_categoria"]["values"] = nombres_cat
        if nombres_cat:
            self.widgets["combo_categoria"].current(0)

        # 2. Proveedores
        self.proveedores_cache = ProveedorModel.listar_proveedores()
        nombres_prov = [f"{p['ruc_dni']} - {p['razon_social']}" for p in self.proveedores_cache]
        self.widgets["combo_proveedor"]["values"] = ["(Ninguno / No asignado)"] + nombres_prov
        self.widgets["combo_proveedor"].current(0)

    def cargar_productos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        texto = self.entry_buscar.get().strip()
        productos = ProductoModel.listar_productos(texto)
        es_admin = (self.usuario_sesion.get("rol") == "administrador")

        productos_bajo_stock = 0
        for p in productos:
            es_bajo = p["stock"] <= p["stock_minimo"]
            if es_bajo:
                productos_bajo_stock += 1
            tag = "stock_bajo" if es_bajo else ""

            if es_admin:
                valores = (
                    p["id"],
                    p["codigo"],
                    p["nombre"],
                    p["categoria_nombre"] or "-",
                    p["marca"] or "-",
                    p["proveedor_nombre"] or "-",
                    f"S/ {p['precio_compra']:.2f}",
                    f"S/ {p['precio_venta']:.2f}",
                    p["stock"],
                    p["stock_minimo"]
                )
            else:
                valores = (
                    p["id"],
                    p["codigo"],
                    p["nombre"],
                    p["categoria_nombre"] or "-",
                    p["marca"] or "-",
                    p["proveedor_nombre"] or "-",
                    f"S/ {p['precio_venta']:.2f}",
                    p["stock"],
                    p["stock_minimo"]
                )

            self.tree.insert("", "end", values=valores, tags=(tag,))

        if productos_bajo_stock > 0:
            self.lbl_alerta_stock.config(text=f"⚠ {productos_bajo_stock} producto(s) con stock igual o menor al mínimo!")
        else:
            self.lbl_alerta_stock.config(text="✔ Stock en niveles óptimos", foreground=Color.EXITO)

    def _restablecer_busqueda(self):
        self.entry_buscar.delete(0, tk.END)
        self.cargar_productos()

    def seleccionar_producto(self, event=None):
        seleccion = self.tree.selection()
        if not seleccion:
            return

        item = self.tree.item(seleccion[0])
        producto_id = item["values"][0]
        self.producto_seleccionado_id = producto_id

        p = ProductoModel.obtener_por_id(producto_id)
        if not p:
            return

        self.limpiar_formulario(limpiar_id=False)
        self.widgets["entry_codigo"].insert(0, p["codigo"])
        self.widgets["entry_nombre"].insert(0, p["nombre"])
        self.widgets["entry_marca"].insert(0, p["marca"] or "")

        es_admin = (self.usuario_sesion.get("rol") == "administrador")
        if es_admin:
            self.widgets["entry_pcompra"].insert(0, str(p["precio_compra"]))
        else:
            self.widgets["entry_pcompra"].config(state="normal")
            self.widgets["entry_pcompra"].delete(0, tk.END)
            self.widgets["entry_pcompra"].insert(0, str(p["precio_compra"]))
            self.widgets["entry_pcompra"].config(state="disabled")

        self.widgets["entry_pventa"].insert(0, str(p["precio_venta"]))
        self.widgets["entry_stock"].insert(0, str(p["stock"]))
        self.widgets["entry_stock_min"].insert(0, str(p["stock_minimo"]))
        self.widgets["entry_desc"].insert("1.0", p["descripcion"] or "")

        # Seleccionar categoría
        for idx, cat in enumerate(self.categorias_cache):
            if cat["id"] == p["categoria_id"]:
                self.widgets["combo_categoria"].current(idx)
                break

        # Seleccionar proveedor
        self.widgets["combo_proveedor"].current(0)
        if p.get("proveedor_id"):
            for idx, prov in enumerate(self.proveedores_cache):
                if prov["id"] == p["proveedor_id"]:
                    self.widgets["combo_proveedor"].current(idx + 1)
                    break

    def _obtener_datos_formulario(self):
        codigo = self.widgets["entry_codigo"].get().strip()
        nombre = self.widgets["entry_nombre"].get().strip()
        marca = self.widgets["entry_marca"].get().strip()
        pcompra_str = self.widgets["entry_pcompra"].get().strip()
        pventa_str = self.widgets["entry_pventa"].get().strip()
        stock_str = self.widgets["entry_stock"].get().strip()
        stock_min_str = self.widgets["entry_stock_min"].get().strip()
        desc = self.widgets["entry_desc"].get("1.0", tk.END).strip()

        if not codigo or not nombre:
            messagebox.showwarning("Atención", "El código y el nombre del producto son obligatorios.", parent=self)
            return None

        cat_idx = self.widgets["combo_categoria"].current()
        categoria_id = self.categorias_cache[cat_idx]["id"] if cat_idx >= 0 else None

        prov_idx = self.widgets["combo_proveedor"].current()
        proveedor_id = self.proveedores_cache[prov_idx - 1]["id"] if prov_idx > 0 else None

        try:
            pcompra = float(pcompra_str) if pcompra_str else 0.0
            pventa = float(pventa_str)
            stock = int(stock_str)
            stock_min = int(stock_min_str)
            if pcompra < 0 or pventa < 0 or stock < 0 or stock_min < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Los precios deben ser decimales y el stock números enteros no negativos.", parent=self)
            return None

        return (codigo, nombre, categoria_id, marca, pcompra, pventa, stock, stock_min, desc, proveedor_id)

    def guardar_producto(self):
        rol = self.usuario_sesion.get("rol", "administrador")
        if not UsuarioModel.tiene_permiso(rol, "gestionar_productos"):
            messagebox.showwarning("Acceso Denegado", "Su rol de Vendedor no tiene autorización para agregar nuevos productos.", parent=self)
            return

        datos = self._obtener_datos_formulario()
        if not datos:
            return

        codigo = datos[0]
        if not ProductoModel.es_codigo_disponible(codigo):
            messagebox.showwarning(
                "Código SKU Duplicado",
                f"El código SKU '{codigo}' ya está asignado a otro producto en el catálogo.\n\n"
                f"Por favor presione '⚡ Sugerir SKU' para obtener automáticamente el siguiente correlativo libre.",
                parent=self
            )
            return

        usuario_id = self.usuario_sesion.get("id")
        nuevo_id, err = ProductoModel.crear_producto(
            codigo=datos[0], nombre=datos[1], categoria_id=datos[2], marca=datos[3],
            precio_compra=datos[4], precio_venta=datos[5], stock=datos[6], stock_minimo=datos[7],
            descripcion=datos[8], proveedor_id=datos[9], usuario_id=usuario_id
        )
        if err:
            messagebox.showerror("Error al guardar", f"No se pudo guardar el producto:\n{err}", parent=self)
        else:
            messagebox.showinfo("Éxito", "Producto registrado correctamente con movimiento inicial de stock.", parent=self)
            self.limpiar_formulario()
            self.cargar_productos()

    def actualizar_producto(self):
        rol = self.usuario_sesion.get("rol", "administrador")
        if not UsuarioModel.tiene_permiso(rol, "gestionar_productos"):
            messagebox.showwarning("Acceso Denegado", "Su rol de Vendedor no tiene autorización para modificar productos.", parent=self)
            return

        if not self.producto_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione primero un producto de la tabla para actualizar.", parent=self)
            return

        datos = self._obtener_datos_formulario()
        if not datos:
            return

        codigo = datos[0]
        if not ProductoModel.es_codigo_disponible(codigo, excluir_producto_id=self.producto_seleccionado_id):
            messagebox.showwarning(
                "Código SKU Duplicado",
                f"El código SKU '{codigo}' ya está asignado a otro producto en el catálogo.\n\n"
                f"Por favor presione '⚡ Sugerir SKU' para obtener un código único libre.",
                parent=self
            )
            return

        ok, err = ProductoModel.actualizar_producto(
            producto_id=self.producto_seleccionado_id,
            codigo=datos[0], nombre=datos[1], categoria_id=datos[2], marca=datos[3],
            precio_compra=datos[4], precio_venta=datos[5], stock=datos[6], stock_minimo=datos[7],
            descripcion=datos[8], proveedor_id=datos[9]
        )
        if not ok:
            messagebox.showerror("Error al actualizar", f"No se pudo actualizar el producto:\n{err}", parent=self)
        else:
            messagebox.showinfo("Éxito", "Producto actualizado correctamente.", parent=self)
            self.limpiar_formulario()
            self.cargar_productos()

    def desactivar_producto(self):
        rol = self.usuario_sesion.get("rol", "administrador")
        if not UsuarioModel.tiene_permiso(rol, "eliminar_productos"):
            messagebox.showwarning("Acceso Denegado", "Solo los administradores pueden desactivar productos.", parent=self)
            return

        if not self.producto_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un producto para desactivar.", parent=self)
            return

        confirmar = messagebox.askyesno(
            "Confirmar Desactivación",
            "¿Está seguro de desactivar este producto?\nEl producto dejará de ofrecerse en ventas, pero todo su historial de compras, ventas y movimientos permanecerá intacto.",
            parent=self
        )
        if confirmar:
            ok, err = ProductoModel.eliminar_producto(self.producto_seleccionado_id)
            if not ok:
                messagebox.showerror("Error", f"No se pudo desactivar el producto:\n{err}", parent=self)
            else:
                messagebox.showinfo("Éxito", "Producto desactivado correctamente (historial conservado).", parent=self)
                self.limpiar_formulario()
                self.cargar_productos()

    def abrir_historial_producto(self):
        """Abre una ventana modal con el Kardex detallado del producto seleccionado."""
        if not self.producto_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione primero un producto de la tabla para ver su historial.", parent=self)
            return

        prod = ProductoModel.obtener_por_id(self.producto_seleccionado_id)
        if not prod:
            return

        modal = tk.Toplevel(self)
        modal.title(f"Historial de Movimientos (Kardex) - [{prod['codigo']}] {prod['nombre']}")
        modal.geometry("820x450")
        modal.transient(self)
        modal.grab_set()

        # Cabecera del modal
        lbl_info = ttk.Label(
            modal,
            text=f"Kardex del Producto: {prod['nombre']}\nStock Actual: {prod['stock']} | Stock Mínimo: {prod['stock_minimo']}",
            font=("Segoe UI", 10, "bold"),
            padding=10
        )
        lbl_info.pack(fill="x")

        # Tabla de movimientos
        cols = ("id", "fecha", "tipo", "cantidad", "motivo", "referencia", "proveedor", "usuario")
        tree_kardex = ttk.Treeview(modal, columns=cols, show="headings", selectmode="browse")

        tree_kardex.heading("id", text="ID")
        tree_kardex.heading("fecha", text="Fecha")
        tree_kardex.heading("tipo", text="Tipo")
        tree_kardex.heading("cantidad", text="Cant.")
        tree_kardex.heading("motivo", text="Motivo")
        tree_kardex.heading("referencia", text="Referencia")
        tree_kardex.heading("proveedor", text="Proveedor")
        tree_kardex.heading("usuario", text="Usuario")

        tree_kardex.column("id", width=35, anchor="center")
        tree_kardex.column("fecha", width=130, anchor="center")
        tree_kardex.column("tipo", width=80, anchor="center")
        tree_kardex.column("cantidad", width=55, anchor="center")
        tree_kardex.column("motivo", width=180, anchor="w")
        tree_kardex.column("referencia", width=120, anchor="center")
        tree_kardex.column("proveedor", width=140, anchor="w")
        tree_kardex.column("usuario", width=80, anchor="center")

        scroll_y = ttk.Scrollbar(modal, orient="vertical", command=tree_kardex.yview)
        tree_kardex.configure(yscrollcommand=scroll_y.set)

        tree_kardex.pack(fill="both", expand=True, padx=10, pady=10)
        scroll_y.pack(side="right", fill="y")

        tree_kardex.tag_configure("ENTRADA", foreground=Color.EXITO)
        tree_kardex.tag_configure("SALIDA", foreground=Color.PELIGRO_OSCURO)

        movimientos = MovimientoStockModel.listar_movimientos(producto_id=prod["id"], limite=200)
        for m in movimientos:
            tipo = m["tipo_movimiento"]
            signo = "+" if tipo == "ENTRADA" else "-"
            tree_kardex.insert("", "end", values=(
                m["id"],
                m["fecha"],
                tipo,
                f"{signo}{m['cantidad']}",
                m["motivo"] or "-",
                m["referencia"] or "-",
                m["proveedor_nombre"] or "-",
                m["usuario_nombre"] or "Admin"
            ), tags=(tipo,))

        btn_cerrar = ttk.Button(modal, text="Cerrar", command=modal.destroy)
        btn_cerrar.pack(pady=10)

    def sugerir_sku(self, silencioso=False):
        """Genera y propone el siguiente código SKU inteligente correlativo según categoría y marca."""
        cat_idx = self.widgets["combo_categoria"].current()
        categoria_id = self.categorias_cache[cat_idx]["id"] if cat_idx >= 0 and self.categorias_cache else None
        categoria_nombre = self.categorias_cache[cat_idx]["nombre"] if cat_idx >= 0 and self.categorias_cache else None
        marca = self.widgets["entry_marca"].get().strip()

        sku = ProductoModel.generar_sku_sugerido(
            categoria_id=categoria_id,
            marca=marca,
            categoria_nombre=categoria_nombre
        )
        self.widgets["entry_codigo"].delete(0, tk.END)
        self.widgets["entry_codigo"].insert(0, sku)

    def _on_cambio_categoria_o_marca(self, event=None):
        """Auto-propone el SKU inteligente cuando se cambia la categoría o marca si es un nuevo producto."""
        if self.producto_seleccionado_id is not None:
            return

        codigo_actual = self.widgets["entry_codigo"].get().strip()
        import re
        es_patron_sugerido = bool(re.match(r"^[A-Z0-9]{3}-[A-Z0-9]{3}-\d{3}$", codigo_actual))
        if not codigo_actual or es_patron_sugerido:
            self.sugerir_sku(silencioso=True)

    def abrir_asistente_reposicion(self, producto_id=None):
        """Abre la ventana modal del Asistente Inteligente de Reposición."""
        from ui.views.asistente_reposicion_dialog import AsistenteReposicionDialog
        AsistenteReposicionDialog(
            self,
            on_registrar_entrada=self.on_registrar_entrada,
            producto_id_foco=producto_id or self.producto_seleccionado_id
        )

    def limpiar_formulario(self, limpiar_id=True):
        if limpiar_id:
            self.producto_seleccionado_id = None
            self.tree.selection_remove(self.tree.selection())

        self.widgets["entry_codigo"].delete(0, tk.END)
        self.widgets["entry_nombre"].delete(0, tk.END)
        self.widgets["entry_marca"].delete(0, tk.END)

        self.widgets["entry_pcompra"].config(state="normal")
        self.widgets["entry_pcompra"].delete(0, tk.END)
        if self.usuario_sesion.get("rol") != "administrador":
            self.widgets["entry_pcompra"].config(state="disabled")

        self.widgets["entry_pventa"].delete(0, tk.END)
        self.widgets["entry_stock"].delete(0, tk.END)
        self.widgets["entry_stock_min"].delete(0, tk.END)
        self.widgets["entry_desc"].delete("1.0", tk.END)
        if self.categorias_cache:
            self.widgets["combo_categoria"].current(0)
        self.widgets["combo_proveedor"].current(0)
        if limpiar_id and self.categorias_cache:
            self.sugerir_sku(silencioso=True)
