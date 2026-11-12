"""
Componentes reutilizables de formulario.
Todas las vistas usan estas clases para que etiquetas, campos, secciones y
botones tengan la misma distribución y espaciado en toda la aplicación.
"""
import tkinter as tk
from tkinter import ttk

from ui.theme import Color, FUENTE

ESTILOS_BOTON = {
    "primario": "Accent.TButton",
    "peligro": "Danger.TButton",
    "exito": "Success.TButton",
    "secundario": "TButton",
    "neutro": "TButton",
}


class Formulario(ttk.LabelFrame):
    """
    Panel de formulario con dos columnas: etiquetas a la izquierda y campos a la derecha.
    Uso básico:
        form = Formulario(parent, "Datos del Cliente")
        form.seccion("Identificación")
        form.campo("entry_nombre", "Nombre completo", ttk.Entry(form), requerido=True)
        botones = form.acciones([("guardar", "Guardar", cmd, "primario")])
    """

    def __init__(self, parent, titulo):
        super().__init__(parent, text=f"  {titulo}  ", padding=(14, 8, 14, 14))
        self.columnconfigure(1, weight=1)
        self._fila = 0
        self.campos = {}
        self.etiquetas = {}
        self.ayudas = {}
        self.botones = {}

    def seccion(self, texto):
        """Título de grupo dentro del formulario (ej: IDENTIFICACIÓN)."""
        if self._fila > 0:
            self._fila += 1  # espacio antes de cada sección que no es la primera
        ttk.Label(self, text=texto.upper(), style="Seccion.TLabel").grid(
            row=self._fila, column=0, columnspan=2, sticky="w", pady=(0, 3)
        )
        self._fila += 1

    def campo(self, clave, etiqueta, widget, requerido=False, ayuda=None):
        """Agrega una fila etiqueta + campo. Devuelve el widget."""
        texto = etiqueta + (" *" if requerido else "")
        lbl = ttk.Label(self, text=texto, style="Campo.TLabel")
        lbl.grid(row=self._fila, column=0, sticky="w", padx=(0, 12), pady=3)
        widget.grid(row=self._fila, column=1, sticky="ew", pady=3)
        self._fila += 1
        if ayuda:
            nota_lbl = ttk.Label(self, text=ayuda, style="Nota.TLabel", wraplength=260, justify="left")
            nota_lbl.grid(row=self._fila, column=1, sticky="w", pady=(0, 2))
            self.ayudas[clave] = nota_lbl
            self._fila += 1
        self.campos[clave] = widget
        self.etiquetas[clave] = lbl
        return widget

    def ancho(self, widget, pady=(0, 4)):
        """Coloca un widget (texto, radios, marco) ocupando las dos columnas."""
        widget.grid(row=self._fila, column=0, columnspan=2, sticky="ew", pady=pady)
        self._fila += 1
        return widget

    def nota(self, texto):
        """Texto informativo a ancho completo."""
        ttk.Label(self, text=texto, style="Nota.TLabel", wraplength=340, justify="left").grid(
            row=self._fila, column=0, columnspan=2, sticky="w", pady=(4, 2)
        )
        self._fila += 1

    def acciones(self, lista, columnas=1):
        """
        Barra de botones al final del formulario.
        lista: [(clave, texto, comando, estilo)] con estilo en ESTILOS_BOTON.
        columnas: 1 = un botón por fila (ancho completo); 2 = dos por fila.
        Devuelve un dict {clave: boton}.
        """
        if self._fila > 0:
            self._fila += 1
        barra = ttk.Frame(self)
        barra.grid(row=self._fila, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        for c in range(columnas):
            barra.columnconfigure(c, weight=1, uniform="botones")
        for i, (clave, texto, comando, estilo) in enumerate(lista):
            fila, col = divmod(i, columnas)
            boton = ttk.Button(barra, text=texto, command=comando,
                               style=ESTILOS_BOTON.get(estilo, "TButton"))
            boton.grid(row=fila, column=col, sticky="ew", padx=2, pady=2)
            self.botones[clave] = boton
        self._fila += 1
        return self.botones


class EncabezadoVista(ttk.Frame):
    """Título y descripción breve en la parte superior de una vista."""

    def __init__(self, parent, titulo, descripcion=""):
        super().__init__(parent, padding=(12, 10, 12, 4))
        ttk.Label(self, text=titulo, style="Titulo.TLabel").pack(anchor="w")
        if descripcion:
            ttk.Label(self, text=descripcion, style="Descripcion.TLabel").pack(anchor="w", pady=(2, 0))
