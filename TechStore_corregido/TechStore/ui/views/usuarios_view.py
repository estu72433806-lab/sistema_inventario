"""
Vista de Gestión de Usuarios y Permisos del Sistema.
Accesible únicamente para usuarios con rol de Administrador.
Diseñada para ser clara, intuitiva y fácil de usar, permitiendo:
- Comprender claramente qué puede hacer cada rol (Administrador vs Vendedor).
- Sugerir automáticamente nombres de usuario (login) y contraseñas seguras.
- Ordenar la tabla de usuarios por cualquier columna (ID, nombre, rol, estado, fecha).
- Filtrar por búsqueda en tiempo real, rol o estado (activos/inactivos).
- Registrar nuevos usuarios, editar roles, cambiar contraseñas y desactivar o reactivar cuentas.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from models.usuario import UsuarioModel
from ui.theme import Color
from ui.widgets import Formulario

class UsuariosView(ttk.Frame):
    ROL_VENDEDOR_DISPLAY = "🛒 Vendedor (Ventas y Atención al Cliente)"
    ROL_ADMIN_DISPLAY = "👑 Administrador (Control Total del Negocio)"

    def __init__(self, parent, usuario_sesion):
        super().__init__(parent)
        self.usuario_sesion = usuario_sesion
        self.usuario_seleccionado_id = None
        self.modo_edicion = False

        # Estado de ordenamiento de la tabla
        self.columna_orden_actual = "id"
        self.orden_dir_actual = "ASC"

        self._construir_ui()
        self.cargar_usuarios()

    def _construir_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # 1. Banner Superior Informativo
        frame_banner = tk.Frame(self, bg=Color.OSCURO, padx=16, pady=10)
        frame_banner.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))

        lbl_banner_tit = tk.Label(
            frame_banner,
            text="👤 Gestión de Personal y Control de Acceso por Roles",
            font=("Segoe UI", 11, "bold"),
            fg=Color.ACENTO_CLARO,
            bg=Color.OSCURO
        )
        lbl_banner_tit.pack(anchor="w")

        lbl_banner_sub = tk.Label(
            frame_banner,
            text="Crea cuentas para tus empleados y asígnales el rol adecuado. Los vendedores pueden emitir ventas sin ver los precios de compra ni las utilidades.",
            font=("Segoe UI", 8),
            fg=Color.GRIS_CLARO,
            bg=Color.OSCURO
        )
        lbl_banner_sub.pack(anchor="w", pady=(2, 0))

        # 2. Panel izquierdo: formulario de usuario con explicación de roles
        form = Formulario(self, "Registrar nuevo usuario")
        form.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=5)
        self.frame_form = form

        form.seccion("Datos personales")
        self.ent_nombre = form.campo("ent_nombre", "Nombre completo",
                                     ttk.Entry(form, width=32), requerido=True)
        self.ent_nombre.bind("<FocusOut>", self._on_nombre_focus_out)

        form.seccion("Acceso al sistema")
        frame_user_gen = ttk.Frame(form)
        self.ent_username = ttk.Entry(frame_user_gen, width=20)
        self.ent_username.pack(side="left", fill="x", expand=True)
        self.btn_sugerir_user = ttk.Button(frame_user_gen, text="Sugerir login",
                                           command=self._sugerir_login_automatico, width=13)
        self.btn_sugerir_user.pack(side="left", padx=(6, 0))
        form.campo("ent_username", "Nombre de usuario (login)", frame_user_gen, requerido=True)

        self.combo_rol = form.campo("combo_rol", "Rol asignado", ttk.Combobox(
            form, values=[self.ROL_VENDEDOR_DISPLAY, self.ROL_ADMIN_DISPLAY],
            state="readonly", width=30), requerido=True)
        self.combo_rol.current(0)  # Vendedor por defecto
        self.combo_rol.bind("<<ComboboxSelected>>", self._on_rol_cambiado)

        # Tarjeta dinámica con los permisos del rol seleccionado
        self.frame_permisos = tk.Frame(form, bg=Color.FONDO, padx=10, pady=8, relief="solid", bd=1)
        form.ancho(self.frame_permisos, pady=(2, 6))
        self.lbl_permisos_tit = tk.Label(self.frame_permisos, text="", font=("Segoe UI", 9, "bold"), bg=Color.FONDO)
        self.lbl_permisos_tit.pack(anchor="w")
        self.lbl_permisos_desc = tk.Label(self.frame_permisos, text="", font=("Segoe UI", 8), bg=Color.FONDO,
                                          fg=Color.TEXTO_SUAVE, justify="left", wraplength=290)
        self.lbl_permisos_desc.pack(anchor="w", pady=(2, 4))
        self.lbl_permisos_items = tk.Label(self.frame_permisos, text="", font=("Segoe UI", 8), bg=Color.FONDO,
                                           justify="left")
        self.lbl_permisos_items.pack(anchor="w")

        form.seccion("Contraseña")
        frame_pwd = ttk.Frame(form)
        self.ent_pwd = ttk.Entry(frame_pwd, show="•", width=18, font=("Segoe UI", 9))
        self.ent_pwd.pack(side="left", fill="x", expand=True)
        self.btn_ver_pwd = ttk.Button(frame_pwd, text="Ver", width=5, command=self._toggle_ver_pwd)
        self.btn_ver_pwd.pack(side="left", padx=(6, 0))
        self.btn_gen_pwd = ttk.Button(frame_pwd, text="Generar", width=8, command=self._sugerir_password_automatico)
        self.btn_gen_pwd.pack(side="left", padx=(4, 0))
        form.campo("ent_pwd", "Contraseña", frame_pwd, requerido=True, ayuda="Mínimo 4 caracteres")
        self.lbl_pwd_hint = form.ayudas["ent_pwd"]

        botones = form.acciones([
            ("guardar", "Registrar usuario", self.guardar_usuario, "primario"),
            ("nuevo", "Modo nuevo usuario", self.modo_nuevo_usuario, "secundario"),
            ("cambiar_pwd", "Cambiar contraseña", self.cambiar_password_usuario, "secundario"),
            ("desactivar", "Desactivar usuario", self.desactivar_usuario, "peligro"),
            ("reactivar", "Reactivar usuario", self.reactivar_usuario, "exito"),
            ("limpiar", "Limpiar campos", self.limpiar_formulario, "neutro"),
        ])
        self.btn_guardar = botones["guardar"]
        self.btn_nuevo = botones["nuevo"]
        self.btn_cambiar_pwd = botones["cambiar_pwd"]
        self.btn_desactivar = botones["desactivar"]
        self.btn_reactivar = botones["reactivar"]
        self.btn_limpiar = botones["limpiar"]

        # 3. Panel Derecho: Tabla de Usuarios con Filtros y Ordenamiento
        frame_derecho = ttk.LabelFrame(self, text=" Cuentas de Usuario Registradas en la Tienda ", padding=10)
        frame_derecho.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=5)
        frame_derecho.rowconfigure(1, weight=1)
        frame_derecho.columnconfigure(0, weight=1)

        # Barra de Búsqueda y Filtros
        frame_filtros = ttk.Frame(frame_derecho)
        frame_filtros.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(frame_filtros, text="🔍 Buscar:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 4))
        self.ent_buscar = ttk.Entry(frame_filtros, width=20, font=("Segoe UI", 9))
        self.ent_buscar.pack(side="left", padx=(0, 10))
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.cargar_usuarios())

        ttk.Label(frame_filtros, text="Rol:", font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        self.combo_filtro_rol = ttk.Combobox(
            frame_filtros,
            values=["Todos los roles", "Solo Administradores", "Solo Vendedores"],
            state="readonly",
            width=18
        )
        self.combo_filtro_rol.current(0)
        self.combo_filtro_rol.pack(side="left", padx=(0, 10))
        self.combo_filtro_rol.bind("<<ComboboxSelected>>", lambda e: self.cargar_usuarios())

        ttk.Label(frame_filtros, text="Estado:", font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        self.combo_filtro_estado = ttk.Combobox(
            frame_filtros,
            values=["🟢 Solo Activos", "🔴 Solo Desactivados", "Todos los estados"],
            state="readonly",
            width=18
        )
        self.combo_filtro_estado.current(0)
        self.combo_filtro_estado.pack(side="left", padx=(0, 10))
        self.combo_filtro_estado.bind("<<ComboboxSelected>>", lambda e: self.cargar_usuarios())

        btn_reset_filtros = ttk.Button(frame_filtros, text="Limpiar Filtros", command=self._restablecer_filtros)
        btn_reset_filtros.pack(side="right")

        # Tabla (Treeview)
        frame_tabla_sub = ttk.Frame(frame_derecho)
        frame_tabla_sub.grid(row=1, column=0, sticky="nsew")
        frame_tabla_sub.rowconfigure(0, weight=1)
        frame_tabla_sub.columnconfigure(0, weight=1)

        columnas = ("id", "username", "nombre", "rol", "estado", "fecha")
        self.tree = ttk.Treeview(frame_tabla_sub, columns=columnas, show="headings", selectmode="browse")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("username", width=120, anchor="center")
        self.tree.column("nombre", width=220, anchor="w")
        self.tree.column("rol", width=130, anchor="center")
        self.tree.column("estado", width=105, anchor="center")
        self.tree.column("fecha", width=140, anchor="center")

        scroll_y = ttk.Scrollbar(frame_tabla_sub, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(frame_tabla_sub, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        # Configurar encabezados con ordenamiento interactivo
        self._actualizar_encabezados_orden()

        self.tree.bind("<<TreeviewSelect>>", self._on_usuario_seleccionado)

        # Tags de colores para estado
        self.tree.tag_configure("ACTIVO", foreground=Color.OSCURO)
        self.tree.tag_configure("INACTIVO", foreground=Color.GRIS)

        # Barra inferior de resumen
        self.lbl_resumen = ttk.Label(frame_derecho, text="", font=("Segoe UI", 8), foreground=Color.TEXTO_SUAVE)
        self.lbl_resumen.grid(row=2, column=0, sticky="w", pady=(6, 0))

        # Inicializar tarjeta de permisos con el rol por defecto
        self._on_rol_cambiado()

    def _actualizar_encabezados_orden(self):
        """Actualiza los títulos de las columnas mostrando la flecha de ordenación activa."""
        titulos = {
            "id": "ID",
            "username": "Usuario",
            "nombre": "Nombre Completo",
            "rol": "Rol Asignado",
            "estado": "Estado",
            "fecha": "Fecha Creación"
        }

        for col, texto in titulos.items():
            flecha = ""
            if col == self.columna_orden_actual:
                flecha = " ▲" if self.orden_dir_actual == "ASC" else " ▼"
            self.tree.heading(
                col,
                text=f"{texto}{flecha}",
                command=lambda c=col: self._ordenar_por_columna(c)
            )

    def _ordenar_por_columna(self, columna):
        """Alterna el ordenamiento ascendente/descendente al hacer clic en un encabezado."""
        if self.columna_orden_actual == columna:
            self.orden_dir_actual = "DESC" if self.orden_dir_actual == "ASC" else "ASC"
        else:
            self.columna_orden_actual = columna
            self.orden_dir_actual = "ASC"

        self._actualizar_encabezados_orden()
        self.cargar_usuarios()

    def _on_rol_cambiado(self, event=None):
        """Actualiza en tiempo real la tarjeta explicativa de permisos según el rol seleccionado."""
        rol_display = self.combo_rol.get()
        if "Administrador" in rol_display:
            self.lbl_permisos_tit.config(text="👑 Permisos: Administrador (Dueño o Gerente)", fg=Color.ACENTO_OSCURO)
            self.lbl_permisos_desc.config(
                text="Tiene autorización absoluta en el negocio. Recomendado para administradores o socios."
            )
            self.lbl_permisos_items.config(
                text="✔ Control total de inventario y modificación de precios\n"
                     "✔ Puede ver precios de costo (compra) y utilidades\n"
                     "✔ Acceso a reportes financieros y exportación a Excel\n"
                     "✔ Configuración y sincronización con la Nube\n"
                     "✔ Crear, editar y administrar usuarios y contraseñas",
                fg=Color.EXITO
            )
        else:
            self.lbl_permisos_tit.config(text="🛒 Permisos: Vendedor (Personal de Atención / Caja)", fg=Color.ADVERTENCIA_OSCURO)
            self.lbl_permisos_desc.config(
                text="Diseñado para atender al público y registrar ventas. Protege los márgenes y costos del local."
            )
            self.lbl_permisos_items.config(
                text="✔ Realizar ventas y cobros en el Punto de Venta\n"
                     "✔ Consultar stock disponible de computadoras y componentes\n"
                     "✔ Registrar clientes para comprobantes de pago\n"
                     "🔒 Precios de compra y costos OCULTOS (Protegido)\n"
                     "🔒 No puede dar de baja ni editar productos del catálogo\n"
                     "🔒 Reportes de ganancias y finanzas BLOQUEADOS\n"
                     "🔒 No puede gestionar otros usuarios",
                fg=Color.GRIS_PIZARRA
            )

    def _on_nombre_focus_out(self, event=None):
        """Sugiere automáticamente un username cuando el usuario termina de escribir su nombre."""
        if not self.modo_edicion and not self.ent_username.get().strip():
            nombre = self.ent_nombre.get().strip()
            if nombre:
                login_sug = UsuarioModel.sugerir_username(nombre)
                self.ent_username.delete(0, tk.END)
                self.ent_username.insert(0, login_sug)

    def _sugerir_login_automatico(self):
        nombre = self.ent_nombre.get().strip()
        login_sug = UsuarioModel.sugerir_username(nombre)
        self.ent_username.delete(0, tk.END)
        self.ent_username.insert(0, login_sug)

    def _sugerir_password_automatico(self):
        clave_sug = UsuarioModel.generar_password_seguro()
        self.ent_pwd.delete(0, tk.END)
        self.ent_pwd.insert(0, clave_sug)
        self.ent_pwd.config(show="") # Mostrar temporalmente para que la vea
        messagebox.showinfo(
            "Contraseña Segura Generada",
            f"Se ha generado la clave temporal:\n\n{clave_sug}\n\n"
            "Anótela o entréguesela al empleado para su primer inicio de sesión.",
            parent=self
        )

    def _toggle_ver_pwd(self):
        if self.ent_pwd.cget("show") == "":
            self.ent_pwd.config(show="•")
        else:
            self.ent_pwd.config(show="")

    def _restablecer_filtros(self):
        self.ent_buscar.delete(0, tk.END)
        self.combo_filtro_rol.current(0)
        self.combo_filtro_estado.current(0)
        self.cargar_usuarios()

    def cargar_usuarios(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        busqueda = self.ent_buscar.get().strip()

        # Determinar filtro de rol
        rol_sel = self.combo_filtro_rol.get()
        rol_param = None
        if "Administradores" in rol_sel:
            rol_param = "administrador"
        elif "Vendedores" in rol_sel:
            rol_param = "vendedor"

        # Determinar filtro de estado
        est_sel = self.combo_filtro_estado.get()
        if "Solo Activos" in est_sel:
            solo_activos = True
        elif "Solo Desactivados" in est_sel:
            solo_activos = "inactivos"
        else:
            solo_activos = "todos"

        usuarios = UsuarioModel.listar_usuarios(
            solo_activos=solo_activos,
            busqueda=busqueda,
            rol=rol_param,
            orden_columna=self.columna_orden_actual,
            orden_dir=self.orden_dir_actual
        )

        total_activos = 0
        total_inactivos = 0

        for u in usuarios:
            es_activo = (u["activo"] == 1)
            if es_activo:
                total_activos += 1
            else:
                total_inactivos += 1

            rol_str = "👑 Administrador" if u["rol"].lower() == "administrador" else "🛒 Vendedor"
            estado_str = "🟢 Activo" if es_activo else "🔴 Desactivado"
            tag = "ACTIVO" if es_activo else "INACTIVO"

            self.tree.insert("", "end", values=(
                u["id"],
                u["username"],
                u["nombre_completo"],
                rol_str,
                estado_str,
                u["creado_en"]
            ), tags=(tag,))

        # Actualizar resumen informativo
        self.lbl_resumen.config(
            text=f"Total: {len(usuarios)} usuario(s) listados  |  🟢 Activos: {total_activos}  |  🔴 Desactivados: {total_inactivos}"
        )

    def _on_usuario_seleccionado(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        valores = item["values"]
        if not valores:
            return

        user_id = int(valores[0])
        self.usuario_seleccionado_id = user_id
        self.modo_edicion = True

        username = str(valores[1])
        nombre = str(valores[2])
        rol_str = str(valores[3])
        estado_str = str(valores[4])

        # Actualizar formulario al modo edición
        self.frame_form.config(text=f" ✏ Modificar Usuario: {username} (ID #{user_id}) ")

        self.ent_nombre.delete(0, tk.END)
        self.ent_nombre.insert(0, nombre)

        self.ent_username.delete(0, tk.END)
        self.ent_username.insert(0, username)
        self.ent_username.config(state="disabled") # No permitir cambiar username para mantener consistencia
        self.btn_sugerir_user.config(state="disabled")

        if "Administrador" in rol_str:
            self.combo_rol.set(self.ROL_ADMIN_DISPLAY)
        else:
            self.combo_rol.set(self.ROL_VENDEDOR_DISPLAY)
        self._on_rol_cambiado()

        self.ent_pwd.delete(0, tk.END)
        self.lbl_pwd_hint.config(text="(Opcional: Dejar en blanco para mantener la contraseña actual)")

        self.btn_guardar.config(text="💾 Guardar Cambios de Usuario")

        # Controlar botones según el estado
        if "Desactivado" in estado_str:
            self.btn_desactivar.config(state="disabled")
            self.btn_reactivar.config(state="normal")
        else:
            self.btn_desactivar.config(state="normal" if user_id != 1 else "disabled")
            self.btn_reactivar.config(state="disabled")

    def modo_nuevo_usuario(self):
        """Pasa el formulario al modo de registro de un nuevo usuario."""
        self.limpiar_formulario()

    def guardar_usuario(self):
        nombre = self.ent_nombre.get().strip()
        username = self.ent_username.get().strip().lower()
        rol_sel = self.combo_rol.get()
        rol = "administrador" if "Administrador" in rol_sel else "vendedor"
        password = self.ent_pwd.get().strip()

        if self.modo_edicion:
            # Actualización de usuario existente
            if not nombre:
                messagebox.showwarning("Campo Requerido", "El nombre completo del empleado es obligatorio.", parent=self)
                return

            ok, err = UsuarioModel.actualizar_usuario(self.usuario_seleccionado_id, nombre, rol)
            if not ok:
                messagebox.showerror("Error al Actualizar", err, parent=self)
                return

            # Si ingresó contraseña nueva, actualizarla también
            if password:
                if len(password) < 4:
                    messagebox.showwarning("Contraseña Muy Corta", "La nueva contraseña debe tener al menos 4 caracteres.", parent=self)
                    return
                ok_pwd, err_pwd = UsuarioModel.cambiar_password(self.usuario_seleccionado_id, password)
                if not ok_pwd:
                    messagebox.showerror("Error en Contraseña", err_pwd, parent=self)
                    return

            messagebox.showinfo(
                "¡Usuario Actualizado!",
                f"Los datos de la cuenta '{username}' con rol [{rol.capitalize()}] se guardaron correctamente.",
                parent=self
            )
            self.cargar_usuarios()
        else:
            # Creación de nuevo usuario
            if not nombre or not username or not password:
                messagebox.showwarning(
                    "Campos Incompletos",
                    "Por favor complete todos los campos obligatorios:\n\n"
                    "• Nombre Completo\n"
                    "• Nombre de Usuario (Login)\n"
                    "• Contraseña (mínimo 4 caracteres)",
                    parent=self
                )
                return

            nuevo_id, err = UsuarioModel.crear_usuario(
                username=username,
                password=password,
                nombre_completo=nombre,
                rol=rol
            )

            if err:
                messagebox.showerror("Error al Crear Usuario", err, parent=self)
                return

            messagebox.showinfo(
                "¡Usuario Registrado con Éxito! 🎉",
                f"El colaborador '{nombre}' ha sido registrado en el sistema.\n\n"
                f"• Login: {username}\n"
                f"• Rol Asignado: {rol.capitalize()}\n\n"
                "Ya puede iniciar sesión para realizar sus funciones.",
                parent=self
            )
            self.limpiar_formulario()
            self.cargar_usuarios()

    def cambiar_password_usuario(self):
        """Abre un diálogo rápido para actualizar la contraseña del usuario seleccionado."""
        if not self.usuario_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un usuario de la tabla para cambiar su contraseña.", parent=self)
            return

        username = self.ent_username.get()
        nueva_clave = simpledialog.askstring(
            "Cambiar Contraseña",
            f"Ingrese la nueva contraseña para el usuario '{username}' (mínimo 4 caracteres):",
            show="•",
            parent=self
        )

        if nueva_clave is None:
            return # Cancelado

        nueva_clave = nueva_clave.strip()
        if len(nueva_clave) < 4:
            messagebox.showerror("Error", "La contraseña debe tener al menos 4 caracteres.", parent=self)
            return

        ok, err = UsuarioModel.cambiar_password(self.usuario_seleccionado_id, nueva_clave)
        if ok:
            messagebox.showinfo("Contraseña Actualizada", f"La contraseña de '{username}' fue cambiada exitosamente.", parent=self)
        else:
            messagebox.showerror("Error", err, parent=self)

    def desactivar_usuario(self):
        if not self.usuario_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un usuario de la tabla para desactivar.", parent=self)
            return

        if self.usuario_seleccionado_id == 1:
            messagebox.showerror("Acción Denegada", "No es posible desactivar al Administrador Principal del sistema.", parent=self)
            return

        username = self.ent_username.get()
        confirmar = messagebox.askyesno(
            "Confirmar Desactivación",
            f"¿Está seguro de desactivar la cuenta de '{username}'?\n\n"
            "El usuario no podrá iniciar sesión pero todo su historial de ventas se conservará.",
            parent=self
        )
        if confirmar:
            ok, err = UsuarioModel.desactivar_usuario(self.usuario_seleccionado_id)
            if not ok:
                messagebox.showerror("Error", err, parent=self)
            else:
                messagebox.showinfo("Usuario Desactivado", f"La cuenta de '{username}' ha sido desactivada.", parent=self)
                self.limpiar_formulario()
                self.cargar_usuarios()

    def reactivar_usuario(self):
        if not self.usuario_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un usuario desactivado para reactivar.", parent=self)
            return

        username = self.ent_username.get()
        confirmar = messagebox.askyesno(
            "Confirmar Reactivación",
            f"¿Desea reactivar la cuenta de '{username}' para que vuelva a iniciar sesión?",
            parent=self
        )
        if confirmar:
            ok, err = UsuarioModel.reactivar_usuario(self.usuario_seleccionado_id)
            if not ok:
                messagebox.showerror("Error", err, parent=self)
            else:
                messagebox.showinfo("Usuario Reactivado", f"La cuenta de '{username}' está nuevamente activa.", parent=self)
                self.limpiar_formulario()
                self.cargar_usuarios()

    def limpiar_formulario(self):
        self.usuario_seleccionado_id = None
        self.modo_edicion = False
        self.tree.selection_remove(self.tree.selection())

        self.frame_form.config(text=" ➕ Registrar Nuevo Usuario ")
        self.ent_nombre.delete(0, tk.END)

        self.ent_username.config(state="normal")
        self.ent_username.delete(0, tk.END)
        self.btn_sugerir_user.config(state="normal")

        self.combo_rol.current(0) # Vendedor por defecto
        self._on_rol_cambiado()

        self.ent_pwd.delete(0, tk.END)
        self.lbl_pwd_hint.config(text="(Mínimo 4 caracteres)")

        self.btn_guardar.config(text="✔ Registrar Usuario")
        self.btn_desactivar.config(state="normal")
        self.btn_reactivar.config(state="disabled")
