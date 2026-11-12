"""
Tema visual de TechStore: paleta de colores y estilos ttk.
Para cambiar la apariencia de toda la aplicación, edita solo este archivo.
"""
from tkinter import ttk

FUENTE = "Segoe UI"


class Color:
    # Neutros de fondo y texto
    OSCURO = "#0f172a"          # encabezado, login
    OSCURO_2 = "#1e293b"        # tarjetas oscuras, texto de títulos
    FONDO = "#f8fafc"           # fondo general
    FONDO_ALT = "#f1f5f9"       # encabezados de tabla, filas alternas
    BLANCO = "#ffffff"
    BORDE = "#e2e8f0"
    TEXTO = "#0f172a"
    TEXTO_SUAVE = "#475569"
    GRIS_PIZARRA = "#334155"
    GRIS = "#94a3b8"
    GRIS_OSCURO = "#64748b"
    GRIS_CLARO = "#cbd5e1"

    # Acento principal (azul)
    ACENTO = "#0284c7"
    ACENTO_OSCURO = "#0369a1"
    ACENTO_CLARO = "#38bdf8"
    ACENTO_PALIDO = "#e0f2fe"

    # Estados
    EXITO = "#15803d"
    EXITO_2 = "#059669"
    TEAL = "#0f766e"
    ADVERTENCIA = "#f59e0b"
    ADVERTENCIA_OSCURO = "#b45309"
    AMBAR = "#d97706"
    AMBAR_TEXTO = "#92400e"
    AMBAR_PALIDO = "#fef3c7"
    AMBAR_CLARO = "#f59e0b"
    NARANJA_OSCURO = "#9a3412"
    NARANJA_PALIDO = "#ffedd5"
    PELIGRO = "#ef4444"
    PELIGRO_HOVER = "#dc2626"
    PELIGRO_OSCURO = "#b91c1c"
    PELIGRO_MUY_OSCURO = "#991b1b"
    PELIGRO_PALIDO = "#fee2e2"


def aplicar_tema(root):
    """Configura el tema ttk global sobre la ventana raíz y devuelve el objeto Style."""
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    root.configure(bg=Color.FONDO)
    style.configure(".", font=(FUENTE, 9), background=Color.FONDO, foreground=Color.TEXTO)

    # Pestañas
    style.configure("TNotebook", background=Color.FONDO, borderwidth=0)
    style.configure("TNotebook.Tab", font=(FUENTE, 9, "bold"), padding=[12, 7],
                    background=Color.BORDE, foreground=Color.TEXTO_SUAVE)
    style.map("TNotebook.Tab",
              background=[("selected", Color.BLANCO)],
              foreground=[("selected", Color.ACENTO)])

    # Botones: normal, de acción principal, peligro y éxito
    style.configure("TButton", font=(FUENTE, 9, "bold"), padding=[7, 5])
    style.map("TButton", background=[("active", Color.BORDE)])
    style.configure("Accent.TButton", background=Color.ACENTO, foreground=Color.BLANCO)
    style.map("Accent.TButton", background=[("active", Color.ACENTO_OSCURO)])
    style.configure("Danger.TButton", background=Color.PELIGRO_OSCURO, foreground=Color.BLANCO)
    style.map("Danger.TButton", background=[("active", Color.PELIGRO_HOVER)])
    style.configure("Success.TButton", background=Color.EXITO, foreground=Color.BLANCO)
    style.map("Success.TButton", background=[("active", Color.TEAL)])

    # Campos de entrada
    style.configure("TEntry", fieldbackground=Color.BLANCO, padding=4)
    style.configure("TCombobox", fieldbackground=Color.BLANCO, padding=3)

    # Tablas
    style.configure("Treeview", font=(FUENTE, 9), rowheight=25,
                    background=Color.BLANCO, fieldbackground=Color.BLANCO)
    style.configure("Treeview.Heading", font=(FUENTE, 9, "bold"),
                    background=Color.FONDO_ALT, foreground=Color.OSCURO_2, relief="flat")
    style.map("Treeview",
              background=[("selected", Color.ACENTO)],
              foreground=[("selected", Color.BLANCO)])

    # Marcos con título
    style.configure("TLabelframe", background=Color.FONDO)
    style.configure("TLabelframe.Label", font=(FUENTE, 9, "bold"),
                    foreground=Color.OSCURO_2, background=Color.FONDO)

    # Tipografía de formularios
    style.configure("Seccion.TLabel", font=(FUENTE, 8, "bold"), foreground=Color.ACENTO_OSCURO)
    style.configure("Campo.TLabel", font=(FUENTE, 9), foreground=Color.TEXTO)
    style.configure("Nota.TLabel", font=(FUENTE, 8), foreground=Color.GRIS_OSCURO)
    style.configure("Titulo.TLabel", font=(FUENTE, 13, "bold"), foreground=Color.OSCURO_2)
    style.configure("Descripcion.TLabel", font=(FUENTE, 9), foreground=Color.GRIS_OSCURO)

    # Login (fondo oscuro)
    style.configure("Login.TEntry", fieldbackground=Color.BLANCO, padding=6)
    style.configure("Login.TButton", font=(FUENTE, 11, "bold"), background=Color.ACENTO,
                    foreground=Color.BLANCO, padding=8)
    style.map("Login.TButton", background=[("active", Color.ACENTO_OSCURO)])

    return style
