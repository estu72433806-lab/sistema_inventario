"""
Vista unificada de Gestión de Contactos (Clientes y Proveedores).
Utiliza sub-pestañas para alternar entre el registro y consulta de Clientes y Proveedores.
Permite registrar, consultar, modificar y desactivar registros sin borrar el historial.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from models.cliente import ClienteModel
from ui.widgets import Formulario
from models.proveedor import ProveedorModel
from models.usuario import UsuarioModel

class ContactosView(ttk.Frame):
    def __init__(self, parent, usuario_sesion=None):
        super().__init__(parent)
        self.usuario_sesion = usuario_sesion or {"rol": "administrador"}
        self._construir_ui()

    def _construir_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Sub-pestañas para alternar entre Clientes y Proveedores en la misma pantalla
        self.sub_notebook = ttk.Notebook(self)
        self.sub_notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.tab_clientes = TabClientes(self.sub_notebook, self.usuario_sesion)
        self.tab_proveedores = TabProveedores(self.sub_notebook, self.usuario_sesion)

        self.sub_notebook.add(self.tab_clientes, text="  👥 Registro de Clientes  ")
        self.sub_notebook.add(self.tab_proveedores, text="  🏢 Registro de Proveedores  ")

    def recargar_datos(self):
        self.tab_clientes.cargar_clientes()
        self.tab_proveedores.cargar_proveedores()


class TabClientes(ttk.Frame):
    def __init__(self, parent, usuario_sesion):
        super().__init__(parent)
        self.usuario_sesion = usuario_sesion
        self.cliente_seleccionado_id = None
        self._construir_ui()
        self.cargar_clientes()

    def _construir_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Formulario de clientes
        form = Formulario(self, "Datos del Cliente")
        form.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)

        form.seccion("Identificación")
        combo_tipo = ttk.Combobox(form, values=["DNI", "RUC", "Cédula", "Pasaporte"], state="readonly", width=26)
        combo_tipo.current(0)
        form.campo("combo_tipo_doc", "Tipo de documento", combo_tipo, requerido=True)
        form.campo("entry_num_doc", "Número de documento", ttk.Entry(form, width=28), requerido=True)
        form.campo("entry_nombre", "Nombre / razón social", ttk.Entry(form, width=28), requerido=True)

        form.seccion("Contacto")
        form.campo("entry_telefono", "Teléfono / móvil", ttk.Entry(form, width=28), requerido=True)
        form.campo("entry_email", "Correo electrónico", ttk.Entry(form, width=28))
        form.campo("entry_direccion", "Dirección", ttk.Entry(form, width=28), requerido=True)

        self.widgets = form.campos

        botones = form.acciones([
            ("guardar", "Registrar cliente", self.guardar_cliente, "primario"),
            ("actualizar", "Actualizar cliente", self.actualizar_cliente, "secundario"),
            ("desactivar", "Desactivar cliente", self.desactivar_cliente, "peligro"),
            ("limpiar", "Limpiar formulario", self.limpiar_formulario, "neutro"),
        ])
        self.btn_guardar = botones["guardar"]
        self.btn_actualizar = botones["actualizar"]
        self.btn_desactivar = botones["desactivar"]
        self.btn_limpiar = botones["limpiar"]

        # Tabla y Búsqueda
        frame_tabla = ttk.Frame(self, padding=10)
        frame_tabla.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        frame_tabla.rowconfigure(1, weight=1)
        frame_tabla.columnconfigure(0, weight=1)

        frame_busqueda = ttk.Frame(frame_tabla)
        frame_busqueda.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(frame_busqueda, text="Buscar cliente:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 5))
        self.entry_buscar = ttk.Entry(frame_busqueda, width=25)
        self.entry_buscar.pack(side="left", padx=5)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.cargar_clientes())

        btn_buscar = ttk.Button(frame_busqueda, text="Buscar", command=self.cargar_clientes)
        btn_buscar.pack(side="left", padx=5)

        btn_todos = ttk.Button(frame_busqueda, text="Ver Todos", command=self._restablecer_busqueda)
        btn_todos.pack(side="left", padx=5)

        columnas = ("id", "tipo_doc", "num_doc", "nombre", "telefono", "direccion", "email")
        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("tipo_doc", text="Tipo")
        self.tree.heading("num_doc", text="N° Documento")
        self.tree.heading("nombre", text="Nombre / Razón Social")
        self.tree.heading("telefono", text="Teléfono")
        self.tree.heading("direccion", text="Dirección")
        self.tree.heading("email", text="Correo Electrónico")

        self.tree.column("id", width=35, anchor="center")
        self.tree.column("tipo_doc", width=60, anchor="center")
        self.tree.column("num_doc", width=110, anchor="center")
        self.tree.column("nombre", width=220, anchor="w")
        self.tree.column("telefono", width=100, anchor="w")
        self.tree.column("direccion", width=180, anchor="w")
        self.tree.column("email", width=150, anchor="w")

        scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        scroll_y.grid(row=1, column=1, sticky="ns")
        scroll_x.grid(row=2, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self.seleccionar_cliente)

    def cargar_clientes(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        texto = self.entry_buscar.get().strip()
        clientes = ClienteModel.listar_clientes(texto)
        for c in clientes:
            self.tree.insert("", "end", values=(
                c["id"],
                c["tipo_documento"],
                c["numero_documento"],
                c["nombre"],
                c["telefono"] or "-",
                c["direccion"] or "-",
                c["email"] or "-"
            ))

    def _restablecer_busqueda(self):
        self.entry_buscar.delete(0, tk.END)
        self.cargar_clientes()

    def seleccionar_cliente(self, event=None):
        seleccion = self.tree.selection()
        if not seleccion:
            return

        item = self.tree.item(seleccion[0])
        cliente_id = item["values"][0]
        self.cliente_seleccionado_id = cliente_id

        c = ClienteModel.obtener_por_id(cliente_id)
        if not c:
            return

        self.limpiar_formulario(limpiar_id=False)
        self.widgets["combo_tipo_doc"].set(c["tipo_documento"])
        self.widgets["entry_num_doc"].insert(0, c["numero_documento"])
        self.widgets["entry_nombre"].insert(0, c["nombre"])
        self.widgets["entry_telefono"].insert(0, c["telefono"] or "")
        self.widgets["entry_direccion"].insert(0, c["direccion"] or "")
        self.widgets["entry_email"].insert(0, c["email"] or "")

    def _obtener_datos_formulario(self):
        tipo_doc = self.widgets["combo_tipo_doc"].get()
        num_doc = self.widgets["entry_num_doc"].get().strip()
        nombre = self.widgets["entry_nombre"].get().strip()
        telefono = self.widgets["entry_telefono"].get().strip()
        direccion = self.widgets["entry_direccion"].get().strip()
        email = self.widgets["entry_email"].get().strip()

        if not num_doc or not nombre:
            messagebox.showwarning("Atención", "El número de documento y el nombre son obligatorios.", parent=self)
            return None

        return (tipo_doc, num_doc, nombre, telefono, email, direccion)

    def guardar_cliente(self):
        datos = self._obtener_datos_formulario()
        if not datos:
            return

        nuevo_id, err = ClienteModel.crear_cliente(*datos)
        if err:
            messagebox.showerror("Error al guardar", f"No se pudo registrar al cliente:\n{err}", parent=self)
        else:
            messagebox.showinfo("Éxito", "Cliente registrado exitosamente.", parent=self)
            self.limpiar_formulario()
            self.cargar_clientes()

    def actualizar_cliente(self):
        if not self.cliente_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un cliente de la lista para actualizar.", parent=self)
            return

        datos = self._obtener_datos_formulario()
        if not datos:
            return

        ok, err = ClienteModel.actualizar_cliente(self.cliente_seleccionado_id, *datos)
        if not ok:
            messagebox.showerror("Error", f"No se pudo actualizar el cliente:\n{err}", parent=self)
        else:
            messagebox.showinfo("Éxito", "Cliente actualizado correctamente.", parent=self)
            self.limpiar_formulario()
            self.cargar_clientes()

    def desactivar_cliente(self):
        if not self.cliente_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un cliente para desactivar.", parent=self)
            return

        confirmar = messagebox.askyesno(
            "Confirmar Desactivación",
            "¿Desea desactivar este cliente?\nSu historial de compras y comprobantes emitidos se conservará intacto.",
            parent=self
        )
        if confirmar:
            ok, err = ClienteModel.desactivar_cliente(self.cliente_seleccionado_id)
            if not ok:
                messagebox.showerror("Error", f"No se pudo desactivar:\n{err}", parent=self)
            else:
                messagebox.showinfo("Éxito", "Cliente desactivado correctamente (historial conservado).", parent=self)
                self.limpiar_formulario()
                self.cargar_clientes()

    def limpiar_formulario(self, limpiar_id=True):
        if limpiar_id:
            self.cliente_seleccionado_id = None
            self.tree.selection_remove(self.tree.selection())

        self.widgets["combo_tipo_doc"].current(0)
        self.widgets["entry_num_doc"].delete(0, tk.END)
        self.widgets["entry_nombre"].delete(0, tk.END)
        self.widgets["entry_telefono"].delete(0, tk.END)
        self.widgets["entry_direccion"].delete(0, tk.END)
        self.widgets["entry_email"].delete(0, tk.END)


class TabProveedores(ttk.Frame):
    def __init__(self, parent, usuario_sesion):
        super().__init__(parent)
        self.usuario_sesion = usuario_sesion
        self.proveedor_seleccionado_id = None
        self._construir_ui()
        self.cargar_proveedores()

    def _construir_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Formulario de proveedores
        form = Formulario(self, "Datos del Proveedor Mayorista")
        form.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)

        form.seccion("Identificación")
        form.campo("entry_ruc", "RUC / DNI", ttk.Entry(form, width=28), requerido=True)
        form.campo("entry_razon", "Razón social / nombre", ttk.Entry(form, width=28), requerido=True)
        form.campo("entry_contacto", "Contacto / asesor", ttk.Entry(form, width=28))

        form.seccion("Contacto")
        form.campo("entry_telefono", "Teléfono / central", ttk.Entry(form, width=28), requerido=True)
        form.campo("entry_email", "Correo electrónico", ttk.Entry(form, width=28))
        form.campo("entry_direccion", "Dirección fiscal", ttk.Entry(form, width=28), requerido=True)

        self.widgets = form.campos

        botones = form.acciones([
            ("guardar", "Registrar proveedor", self.guardar_proveedor, "primario"),
            ("actualizar", "Actualizar proveedor", self.actualizar_proveedor, "secundario"),
            ("desactivar", "Desactivar proveedor", self.desactivar_proveedor, "peligro"),
            ("limpiar", "Limpiar formulario", self.limpiar_formulario, "neutro"),
        ])
        self.btn_guardar = botones["guardar"]
        self.btn_actualizar = botones["actualizar"]
        self.btn_desactivar = botones["desactivar"]
        self.btn_limpiar = botones["limpiar"]

        # Tabla y Búsqueda
        frame_tabla = ttk.Frame(self, padding=10)
        frame_tabla.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        frame_tabla.rowconfigure(1, weight=1)
        frame_tabla.columnconfigure(0, weight=1)

        frame_busqueda = ttk.Frame(frame_tabla)
        frame_busqueda.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(frame_busqueda, text="Buscar proveedor:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 5))
        self.entry_buscar = ttk.Entry(frame_busqueda, width=25)
        self.entry_buscar.pack(side="left", padx=5)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.cargar_proveedores())

        btn_buscar = ttk.Button(frame_busqueda, text="Buscar", command=self.cargar_proveedores)
        btn_buscar.pack(side="left", padx=5)

        btn_todos = ttk.Button(frame_busqueda, text="Ver Todos", command=self._restablecer_busqueda)
        btn_todos.pack(side="left", padx=5)

        columnas = ("id", "ruc", "razon", "contacto", "telefono", "direccion", "email")
        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("ruc", text="RUC / Doc.")
        self.tree.heading("razon", text="Razón Social / Proveedor")
        self.tree.heading("contacto", text="Contacto Comercial")
        self.tree.heading("telefono", text="Teléfono")
        self.tree.heading("direccion", text="Dirección")
        self.tree.heading("email", text="Correo Electrónico")

        self.tree.column("id", width=35, anchor="center")
        self.tree.column("ruc", width=110, anchor="center")
        self.tree.column("razon", width=220, anchor="w")
        self.tree.column("contacto", width=140, anchor="w")
        self.tree.column("telefono", width=100, anchor="w")
        self.tree.column("direccion", width=180, anchor="w")
        self.tree.column("email", width=150, anchor="w")

        scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        scroll_y.grid(row=1, column=1, sticky="ns")
        scroll_x.grid(row=2, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self.seleccionar_proveedor)

    def cargar_proveedores(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        texto = self.entry_buscar.get().strip()
        proveedores = ProveedorModel.listar_proveedores(texto)
        for p in proveedores:
            self.tree.insert("", "end", values=(
                p["id"],
                p["ruc_dni"],
                p["razon_social"],
                p["contacto"] or "-",
                p["telefono"] or "-",
                p["direccion"] or "-",
                p["email"] or "-"
            ))

    def _restablecer_busqueda(self):
        self.entry_buscar.delete(0, tk.END)
        self.cargar_proveedores()

    def seleccionar_proveedor(self, event=None):
        seleccion = self.tree.selection()
        if not seleccion:
            return

        item = self.tree.item(seleccion[0])
        proveedor_id = item["values"][0]
        self.proveedor_seleccionado_id = proveedor_id

        p = ProveedorModel.obtener_por_id(proveedor_id)
        if not p:
            return

        self.limpiar_formulario(limpiar_id=False)
        self.widgets["entry_ruc"].insert(0, p["ruc_dni"])
        self.widgets["entry_razon"].insert(0, p["razon_social"])
        self.widgets["entry_contacto"].insert(0, p["contacto"] or "")
        self.widgets["entry_telefono"].insert(0, p["telefono"] or "")
        self.widgets["entry_direccion"].insert(0, p["direccion"] or "")
        self.widgets["entry_email"].insert(0, p["email"] or "")

    def _obtener_datos_formulario(self):
        ruc = self.widgets["entry_ruc"].get().strip()
        razon = self.widgets["entry_razon"].get().strip()
        contacto = self.widgets["entry_contacto"].get().strip()
        telefono = self.widgets["entry_telefono"].get().strip()
        direccion = self.widgets["entry_direccion"].get().strip()
        email = self.widgets["entry_email"].get().strip()

        if not ruc or not razon:
            messagebox.showwarning("Atención", "El RUC/DNI y la Razón Social del proveedor son obligatorios.", parent=self)
            return None

        return (ruc, razon, contacto, telefono, email, direccion)

    def guardar_proveedor(self):
        datos = self._obtener_datos_formulario()
        if not datos:
            return

        nuevo_id, err = ProveedorModel.crear_proveedor(*datos)
        if err:
            messagebox.showerror("Error al guardar", f"No se pudo registrar al proveedor:\n{err}", parent=self)
        else:
            messagebox.showinfo("Éxito", "Proveedor registrado exitosamente.", parent=self)
            self.limpiar_formulario()
            self.cargar_proveedores()

    def actualizar_proveedor(self):
        if not self.proveedor_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un proveedor de la tabla para actualizar.", parent=self)
            return

        datos = self._obtener_datos_formulario()
        if not datos:
            return

        ok, err = ProveedorModel.actualizar_proveedor(self.proveedor_seleccionado_id, *datos)
        if not ok:
            messagebox.showerror("Error", f"No se pudo actualizar el proveedor:\n{err}", parent=self)
        else:
            messagebox.showinfo("Éxito", "Proveedor actualizado correctamente.", parent=self)
            self.limpiar_formulario()
            self.cargar_proveedores()

    def desactivar_proveedor(self):
        if not self.proveedor_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un proveedor para desactivar.", parent=self)
            return

        confirmar = messagebox.askyesno(
            "Confirmar Desactivación",
            "¿Desea desactivar este proveedor?\nEl historial de entradas y compras de productos se conservará.",
            parent=self
        )
        if confirmar:
            ok, err = ProveedorModel.desactivar_proveedor(self.proveedor_seleccionado_id)
            if not ok:
                messagebox.showerror("Error", f"No se pudo desactivar el proveedor:\n{err}", parent=self)
            else:
                messagebox.showinfo("Éxito", "Proveedor desactivado correctamente (historial conservado).", parent=self)
                self.limpiar_formulario()
                self.cargar_proveedores()

    def limpiar_formulario(self, limpiar_id=True):
        if limpiar_id:
            self.proveedor_seleccionado_id = None
            self.tree.selection_remove(self.tree.selection())

        self.widgets["entry_ruc"].delete(0, tk.END)
        self.widgets["entry_razon"].delete(0, tk.END)
        self.widgets["entry_contacto"].delete(0, tk.END)
        self.widgets["entry_telefono"].delete(0, tk.END)
        self.widgets["entry_direccion"].delete(0, tk.END)
        self.widgets["entry_email"].delete(0, tk.END)
