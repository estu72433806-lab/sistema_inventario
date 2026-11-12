"""
Diálogo de Configuración de PostgreSQL en la Nube / Servidor Central.
Diseñado para ser 100% entendible y asistido, incluso para usuarios que nunca
han configurado una base de datos o sistema de inventario.
Permite configurar mediante asistente de URL o campos directos de forma segura
sin exponer contraseñas en el código fuente.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from database.pg_config import obtener_configuracion_pg, guardar_configuracion_pg, parse_connection_string, tiene_credenciales_pg
from database.pg_db import probar_conexion_pg
from services.sync_service import SyncService
from ui.theme import Color
from ui.widgets import Formulario

class ConfigNubeDialog(tk.Toplevel):
    def __init__(self, parent, on_guardado=None):
        super().__init__(parent)
        self.on_guardado = on_guardado
        self.title("☁ Configuración de Base de Datos en la Nube (TechStore)")
        self.geometry("640x660")
        self.minsize(580, 600)
        self.transient(parent)
        self.grab_set()

        self.config_actual = obtener_configuracion_pg()
        self.mostrar_guia = False

        self._construir_ui()
        self._actualizar_tarjeta_estado()

    def _construir_ui(self):
        # 1. Cabecera explicativa destacada
        frame_head = tk.Frame(self, bg=Color.OSCURO, padx=18, pady=12)
        frame_head.pack(fill="x")

        lbl_t = tk.Label(
            frame_head,
            text="☁ Conexión y Respaldo en la Nube (PostgreSQL)",
            font=("Segoe UI", 12, "bold"),
            fg=Color.ACENTO_CLARO,
            bg=Color.OSCURO
        )
        lbl_t.pack(anchor="w")

        lbl_sub = tk.Label(
            frame_head,
            text="Permite compartir stock y ventas entre computadoras y respaldar tus datos.\n"
                 "💡 Si no hay Internet, tu tienda continúa funcionando al 100% en Modo Local.",
            font=("Segoe UI", 8),
            fg=Color.GRIS_CLARO,
            bg=Color.OSCURO,
            justify="left"
        )
        lbl_sub.pack(anchor="w", pady=(3, 0))

        # Contenedor con scroll o directo
        frame_body = ttk.Frame(self, padding=12)
        frame_body.pack(fill="both", expand=True)

        # 2. Panel de Estado Actual (Semáforo de Conexión en Vivo)
        self.frame_estado = tk.Frame(frame_body, bg=Color.FONDO_ALT, padx=12, pady=10, relief="solid", bd=1)
        self.frame_estado.pack(fill="x", pady=(0, 10))

        frame_estado_info = tk.Frame(self.frame_estado, bg=Color.FONDO_ALT)
        frame_estado_info.pack(side="left", fill="both", expand=True)

        self.lbl_estado_icono = tk.Label(frame_estado_info, text="🟡", font=("Segoe UI Emoji", 14), bg=Color.FONDO_ALT)
        self.lbl_estado_icono.pack(side="left", padx=(0, 8))

        frame_estado_textos = tk.Frame(frame_estado_info, bg=Color.FONDO_ALT)
        frame_estado_textos.pack(side="left", fill="both", expand=True)

        self.lbl_estado_titulo = tk.Label(
            frame_estado_textos,
            text="Verificando estado...",
            font=("Segoe UI", 9, "bold"),
            bg=Color.FONDO_ALT,
            fg=Color.OSCURO
        )
        self.lbl_estado_titulo.pack(anchor="w")

        self.lbl_estado_desc = tk.Label(
            frame_estado_textos,
            text="",
            font=("Segoe UI", 8),
            bg=Color.FONDO_ALT,
            fg=Color.TEXTO_SUAVE
        )
        self.lbl_estado_desc.pack(anchor="w")

        self.btn_sync_directo = ttk.Button(
            self.frame_estado,
            text="🔄 Sincronizar Ahora",
            command=self._ejecutar_sync_inmediata
        )
        self.btn_sync_directo.pack(side="right", padx=(8, 0))

        # 3. Asistente Rápido: Pegar Cadena de Conexión (Connection String)
        frame_asistente = ttk.LabelFrame(frame_body, text=" ⚡ Asistente Rápido: Pegar Enlace de Conexión (URL) ", padding=10)
        frame_asistente.pack(fill="x", pady=(0, 10))

        lbl_asistente_info = ttk.Label(
            frame_asistente,
            text="Si usas Neon.tech, Supabase o Render, copia la URL completa de tu base de datos y pégala aquí:",
            font=("Segoe UI", 8),
            foreground=Color.TEXTO_SUAVE
        )
        lbl_asistente_info.pack(anchor="w", pady=(0, 4))

        frame_url = ttk.Frame(frame_asistente)
        frame_url.pack(fill="x")

        self.ent_url = ttk.Entry(frame_url, font=("Segoe UI", 9))
        self.ent_url.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.ent_url.insert(0, "")

        btn_desglosar = ttk.Button(
            frame_url,
            text="⚡ Desglosar URL",
            command=self._desglosar_url_conexion
        )
        btn_desglosar.pack(side="right")

        # 4. Formulario de parámetros de conexión
        form = Formulario(frame_body, "Credenciales del Servidor PostgreSQL")
        form.pack(fill="both", expand=True, pady=(0, 8))

        form.seccion("Servidor")
        self.ent_host = form.campo("ent_host", "Servidor / host", ttk.Entry(form), requerido=True)
        self.ent_host.insert(0, self.config_actual.get("pg_host", ""))
        self.ent_port = form.campo("ent_port", "Puerto", ttk.Entry(form, width=12), requerido=True)
        self.ent_port.insert(0, str(self.config_actual.get("pg_port", 5432)))
        self.ent_db = form.campo("ent_db", "Base de datos", ttk.Entry(form), requerido=True)
        self.ent_db.insert(0, self.config_actual.get("pg_database", ""))

        form.seccion("Acceso")
        self.ent_user = form.campo("ent_user", "Usuario", ttk.Entry(form), requerido=True)
        self.ent_user.insert(0, self.config_actual.get("pg_user", ""))

        frame_pwd = ttk.Frame(form)
        self.ent_pwd = ttk.Entry(frame_pwd, show="•")
        self.ent_pwd.pack(side="left", fill="x", expand=True)
        self.ent_pwd.insert(0, self.config_actual.get("pg_password", ""))
        self.btn_ver_pwd = ttk.Button(frame_pwd, text="Ver", width=5, command=self._toggle_ver_pwd)
        self.btn_ver_pwd.pack(side="right", padx=(6, 0))
        form.campo("ent_pwd", "Contraseña", frame_pwd, requerido=True)

        form.seccion("Seguridad de la conexión")
        frame_ssl = ttk.Frame(form)
        self.cb_ssl = ttk.Combobox(frame_ssl, values=["require", "prefer", "disable"], state="readonly", width=12)
        self.cb_ssl.pack(side="left")
        self.cb_ssl.set(self.config_actual.get("pg_sslmode", "require"))
        ttk.Label(frame_ssl, text="require: Neon / Supabase   ·   prefer: red local",
                  style="Nota.TLabel").pack(side="left", padx=(10, 0))
        form.campo("cb_ssl", "Modo SSL", frame_ssl)

        # 5. Guía Interactiva para Principiantes (Desplegable)
        self.frame_guia = tk.Frame(frame_body, bg=Color.FONDO, padx=10, pady=8, relief="groove", bd=1)

        self.btn_toggle_guia = ttk.Button(
            frame_body,
            text="💡 ¿Para qué sirve la Nube y cómo tener una gratis? (Clic para ver guía)",
            command=self._toggle_guia
        )
        self.btn_toggle_guia.pack(fill="x", pady=(2, 6))

        texto_guia = (
            "📌 1. ¿Para qué sirve?\n"
            "   Si tienes varias computadoras en tu tienda de computadoras (ej. una en mostrador y otra en caja),\n"
            "   todas comparten el mismo stock en tiempo real. Además, tus datos quedan respaldados de forma segura.\n\n"
            "🔌 2. ¿Qué pasa si no hay Internet o se corta la luz?\n"
            "   ¡Absolutamente nada! El sistema continúa vendiendo en tu computadora (SQLite Local).\n"
            "   Cuando vuelva el Internet, presionas 'Sincronizar' y todo se actualiza sin duplicados.\n\n"
            "🆓 3. ¿Cómo tener una base de datos en la nube gratis en 2 minutos?\n"
            "   1) Entra en tu navegador a https://neon.tech o https://supabase.com y crea una cuenta gratis.\n"
            "   2) Crea un proyecto nuevo de PostgreSQL.\n"
            "   3) Copia la 'Connection String' (empieza con postgresql://...).\n"
            "   4) Pégala en el Asistente Rápido de arriba y presiona '⚡ Desglosar URL'."
        )
        lbl_guia_detalle = tk.Label(
            self.frame_guia,
            text=texto_guia,
            font=("Segoe UI", 8),
            bg=Color.FONDO,
            fg=Color.GRIS_PIZARRA,
            justify="left"
        )
        lbl_guia_detalle.pack(anchor="w")

        # 6. Botones de Acción Inferiores
        frame_acciones = ttk.Frame(self, padding=(15, 0, 15, 12))
        frame_acciones.pack(fill="x", side="bottom")

        btn_probar = ttk.Button(frame_acciones, text="🔍 Probar Conexión", command=self.probar_conexion)
        btn_probar.pack(side="left")

        btn_cancelar = ttk.Button(frame_acciones, text="Cerrar", command=self.destroy)
        btn_cancelar.pack(side="right", padx=(5, 0))

        btn_guardar = ttk.Button(frame_acciones, text="💾 Guardar Parámetros", command=self.guardar_configuracion)
        btn_guardar.pack(side="right")

    def _actualizar_tarjeta_estado(self):
        """Actualiza el panel visual del estado de conexión de la nube."""
        try:
            pendientes = SyncService.obtener_conteo_pendientes()
            info = SyncService.obtener_info_ultima_sincronizacion()
            ult_sync = info.get("ultima_sincronizacion", "Sin registros previos")

            tiene_cred = tiene_credenciales_pg()

            if not tiene_cred:
                self.lbl_estado_icono.config(text="⚪")
                self.lbl_estado_titulo.config(
                    text="Nube No Configurada (Operando 100% en Modo Local)",
                    fg=Color.TEXTO_SUAVE
                )
                self.lbl_estado_desc.config(
                    text=f"Todos tus datos se guardan en esta PC (SQLite). Tienes {pendientes} registro(s) locales."
                )
                return

            modo, detalle = SyncService.obtener_estado_conexion()
            if modo == "EN_LINEA":
                self.lbl_estado_icono.config(text="🟢")
                self.lbl_estado_titulo.config(
                    text="Conexión en Línea Activa con la Nube (PostgreSQL)",
                    fg=Color.EXITO
                )
                if pendientes == 0:
                    self.lbl_estado_desc.config(
                        text=f"✔ Tu inventario y ventas están 100% sincronizados. Última sincronización: {ult_sync}"
                    )
                else:
                    self.lbl_estado_desc.config(
                        text=f"⚠ Tienes {pendientes} registro(s) pendiente(s) por subir a la nube. Presiona 'Sincronizar Ahora'."
                    )
            else:
                self.lbl_estado_icono.config(text="🟡")
                self.lbl_estado_titulo.config(
                    text="Modo Local Activo (Servidor en la Nube no responde o sin Internet)",
                    fg=Color.ADVERTENCIA_OSCURO
                )
                self.lbl_estado_desc.config(
                    text=f"Puedes seguir vendiendo con normalidad. Tienes {pendientes} registro(s) pendientes de subir."
                )
        except Exception as e:
            self.lbl_estado_titulo.config(text="Estado de la Nube", fg=Color.TEXTO_SUAVE)
            self.lbl_estado_desc.config(text=str(e))

    def _toggle_guia(self):
        """Muestra u oculta la guía educativa para principiantes."""
        if self.mostrar_guia:
            self.frame_guia.pack_forget()
            self.btn_toggle_guia.config(text="💡 ¿Para qué sirve la Nube y cómo tener una gratis? (Clic para ver guía)")
            self.mostrar_guia = False
        else:
            self.frame_guia.pack(fill="x", pady=(0, 6), before=self.btn_toggle_guia)
            self.btn_toggle_guia.config(text="▲ Ocultar guía de ayuda")
            self.mostrar_guia = True

    def _desglosar_url_conexion(self):
        """Parsea una URL de tipo postgresql://... y llena automáticamente el formulario."""
        url_texto = self.ent_url.get().strip()
        if not url_texto:
            messagebox.showwarning(
                "URL Vacía",
                "Por favor pegue la URL o Connection String que le proporcionó su servicio (ej. Neon o Supabase).\n\n"
                "Ejemplo:\npostgresql://usuario:clave@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require",
                parent=self
            )
            return

        datos, err = parse_connection_string(url_texto)
        if err:
            messagebox.showerror(
                "Error al Desglosar URL",
                f"No se pudo interpretar el enlace ingresado:\n\n{err}\n\n"
                "Asegúrese de que el enlace empiece con 'postgresql://' o 'postgres://'.",
                parent=self
            )
            return

        # Rellenar campos del formulario
        self.ent_host.delete(0, tk.END)
        self.ent_host.insert(0, datos["pg_host"])

        self.ent_port.delete(0, tk.END)
        self.ent_port.insert(0, str(datos["pg_port"]))

        self.ent_db.delete(0, tk.END)
        self.ent_db.insert(0, datos["pg_database"])

        self.ent_user.delete(0, tk.END)
        self.ent_user.insert(0, datos["pg_user"])

        self.ent_pwd.delete(0, tk.END)
        self.ent_pwd.insert(0, datos["pg_password"])

        self.cb_ssl.set(datos.get("pg_sslmode", "require"))

        messagebox.showinfo(
            "¡Desglose Exitoso!",
            f"Se extrajeron correctamente los parámetros:\n\n"
            f"• Servidor: {datos['pg_host']}\n"
            f"• Base de Datos: {datos['pg_database']}\n"
            f"• Usuario: {datos['pg_user']}\n"
            f"• Modo SSL: {datos['pg_sslmode']}\n\n"
            "Ahora presione '🔍 Probar Conexión' para comprobar el acceso.",
            parent=self
        )

    def _ejecutar_sync_inmediata(self):
        """Ejecuta la sincronización en vivo y actualiza la tarjeta de estado."""
        self.btn_sync_directo.config(state="disabled", text="⏳ Sincronizando...")
        self.update_idletasks()
        try:
            res = SyncService.sincronizar_todo()
            if res["exito"]:
                messagebox.showinfo(
                    "Sincronización Exitosa",
                    f"¡Operación completada con éxito!\n\n"
                    f"• Registros subidos a la nube: {res.get('subidos', 0)}\n"
                    f"• Registros actualizados desde la nube: {res.get('descargados', 0)}",
                    parent=self
                )
            else:
                messagebox.showwarning(
                    "Aviso de Sincronización",
                    f"{res.get('mensaje', 'No se pudo sincronizar')}\n\n"
                    "Recuerde que sus datos locales en esta computadora se mantienen seguros e intactos.",
                    parent=self
                )
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al sincronizar: {str(e)}", parent=self)
        finally:
            self.btn_sync_directo.config(state="normal", text="🔄 Sincronizar Ahora")
            self._actualizar_tarjeta_estado()
            if self.on_guardado:
                self.on_guardado()

    def _toggle_ver_pwd(self):
        if self.ent_pwd.cget("show") == "":
            self.ent_pwd.config(show="•")
        else:
            self.ent_pwd.config(show="")

    def _obtener_datos_formulario(self):
        try:
            puerto = int(self.ent_port.get().strip() or 5432)
        except ValueError:
            puerto = 5432

        return {
            "pg_host": self.ent_host.get().strip(),
            "pg_port": puerto,
            "pg_database": self.ent_db.get().strip(),
            "pg_user": self.ent_user.get().strip(),
            "pg_password": self.ent_pwd.get(),
            "pg_sslmode": self.cb_ssl.get().strip(),
            "timeout_segundos": 4,
            "auto_sync": True
        }

    def probar_conexion(self):
        datos = self._obtener_datos_formulario()
        if not datos["pg_host"] or not datos["pg_database"] or not datos["pg_user"]:
            messagebox.showwarning(
                "Campos Requeridos",
                "Para probar la conexión debe completar al menos:\n\n"
                "• Servidor / Host\n"
                "• Base de Datos\n"
                "• Usuario",
                parent=self
            )
            return

        ok, msg = probar_conexion_pg(config_override=datos)
        if ok:
            messagebox.showinfo(
                "¡Conexión Exitosa con la Nube! 🟢",
                f"¡Excelente! El sistema se conectó exitosamente al servidor PostgreSQL:\n\n"
                f"{msg}\n\n"
                "Ya puedes presionar '💾 Guardar Parámetros' para activar la sincronización.",
                parent=self
            )
            self._actualizar_tarjeta_estado()
        else:
            diagnostico = self._generar_diagnostico_amigable(msg)
            messagebox.showerror(
                "Fallo al Conectar con la Nube 🔴",
                f"No se pudo establecer comunicación con el servidor remoto:\n\n"
                f"{msg}\n\n"
                f"🔍 Ayuda y Diagnóstico:\n{diagnostico}",
                parent=self
            )

    def _generar_diagnostico_amigable(self, msg_tecnico: str) -> str:
        """Traduce errores crípticos de base de datos a explicaciones claras en español."""
        m = msg_tecnico.lower()
        if "timeout" in m or "tiempo de espera" in m or "name or service not known" in m or "could not translate host name" in m:
            return (
                "• Verifica que tu computadora tenga conexión a Internet activa.\n"
                "• Revisa que la dirección del Host / Servidor esté bien escrita sin espacios adicionales."
            )
        elif "password authentication failed" in m or "authentication failed" in m:
            return (
                "• El usuario o la contraseña ingresados son incorrectos.\n"
                "• Si copiaste la contraseña, verifica que no tenga un espacio accidental al inicio o al final."
            )
        elif "database" in m and "does not exist" in m:
            return (
                "• El nombre de la base de datos no existe en el servidor remoto.\n"
                "• En servicios como Neon, la base de datos por defecto suele llamarse 'neondb'."
            )
        elif "ssl" in m or "no encryption" in m:
            return (
                "• Servicios en la nube como Neon y Supabase exigen conexión cifrada SSL.\n"
                "• Selecciona Modo SSL: 'require'."
            )
        else:
            return (
                "• Comprueba tus credenciales o vuelve a copiar la Cadena de Conexión (URL) desde tu proveedor.\n"
                "• Si no tienes internet ahora, no te preocupes: tu tienda sigue operando en Modo Local."
            )

    def guardar_configuracion(self):
        datos = self._obtener_datos_formulario()
        ok, msg = guardar_configuracion_pg(datos)
        if ok:
            messagebox.showinfo(
                "Guardado Exitoso",
                "¡Parámetros de conexión guardados con éxito!\n\n"
                "El archivo 'config_db.json' fue actualizado de forma segura (ignorado por git).\n"
                "El sistema ahora utilizará esta configuración para sincronizar tu inventario y ventas.",
                parent=self
            )
            if self.on_guardado:
                self.on_guardado()
            self.destroy()
        else:
            messagebox.showerror("Error al Guardar", msg, parent=self)
