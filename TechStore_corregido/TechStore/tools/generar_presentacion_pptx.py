import _path  # noqa: F401  (prepara rutas del proyecto)
"""
Script profesional para generar la presentación PowerPoint:
'Presentacion_TechStore_Exposicion.pptx'
Diseño en formato panorámico 16:9 con paleta corporativa moderna:
- Fondo oscuro Navy (#0F172A) y fondos claros (#F8FAFC)
- Acentos Azul Eléctrico (#0284C7), Verde Esmeralda (#10B981) y Ámbar (#F59E0B)
- Capturas reales de cada pantalla del sistema
- Notas del orador (Speaker Notes) integradas en cada diapositiva con el guion exacto
"""
import os
import sys

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Paleta de Colores
C_NAVY = RGBColor(15, 23, 42)       # #0F172A
C_BLUE = RGBColor(2, 132, 199)      # #0284C7
C_CYAN = RGBColor(56, 189, 248)     # #38BDF8
C_GREEN = RGBColor(16, 185, 129)    # #10B981
C_AMBER = RGBColor(245, 158, 11)    # #F59E0B
C_RED = RGBColor(239, 68, 68)       # #EF4444
C_WHITE = RGBColor(255, 255, 255)   # #FFFFFF
C_GRAY_LIGHT = RGBColor(241, 245, 249) # #F1F5F9
C_GRAY_TEXT = RGBColor(100, 116, 139)  # #64748B
C_DARK_CARD = RGBColor(30, 41, 59)  # #1E293B

def aplicar_fondo(slide, prs, color):
    """Crea un rectángulo que cubre todo el fondo de la diapositiva."""
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background() # sin borde
    return bg

