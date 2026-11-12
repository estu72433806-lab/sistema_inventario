import _path  # noqa: F401  (prepara rutas del proyecto)
"""
Script integral para generar los 2 documentos Word solicitados:
1. 'Guion_de_Exposicion_TechStore.docx' -> Guion breve, claro, ilustrado y directo para la presentación oral.
2. 'Manual_Detallado_Sistema_TechStore.docx' -> Manual técnico y operativo completo con todas las explicaciones y capturas.
"""
import os
import sys

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def aplicar_sombreado_celda(celda, color_hex):
    """Aplica color de fondo hexadecimal a una celda de tabla."""
    tcPr = celda._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    tcPr.append(shd)

def aplicar_bordes_celda(celda, top="none", bottom="none", left="none", right="none", color="CBD5E1", sz="8"):
    """Configura bordes específicos en una celda."""
    tcPr = celda._tc.get_or_add_tcPr()
    b_xml = (
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="{top}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{bottom}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="{left}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="{right}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(parse_xml(b_xml))

def crear_caja_estilizada(doc, titulo, parrafos, tipo="guion"):
    """Crea una tarjeta de texto destacada (Callout box)."""
    if tipo == "guion":
        b_color = "0284C7"
        bg_color = "F0F9FF"
        icono = "🎙️ GUION DE EXPOSICIÓN (QUÉ DECIR EN TU PRESENTACIÓN)"
        tit_color = RGBColor(2, 132, 199)
    elif tipo == "punchline":
        b_color = "10B981"
        bg_color = "F0FDF4"
        icono = "💡 PUNTOS CLAVE PARA EL JURADO (ARGUMENTOS FUERTES)"
        tit_color = RGBColor(16, 185, 129)
    elif tipo == "tiempo":
        b_color = "F59E0B"
        bg_color = "FFFBEB"
        icono = "⏱️ TIEMPO Y ACCIÓN EN PANTALLA"
        tit_color = RGBColor(217, 119, 6)
    else:
        b_color = "64748B"
        bg_color = "F8FAFC"
        icono = "📌 INFORMACIÓN TÉCNICA"
        tit_color = RGBColor(71, 85, 105)

    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    aplicar_sombreado_celda(cell, bg_color)
    aplicar_bordes_celda(cell, left="single", color=b_color, sz="24")

    p_tit = cell.paragraphs[0]
    p_tit.paragraph_format.space_before = Pt(3)
    p_tit.paragraph_format.space_after = Pt(2)
    run_tit = p_tit.add_run(f"{icono}\n{titulo}")
    run_tit.bold = True
    run_tit.font.name = "Segoe UI"
    run_tit.font.size = Pt(9.5)
    run_tit.font.color.rgb = tit_color

    for t in parrafos:
        p = cell.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(t)
        run.font.name = "Segoe UI"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def insertar_imagen_con_caption(doc, ruta_img, caption_texto, ancho_pulgadas=6.0):
    """Inserta una imagen centrada con borde y pie de foto estilizado."""
    if not os.path.exists(ruta_img):
        p_warn = doc.add_paragraph(f"[Imagen no encontrada: {ruta_img}]")
        p_warn.runs[0].font.color.rgb = RGBColor(220, 38, 38)
        return

    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(6)
    p_img.paragraph_format.space_after = Pt(2)

    run = p_img.add_run()
    run.add_picture(ruta_img, width=Inches(ancho_pulgadas))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(0)
    p_cap.paragraph_format.space_after = Pt(8)
    run_cap = p_cap.add_run(f"📸 {caption_texto}")
    run_cap.font.name = "Segoe UI"
    run_cap.font.size = Pt(8.5)
    run_cap.font.italic = True
    run_cap.font.color.rgb = RGBColor(71, 85, 105)

def crear_tabla_estilizada(doc, encabezados, filas, anchos=None, col_fondo_enc="1E293B"):
    """Crea una tabla con cabecera oscura y bordes limpios."""
    tbl = doc.add_table(rows=len(filas) + 1, cols=len(encabezados))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    # Cabecera
    for c_idx, h_text in enumerate(encabezados):
        cell = tbl.cell(0, c_idx)
        if anchos and c_idx < len(anchos):
            cell.width = Inches(anchos[c_idx])
        aplicar_sombreado_celda(cell, col_fondo_enc)
        aplicar_bordes_celda(cell, bottom="single", color="0284C7", sz="16")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(h_text)
        run.bold = True
        run.font.name = "Segoe UI"
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(255, 255, 255)

    # Filas
    for r_idx, fila in enumerate(filas):
        bg = "FFFFFF" if r_idx % 2 == 0 else "F8FAFC"
        for c_idx, val in enumerate(fila):
            cell = tbl.cell(r_idx + 1, c_idx)
            if anchos and c_idx < len(anchos):
                cell.width = Inches(anchos[c_idx])
            aplicar_sombreado_celda(cell, bg)
            aplicar_bordes_celda(cell, bottom="single", color="E2E8F0", sz="4")
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            run = p.add_run(str(val))
            run.font.name = "Segoe UI"
            run.font.size = Pt(8.5)
            run.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)


# ==============================================================================
# 1. GENERACIÓN DEL GUION DE EXPOSICIÓN (BREVE, CLARO Y CON IMÁGENES)
# ==============================================================================
def generar_guion_exposicion():
    print("Generando 'Guion_de_Exposicion_TechStore.docx'...")
    doc = docx.Document()

    # Configurar márgenes
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)

    # Portada / Cabecera del Guion
    p_port = doc.add_paragraph()
    p_port.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_badge = p_port.add_run("GUION OFICIAL DE EXPOSICIÓN Y DEFENSA DEL PROYECTO\n")
    run_badge.font.name = "Segoe UI"
    run_badge.font.size = Pt(11)
    run_badge.font.bold = True
    run_badge.font.color.rgb = RGBColor(2, 132, 199)

    run_tit = p_port.add_run("TechStore: Sistema de Inventario y Ventas\n")
    run_tit.font.name = "Segoe UI"
    run_tit.font.size = Pt(22)
    run_tit.font.bold = True
    run_tit.font.color.rgb = RGBColor(15, 23, 42)

    run_sub = p_port.add_run("Guía Oral Paso a Paso para el Expositor • Pitch Ejecutivo de 5 Minutos • Respuestas Infalibles ante el Jurado\n")
    run_sub.font.name = "Segoe UI"
    run_sub.font.size = Pt(10)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Consejos rápidos para el expositor
    crear_caja_estilizada(
        doc,
        "ESTRATEGIA DE ÉXITO EN LA EXPOSICIÓN (CONSEJOS RÁPIDOS)",
        [
            "1. Tono y Ritmo: Habla con seguridad, pausado y mirando a los ojos del jurado. No leas la diapositiva; guíate por este documento.",
            "2. Enfoque de Valor: En cada módulo, resalta primero 'qué problema resuelve en una tienda de computadoras' y luego 'cómo lo hace técnicamente'.",
            "3. Las 3 Joyas a Destacar: (1) Generador de SKU Inteligente, (2) Asistente Inteligente de Reposición, y (3) Resiliencia Offline Híbrida.",
            "4. Duración Total Recomendada: Entre 5 y 7 minutos de exposición + ronda de preguntas."
        ],
        tipo="punchline"
    )

    doc.add_heading("Estructura de la Exposición Pantalla por Pantalla", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    # Lista de pantallas a exponer
    pantallas_guion = [
        {
            "num": 1,
            "titulo": "Pantalla 1: Acceso Seguro y Ciberseguridad (Login)",
            "img": "capturas_guia/01_login.png",
            "cap": "Pantalla de Inicio de Sesión con autenticación criptográfica PBKDF2.",
            "tiempo": "30 a 45 segundos",
            "accion": "Mostrar la ventana de login con los campos 'admin' y contraseña oculta.",
            "guion": (
                "\"Buenos días, miembros del jurado. Comenzamos la presentación en la pantalla de acceso seguro de TechStore. "
                "En una tienda de tecnología donde se comercializan procesadores y tarjetas de video de alto valor, la seguridad es crítica. "
                "Aquí destacamos dos pilares: primero, las contraseñas nunca se guardan en texto plano; aplicamos hash criptográfico "
                "PBKDF2-HMAC-SHA256 con 100,000 iteraciones y una sal (salt) aleatoria de 16 bytes por usuario, cumpliendo estándares internacionales. "
                "Y segundo, aplicamos separación estricta de roles: el Administrador tiene control total del negocio, mientras que el rol Vendedor "
                "está enfocado en cobrar rápido y tiene bloqueados los costos mayoristas y la eliminación de productos para salvaguardar la empresa.\""
            ),
            "punch": [
                "Ciberseguridad bancaria: PBKDF2 con sal individual de 16 bytes.",
                "Separación de perfiles: Administrador (Control gerencial) vs Vendedor (Mostrador/Caja).",
                "Blindaje contra filtraciones de base de datos."
            ]
        },
        {
            "num": 2,
            "titulo": "Pantalla 2: Panel Ejecutivo en Tiempo Real (Dashboard)",
            "img": "capturas_guia/02_dashboard.png",
            "cap": "Dashboard Ejecutivo con 4 tarjetas métricas calculadas automáticamente desde SQLite.",
            "tiempo": "40 segundos",
            "accion": "Ingresar al sistema y señalar las 4 tarjetas KPI superiores y el indicador dinámico de Nube.",
            "guion": (
                "\"Al iniciar sesión, el gerente visualiza este Dashboard Ejecutivo. A diferencia de sistemas anticuados que requieren botones "
                "de 'refrescar', en TechStore las cuatro tarjetas métricas se calculan en tiempo real desde la base de datos local SQLite: "
                "las ventas acumuladas del día, el número de componentes activos en catálogo, los productos en nivel crítico de inventario "
                "y el estado del Modo Híbrido con la nube. "
                "Noten la usabilidad: la tarjeta de 'Alerta Stock Bajo' es interactiva; con solo hacer un clic sobre ella, el sistema nos transporta "
                "inmediatamente al Asistente Inteligente de Reposición.\""
            ),
            "punch": [
                "Cero botones de refrescar: métricas calculadas en vivo tras cada venta o entrada.",
                "Tarjeta de Stock Bajo interactiva (abre el asistente con 1 clic).",
                "Monitoreo visual del estado híbrido local/nube."
            ]
        },
        {
            "num": 3,
            "titulo": "Pantalla 3: Catálogo Inteligente y Generador de SKU",
            "img": "capturas_guia/03_inventario_productos.png",
            "cap": "Módulo de Inventario con generador automático de código nemotécnico '⚡ Sugerir SKU'.",
            "tiempo": "45 segundos",
            "accion": "Seleccionar una categoría y marca en el formulario y pulsar '⚡ Sugerir SKU'.",
            "guion": (
                "\"Uno de los mayores dolores de cabeza en tiendas de computación es el desorden en los códigos de productos. "
                "En TechStore creamos el generador de Código SKU Inteligente. Al elegir la categoría 'Laptops' y la marca 'Lenovo', "
                "el sistema analiza automáticamente los nemotécnicos 'LAP' y 'LEN', consulta en la base de datos el último número registrado "
                "y propone de inmediato 'LAP-LEN-001' o el siguiente correlativo libre. "
                "Esto elimina por completo los códigos duplicados, acelera el registro de mercadería nueva y facilita la búsqueda en almacén. "
                "Además, aplicamos borrado lógico: desactivar un producto no borra sus ventas históricas ni su kardex.\""
            ),
            "punch": [
                "Nemotécnica inteligente: [CAT]-[MAR]-[001] generado en milisegundos.",
                "Garantía de unicidad: doble validación en backend y restricción UNIQUE en SQLite.",
                "Borrado lógico seguro: integridad referencial intacta para contabilidad."
            ]
        },
        {
            "num": 4,
            "titulo": "Pantalla 4: La Joya: Asistente Inteligente de Reposición",
            "img": "capturas_guia/04_asistente_reposicion.png",
            "cap": "Asistente Inteligente de Reposición con cálculo de demanda, autonomía y presupuesto.",
            "tiempo": "60 segundos (Momento Cumbre de la Exposición)",
            "accion": "Mostrar el cuadro de KPIs (Unidades sugeridas, Inversión estimada) y hacer clic en una fila para ver la justificación.",
            "guion": (
                "\"Señores del jurado, esta es la joya analítica de TechStore. La mayoría de sistemas solo muestran un número en rojo cuando ya te quedaste "
                "sin stock y ya perdiste ventas. Nuestro Asistente de Reposición va un paso adelante: aplica un modelo matemático de inventarios "
                "que evalúa el stock actual frente a las ventas reales de los últimos 30 días. "
                "Calcula la velocidad diaria de rotación y nos dice exactamente cuántos días de autonomía nos quedan antes del quiebre. "
                "Si elegimos una cobertura de 30 días, nos calcula con precisión cuántas unidades debemos comprarle a cada mayorista y cuánto dinero "
                "en Soles debemos presupuestar. "
                "Y miren este detalle de ingeniería: al presionar 'Registrar Entrada de Mercadería', el sistema nos traslada a la pestaña de Kardex "
                "con el producto, el mayorista y la cantidad sugerida ya cargados, listos para confirmar.\""
            ),
            "punch": [
                "Modelo predictivo: Demanda Diaria = Ventas 30d / 30; Autonomía = Stock / Demanda.",
                "Cálculo automático de presupuesto en Soles (S/) para negociar con mayoristas.",
                "Traspaso asistido con 1 clic hacia el Kardex y exportación a Excel."
            ]
        },
        {
            "num": 5,
            "titulo": "Pantalla 5: Auditoría Total y Kardex de Mercadería",
            "img": "capturas_guia/05_movimientos_kardex.png",
            "cap": "Kardex de Auditoría con registro de entradas de proveedor y ajustes por daño físico.",
            "tiempo": "30 a 40 segundos",
            "accion": "Mostrar el formulario de registro de movimiento y el historial multicolor (verde = entrada, rojo = salida).",
            "guion": (
                "\"El módulo de Movimientos de Stock garantiza la auditoría integral de cada pieza de hardware. "
                "Manejamos dos operaciones: Entradas de mercadería vinculadas a un proveedor mayorista con su factura o guía de remisión; "
                "y Ajustes por daño físico o merma, donde un técnico puede justificar, por ejemplo, una placa madre averiada durante el ensamblaje. "
                "Cada registro almacena fecha, hora exacta y el usuario responsable, impidiendo cualquier descuadre de almacén.\""
            ),
            "punch": [
                "Trazabilidad legal: cada entrada exige proveedor y documento de compra.",
                "Gestión de mermas técnicas justificada con acta.",
                "Auditoría con usuario y marca de tiempo exacta."
            ]
        },
        {
            "num": 6,
            "titulo": "Pantalla 6: Directorio Unificado de Clientes y Proveedores",
            "img": "capturas_guia/06_contactos.png",
            "cap": "Directorio de Contactos con soporte de cliente rápido '00000000'.",
            "tiempo": "30 segundos",
            "accion": "Alternar entre las pestañas de Registro de Clientes y Proveedores.",
            "guion": (
                "\"En el módulo de Contactos centralizamos los datos de compradores y proveedores mayoristas. "
                "Para agilizar el mostrador, creamos un cliente por defecto llamado 'Público General / Venta Rápida' con documento '00000000'. "
                "Esto permite a los vendedores emitir boletas en menos de 5 segundos para compras pequeñas al paso, "
                "o ingresar clientes con RUC completo cuando solicitan factura empresarial.\""
            ),
            "punch": [
                "Directorio centralizado de clientes y mayoristas.",
                "Venta rápida al paso con DNI '00000000' en 5 segundos.",
                "Soporte completo para emisión de Facturas con RUC."
            ]
        },
        {
            "num": 7,
            "titulo": "Pantalla 7: Punto de Venta (POS) y Facturación Rápida",
            "img": "capturas_guia/07_punto_venta_pos.png",
            "cap": "Punto de Venta con validación atómica de stock, cálculo de IGV/descuentos y PDF.",
            "tiempo": "50 segundos",
            "accion": "Señalar el carrito de compras, los descuentos aplicados y el botón de confirmar venta.",
            "guion": (
                "\"Llegamos al motor comercial del negocio: el Punto de Venta. Aquí la prioridad es la velocidad y la seguridad transaccional. "
                "Agregamos los artículos al carrito, seleccionamos si es Boleta o Factura, método de pago y descuentos en monto fijo o porcentaje. "
                "Pero quiero destacar una protección clave de ingeniería de software: la validación atómica de stock. "
                "Si un vendedor intenta vender más unidades de las que hay físicamente en almacén, el sistema bloquea la operación y ejecuta "
                "un Rollback automático en SQLite. No se descuenta nada y se evita vender mercadería inexistente. "
                "Al confirmar la venta válida, en una fracción de segundo se descuenta el stock, se genera el asiento en el Kardex y se emite "
                "el comprobante en PDF profesional listo para imprimir usando ReportLab.\""
            ),
            "punch": [
                "Transacciones atómicas: control estricto de concurrencia y stock.",
                "Rollback inmediato ante intentos de sobre-venta.",
                "Emisión instantánea de Boletas y Facturas en PDF con ReportLab."
            ]
        },
        {
            "num": 8,
            "titulo": "Pantalla 8: Inteligencia de Negocios y Reportes Excel",
            "img": "capturas_guia/08_reportes_excel.png",
            "cap": "Módulo de Reportes con consolidado gerencial y exportación nativa a Excel (.xlsx).",
            "tiempo": "35 segundos",
            "accion": "Mostrar el filtro de fechas y los botones de exportación a Excel.",
            "guion": (
                "\"Para el análisis gerencial, el módulo de Reportes consolida los ingresos, la cantidad de comprobantes emitidos y los descuentos "
                "otorgados en cualquier rango de fechas. "
                "Lo más valioso para la administración es la exportación nativa a Microsoft Excel (.xlsx) con openpyxl. "
                "Con un solo clic se generan reportes ejecutivos con cabeceras corporativas, fórmulas de suma automática y formato de moneda en Soles, "
                "listos para presentar a contabilidad o a la gerencia general.\""
            ),
            "punch": [
                "Filtros flexibles por día, mes o rango personalizado AAAA-MM-DD.",
                "Generación de archivos Excel .xlsx reales con openpyxl.",
                "Diseño visual corporativo con fórmulas integradas."
            ]
        },
        {
            "num": 9,
            "titulo": "Pantalla 9: Nueva Gestión de Usuarios y Matriz de Roles",
            "img": "capturas_guia/09_usuarios.png",
            "cap": "Gestión de Usuarios mejorada con sugerencia de login, generador de claves, tarjeta de permisos y tabla interactiva.",
            "tiempo": "50 segundos",
            "accion": "Mostrar el formulario con la tarjeta de permisos y la tabla ordenada con encabezados interactivos.",
            "guion": (
                "\"En la gestión de usuarios implementamos una de las mejoras más solicitadas: hacerla intuitiva para quienes nunca han usado "
                "un sistema de inventario. "
                "Primero, agregamos asistentes automáticos: al escribir el nombre del empleado, el botón '⚡ Sugerir Login' genera un usuario único "
                "libre de duplicados, y el botón '🎲 Clave' propone una contraseña segura temporal. "
                "Segundo, la Tarjeta Dinámica de Permisos: al seleccionar el rol 'Vendedor', el sistema le explica al usuario en lenguaje humano "
                "qué puede hacer (vender y consultar stock) y qué tiene protegido (los costos de compra de las computadoras y las ganancias están ocultos). "
                "Y tercero, el orden total: la tabla permite ordenar por cualquier columna haciendo clic en su cabecera (▲/▼), filtrar en tiempo real "
                "por búsqueda o estado, y reactivar cuentas suspendidas con un solo clic, manteniendo siempre blindado al Administrador principal ID 1.\""
            ),
            "punch": [
                "Asistentes inteligentes: '⚡ Sugerir Login' y '🎲 Clave Segura'.",
                "Tarjeta explicativa de permisos en vivo (Costos ocultos para el vendedor).",
                "Tabla interactiva ordenable por columnas y buscador en tiempo real."
            ]
        },
        {
            "num": 10,
            "titulo": "Pantalla 10: Nueva Conexión y Respaldo Híbrido en la Nube",
            "img": "capturas_guia/10_config_nube.png",
            "cap": "Configuración de Nube con asistente de URL directa (Neon/Supabase), semáforo en vivo y sincronización.",
            "tiempo": "50 segundos",
            "accion": "Mostrar el asistente para pegar la URL directa y el semáforo de estado de conexión.",
            "guion": (
                "\"Finalizamos con nuestra arquitectura de Continuidad Operativa: el Modo Híbrido SQLite + PostgreSQL en la nube. "
                "Para que conectar la nube no sea complicado, añadimos el 'Asistente de Pegado de URL': si el dueño crea una base de datos "
                "gratuita en Neon.tech o Supabase, solo pega su enlace de conexión y presiona '⚡ Desglosar URL'. El sistema extrae servidor, "
                "puerto, base de datos y usuario automáticamente. "
                "El semáforo visual muestra si estamos en línea o en modo local. "
                "¿Y cuál es la mayor ventaja para el negocio? Si en la tienda se corta el internet o la luz, la tienda no se detiene: sigue "
                "vendiendo normalmente en SQLite local. Y cuando regresa el internet, presionamos 'Sincronizar' y todo sube a la nube sin duplicados "
                "gracias a nuestros identificadores globales UUID.\""
            ),
            "punch": [
                "Asistente '⚡ Desglosar URL' para Neon, Supabase o Render.",
                "Arquitectura Offline-First: la tienda jamás se detiene sin internet.",
                "Sincronización desduplicada mediante UUIDs y control de transacciones."
            ]
        }
    ]

    for p_info in pantallas_guion:
        doc.add_heading(f"{p_info['titulo']}", level=2)
        doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(2, 132, 199)

        insertar_imagen_con_caption(doc, p_info["img"], p_info["cap"], ancho_pulgadas=5.8)

        # Caja de Tiempo y Acción
        crear_caja_estilizada(
            doc,
            f"DURACIÓN: {p_info['tiempo']}",
            [f"🎯 Acción en Pantalla: {p_info['accion']}"],
            tipo="tiempo"
        )

        # Caja de Guion Oral
        crear_caja_estilizada(
            doc,
            "PALABRAS EXACTAS A PRONUNCIAR FRENTE AL JURADO",
            [p_info["guion"]],
            tipo="guion"
        )

        # Caja de Punchlines
        crear_caja_estilizada(
            doc,
            "ARGUMENTOS DE IMPACTO PARA DESTACAR",
            p_info["punch"],
            tipo="punchline"
        )

    # Pitch Maestro de 5 Minutos Corrido
    doc.add_page_break()
    doc.add_heading("Guion Maestro Corrido (Pitch de 5 Minutos)", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "Si el jurado te solicita una exposición estricta y cronometrada de exactamente 5 minutos, "
        "utiliza la siguiente tabla para sincronizar tus palabras minuto a minuto:"
    )

    tabla_pitch = [
        ("Minuto 1: Problema e Introducción", "Buenos días jurado y profesores. Hoy presentamos TechStore, un sistema integral para tiendas de hardware y cómputo. Gestionar componentes tecnológicos es complejo: son costosos, hay cientos de modelos y quedarse sin stock significa perder ventas de miles de Soles. TechStore resuelve esto combinando velocidad local offline en SQLite, seguridad criptográfica y un motor analítico de inventarios."),
        ("Minuto 2: Inventario y SKU Inteligente", "En Inventario mostramos nuestra primera innovación: el generador de SKU Inteligente. Al registrar una laptop Lenovo, el sistema propone automáticamente 'LAP-LEN-001' y verifica en toda la base de datos que no exista repetición. Esto estandariza el almacén y elimina errores humanos de digitación."),
        ("Minuto 3: La Joya: Asistente de Reposición", "Aquí está la joya de nuestro software: el Asistente Inteligente de Reposición. No es una simple alerta: evalúa las ventas reales de los últimos 30 días, calcula la demanda diaria y los días de autonomía restante. Para una cobertura deseada, calcula con precisión matemática cuántas unidades comprarle a cada mayorista y qué presupuesto de inversión se necesita, enlazándose directamente con el Kardex."),
        ("Minuto 4: Venta en POS y Transacción Atómica", "En el Punto de Venta demostramos la agilidad de cobro. Agregamos artículos, aplicamos descuentos y validamos el stock en tiempo real. Si alguien intenta vender más piezas de las existentes, el sistema bloquea la venta mediante Rollback transaccional. Al cobrar, se descuenta el stock de inmediato y se emite la Boleta o Factura en PDF profesional con ReportLab."),
        ("Minuto 5: Usuarios, Nube Híbrida y Cierre", "En Usuarios y Nube destacamos la usabilidad para principiantes: generador automático de login y contraseñas, tarjeta de permisos donde el vendedor tiene ocultos los costos de compra, y un asistente para conectar PostgreSQL en la nube con un solo enlace. Si se corta el internet, la tienda sigue vendiendo en local sin detenerse. TechStore es una solución robusta, segura y lista para producción. Muchas gracias.")
    ]

    crear_tabla_estilizada(
        doc,
        ["TIEMPO Y SECCIÓN", "GUION EXACTO A PRONUNCIAR"],
        tabla_pitch,
        anchos=[1.8, 4.7],
        col_fondo_enc="0F172A"
    )

    # Banco de Preguntas y Respuestas Infalibles
    doc.add_page_break()
    doc.add_heading("Banco de Preguntas Típicas del Jurado y Respuestas Infalibles", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "Prepárate con estos argumentos técnicos y de negocio ante las preguntas más exigentes que suele formular el jurado examinador:"
    )

    preguntas_jurado = [
        ("1. ¿Qué sucede si la tienda se queda sin internet a mitad de una jornada comercial?",
         "El sistema continúa operando al 100% de su capacidad. Gracias a nuestra arquitectura Offline-First en SQLite local, los cajeros pueden seguir cobrando, emitiendo comprobantes PDF y registrando clientes sin depender de la red. Cuando la conexión a internet se restablece, el servicio de sincronización híbrida detecta la conexión y sube los registros pendientes a PostgreSQL sin duplicados mediante UUIDs."),
        ("2. ¿Cómo garantizan que el código SKU no se repita nunca entre productos?",
         "Implementamos una doble barrera: en la capa de software, la función 'generar_sku_sugerido' consulta el correlativo más alto libre en tiempo real; y en la capa de persistencia, la columna 'codigo' en la tabla SQLite 'productos' cuenta con una restricción UNIQUE a nivel de esquema, imposibilitando cualquier inserción duplicada."),
        ("3. ¿Por qué el Asistente de Reposición es superior a una simple alerta de stock bajo?",
         "Porque las alertas tradicionales son estáticas y pasivas: te avisan cuando el producto ya se agotó y perdiste ventas. Nuestro Asistente es predictivo: calcula la velocidad diaria de rotación (Ventas 30d / 30) y los días de autonomía. Esto permite anticiparse semanas antes del desabastecimiento, calculando exactamente cuántas unidades pedir a cada mayorista y el presupuesto en Soles requerido."),
        ("4. ¿Cómo evitan que un cajero venda un producto que físicamente no existe en almacén?",
         "Mediante control transaccional atómico. Antes de insertar la cabecera de la venta, el modelo VentaModel ejecuta una verificación de stock con SELECT FOR UPDATE conceptual en SQLite. Si cualquiera de los ítems del carrito supera la existencia real, se ejecuta un 'conn.rollback()' y la transacción entera se anula, informando al usuario y protegiendo el inventario."),
        ("5. ¿Qué pasa si un administrador desactiva un producto o a un empleado?",
         "Aplicamos Borrado Lógico mediante la columna 'activo = 0'. El registro deja de aparecer en los selectores de venta o pierde acceso al login, pero todas sus compras, ventas pasadas y movimientos en el Kardex se conservan intactos para auditoría fiscal y contable."),
        ("6. ¿Por qué es seguro el almacenamiento de contraseñas en TechStore?",
         "Porque no utilizamos texto plano ni algoritmos vulnerables como MD5 o SHA1. Usamos PBKDF2-HMAC-SHA256 con 100,000 rondas y una sal criptográfica pseudoaleatoria de 16 bytes generada por 'os.urandom()'. Esto protege las credenciales incluso contra ataques de diccionario o tablas Rainbow en caso de una filtración de base de datos."),
        ("7. ¿Cómo protegieron los costos del negocio frente a los vendedores?",
         "A través de la matriz de permisos y vistas restringidas. Cuando un usuario inicia sesión con rol 'vendedor', el sistema oculta las columnas de precio de compra en el inventario, bloquea el acceso a reportes financieros de ganancias y desactiva la gestión de usuarios. El vendedor solo puede emitir ventas y consultar existencias disponibles."),
        ("8. ¿Cómo facilitaron la configuración de la base de datos en la nube para usuarios sin experiencia?",
         "Creamos el 'Asistente de Desglose de URL'. Servicios modernos como Neon o Supabase entregan una sola cadena de conexión 'postgresql://...'. Nuestro sistema desglosa automáticamente servidor, puerto, base de datos, usuario, contraseña y modo SSL en milisegundos, eliminando los errores de tipeo y ofreciendo diagnósticos comprensibles en español ante fallos de conexión.")
    ]

    crear_tabla_estilizada(
        doc,
        ["PREGUNTA DEL JURADO", "RESPUESTA TÉCNICA Y DE NEGOCIO"],
        preguntas_jurado,
        anchos=[2.2, 4.3],
        col_fondo_enc="1E293B"
    )

    ruta_guion = "Guion_de_Exposicion_TechStore.docx"
    doc.save(ruta_guion)
    print(f"✔ [ÉXITO] Archivo generado: {ruta_guion}")


# ==============================================================================
# 2. GENERACIÓN DEL MANUAL DETALLADO (DOCUMENTACIÓN COMPLETA CON IMÁGENES)
# ==============================================================================
def generar_manual_detallado():
    print("Generando 'Manual_Detallado_Sistema_TechStore.docx'...")
    doc = docx.Document()

    # Configurar márgenes
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)

    # Portada Ejecutiva Formal
    p_port = doc.add_paragraph()
    p_port.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p_port.add_run("\n\n")
    run_badge = p_port.add_run("MANUAL TÉCNICO Y OPERATIVO DEL SISTEMA\n")
    run_badge.font.name = "Segoe UI"
    run_badge.font.size = Pt(12)
    run_badge.font.bold = True
    run_badge.font.color.rgb = RGBColor(2, 132, 199)

    run_tit = p_port.add_run("TECHSTORE COMPUTADORAS\n")
    run_tit.font.name = "Segoe UI"
    run_tit.font.size = Pt(26)
    run_tit.font.bold = True
    run_tit.font.color.rgb = RGBColor(15, 23, 42)

    run_sub = p_port.add_run(
        "Sistema Integral de Gestión de Inventario, Punto de Venta (POS), Kardex,\n"
        "Código SKU Inteligente, Asistente de Reposición por Demanda,\n"
        "Control de Usuarios por Roles y Conexión Híbrida en la Nube (SQLite + PostgreSQL)\n\n"
    )
    run_sub.font.name = "Segoe UI"
    run_sub.font.size = Pt(11)
    run_sub.font.color.rgb = RGBColor(71, 85, 105)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    crear_caja_estilizada(
        doc,
        "FICHA TÉCNICA DEL PROYECTO",
        [
            "• Lenguaje y Entorno: Python 3.10+ con Tkinter y arquitectura orientada a servicios.",
            "• Bases de Datos: SQLite 3 local (Offline-First) + PostgreSQL remoto en la nube (Neon/Supabase).",
            "• Seguridad: PBKDF2-HMAC-SHA256 (100,000 iteraciones, sal criptográfica de 16 bytes).",
            "• Motores de Generación: ReportLab (Comprobantes en PDF nativo) y openpyxl (Libros Excel .xlsx).",
            "• Control de Concurrencia: Transacciones ACID, bloqueo de stock y reversión automática (Rollback).",
            "• Estado del Proyecto: Versión 2.0 (Con mejoras de usabilidad en Nube y Gestión de Usuarios)."
        ],
        tipo="punchline"
    )

    doc.add_page_break()

    # Índice de Contenidos
    doc.add_heading("Índice General de Contenidos", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    indice_items = [
        ("1. Arquitectura del Sistema y Tecnologías Utilizadas", "Página 3"),
        ("2. Módulo de Seguridad y Autenticación Criptográfica (Login)", "Página 4"),
        ("3. Módulo de Panel Principal (Dashboard Ejecutivo en Tiempo Real)", "Página 6"),
        ("4. Módulo de Inventario de Productos y Generador de SKU Nemotécnico", "Página 8"),
        ("5. Módulo del Asistente Inteligente de Reposición y Modelo de Demanda", "Página 11"),
        ("6. Módulo de Movimientos de Stock y Kardex de Auditoría", "Página 14"),
        ("7. Módulo de Directorio Unificado de Clientes y Proveedores Mayoristas", "Página 16"),
        ("8. Módulo de Punto de Venta (POS), Facturación y Reversión Transaccional", "Página 18"),
        ("9. Módulo de Reportes Gerenciales y Exportación a Microsoft Excel", "Página 21"),
        ("10. Módulo de Gestión de Usuarios, Asignación de Roles y Control de Acceso", "Página 23"),
        ("11. Módulo de Conexión y Respaldo Híbrido en la Nube (PostgreSQL)", "Página 26"),
        ("12. Diccionario de Datos del Modelo Relacional", "Página 29"),
        ("13. Matriz Comparativa de Permisos por Rol (Administrador vs Vendedor)", "Página 32"),
        ("14. Guía de Despliegue e Instalación en Nuevos Equipos", "Página 33")
    ]

    crear_tabla_estilizada(
        doc,
        ["CAPÍTULO / SECCIÓN", "UBICACIÓN"],
        indice_items,
        anchos=[5.2, 1.3],
        col_fondo_enc="1E293B"
    )

    doc.add_page_break()

    # CAPÍTULO 1: ARQUITECTURA
    doc.add_heading("1. Arquitectura del Sistema y Tecnologías Utilizadas", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "TechStore ha sido desarrollado bajo un patrón de capas desacopladas (Model-View-Service), garantizando que "
        "la interfaz gráfica de usuario en Tkinter no se comunique directamente con consultas SQL desordenadas, sino que interactúe "
        "con modelos de datos encapsulados y servicios especializados de negocio."
    )

    arq_tabla = [
        ("Capa de Presentación (UI)", "Tkinter con ttk estilizado", "Ventanas modales, notebooks con pestañas, tablas Treeview con ordenamiento dinámico y validaciones en tiempo real."),
        ("Capa de Modelos (Models)", "Usuario, Producto, Venta, Movimiento, Cliente, Proveedor", "Encapsulan las reglas de negocio, validaciones atómicas de stock, hashes de contraseñas y transacciones ACID."),
        ("Capa de Servicios (Services)", "SyncService, ExcelService, PDFService, ReposicionService", "Generación de comprobantes en PDF con ReportLab, hojas Excel corporativas con openpyxl y sincronización híbrida."),
        ("Capa de Persistencia Híbrida", "SQLite 3 (Local) + PostgreSQL (Nube)", "Almacenamiento local ultrarrápido sin dependencia de internet, respaldado por sincronización bidireccional idempotente.")
    ]

    crear_tabla_estilizada(
        doc,
        ["CAPA DE SOFTWARE", "TECNOLOGÍA", "RESPONSABILIDAD PRINCIPAL"],
        arq_tabla,
        anchos=[1.8, 1.9, 2.8],
        col_fondo_enc="0F172A"
    )

    # CAPÍTULO 2: LOGIN
    doc.add_heading("2. Módulo de Seguridad y Autenticación Criptográfica (Login)", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "El acceso al sistema está blindado mediante el estándar criptográfico PBKDF2 (Password-Based Key Derivation Function 2) "
        "utilizando el algoritmo HMAC-SHA256 con 100,000 rondas de derivación. Por cada usuario registrado se genera una sal aleatoria "
        "de 16 bytes mediante os.urandom(), lo que neutraliza por completo los ataques de tablas Rainbow y fuerza bruta."
    )

    insertar_imagen_con_caption(doc, "capturas_guia/01_login.png", "Pantalla de Inicio de Sesión seguro con control de credenciales y roles.")

    crear_caja_estilizada(
        doc,
        "REGLAS DE NEGOCIO Y OPERACIÓN DEL LOGIN",
        [
            "1. Validación de Entrada: Nombre de usuario y contraseña obligatorios. No es sensible a mayúsculas en el username.",
            "2. Control de Estado Activo: Si la cuenta fue desactivada por el administrador, el login rechaza el acceso informando el estado sin exponer detalles internos.",
            "3. Enrutamiento por Rol: Si inicia un Administrador, se habilita la pestaña '👤 Usuarios', la edición de precios de costo y los reportes financieros. Si inicia un Vendedor, dichas áreas quedan completamente bloqueadas.",
            "4. Credenciales de Demostración: Administrador ('admin' / 'admin123') y Vendedor ('vendedor' / 'ven123')."
        ],
        tipo="punchline"
    )

    # CAPÍTULO 3: DASHBOARD
    doc.add_heading("3. Módulo de Panel Principal (Dashboard Ejecutivo)", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "El Dashboard Ejecutivo centraliza los principales indicadores clave de rendimiento (KPIs) del negocio en cuatro tarjetas "
        "calculadas de forma automática al abrir la aplicación o cambiar de pestaña. No requiere de botones manuales de actualización."
    )

    insertar_imagen_con_caption(doc, "capturas_guia/02_dashboard.png", "Dashboard Ejecutivo con métricas en tiempo real y accesos directos a módulos.")

    dash_tabla = [
        ("VENTAS DEL DÍA", "Muestra el importe acumulado en Soles (S/) de las ventas del día actual y el conteo de comprobantes emitidos.", "Permite al gerente conocer la recaudación diaria al instante."),
        ("PRODUCTOS ACTIVOS", "Conteo total de componentes de computación y periféricos vigentes en el catálogo de almacén.", "Control del volumen del portafolio comercial."),
        ("ALERTA STOCK BAJO (💡 ASISTENTE)", "Conteo de productos con stock igual o menor a su stock mínimo configurado. ¡Es interactiva y abre el Asistente al hacer clic!", "Prevención temprana de quiebres de inventario."),
        ("MODO HÍBRIDO (NUBE)", "Indica el estado de la conexión en la nube y el número de registros locales pendientes de sincronizar.", "Monitoreo de la sincronización entre sucursales.")
    ]

    crear_tabla_estilizada(
        doc,
        ["TARJETA KPI", "DESCRIPCIÓN DEL CÁLCULO", "UTILIDAD DE GESTIÓN"],
        dash_tabla,
        anchos=[1.9, 2.7, 1.9],
        col_fondo_enc="0284C7"
    )

    # CAPÍTULO 4: INVENTARIO
    doc.add_heading("4. Módulo de Inventario y Generador de SKU Nemotécnico", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "El módulo de Inventario gestiona el catálogo de componentes de computación. Su innovación central es el generador "
        "automático de código SKU inteligente con estructura nemotécnica [CAT]-[MAR]-[001], garantizando códigos limpios y organizados."
    )

    insertar_imagen_con_caption(doc, "capturas_guia/03_inventario_productos.png", "Catálogo de Inventario con botón '⚡ Sugerir SKU' y formulario asistido.")

    crear_caja_estilizada(
        doc,
        "FUNCIONAMIENTO DEL GENERADOR DE CÓDIGO SKU INTELIGENTE",
        [
            "• Prefijo de Categoría: Toma 3 letras nemotécnicas representativas (ej. Laptops -> 'LAP', Procesadores -> 'CPU', Tarjetas Gráficas -> 'GPU', Memorias RAM -> 'RAM', Almacenamiento -> 'SSD', Fuentes -> 'PSU').",
            "• Prefijo de Marca: Toma las primeras 3 letras del fabricante (ej. Lenovo -> 'LEN', AMD -> 'AMD', Kingston -> 'KNG', ASUS -> 'ASU').",
            "• Correlativo Secuencial: Consulta en SQLite todos los códigos con ese prefijo y determina el siguiente número disponible en formato de 3 dígitos ('001', '002', etc.).",
            "• Validación Anti-Duplicados: Si un código ya existe, avanza automáticamente al siguiente hasta encontrar uno libre."
        ],
        tipo="punchline"
    )

    # CAPÍTULO 5: ASISTENTE DE REPOSICIÓN
    doc.add_heading("5. Módulo del Asistente Inteligente de Reposición y Modelo de Demanda", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "El Asistente Inteligente de Reposición es el motor analítico de compras de TechStore. Aplica un modelo cuantitativo de "
        "gestión de inventarios que evalúa las existencias físicas frente a la demanda real de los últimos 30 días."
    )

    insertar_imagen_con_caption(doc, "capturas_guia/04_asistente_reposicion.png", "Asistente Inteligente de Reposición con cálculo de cobertura, autonomía y presupuesto.")

    doc.add_heading("Modelo Matemático de Demanda y Reposición", level=2)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(2, 132, 199)

    doc.add_paragraph(
        "El asistente calcula tres métricas matemáticas clave por cada producto del catálogo:\n\n"
        "1. Demanda Diaria Promedio (D): D = Ventas_Últimos_30_Días / 30\n"
        "2. Autonomía de Stock en Días (A): A = Stock_Actual / D (Si D > 0)\n"
        "3. Cantidad Sugerida a Comprar (Q): Q = (D × Días_Cobertura) + Stock_Mínimo - Stock_Actual\n"
        "4. Presupuesto de Inversión en Soles: Inversión = Cantidad_Sugerida × Precio_Compra"
    )

    urg_tabla = [
        ("🔴 CRÍTICO", "Stock = 0", "Agotamiento total. Quiebre de stock activo con ventas perdidas."),
        ("🟠 URGENTE", "Stock <= Mínimo / 2 o Autonomía <= 3 días", "Queda menos de la mitad del mínimo o se agotará en menos de 72 horas."),
        ("🟡 ALERTA", "Stock <= Stock Mínimo", "Alcanzó el nivel de seguridad de reserva establecido."),
        ("🔵 PREVENTIVO", "Stock > Mínimo pero Autonomía <= 7 días", "Hay stock disponible pero su alta rotación de ventas causará desabastecimiento pronto.")
    ]

    crear_tabla_estilizada(
        doc,
        ["NIVEL DE URGENCIA", "CRITERIO DE DISPARO", "DESCRIPCIÓN DEL ESTADO"],
        urg_tabla,
        anchos=[1.8, 2.5, 2.2],
        col_fondo_enc="0F172A"
    )

    # CAPÍTULO 6: KARDEX
    doc.add_heading("6. Módulo de Movimientos de Stock y Kardex de Auditoría", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "El Kardex audita todos los ingresos y salidas físicas de mercadería. Garantiza la trazabilidad legal y contable "
        "asociando cada entrada a una factura o guía de proveedor mayorista, y cada salida por merma a un motivo técnico justificado."
    )

    insertar_imagen_con_caption(doc, "capturas_guia/05_movimientos_kardex.png", "Kardex de Auditoría con historial detallado de entradas, salidas y mermas.")

    # CAPÍTULO 7: CONTACTOS
    doc.add_heading("7. Módulo de Directorio Unificado de Clientes y Proveedores", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "Centraliza el directorio de compradores (para emisión de boletas y facturas) y de proveedores mayoristas "
        "(para registrar órdenes de compra en el Kardex). Incluye el cliente por defecto 'Público General' con DNI '00000000' "
        "para ventas rápidas en mostrador en menos de 5 segundos."
    )

    insertar_imagen_con_caption(doc, "capturas_guia/06_contactos.png", "Directorio unificado de Clientes y Proveedores Mayoristas.")

    # CAPÍTULO 8: POS
    doc.add_heading("8. Módulo de Punto de Venta (POS) y Facturación", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "El Punto de Venta combina alta velocidad de facturación con validación estricta de stock en tiempo real y protección "
        "transaccional mediante Rollback. Si un vendedor intenta facturar unidades no disponibles físicamente en almacén, "
        "el sistema cancela la operación automáticamente, impidiendo cualquier descuadre de inventario."
    )

    insertar_imagen_con_caption(doc, "capturas_guia/07_punto_venta_pos.png", "Punto de Venta con carrito dinámico, descuentos y emisión de PDF con ReportLab.")

    crear_caja_estilizada(
        doc,
        "CARACTERÍSTICAS DEL COMPROBANTE EN PDF CON REPORTLAB",
        [
            "• Cabecera Corporativa con RUC, dirección, teléfono y numeración correlativa (Boleta B-XXXXXX o Factura F-XXXXXX).",
            "• Desglose Detallado: Código SKU, descripción del componente, cantidad, precio unitario y total.",
            "• Discriminación de Impuestos: Subtotal neto, descuentos aplicados, IGV (18%) y total a pagar en Soles.",
            "• Guardado Automático: El PDF se almacena en la carpeta 'documentos_generados/comprobantes/' para reimpresión inmediata."
        ],
        tipo="punchline"
    )

    # CAPÍTULO 9: REPORTES EXCEL
    doc.add_heading("9. Módulo de Reportes Gerenciales y Exportación a Excel", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "Consolida los ingresos por ventas, descuentos aplicados y ticket promedio por cualquier rango de fechas. "
        "Utiliza la librería openpyxl para generar planillas nativas de Microsoft Excel (.xlsx) con estilos corporativos, "
        "colores de cabecera, bordes y fórmulas SUM integradas."
    )

    insertar_imagen_con_caption(doc, "capturas_guia/08_reportes_excel.png", "Módulo de Reportes con indicadores de facturación y botones de exportación a Excel.")

    # CAPÍTULO 10: USUARIOS MEJORADA
    doc.add_heading("10. Módulo de Gestión de Usuarios y Matriz de Roles (Versión Mejorada)", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "El módulo de usuarios ha sido completamente renovado para brindar una experiencia ordenada, clara y asistida, "
        "incluso para usuarios sin experiencia previa en sistemas administrativos."
    )

    insertar_imagen_con_caption(doc, "capturas_guia/09_usuarios.png", "Gestión de Usuarios con sugerencia de login, contraseñas, tarjeta de permisos y ordenamiento interactivo.")

    crear_caja_estilizada(
        doc,
        "MEJORAS INCORPORADAS EN LA GESTIÓN DE USUARIOS",
        [
            "1. ⚡ Sugerir Login Automático: Al escribir el nombre del colaborador (ej. 'Carlos Mendoza'), el sistema genera automáticamente un usuario único (ej. 'cmendoza') sin duplicados.",
            "2. 🎲 Generador de Claves Seguras: Genera contraseñas temporales fáciles de recordar (ej. 'Tech2026!') para entregarlas al nuevo empleado.",
            "3. 📋 Tarjeta Dinámica de Permisos: Al seleccionar 'Vendedor' o 'Administrador', la tarjeta explica en tiempo real qué acciones tiene permitidas y cuáles protegidas (los costos mayoristas y ganancias quedan ocultos para el vendedor).",
            "4. 📊 Ordenamiento Interactivo por Columnas: Haz clic sobre ID, Usuario, Nombre, Rol, Estado o Fecha para ordenar en orden ascendente (▲) o descendente (▼).",
            "5. 🔍 Buscador y Filtros en Tiempo Real: Búsqueda instantánea mientras escribes y filtros por Rol (Administrador/Vendedor) y Estado (Activos/Desactivados).",
            "6. 🔄 Reactivación de Cuentas: Permite recuperar usuarios suspendidos sin perder su historial y con blindaje total del Administrador Principal ID 1."
        ],
        tipo="punchline"
    )

    # CAPÍTULO 11: NUBE MEJORADA
    doc.add_heading("11. Módulo de Conexión y Respaldo Híbrido en la Nube (PostgreSQL)", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "Permite operar con arquitectura híbrida: velocidad local instantánea en SQLite y sincronización central en PostgreSQL. "
        "La interfaz ha sido rediseñada para ofrecer máxima claridad y facilidad de conexión."
    )

    insertar_imagen_con_caption(doc, "capturas_guia/10_config_nube.png", "Configuración de Nube con asistente de URL directa, semáforo en vivo y sincronización.")

    crear_caja_estilizada(
        doc,
        "MEJORAS INCORPORADAS EN LA CONEXIÓN A LA NUBE",
        [
            "1. ⚡ Asistente de Desglose de URL: Copia el 'Connection String' directo de proveedores como Neon.tech o Supabase (ej. postgresql://...) y el sistema desglosa servidor, puerto, base de datos, usuario y SSL automáticamente.",
            "2. 🟢 Semáforo de Estado en Vivo: Tarjeta visual que informa en tiempo real si el sistema está 'En Línea' o en 'Modo Local Offline', junto al conteo de registros pendientes de subir.",
            "3. 💡 Guía Integrada para Principiantes: Acordeón explicativo que responde qué es la nube, cómo protege los datos ante cortes de luz y cómo obtener una base de datos gratis en 2 minutos.",
            "4. 🔍 Diagnósticos en Español Comprensible: Traduce errores de red a recomendaciones prácticas (verificar internet, revisar espacios en contraseñas o activar modo SSL 'require').",
            "5. 🔄 Sincronización Inmediata: Botón para probar la subida y descarga de datos directamente desde la ventana de configuración sin salir."
        ],
        tipo="punchline"
    )

    # CAPÍTULO 12: DICCIONARIO DE DATOS
    doc.add_heading("12. Diccionario de Datos del Modelo Relacional", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "La base de datos SQLite cuenta con 8 tablas relacionales principales y columnas de auditoría distribuida "
        "(uuid, sincronizado, fecha_modificacion) para permitir la sincronización híbrida con PostgreSQL sin conflictos de claves autoincrementales:"
    )

    dicc_tablas = [
        ("usuarios", "id (PK), uuid, username, password_hash, salt, nombre_completo, rol, activo, creado_en", "Almacena las cuentas del personal con contraseñas PBKDF2 y roles (administrador/vendedor)."),
        ("categorias", "id (PK), uuid, nombre, descripcion, activo", "Familias de componentes de cómputo (Procesadores, GPUs, Laptops, etc.)."),
        ("proveedores", "id (PK), uuid, ruc, razon_social, contacto_nombre, telefono, email, direccion, activo", "Distribuidores mayoristas de tecnología con RUC y datos de contacto."),
        ("productos", "id (PK), uuid, codigo (UNIQUE), nombre, categoria_id (FK), proveedor_id (FK), marca, precio_compra, precio_venta, stock, stock_minimo, descripcion, activo", "Catálogo maestro de hardware con SKU nemotécnico, existencias y costos."),
        ("clientes", "id (PK), uuid, tipo_documento, numero_documento, nombre_razon_social, telefono, email, direccion, activo", "Directorio de compradores para emisión de comprobantes."),
        ("movimientos_stock", "id (PK), uuid, producto_id (FK), tipo_movimiento, cantidad, motivo, referencia, fecha, usuario_id (FK), proveedor_id (FK)", "Kardex de auditoría física de entradas y salidas de almacén."),
        ("ventas", "id (PK), uuid, numero_comprobante, tipo_comprobante, cliente_id (FK), usuario_id (FK), subtotal, descuento, igv, total, metodo_pago, fecha_hora, estado", "Cabecera transaccional de facturación y comprobantes."),
        ("detalle_ventas", "id (PK), uuid, venta_id (FK), producto_id (FK), cantidad, precio_unitario, subtotal, total", "Líneas de productos vendidos en cada comprobante emitido.")
    ]

    crear_tabla_estilizada(
        doc,
        ["TABLA SQLITE", "COLUMNAS Y CLAVES", "PROPÓSITO EN EL NEGOCIO"],
        dicc_tablas,
        anchos=[1.5, 2.7, 2.3],
        col_fondo_enc="0F172A"
    )

    # CAPÍTULO 13: MATRIZ DE PERMISOS
    doc.add_heading("13. Matriz Comparativa de Permisos por Rol", level=1)
    doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(15, 23, 42)

    matriz_perm = [
        ("Acceso al Punto de Venta (POS) y emisión de comprobantes", "✔ Sí permitido", "✔ Sí permitido"),
        ("Consultar catálogo de hardware y stock disponible", "✔ Sí permitido", "✔ Sí permitido"),
        ("Visualizar Precios de Compra (Costos Mayoristas)", "✔ Visible y editable", "❌ Oculto y bloqueado"),
        ("Registrar nuevos clientes en mostrador", "✔ Sí permitido", "✔ Sí permitido"),
        ("Registrar entradas de mercadería mayorista en Kardex", "✔ Sí permitido", "❌ Bloqueado"),
        ("Ajustar stock por pérdida o daño físico de piezas", "✔ Sí permitido", "❌ Bloqueado"),
        ("Acceso al Asistente Inteligente de Reposición", "✔ Sí permitido", "✔ Sí permitido"),
        ("Exportar reportes de ventas y utilidades a Excel", "✔ Sí permitido", "❌ Pestaña oculta"),
        ("Crear, editar, ordenar y reactivar cuentas de usuarios", "✔ Sí permitido", "❌ Pestaña oculta"),
        ("Configurar parámetros de PostgreSQL en la Nube", "✔ Sí permitido", "❌ Bloqueado")
    ]

    crear_tabla_estilizada(
        doc,
        ["FUNCIÓN / CAPACIDAD DEL SISTEMA", "ROL ADMINISTRADOR", "ROL VENDEDOR"],
        matriz_perm,
        anchos=[3.3, 1.6, 1.6],
        col_fondo_enc="1E293B"
    )

    ruta_manual = "Manual_Detallado_Sistema_TechStore.docx"
    doc.save(ruta_manual)
    print(f"✔ [ÉXITO] Archivo generado: {ruta_manual}")

if __name__ == "__main__":
    generar_guion_exposicion()
    generar_manual_detallado()