def agregar_tarjeta(slide, left, top, width, height, fill_color, border_color=None):
    """Crea un contenedor tipo tarjeta."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = fill_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(1.5)
    else:
        card.line.fill.background()
    return card

def agregar_encabezado_modulo(slide, categoria, titulo, subtitulo):
    """Agrega el bloque de títulos estándar en la columna izquierda."""
    # Badge categoría
    tx_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(5.0), Inches(0.4))
    tf_c = tx_cat.text_frame
    tf_c.word_wrap = True
    p_c = tf_c.paragraphs[0]
    p_c.text = categoria.upper()
    p_c.font.name = "Segoe UI"
    p_c.font.size = Pt(9.5)
    p_c.font.bold = True
    p_c.font.color.rgb = C_BLUE

    # Título Principal
    tx_tit = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(5.0), Inches(0.9))
    tf_t = tx_tit.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = titulo
    p_t.font.name = "Segoe UI"
    p_t.font.size = Pt(18)
    p_t.font.bold = True
    p_t.font.color.rgb = C_NAVY

    # Subtítulo explicativo
    tx_sub = slide.shapes.add_textbox(Inches(0.8), Inches(1.75), Inches(4.8), Inches(0.6))
    tf_s = tx_sub.text_frame
    tf_s.word_wrap = True
    p_s = tf_s.paragraphs[0]
    p_s.text = subtitulo
    p_s.font.name = "Segoe UI"
    p_s.font.size = Pt(10)
    p_s.font.color.rgb = C_GRAY_TEXT

def agregar_bullets(slide, left, top, width, height, bullets):
    """Crea un listado de viñetas con iconos y texto estilizado."""
    tx = slide.shapes.add_textbox(left, top, width, height)
    tf = tx.text_frame
    tf.word_wrap = True
    for idx, (icono, tit, desc) in enumerate(bullets):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.space_after = Pt(10)
        p.space_before = Pt(4)

        run_ico = p.add_run()
        run_ico.text = f"{icono} "
        run_ico.font.name = "Segoe UI Emoji"
        run_ico.font.size = Pt(11)

        run_tit = p.add_run()
        run_tit.text = f"{tit}: "
        run_tit.font.name = "Segoe UI"
        run_tit.font.size = Pt(10.5)
        run_tit.font.bold = True
        run_tit.font.color.rgb = C_NAVY

        run_desc = p.add_run()
        run_desc.text = desc
        run_desc.font.name = "Segoe UI"
        run_desc.font.size = Pt(9.5)
        run_desc.font.color.rgb = RGBColor(51, 65, 85)

def insertar_captura(slide, ruta_img, left=Inches(6.0), top=Inches(1.2), width=Inches(6.5)):
    """Inserta la captura de pantalla con sombra y borde sutil."""
    if os.path.exists(ruta_img):
        # Marco de fondo para simular ventana / borde
        borde = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left - Inches(0.04), top - Inches(0.04), width + Inches(0.08), Inches(5.4) + Inches(0.08))
        borde.fill.solid()
        borde.fill.fore_color.rgb = RGBColor(226, 232, 240)
        borde.line.fill.background()

        pic = slide.shapes.add_picture(ruta_img, left, top, width=width)
        return pic
    else:
        # Placeholder si no existe
        ph = agregar_tarjeta(slide, left, top, width, Inches(5.0), C_GRAY_LIGHT)
        p = ph.text_frame.paragraphs[0]
        p.text = f"[Captura: {ruta_img}]"
        return ph

def asignar_notas_orador(slide, guion_texto, tiempo="40 seg", tip=""):
    """Inserta las notas del orador para que aparezcan en la vista del moderador de PowerPoint."""
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = (
        f"⏱️ TIEMPO ESTIMADO: {tiempo}\n\n"
        f"🎙️ GUION A PRONUNCIAR (QUÉ DECIR):\n"
        f"\"{guion_texto}\"\n\n"
        f"💡 CONSEJO PARA EL JURADO: {tip}"
    )

def generar_presentacion():
    print("Creando presentación PowerPoint 'Presentacion_TechStore_Exposicion.pptx'...")
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: PORTADA EJECUTIVA
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    aplicar_fondo(s1, prs, C_NAVY)

    # Detalle gráfico decorativo
    linea = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(1.8), Inches(1.5), Inches(0.08))
    linea.fill.solid()
    linea.fill.fore_color.rgb = C_BLUE
    linea.line.fill.background()

    # Títulos
    tx_port = s1.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(11.3), Inches(3.5))
    tf1 = tx_port.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "SISTEMA INTEGRAL DE INVENTARIO Y VENTAS (POS)"
    p0.font.name = "Segoe UI"
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = C_CYAN
    p0.space_after = Pt(8)

    p1 = tf1.add_paragraph()
    p1.text = "TECHSTORE COMPUTADORAS"
    p1.font.name = "Segoe UI"
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = C_WHITE
    p1.space_after = Pt(14)

    p2 = tf1.add_paragraph()
    p2.text = "Código SKU Inteligente • Asistente de Reposición por Demanda • Kardex • Control de Roles • Nube Híbrida"
    p2.font.name = "Segoe UI"
    p2.font.size = Pt(13)
    p2.font.color.rgb = RGBColor(203, 213, 225)
    p2.space_after = Pt(28)

    p3 = tf1.add_paragraph()
    p3.text = "💻 Desarrollado en Python 3 + SQLite + PostgreSQL + ReportLab + openpyxl"
    p3.font.name = "Segoe UI"
    p3.font.size = Pt(11)
    p3.font.color.rgb = C_GREEN

    asignar_notas_orador(
        s1,
        "Buenos días jurado y profesores. Hoy presentamos TechStore, un sistema especializado para tiendas de hardware y computación. "
        "Gestionar tecnología es complejo: los componentes son costosos, tienen múltiples marcas y un quiebre de stock significa perder ventas de miles de Soles. "
        "TechStore resuelve esto combinando alta velocidad local offline con SQLite, seguridad criptográfica y un motor analítico de inventarios.",
        tiempo="30 seg",
        tip="Comienza con tono firme y seguro. Establece el problema de la tienda desde la primera frase."
    )

    # =========================================================================
    # SLIDE 2: EL PROBLEMA EN TIENDAS DE CÓMPUTO VS LA SOLUCIÓN
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    aplicar_fondo(s2, prs, C_WHITE)

    agregar_encabezado_modulo(
        s2,
        "DIAGNÓSTICO COMERCIAL Y PROPUESTA DE VALOR",
        "El Reto en Tiendas de Hardware vs Solución TechStore",
        "Cómo el software transforma el caos operativo en rentabilidad y control total."
    )

    # Tarjeta Izquierda: Problemas Típicos
    c_prob = agregar_tarjeta(s2, Inches(0.8), Inches(2.5), Inches(5.6), Inches(4.3), RGBColor(254, 242, 242), RGBColor(254, 202, 202))
    tf_pr = c_prob.text_frame
    tf_pr.word_wrap = True
    p = tf_pr.paragraphs[0]
    p.text = "❌ PROBLEMAS EN TIENDAS TRADICIONALES"
    p.font.name = "Segoe UI"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_RED
    p.space_after = Pt(10)

    probs = [
        "• Quiebres de Stock Invisibles: Solo se enteran de que no hay memorias RAM cuando el cliente ya está en caja para pagar.",
        "• Códigos Duplicados y Desorden: Cada técnico registra los productos con nombres distintos, duplicando artículos en el catálogo.",
        "• Costos Expuestos a Empleados: Los cajeros ven los márgenes de ganancia y costos mayoristas de la tienda.",
        "• Bloqueo Total por Caída de Internet: Sistemas web en la nube dejan de facturar si se corta la conexión.",
        "• Compras a Ciegas: El dueño compra mercadería por intuición y no por demanda real proyectada."
    ]
    for pb in probs:
        p_sub = tf_pr.add_paragraph()
        p_sub.text = pb
        p_sub.font.name = "Segoe UI"
        p_sub.font.size = Pt(9.5)
        p_sub.font.color.rgb = RGBColor(69, 10, 10)
        p_sub.space_after = Pt(6)

    # Tarjeta Derecha: Solución TechStore
    c_sol = agregar_tarjeta(s2, Inches(6.8), Inches(2.5), Inches(5.7), Inches(4.3), RGBColor(240, 253, 244), RGBColor(187, 247, 208))
    tf_sol = c_sol.text_frame
    tf_sol.word_wrap = True
    p_s_tit = tf_sol.paragraphs[0]
    p_s_tit.text = "✔ LA RESPUESTA DE TECHSTORE"
    p_s_tit.font.name = "Segoe UI"
    p_s_tit.font.size = Pt(11)
    p_s_tit.font.bold = True
    p_s_tit.font.color.rgb = C_GREEN
    p_s_tit.space_after = Pt(10)

    soluciones = [
        "• Asistente Inteligente de Reposición: Proyecta la demanda de 30 días y avisa semanas antes de que se agote el stock.",
        "• Código SKU Nemotécnico: Autogeneración [CAT]-[MAR]-[001] que estandariza todo el catálogo sin duplicados.",
        "• Seguridad por Roles: Vendedores cobran con rapidez pero tienen los costos mayoristas y ganancias 100% ocultos.",
        "• Modo Híbrido Resiliente: Funciona al 100% offline en SQLite y se sincroniza a la nube en PostgreSQL con 1 clic.",
        "• Auditoría Total en Kardex: Trazabilidad por usuario, fecha y comprobante en cada entrada o salida."
    ]
    for sl in soluciones:
        p_sub = tf_sol.add_paragraph()
        p_sub.text = sl
        p_sub.font.name = "Segoe UI"
        p_sub.font.size = Pt(9.5)
        p_sub.font.color.rgb = RGBColor(20, 83, 45)
        p_sub.space_after = Pt(6)

    asignar_notas_orador(
        s2,
        "Antes de ver el software, entendamos el dolor del negocio: en una tienda de computadoras, si no tienes la tarjeta gráfica que busca el cliente gamer, pierdes una venta de 2,000 Soles al instante. Además, los sistemas web fallan si se corta el internet. TechStore nació para solucionar estos quiebres con un motor predictivo y permitir vender sin interrupciones en modo local.",
        tiempo="40 seg",
        tip="Enfócate en la pérdida de dinero que sufría la tienda antes de usar TechStore."
    )

    # =========================================================================
    # SLIDE 3: MÓDULO 1 - LOGIN Y CIBERSEGURIDAD
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    aplicar_fondo(s3, prs, C_WHITE)

    agregar_encabezado_modulo(
        s3,
        "MÓDULO 01 • CIBERSEGURIDAD Y CONTROL DE ACCESO",
        "Autenticación Criptográfica Robusta",
        "Protección de contraseñas y separación estricta de privilegios."
    )

    bullets_s3 = [
        ("🔐", "Hash PBKDF2-HMAC-SHA256", "100,000 iteraciones con salt aleatorio de 16 bytes. Cero contraseñas en texto plano."),
        ("🛡️", "Protección Anti-Rainbow", "Inmune a ataques de diccionario y filtraciones de base de datos."),
        ("👥", "Separación Estricta de Roles", "Administrador (Control total) vs Vendedor (Caja y mostrador, costos protegidos)."),
        ("⚡", "Acceso Inmediato", "Validación local en SQLite en menos de 10 milisegundos.")
    ]
    agregar_bullets(s3, Inches(0.8), Inches(2.4), Inches(4.8), Inches(4.5), bullets_s3)
    insertar_captura(s3, "capturas_guia/01_login.png", left=Inches(6.8), top=Inches(1.2), width=Inches(5.6))

    asignar_notas_orador(
        s3,
        "Iniciamos en la pantalla de acceso seguro. Aquí la prioridad es la ciberseguridad: las contraseñas nunca se almacenan en texto plano. Utilizamos PBKDF2-HMAC-SHA256 con 100,000 iteraciones y una sal criptográfica individual. Esto garantiza que aunque alguien robe el archivo de base de datos, no podrá descifrar las claves. Además, el login enruta automáticamente las vistas según el rol del usuario.",
        tiempo="35 seg",
        tip="Menciona '100,000 iteraciones con sal individual' como argumento técnico sólido."
    )

    # =========================================================================
    # SLIDE 4: MÓDULO 2 - DASHBOARD EJECUTIVO
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    aplicar_fondo(s4, prs, C_WHITE)

    agregar_encabezado_modulo(
        s4,
        "MÓDULO 02 • VISIBILIDAD GERENCIAL EN TIEMPO REAL",
        "Dashboard Ejecutivo con Métricas en Vivo",
        "Consolidado instantáneo de ventas, existencias, alertas y estado de nube."
    )

    bullets_s4 = [
        ("📊", "Cálculo Automático", "Cero botones de refrescar: métricas actualizadas tras cada venta o movimiento."),
        ("🚨", "Alerta Stock Bajo Interactiva", "Un clic en la tarjeta roja abre directamente el Asistente de Reposición."),
        ("☁️", "Monitoreo Híbrido", "Muestra si la tienda está en línea o local, y cuántos registros faltan por sincronizar."),
        ("⚡", "Accesos Directos Rápidos", "Navegación en 1 clic hacia POS, Inventario, Kardex, Contactos y Reportes.")
    ]
    agregar_bullets(s4, Inches(0.8), Inches(2.4), Inches(4.8), Inches(4.5), bullets_s4)
    insertar_captura(s4, "capturas_guia/02_dashboard.png", left=Inches(5.8), top=Inches(1.2), width=Inches(6.8))

    asignar_notas_orador(
        s4,
        "El Dashboard Ejecutivo es el panel de control del gerente. Cuatro tarjetas calculadas en tiempo real desde SQLite muestran las ventas del día, el total de componentes en catálogo, las alertas críticas de stock y el estado de la nube. Lo más valioso es que la tarjeta de 'Alerta Stock Bajo' es interactiva: al hacer un clic sobre ella, el sistema nos abre directamente el Asistente Inteligente de Reposición.",
        tiempo="40 seg",
        tip="Señala la tarjeta roja y destaca que es un atajo interactivo directo."
    )

    # =========================================================================
    # SLIDE 5: MÓDULO 3 - INVENTARIO Y SKU INTELIGENTE
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    aplicar_fondo(s5, prs, C_WHITE)

    agregar_encabezado_modulo(
        s5,
        "MÓDULO 03 • CATALOGACIÓN INTELIGENTE DE HARDWARE",
        "Generador de Código SKU Nemotécnico",
        "Estandarización automática del almacén sin códigos duplicados."
    )

    bullets_s5 = [
        ("⚡", "Algoritmo Nemotécnico", "Estructura [CAT]-[MAR]-[001] (ej. Laptops Lenovo -> 'LAP-LEN-001')."),
        ("🔒", "Garantía de Unicidad", "Valida el correlativo más alto libre en backend y aplica restricción UNIQUE en SQLite."),
        ("🗑️", "Borrado Lógico Protegido", "Desactivar un producto conserva el 100% de su historial contable y movimientos."),
        ("🔔", "Alerta de Stock Mínimo", "Detección visual cuando las existencias igualan o bajan del nivel de seguridad.")
    ]
    agregar_bullets(s5, Inches(0.8), Inches(2.4), Inches(4.8), Inches(4.5), bullets_s5)
    insertar_captura(s5, "capturas_guia/03_inventario_productos.png", left=Inches(5.8), top=Inches(1.2), width=Inches(6.8))

    asignar_notas_orador(
        s5,
        "En Inventario presentamos nuestra primera innovación: el botón '⚡ Sugerir SKU'. Al seleccionar 'Laptops' y marca 'Lenovo', el sistema extrae 'LAP' y 'LEN', revisa la base de datos y propone 'LAP-LEN-001' o el siguiente número libre. Esto agiliza enormemente el almacén y elimina errores humanos de digitación.",
        tiempo="45 seg",
        tip="Resalta que esta función fue sumamente elogiada por facilitar el trabajo operativo."
    )

    # =========================================================================
    # SLIDE 6: MÓDULO 4 - ASISTENTE DE REPOSICIÓN (LA JOYA)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    aplicar_fondo(s6, prs, C_WHITE)

    agregar_encabezado_modulo(
        s6,
        "MÓDULO 04 • MOTOR ANALÍTICO DE COMPRAS (LA JOYA)",
        "Asistente Inteligente de Reposición",
        "Modelo matemático predictivo de demanda, autonomía y presupuesto."
    )

    bullets_s6 = [
        ("📐", "Modelo Predictivo", "Demanda Diaria = Ventas 30d / 30; Autonomía = Stock / Demanda."),
        ("💰", "Cálculo de Presupuesto", "Calcula exactamente cuántas unidades pedir y cuánto dinero en Soles se requiere."),
        ("🚦", "4 Niveles de Urgencia", "🔴 Crítico (Agotado), 🟠 Urgente (< Mitad Mínimo), 🟡 Alerta, 🔵 Preventivo."),
        ("🔄", "Traspaso Directo a Kardex", "Un botón precarga producto, mayorista y cantidad en la orden de entrada.")
    ]
    agregar_bullets(s6, Inches(0.8), Inches(2.4), Inches(4.8), Inches(4.5), bullets_s6)
    insertar_captura(s6, "capturas_guia/04_asistente_reposicion.png", left=Inches(5.8), top=Inches(1.2), width=Inches(6.8))

    asignar_notas_orador(
        s6,
        "Esta pantalla es la joya analítica de TechStore. En vez de una simple alerta pasiva, nuestro software analiza las ventas de los últimos 30 días, calcula la rotación diaria y determina cuántos días de autonomía nos quedan. Además, según la cobertura elegida, calcula el presupuesto exacto en Soles y con un solo clic traslada los datos al Kardex para ingresar la compra mayorista.",
        tiempo="60 seg",
        tip="Tómate tu tiempo aquí: es la pantalla que más impacto causa ante el jurado."
    )

    # =========================================================================
    # SLIDE 7: MÓDULO 5 - KARDEX DE AUDITORÍA
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    aplicar_fondo(s7, prs, C_WHITE)

    agregar_encabezado_modulo(
        s7,
        "MÓDULO 05 • AUDITORÍA Y TRAZABILIDAD DE MERCADERÍA",
        "Movimientos de Stock y Kardex Detallado",
        "Auditoría legal y física de cada entrada de mercadería y ajuste por merma."
    )

    bullets_s7 = [
        ("📦", "Entradas Mayoristas", "Vinculación obligatoria con Proveedor Mayorista y Factura/Guía de Remisión."),
        ("🛠️", "Ajustes Técnicos de Merma", "Permite registrar componentes dañados físicamente con justificación auditada."),
        ("👤", "Trazabilidad por Usuario", "Cada fila registra quién hizo la operación, a qué hora y el motivo exacto."),
        ("🔄", "Impacto Inmediato", "El stock de SQLite se actualiza al instante protegiendo la coherencia contable.")
    ]
    agregar_bullets(s7, Inches(0.8), Inches(2.4), Inches(4.8), Inches(4.5), bullets_s7)
    insertar_captura(s7, "capturas_guia/05_movimientos_kardex.png", left=Inches(5.8), top=Inches(1.2), width=Inches(6.8))

    asignar_notas_orador(
        s7,
        "El módulo de Kardex garantiza la trazabilidad física. Maneja dos operaciones: entradas de proveedor mayorista asociadas a facturas de compra, y ajustes por pérdida o daño físico con justificación técnica. Cada movimiento queda sellado con fecha, hora y usuario responsable, evitando descuadres de almacén.",
        tiempo="35 seg",
        tip="Menciona la importancia del Kardex para auditorías tributarias y contables."
    )

    # =========================================================================
    # SLIDE 8: MÓDULO 6 - CLIENTES Y PROVEEDORES
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    aplicar_fondo(s8, prs, C_WHITE)

    agregar_encabezado_modulo(
        s8,
        "MÓDULO 06 • DIRECTORIO UNIFICADO DE CONTACTOS",
        "Gestión de Clientes y Mayoristas",
        "Directorio comercial con optimización para ventas rápidas en mostrador."
    )

    bullets_s8 = [
        ("⚡", "Venta Rápida en 5 Segundos", "Cliente por defecto 'Público General' (DNI 00000000) para cobros al paso."),
        ("🏢", "Soporte RUC Empresarial", "Registro de empresas para emisión de Facturas electrónicas con validez legal."),
        ("🤝", "Directorio de Proveedores", "Centraliza mayoristas autorizados (Deltron, Tech Global) con RUC y teléfonos."),
        ("🔍", "Búsqueda en Tiempo Real", "Filtro rápido por documento, nombre o razón social.")
    ]
    agregar_bullets(s8, Inches(0.8), Inches(2.4), Inches(4.8), Inches(4.5), bullets_s8)
    insertar_captura(s8, "capturas_guia/06_contactos.png", left=Inches(5.8), top=Inches(1.2), width=Inches(6.8))

    asignar_notas_orador(
        s8,
        "En Contactos centralizamos los compradores y mayoristas. Destacamos el cliente por defecto con DNI '00000000', que permite atender al paso en menos de 5 segundos sin frenar la cola de caja, manteniendo también el registro de clientes con RUC para facturas corporativas.",
        tiempo="30 seg",
        tip="Explica que el DNI 00000000 resuelve las colas en mostrador."
    )

    # =========================================================================
    # SLIDE 9: MÓDULO 7 - PUNTO DE VENTA (POS)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    aplicar_fondo(s9, prs, C_WHITE)

    agregar_encabezado_modulo(
        s9,
        "MÓDULO 07 • FACTURACIÓN RÁPIDA Y TRANSACCIÓN SEGURA",
        "Punto de Venta (POS) y Comprobantes PDF",
        "Control atómico de concurrencia, reversión transaccional y emisión en PDF."
    )

    bullets_s9 = [
        ("🛡️", "Validación Atómica y Rollback", "Si se intenta vender más stock del disponible, se cancela la transacción entera."),
        ("🏷️", "Descuentos Flexibles", "Aplicación de descuentos en monto fijo (S/) o porcentaje (%) con control de límites."),
        ("🧾", "Comprobantes en PDF con ReportLab", "Boletas y Facturas profesionales generadas en milisegundos con desglose e IGV."),
        ("💳", "Múltiples Métodos de Pago", "Efectivo, Tarjeta de Crédito/Débito, Transferencia Bancaria y Billeteras Digitales.")
    ]
    agregar_bullets(s9, Inches(0.8), Inches(2.4), Inches(4.8), Inches(4.5), bullets_s9)
    insertar_captura(s9, "capturas_guia/07_punto_venta_pos.png", left=Inches(5.8), top=Inches(1.2), width=Inches(6.8))

    asignar_notas_orador(
        s9,
        "El Punto de Venta es el corazón operativo. Aquí resaltamos la seguridad: antes de confirmar la venta, el sistema valida que haya stock suficiente. Si no hay piezas, se ejecuta un Rollback automático en SQLite para proteger el inventario. Al cobrar, descuenta el stock, asienta la salida en el Kardex y genera el comprobante en PDF con ReportLab al instante.",
        tiempo="50 seg",
        tip="Menciona la palabra 'Rollback' y 'Atomicidad ACID' para demostrar rigor técnico."
    )

    # =========================================================================
    # SLIDE 10: MÓDULO 8 - REPORTES EXCEL
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    aplicar_fondo(s10, prs, C_WHITE)

    agregar_encabezado_modulo(
        s10,
        "MÓDULO 08 • INTELIGENCIA DE NEGOCIOS Y EXPORTACIÓN",
        "Reportes Gerenciales y Microsoft Excel",
        "Generación nativa de hojas de cálculo .xlsx con openpyxl y análisis contable."
    )

    bullets_s10 = [
        ("📅", "Filtro por Rango de Fechas", "Análisis por día, mes o periodo personalizado con validación estricta AAAA-MM-DD."),
        ("📈", "Indicadores de Rendimiento", "Ingresos brutos, total de ventas, descuentos otorgados y ticket promedio."),
        ("📑", "Exportación Nativa .xlsx", "Hojas de cálculo reales generadas con openpyxl con colores corporativos y fórmulas SUM."),
        ("🔄", "Reimpresión de Comprobantes", "Permite regenerar cualquier Boleta o Factura histórica en PDF con 1 clic.")
    ]
    agregar_bullets(s10, Inches(0.8), Inches(2.4), Inches(4.8), Inches(4.5), bullets_s10)
    insertar_captura(s10, "capturas_guia/08_reportes_excel.png", left=Inches(5.8), top=Inches(1.2), width=Inches(6.8))

    asignar_notas_orador(
        s10,
        "Para el análisis contable, el módulo de Reportes permite filtrar las operaciones por cualquier rango de fechas. Lo más potente es la exportación nativa a Excel con openpyxl: con un solo clic generamos libros con formato de moneda, cabeceras y fórmulas automáticas listos para el contador o la gerencia.",
        tiempo="35 seg",
        tip="Destaca que openpyxl genera archivos .xlsx reales, no simples archivos CSV planos."
    )

    # =========================================================================
    # SLIDE 11: MÓDULO 9 - GESTIÓN DE USUARIOS MEJORADA
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    aplicar_fondo(s11, prs, C_WHITE)

    agregar_encabezado_modulo(
        s11,
        "MÓDULO 09 • NUEVA GESTIÓN DE PERSONAL Y PERMISOS",
        "Control de Usuarios Intuitivo y Ordenado",
        "Generadores asistidos, tarjeta dinámica de permisos y ordenamiento interactivo."
    )

    bullets_s11 = [
        ("⚡", "Sugerir Login Automático", "Genera 'cmendoza' desde 'Carlos Mendoza' comprobando unicidad en base de datos."),
        ("🎲", "Generador de Claves Seguras", "Propone contraseñas temporales memorables (ej. 'Tech2026!') con botón ver 👁."),
        ("📋", "Tarjeta Dinámica de Permisos", "Muestra en tiempo real qué puede hacer el rol: el vendedor tiene los costos ocultos."),
        ("📊", "Tabla Interactiva y Filtros", "Ordenamiento por columnas (▲/▼), buscador en vivo y reactivación de cuentas.")
    ]
    agregar_bullets(s11, Inches(0.8), Inches(2.4), Inches(4.8), Inches(4.5), bullets_s11)
    insertar_captura(s11, "capturas_guia/09_usuarios.png", left=Inches(5.8), top=Inches(1.2), width=Inches(6.8))

    asignar_notas_orador(
        s11,
        "En la gestión de usuarios aplicamos la filosofía de facilitarle la vida a personas que nunca usaron un sistema de inventario. Incluimos sugerencia automática de login y contraseñas, una tarjeta visual que explica claramente qué permisos tiene cada rol (los costos mayoristas están 100% ocultos para los vendedores), ordenamiento interactivo por cualquier columna de la tabla y reactivación de cuentas.",
        tiempo="50 seg",
        tip="Explica que el Administrador ID 1 está blindado contra desactivación accidental."
    )

    # =========================================================================
    # SLIDE 12: MÓDULO 10 - CONEXIÓN EN LA NUBE MEJORADA
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    aplicar_fondo(s12, prs, C_WHITE)

    agregar_encabezado_modulo(
        s12,
        "MÓDULO 10 • CONTINUIDAD OPERATIVA Y NUBE HÍBRIDA",
        "Conexión Asistida a PostgreSQL en la Nube",
        "Desglose de URL directa, semáforo en tiempo real y resiliencia 100% offline."
    )

    bullets_s12 = [
        ("⚡", "Asistente 'Desglosar URL'", "Pega la URL de Neon o Supabase (postgresql://...) y extrae servidor, BD y clave en 1 clic."),
        ("🚦", "Semáforo en Tiempo Real", "🟢 En Línea, 🟡 Modo Local Offline o ⚪ Sin Configurar con contador de pendientes."),
        ("🔌", "100% Resiliente sin Internet", "Si se corta la red o la luz, la tienda sigue facturando en local sin interrupciones."),
        ("🔄", "Sincronización Idempotente", "Sube cambios mediante UUIDs globales sin generar duplicados ni sobreescrituras ciegas.")
    ]
    agregar_bullets(s12, Inches(0.8), Inches(2.4), Inches(4.8), Inches(4.5), bullets_s12)
    insertar_captura(s12, "capturas_guia/10_config_nube.png", left=Inches(5.8), top=Inches(1.2), width=Inches(6.8))

    asignar_notas_orador(
        s12,
        "Finalizamos con nuestra arquitectura híbrida SQLite + PostgreSQL. Para que conectar la nube sea trivial para cualquier usuario, creamos el Asistente de Desglose de URL: solo pegas el enlace de Neon o Supabase y el sistema llena todos los campos automáticamente. Y lo más importante: si se cae el internet, la tienda no se detiene; sigue cobrando en local y cuando vuelve la red, sincroniza con 1 clic sin duplicados gracias a los UUIDs.",
        tiempo="50 seg",
        tip="Destaca que 'la tienda jamás se detiene aunque no haya internet' como mayor ventaja competitiva."
    )

    # =========================================================================
    # SLIDE 13: MATRIZ COMPARATIVA DE ROLES
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    aplicar_fondo(s13, prs, C_WHITE)

    agregar_encabezado_modulo(
        s13,
        "SEGURIDAD Y GOBERNANZA DE ACCESO",
        "Matriz de Permisos: Administrador vs Vendedor",
        "Protección estricta de la información financiera y operativa del negocio."
    )

    # Tabla visual
    rows = 7
    cols = 3
    tbl_shape = s13.shapes.add_table(rows, cols, Inches(0.8), Inches(2.4), Inches(11.7), Inches(4.4))
    table = tbl_shape.table
    table.columns[0].width = Inches(5.7)
    table.columns[1].width = Inches(3.0)
    table.columns[2].width = Inches(3.0)

    encs = ["CAPACIDAD / OPERACIÓN EN EL SISTEMA", "👑 ADMINISTRADOR (GERENTE)", "🛒 VENDEDOR (MOSTRADOR)"]
    for c_i, h in enumerate(encs):
        cell = table.cell(0, c_i)
        cell.fill.solid()
        cell.fill.fore_color.rgb = C_NAVY
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.alignment = PP_ALIGN.CENTER
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = C_WHITE

    filas_matriz = [
        ("Acceso al Punto de Venta (POS) y emisión de comprobantes", "✔ Sí permitido (Total)", "✔ Sí permitido (Total)"),
        ("Consultar stock disponible de hardware y periféricos", "✔ Sí permitido (Total)", "✔ Sí permitido (Total)"),
        ("Visualizar Precios de Compra (Costos Mayoristas)", "✔ Visible y editable", "❌ OCULTO Y BLOQUEADO"),
        ("Dar de baja, modificar o eliminar productos del inventario", "✔ Sí permitido", "❌ BLOQUEADO"),
        ("Registrar entradas de mercadería en Kardex y ajustes", "✔ Sí permitido", "❌ BLOQUEADO"),
        ("Ver Reportes Financieros, caja acumulada y utilidades", "✔ Sí permitido", "❌ PESTAÑA OCULTA")
    ]

    for r_i, fila in enumerate(filas_matriz):
        bg = C_WHITE if r_i % 2 == 0 else C_GRAY_LIGHT
        for c_i, txt in enumerate(fila):
            cell = table.cell(r_i + 1, c_i)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            p = cell.text_frame.paragraphs[0]
            p.text = txt
            p.font.name = "Segoe UI"
            p.font.size = Pt(9.5)
            if c_i == 0:
                p.alignment = PP_ALIGN.LEFT
                p.font.color.rgb = C_NAVY
            else:
                p.alignment = PP_ALIGN.CENTER
                if "OCULTO" in txt or "BLOQUEADO" in txt:
                    p.font.bold = True
                    p.font.color.rgb = C_RED
                else:
                    p.font.bold = True
                    p.font.color.rgb = C_GREEN

    asignar_notas_orador(
        s13,
        "En esta matriz de permisos se evidencia la seguridad de TechStore: un vendedor puede operar con total fluidez cobrando y emitiendo comprobantes, pero los costos de compra mayoristas, la edición de productos y los reportes de utilidades están completamente bloqueados para salvaguardar la rentabilidad y confidencialidad del negocio.",
        tiempo="35 seg",
        tip="Muestra cómo se protege el margen de ganancia de la tienda."
    )

    # =========================================================================
    # SLIDE 14: BANCO DE PREGUNTAS CLAVE DEL JURADO
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    aplicar_fondo(s14, prs, C_WHITE)

    agregar_encabezado_modulo(
        s14,
        "PREPARACIÓN ESTRATÉGICA ANTE EL JURADO EXAMINADOR",
        "Preguntas Clave y Argumentos Técnicos Infalibles",
        "Respuestas concisas respaldadas por la arquitectura del software."
    )

    preguntas_cards = [
        (Inches(0.8), Inches(2.4), "1. ¿Qué pasa si se corta el Internet?",
         "La tienda opera 100% offline en SQLite local. Las ventas, el kardex y los PDFs funcionan sin interrupción. Al volver internet, se sincroniza a PostgreSQL con 1 solo clic."),
        (Inches(6.8), Inches(2.4), "2. ¿Cómo garantizan que el SKU no se repita?",
         "Doble barrera: backend busca el correlativo más alto libre en tiempo real ('generar_sku_sugerido') y la columna en SQLite tiene restricción UNIQUE estricta."),
        (Inches(0.8), Inches(4.7), "3. ¿Por qué el Asistente es mejor que una alerta?",
         "Las alertas avisan cuando ya no hay stock (tarde). El Asistente calcula velocidad diaria de rotación y autonomía, prediciendo cuántas unidades pedir antes del quiebre."),
        (Inches(6.8), Inches(4.7), "4. ¿Cómo evitan vender productos sin stock?",
         "Mediante validación atómica en VentaModel. Si cualquier ítem no tiene unidades suficientes, se ejecuta un Rollback transaccional que anula la operación completa.")
    ]

    for left, top, tit, resp in preguntas_cards:
        c = agregar_tarjeta(s14, left, top, Inches(5.7), Inches(2.1), C_GRAY_LIGHT, C_BLUE)
        tf = c.text_frame
        tf.word_wrap = True
        p_t = tf.paragraphs[0]
        p_t.text = tit
        p_t.font.name = "Segoe UI"
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_NAVY
        p_t.space_after = Pt(4)

        p_r = tf.add_paragraph()
        p_r.text = resp
        p_r.font.name = "Segoe UI"
        p_r.font.size = Pt(9.5)
        p_r.font.color.rgb = RGBColor(51, 65, 85)

    asignar_notas_orador(
        s14,
        "Tengan presentes estas cuatro respuestas maestras: el modo offline garantiza la venta sin internet, la restricción UNIQUE impide duplicados de código, el modelo de demanda predice compras antes de perder ventas, y el Rollback transaccional imposibilita la sobre-venta en caja.",
        tiempo="30 seg",
        tip="Ten estas respuestas en mente para responder de inmediato sin dudar."
    )

    # =========================================================================
    # SLIDE 15: CONCLUSIONES Y DEMOSTRACIÓN EN VIVO
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    aplicar_fondo(s15, prs, C_NAVY)

    linea_cierre = s15.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(1.8), Inches(1.5), Inches(0.08))
    linea_cierre.fill.solid()
    linea_cierre.fill.fore_color.rgb = C_GREEN
    linea_cierre.line.fill.background()

    tx_cierre = s15.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.3), Inches(3.8))
    tfc = tx_cierre.text_frame
    tfc.word_wrap = True

    pc0 = tfc.paragraphs[0]
    pc0.text = "CONCLUSIÓN Y APERTURA A DEMOSTRACIÓN EN VIVO"
    pc0.font.name = "Segoe UI"
    pc0.font.size = Pt(13)
    pc0.font.bold = True
    pc0.font.color.rgb = C_CYAN
    pc0.space_after = Pt(8)

    pc1 = tfc.add_paragraph()
    pc1.text = "TechStore: Listo para Producción Real"
    pc1.font.name = "Segoe UI"
    pc1.font.size = Pt(34)
    pc1.font.bold = True
    pc1.font.color.rgb = C_WHITE
    pc1.space_after = Pt(14)

    pc2 = tfc.add_paragraph()
    pc2.text = (
        "✔ Rentabilidad Protegida: Compras precisas por demanda histórica sin acumular stock muerto.\n"
        "✔ Continuidad Total: Operación híbrida resiliente ante cortes de internet.\n"
        "✔ Seguridad de Grado Bancario: PBKDF2 y roles con costos mayoristas protegidos.\n"
        "✔ Máxima Usabilidad: Diseñado para ser intuitivo incluso para usuarios principiantes."
    )
    pc2.font.name = "Segoe UI"
    pc2.font.size = Pt(12)
    pc2.font.color.rgb = RGBColor(226, 232, 240)
    pc2.space_after = Pt(24)

    pc3 = tfc.add_paragraph()
    pc3.text = "¡Muchas gracias! Quedamos atentos a sus preguntas y listos para la demostración en vivo."
    pc3.font.name = "Segoe UI"
    pc3.font.size = Pt(14)
    pc3.font.bold = True
    pc3.font.color.rgb = C_CYAN

    asignar_notas_orador(
        s15,
        "En conclusión, TechStore no es solo un sistema contable: es una solución estratégica lista para producción que protege la rentabilidad de las tiendas de computadoras mediante tecnología moderna, robusta y accesible. Muchas gracias por su atención, quedamos atentos a sus preguntas y listos para la demostración en vivo.",
        tiempo="30 seg",
        tip="Termina con una sonrisa, postura erguida y agradeciendo al jurado."
    )

    ruta_pptx = "Presentacion_TechStore_Exposicion.pptx"
    prs.save(ruta_pptx)
    print(f"✔ [ÉXITO] Archivo generado: {ruta_pptx}")

if __name__ == "__main__":
    generar_presentacion()

