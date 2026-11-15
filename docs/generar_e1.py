#!/usr/bin/env python3
"""Genera el entregable E1 (documento de diseño de Cerberos) en Word.

Uso:  python3 docs/generar_e1.py     ->  docs/E1-Diseno-Cerberos.docx
Luego: soffice --headless --convert-to pdf docs/E1-Diseno-Cerberos.docx --outdir docs
"""
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "E1-Diseno-Cerberos.docx"
DIAGRAMA = AQUI / "arquitectura.png"
FUENTE = "Arial"
AZUL = RGBColor(0x1F, 0x3A, 0x5F)

doc = Document()

# ---------------------------------------------------------------- estilos --
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.59), Cm(27.94)  # carta
sec.left_margin = sec.right_margin = Cm(2.5)
sec.top_margin = sec.bottom_margin = Cm(2.5)

normal = doc.styles["Normal"]
normal.font.name = FUENTE
normal.font.size = Pt(12)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), FUENTE)
normal.paragraph_format.space_after = Pt(8)
normal.paragraph_format.line_spacing = 1.15

for nombre, tam in (("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 12)):
    st = doc.styles[nombre]
    st.font.name = FUENTE
    st.font.size = Pt(tam)
    st.font.bold = True
    st.font.color.rgb = AZUL
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FUENTE)
    st.element.rPr.rFonts.set(qn("w:ascii"), FUENTE)
    st.element.rPr.rFonts.set(qn("w:hAnsi"), FUENTE)
    st.paragraph_format.space_before = Pt(14)
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.keep_with_next = True


# ------------------------------------------------------------- utilidades --
def p(texto="", negrita=False, centro=False, tam=None, cursiva=False, despues=None):
    par = doc.add_paragraph()
    if centro:
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    _rico(par, texto, negrita=negrita, tam=tam, cursiva=cursiva)
    if despues is not None:
        par.paragraph_format.space_after = Pt(despues)
    return par


def _rico(par, texto, negrita=False, tam=None, cursiva=False):
    """Escribe texto; los tramos entre ** van en negrita y entre ` en monoespaciado."""
    import re

    for trozo in re.split(r"(\*\*.+?\*\*|`.+?`)", texto):
        if not trozo:
            continue
        if trozo.startswith("**"):
            r = par.add_run(trozo[2:-2])
            r.bold = True
        elif trozo.startswith("`"):
            r = par.add_run(trozo[1:-1])
            r.font.name = "Courier New"
            r._element.rPr.rFonts.set(qn("w:eastAsia"), "Courier New")
            r.font.size = Pt((tam or 12) - 1)
            r.bold = negrita
            continue
        else:
            r = par.add_run(trozo)
            r.bold = negrita
        r.italic = cursiva
        if tam:
            r.font.size = Pt(tam)


def vineta(texto):
    par = doc.add_paragraph(style="List Bullet")
    par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    par.paragraph_format.space_after = Pt(3)
    _rico(par, texto)
    return par


def numerado(texto):
    par = doc.add_paragraph(style="List Number")
    par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    par.paragraph_format.space_after = Pt(3)
    _rico(par, texto)
    return par


def _sombra(celda, color):
    tcPr = celda._element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def tabla(encabezados, filas, anchos, tam=9, titulo=None):
    if titulo:
        t = p(titulo, negrita=True, tam=10, despues=3)
        t.alignment = WD_ALIGN_PARAGRAPH.LEFT
        t.paragraph_format.keep_with_next = True
    tb = doc.add_table(rows=1, cols=len(encabezados))
    tb.style = "Table Grid"
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    tb.autofit = False
    for col, a in zip(tb.columns, anchos):
        col.width = Cm(a)
    for i, (h, a) in enumerate(zip(encabezados, anchos)):
        c = tb.rows[0].cells[i]
        c.width = Cm(a)
        _sombra(c, "1F3A5F")
        par = c.paragraphs[0]
        par.paragraph_format.space_after = Pt(0)
        r = par.add_run(h)
        r.bold = True
        r.font.size = Pt(tam)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    # repetir encabezado si la tabla cruza de página
    trPr = tb.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trPr.append(th)
    for n, fila in enumerate(filas):
        celdas = tb.add_row().cells
        for i, (v, a) in enumerate(zip(fila, anchos)):
            celdas[i].width = Cm(a)
            if n % 2:
                _sombra(celdas[i], "F3F4F6")
            par = celdas[i].paragraphs[0]
            par.paragraph_format.space_after = Pt(0)
            par.paragraph_format.line_spacing = 1.0
            _rico(par, v, tam=tam)
    for g, a in zip(tb._tbl.tblGrid.findall(qn("w:gridCol")), anchos):
        g.set(qn("w:w"), str(int(a * 567)))
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return tb


def salto():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def h1(t):
    doc.add_heading(t, level=1)


def h2(t):
    doc.add_heading(t, level=2)


# ---------------------------------------------------------------- portada --
for linea in (
    "UNIVERSIDAD TECNOLÓGICA DE PANAMÁ",
    "FACULTAD DE INGENIERÍA DE SISTEMAS COMPUTACIONALES",
    "DEPARTAMENTO DE ARQUITECTURA Y REDES DE COMPUTADORAS",
    "LICENCIATURA EN CIBERSEGURIDAD",
):
    p(linea, negrita=True, centro=True, tam=13, despues=4)
for _ in range(3):
    p()
p("CIBERSEGURIDAD II", negrita=True, centro=True, tam=14)
p("PROYECTO FINAL", negrita=True, centro=True, tam=14)
p("Seguridad en accesos: identificación, autenticación y autorización", centro=True, tam=12)
p()
p("CERBEROS", negrita=True, centro=True, tam=26, despues=2)
p("Mesa de ayuda de TI con solicitud de accesos", centro=True, tam=14)
p()
p("Entregable E1 — Documento de diseño", negrita=True, centro=True, tam=13)
p("Fase 1: diseño y nomenclatura", centro=True)
for _ in range(2):
    p()
p("Integrantes:", negrita=True, centro=True, despues=2)
p("David Moreno — 8-1039-2423", centro=True, despues=2)
p("______________________ — ____________", centro=True, despues=2)
p("______________________ — ____________", centro=True, despues=2)
p("______________________ — ____________", centro=True)
p()
p("Grupo: 1S3122", centro=True, despues=2)
p("Profesora: Mildred Echezano", centro=True, despues=2)
p("Repositorio: ______________________________", centro=True, despues=2)
p("Noviembre de 2026", centro=True)
salto()

# --------------------------------------------------------- 1. aplicación --
h1("1. Descripción de la aplicación")
p(
    "**Cerberos** es una aplicación web de mesa de ayuda de TI. Los empleados de una organización la usan para dos "
    "cosas: reportar problemas técnicos (tickets de incidencia) y pedir acceso a un sistema (solicitudes de acceso). "
    "El nombre viene del perro de tres cabezas que guarda la entrada: la aplicación vigila quién entra, a qué y con "
    "permiso de quién."
)
p("El recorrido normal de cada tipo de caso es el siguiente:")
vineta(
    "**Ticket de incidencia.** El empleado lo crea; el supervisor de la mesa de ayuda lo asigna a un técnico; el "
    "técnico lo atiende y lo cierra. El empleado solo ve sus propios tickets."
)
vineta(
    "**Solicitud de acceso.** El empleado la crea indicando el sistema y el motivo; el jefe de su área la aprueba o "
    "la rechaza; si se aprueba, el supervisor la asigna y un técnico ejecuta el alta. Nadie aprueba su propia "
    "solicitud, ni siquiera un jefe de área."
)
p(
    "Todas las acciones relevantes (inicios de sesión, aprobaciones, asignaciones, intentos denegados) quedan en un "
    "registro de auditoría que solo pueden leer el administrador y el auditor."
)
p("El proyecto permite demostrar tres controles de la guía:")
vineta("**Control por propiedad:** el empleado solo accede a los registros donde él es el creador.")
vineta(
    "**Separación de funciones:** quien pide no aprueba, quien aprueba no ejecuta y quien audita no modifica."
)
vineta("**Trazabilidad:** un panel de auditoría que se puede proyectar durante la sustentación.")

# ----------------------------------------------------------- 2. conceptos --
h1("2. Conceptos base")
h2("2.1 Identificación, autenticación y autorización")
tabla(
    ["Concepto", "Pregunta que responde", "En Cerberos"],
    [
        [
            "Identificación",
            "¿Quién dice ser?",
            "El nombre de usuario `apellido.nombre` y la convención de nombres de la sección 3. Solo declara una identidad; no prueba nada.",
        ],
        [
            "Autenticación",
            "¿Puede probar que lo es?",
            "Keycloak comprueba la contraseña contra el directorio y, según el rol, un código TOTP. El resultado es un ID token firmado [1].",
        ],
        [
            "Autorización",
            "¿Qué se le permite hacer?",
            "La API revisa en cada petición el rol y los scopes del access token, y además si el registro le pertenece. Lo no permitido se rechaza [11].",
        ],
    ],
    [3.2, 4.0, 9.3],
)
h2("2.2 Proveedor de identidad, Relying Party y API protegida")
vineta(
    "**Proveedor de identidad (IdP).** Es el servidor que autentica a los usuarios y emite los tokens. OpenID Connect "
    "lo llama OpenID Provider: un servidor de autorización OAuth 2.0 que implementa OpenID Connect [1]. En Cerberos es "
    "Keycloak."
)
vineta(
    "**Relying Party (RP).** Es el cliente OAuth 2.0 que usa OpenID Connect: la aplicación que no guarda contraseñas "
    "y confía en el IdP para saber quién es el usuario [1]. En Cerberos es la aplicación web hecha con Flask y Authlib."
)
vineta(
    "**API protegida (servidor de recursos).** Es el servidor que guarda los recursos y solo responde a peticiones "
    "que traen un access token válido [2]. En Cerberos es la API de tickets y solicitudes, que valida la firma del "
    "token con las claves públicas del IdP (JWKS)."
)

# -------------------------------------------------------- 3. nomenclatura --
h1("3. Nomenclatura de identificación")
p(
    "Todos los objetos del proyecto siguen la convención de la sección 6 de la guía. Reglas generales: sin acentos, "
    "sin espacios y sin caracteres especiales; minúsculas, salvo grupos y roles, que van en MAYÚSCULAS."
)
tabla(
    ["Elemento", "Formato", "Ejemplo en Cerberos", "Regla"],
    [
        ["Dominio del directorio", "`<aplicación>.lab`", "`cerberos.lab` (base `DC=cerberos,DC=lab`)", "Se evita `.local` porque choca con mDNS en Linux."],
        ["Usuario final", "`apellido.nombre`", "`perez.juan`", "Homónimos: se agrega un número (`perez.juan2`). El correo nunca es el identificador interno."],
        ["Cuenta de servicio", "`svc-<aplicación>-<función>`", "`svc-cerberos-ldap`", "Sin inicio de sesión interactivo; su contraseña vive fuera del código."],
        ["Unidad organizativa", "`<ÁREA>`", "`OU=FINANZAS,OU=CERBEROS`", "Una OU por área, todas bajo `OU=CERBEROS`."],
        ["Grupo de directorio", "`GRP_<ÁREA>_<ROL>`", "`GRP_FIN_JEFE_AREA`", "Un grupo por rol y área. Área abreviada: TI, AUD, FIN, RRHH, EXT."],
        ["Rol de aplicación", "`ROL_<NOMBRE>`", "`ROL_JEFE_AREA`", "Se obtiene del grupo; nunca se asigna a mano en la aplicación."],
        ["Cliente OAuth/OIDC", "`cli-<aplicación>-<entorno>`", "`cli-cerberos-dev`", "Entornos: dev, qa, prod. Un cliente por entorno."],
        ["Realm de Keycloak", "(fijado por la guía)", "`proyecto-accesos`", "Un solo realm para el proyecto."],
        ["Scope (permiso)", "`<recurso>:<acción>`", "`tickets:leer_propios`", "Acciones: leer, escribir, borrar, admin. Sufijo `_propios` cuando hay control por propiedad."],
    ],
    [3.2, 3.8, 4.6, 4.9],
    titulo="Tabla 1. Convención de nombres",
)

h2("3.1 Roles de la aplicación")
p(
    "Cerberos tiene siete roles. `ROL_EMPLEADO` cumple el papel que la guía llama `ROL_USUARIO`: es el rol sujeto al "
    "control por propiedad."
)
tabla(
    ["Rol", "Quién es", "Función"],
    [
        ["`ROL_ADMIN`", "Administrador de Cerberos", "Administra la configuración y los perfiles; no atiende ni aprueba casos."],
        ["`ROL_SUPERVISOR`", "Supervisor de la mesa de ayuda", "Reparte el trabajo: asigna y reasigna tickets y solicitudes aprobadas."],
        ["`ROL_TECNICO`", "Técnico de soporte", "Atiende lo que tiene asignado."],
        ["`ROL_JEFE_AREA`", "Jefe de un área de negocio", "Aprueba o rechaza las solicitudes de acceso de su área."],
        ["`ROL_AUDITOR`", "Auditor interno", "Revisa todo en modo de solo lectura, incluida la auditoría."],
        ["`ROL_EMPLEADO`", "Cualquier empleado", "Crea tickets y solicitudes y consulta únicamente los suyos."],
        ["`ROL_INVITADO`", "Persona externa", "Solo consulta el catálogo público de servicios."],
    ],
    [3.6, 4.6, 8.3],
    titulo="Tabla 2. Roles",
)

h2("3.2 Unidades organizativas, grupos y mapeo a roles")
tabla(
    ["Unidad organizativa", "Grupo del directorio", "Rol al que mapea"],
    [
        ["`OU=TI`", "`GRP_TI_ADMIN`", "`ROL_ADMIN`"],
        ["`OU=TI`", "`GRP_TI_SUPERVISOR`", "`ROL_SUPERVISOR`"],
        ["`OU=TI`", "`GRP_TI_TECNICO`", "`ROL_TECNICO`"],
        ["`OU=AUDITORIA`", "`GRP_AUD_AUDITOR`", "`ROL_AUDITOR`"],
        ["`OU=FINANZAS`", "`GRP_FIN_JEFE_AREA`", "`ROL_JEFE_AREA`"],
        ["`OU=FINANZAS`", "`GRP_FIN_EMPLEADO`", "`ROL_EMPLEADO`"],
        ["`OU=RRHH`", "`GRP_RRHH_JEFE_AREA`", "`ROL_JEFE_AREA`"],
        ["`OU=RRHH`", "`GRP_RRHH_EMPLEADO`", "`ROL_EMPLEADO`"],
        ["`OU=EXTERNOS`", "`GRP_EXT_INVITADO`", "`ROL_INVITADO`"],
        ["`OU=SERVICIOS`", "(sin grupo de rol)", "Cuenta `svc-cerberos-ldap`"],
    ],
    [5.0, 5.8, 5.7],
    titulo="Tabla 3. OU, grupos y roles (todas las OU cuelgan de OU=CERBEROS,DC=cerberos,DC=lab)",
)
p(
    "Se usan dos áreas de negocio (Finanzas y Recursos Humanos) a propósito: así se puede probar que el jefe de un "
    "área no aprueba solicitudes de otra. El área de cada persona se guarda en el atributo `department` del "
    "directorio y llegará a la aplicación como un claim del token."
)

h2("3.3 Usuarios de prueba")
p("Son personas ficticias. Hay al menos un usuario por rol y un caso de homónimos resuelto con la regla del número.")
tabla(
    ["Usuario", "Nombre", "Área (OU)", "Grupos", "Rol resultante"],
    [
        ["`gonzalez.maria`", "María González", "TI", "`GRP_TI_ADMIN`", "`ROL_ADMIN`"],
        ["`rodriguez.ana`", "Ana Rodríguez", "TI", "`GRP_TI_SUPERVISOR`", "`ROL_SUPERVISOR`"],
        ["`castillo.luis`", "Luis Castillo", "TI", "`GRP_TI_TECNICO`", "`ROL_TECNICO`"],
        ["`vargas.elena`", "Elena Vargas", "AUDITORIA", "`GRP_AUD_AUDITOR`", "`ROL_AUDITOR`"],
        ["`mendoza.carlos`", "Carlos Mendoza", "FINANZAS", "`GRP_FIN_JEFE_AREA`, `GRP_FIN_EMPLEADO`", "`ROL_JEFE_AREA`, `ROL_EMPLEADO`"],
        ["`perez.juan`", "Juan Pérez", "FINANZAS", "`GRP_FIN_EMPLEADO`", "`ROL_EMPLEADO`"],
        ["`herrera.sofia`", "Sofía Herrera", "FINANZAS", "`GRP_FIN_EMPLEADO`", "`ROL_EMPLEADO`"],
        ["`quintero.laura`", "Laura Quintero", "RRHH", "`GRP_RRHH_JEFE_AREA`, `GRP_RRHH_EMPLEADO`", "`ROL_JEFE_AREA`, `ROL_EMPLEADO`"],
        ["`perez.juan2`", "Juan Pérez (homónimo)", "RRHH", "`GRP_RRHH_EMPLEADO`", "`ROL_EMPLEADO`"],
        ["`batista.pedro`", "Pedro Batista", "EXTERNOS", "`GRP_EXT_INVITADO`", "`ROL_INVITADO`"],
    ],
    [3.3, 3.2, 2.4, 4.3, 3.3],
    tam=8,
    titulo="Tabla 4. Usuarios",
)
p(
    "Los jefes de área también son empleados: pueden pedir accesos para sí mismos, pero esa solicitud la debe aprobar "
    "otra persona. `perez.juan` y `herrera.sofia` están en la misma área para probar que un empleado no ve los "
    "tickets de un compañero."
)

h2("3.4 Clientes y scopes")
p(
    "El cliente de la aplicación es `cli-cerberos-dev`. Los clientes `cli-cerberos-qa` y `cli-cerberos-prod` quedan "
    "reservados para los otros entornos y no se crean en este laboratorio."
)
tabla(
    ["Recurso", "Scopes", "Qué permite"],
    [
        ["Tickets", "`tickets:leer_propios`, `tickets:escribir_propios`", "Crear y consultar los tickets propios."],
        ["Tickets", "`tickets:leer`, `tickets:escribir`, `tickets:borrar`", "Consultar, actualizar y borrar tickets de otros, según el rol."],
        ["Solicitudes de acceso", "`solicitudes:leer_propios`, `solicitudes:escribir_propios`", "Crear y consultar las solicitudes propias."],
        ["Solicitudes de acceso", "`solicitudes:leer`, `solicitudes:escribir`, `solicitudes:borrar`", "Consultar, atender y borrar solicitudes de otros."],
        ["Aprobaciones", "`aprobaciones:leer`, `aprobaciones:escribir`", "Ver decisiones; aprobar o rechazar una solicitud."],
        ["Asignaciones", "`asignaciones:leer`, `asignaciones:escribir`", "Ver quién atiende cada caso; asignar y reasignar."],
        ["Comentarios", "`comentarios:escribir_propios`, `comentarios:escribir`", "Comentar en casos propios o en casos de otros."],
        ["Usuarios", "`usuarios:leer`, `usuarios:admin`", "Ver perfiles; administrarlos."],
        ["Estadísticas", "`estadisticas:leer_propios`, `estadisticas:leer`", "Ver cifras propias o globales."],
        ["Auditoría", "`auditoria:leer`", "Leer el registro de auditoría. No existe scope de escritura."],
        ["Configuración", "`config:admin`", "Cambiar categorías, tiempos de atención y el catálogo."],
        ["Catálogo", "`catalogo:leer`", "Ver el catálogo público de servicios."],
    ],
    [3.4, 7.2, 5.9],
    titulo="Tabla 5. Catálogo de scopes",
)

# -------------------------------------------------------- 4. arquitectura --
h1("4. Arquitectura")
p(
    "Cerberos tiene cinco componentes: el navegador del usuario, la aplicación web (Relying Party), el proveedor de "
    "identidad, el directorio y la API protegida con su base de datos. Todos corren en contenedores sobre una red "
    "interna llamada `cerberos-net`; hacia el equipo anfitrión solo se publican los puertos HTTPS."
)
if DIAGRAMA.exists():
    doc.add_picture(str(DIAGRAMA), width=Cm(16.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    f = p("Figura 1. Arquitectura de Cerberos y flujo Authorization Code + PKCE (archivo editable: docs/arquitectura.drawio)", centro=True, tam=10, cursiva=True)
else:
    p("[Insertar aquí la Figura 1: exportar docs/arquitectura.drawio a PNG]", centro=True, cursiva=True)

tabla(
    ["Componente", "Herramienta", "Responsabilidad"],
    [
        ["Navegador", "Cualquier navegador moderno", "Muestra la aplicación y transporta las redirecciones. Nunca recibe la contraseña fuera del formulario del IdP."],
        ["Aplicación web (RP)", "Flask + Authlib", "Inicia el login OIDC, valida el ID token, mantiene la sesión y llama a la API en nombre del usuario."],
        ["Proveedor de identidad", "Keycloak 26.x", "Autentica (contraseña + TOTP), emite tokens firmados, convierte grupos en roles."],
        ["Directorio", "Samba AD DC", "Fuente única de usuarios, grupos y política de contraseñas. Keycloak lo consulta por LDAPS."],
        ["API protegida", "Flask + Authlib", "Valida el access token y decide cada operación por rol, scope y propiedad. Escribe la auditoría."],
    ],
    [3.6, 3.6, 9.3],
    titulo="Tabla 6. Componentes",
)

h2("4.1 Secuencia de autenticación (Authorization Code + PKCE)")
numerado("El usuario pide un recurso protegido. La aplicación genera un `code_verifier`, calcula su `code_challenge` con S256, y crea un `state` y un `nonce` [3].")
numerado("La aplicación redirige el navegador a Keycloak con esos valores. Keycloak muestra su formulario; el usuario escribe su contraseña y, si su rol lo exige, el código TOTP.")
numerado("Keycloak valida la contraseña contra Samba AD DC por LDAPS y lee los grupos del usuario.")
numerado("Keycloak devuelve un código de autorización al `redirect_uri` registrado, que debe coincidir exactamente.")
numerado("La aplicación canjea el código enviando el `code_verifier` y recibe el ID token, el access token y el refresh token. Valida en el ID token `iss`, `aud`, `exp`, `nonce` y la firma, y crea su sesión.")
numerado("La aplicación llama a la API con la cabecera `Authorization: Bearer`.")
numerado("La API valida la firma del access token con las claves públicas del IdP (JWKS), además de `iss`, `aud` y `exp`, y luego el rol, los scopes y la propiedad del registro. Solo entonces responde.")

h2("4.2 Cómo se cumple cada requisito obligatorio")
tabla(
    ["Requisito (guía, 7.2)", "Decisión de diseño"],
    [
        ["HTTPS en todos los componentes", "Certificados locales con mkcert para la aplicación, la API y Keycloak; LDAPS (puerto 636) entre Keycloak y el directorio."],
        ["`redirect_uri` exacto", "Una sola URI registrada en `cli-cerberos-dev`, sin comodines."],
        ["Sin Implicit ni ROPC", "En el cliente solo se habilita el flujo estándar (Authorization Code) con PKCE S256 obligatorio [4]."],
        ["Tokens de vida corta", "Access token de 5 minutos; refresh token con rotación."],
        ["Política de contraseñas", "Se aplica en el directorio: 12 caracteres, historial de 5, bloqueo tras 5 intentos (sección 7)."],
        ["Segundo factor", "TOTP obligatorio para `ROL_ADMIN`, `ROL_AUDITOR` y `ROL_JEFE_AREA` (porque aprueba accesos); recomendado para el resto."],
        ["Secretos fuera del código", "Archivo `.env` excluido por `.gitignore`; en el repositorio solo va `.env.example`."],
        ["Cierre de sesión", "La aplicación borra su sesión y llama al cierre de sesión de Keycloak para revocarla también en el IdP."],
    ],
    [5.2, 11.3],
    titulo="Tabla 7. Requisitos de autenticación",
)

# -------------------------------------------------------- 5. herramientas --
h1("5. Selección de herramientas")
p(
    "Todas las herramientas son gratuitas y funcionan sin conexión a internet una vez instaladas, lo que permite "
    "repetir el laboratorio en cualquier equipo. El equipo de trabajo usa Ubuntu."
)
tabla(
    ["Herramienta", "Función", "Licencia y costo", "Por qué se eligió", "Alternativas evaluadas", "Fuente"],
    [
        ["Keycloak 26.x", "Proveedor de identidad", "Apache 2.0, gratuito", "Implementa OIDC y OAuth 2.0, federa LDAP/AD, trae TOTP y mapeo grupo→rol sin programar.", "Auth0, Okta y Entra ID: planes gratuitos con límites y dependientes de la nube.", "[6]"],
        ["Samba AD DC", "Directorio", "GPLv3, gratuito", "Simula un Active Directory real en Linux, con LDAP, Kerberos y política de contraseñas del dominio.", "Windows Server AD DS: evaluación de 180 días y más recursos. OpenLDAP: más liviano, pero la política exige configuración adicional.", "[7]"],
        ["Python 3 + Flask", "Aplicación web y API", "PSF y BSD-3-Clause, gratuito", "Código corto y fácil de auditar; los decoradores permiten ver el control de acceso en cada endpoint.", "Django: más grande de lo necesario. FastAPI: válido, pero el equipo conoce mejor Flask.", "[9]"],
        ["Authlib", "Cliente OIDC y validación de JWT", "BSD-3-Clause, gratuito", "Implementa Authorization Code con PKCE y la validación de tokens con JWKS; se integra con Flask.", "Flask-OIDC y python-jose: menos mantenidos o cubren solo una parte.", "[8]"],
        ["Podman", "Contenedores", "Apache 2.0, gratuito", "Corre sin privilegios de root y no tiene las condiciones de licencia de Docker Desktop.", "Docker Engine: gratuito en Linux, pero su servicio corre como root.", "[10]"],
        ["mkcert", "Certificados TLS locales", "BSD-3-Clause, gratuito", "Crea una autoridad local de confianza, así el navegador no muestra advertencias.", "OpenSSL: sirve, pero requiere más pasos manuales.", "[14]"],
        ["Bruno", "Pruebas de la API", "MIT, gratuito", "Guarda las colecciones como archivos en el repositorio y no exige cuenta en la nube.", "Postman: plan gratuito, pero requiere cuenta.", "[15]"],
        ["OWASP ZAP", "Escaneo de seguridad", "Apache 2.0, gratuito", "Estándar abierto para pruebas de seguridad web, incluido el control de acceso roto.", "Burp Suite Community: el escáner automático es de pago.", "[16]"],
        ["Wireshark", "Captura de tráfico", "GPLv2, gratuito", "Demuestra que no viajan credenciales ni tokens en texto plano.", "tcpdump: captura igual, pero sin análisis gráfico.", "[17]"],
        ["Git y GitHub", "Control de versiones", "GPLv2; plan gratuito", "Deja registro cronológico del avance y de la autoría.", "GitLab: equivalente; se elige GitHub por ser el que usa el equipo.", "[18]"],
        ["draw.io", "Diagramas", "Apache 2.0, gratuito", "El diagrama se guarda como archivo editable en el repositorio.", "Lucidchart: plan gratuito limitado.", "[19]"],
    ],
    [2.2, 2.1, 2.2, 4.3, 4.3, 1.4],
    tam=8,
    titulo="Tabla 8. Herramientas y justificación",
)

# -------------------------------------------------------------- 6. matriz --
h1("6. Matriz de roles preliminar")
p(
    "Los permisos salen de lo que cada rol necesita para hacer su trabajo. Se aplican dos principios: **mínimo "
    "privilegio** y **denegación por defecto** (lo que no está permitido de forma explícita se rechaza) [11], [12]. "
    "C = crear, R = leer, U = actualizar, D = borrar, — = sin acceso."
)
M = "—"
tabla(
    ["Recurso", "ADMIN", "SUPERVISOR", "TECNICO", "JEFE_AREA", "AUDITOR", "EMPLEADO", "INVITADO"],
    [
        ["Tickets de incidencia", "R, D", "R, U", "R, U (asignados)", "R (de su área)", "R", "C, R (propios)", M],
        ["Solicitudes de acceso", "R, D", "R, U", "R, U (asignadas)", "R (de su área)", "R", "C, R (propias)", M],
        ["Aprobaciones", M, "R", M, "C (su área, nunca propias)", "R", "R (de sus solicitudes)", M],
        ["Asignaciones", M, "C, R, U", "R (propias)", M, "R", M, M],
        ["Comentarios", "R, D", "C, R", "C, R (asignados)", "C, R (de su área)", "R", "C, R (propios)", M],
        ["Usuarios y perfiles", "R, U", "R", M, M, "R", M, M],
        ["Estadísticas", "R", "R", "R (propias)", "R (de su área)", "R", "R (propias)", M],
        ["Registros de auditoría", "R", M, M, M, "R", M, M],
        ["Configuración", "R, U", M, M, M, M, M, M],
        ["Catálogo de servicios", "C, R, U, D", "R", "R", "R", "R", "R", "R"],
    ],
    [2.6, 1.4, 2.3, 2.0, 2.2, 1.7, 2.3, 2.0],
    tam=8,
    titulo="Tabla 9. Matriz de roles y permisos (los nombres de rol llevan el prefijo ROL_)",
)
h2("6.1 Reglas que acompañan a la matriz")
vineta("**Propiedad.** Con un scope `_propios`, la API solo devuelve o modifica registros cuyo creador coincide con el `sub` del token. Un registro ajeno se responde como no encontrado, para no revelar que existe.")
vineta("**Área.** El jefe de área solo ve y aprueba solicitudes cuyo solicitante pertenece a su misma área.")
vineta("**Quien pide no aprueba.** La API rechaza una aprobación si el aprobador es el mismo solicitante, aunque tenga `aprobaciones:escribir`.")
vineta("**Asignación.** El técnico solo actualiza casos que el supervisor le asignó.")
vineta("**Auditoría inalterable.** Nadie tiene permiso para modificar o borrar la auditoría; por eso no existe un scope de escritura.")
vineta("**El rol no viene del cliente.** La API toma el rol del token firmado por Keycloak y lo verifica en cada endpoint; no confía en lo que envíe la interfaz.")

h2("6.2 Scopes y justificación por rol")
tabla(
    ["Rol", "Necesidad funcional", "Scopes asignados", "Justificación del mínimo privilegio"],
    [
        ["`ROL_ADMIN`", "Administrar la configuración y los perfiles", "`usuarios:admin`, `config:admin`, `tickets:leer`, `tickets:borrar`, `solicitudes:leer`, `solicitudes:borrar`, `auditoria:leer`, `estadisticas:leer`, `catalogo:leer`", "Administra, pero no atiende ni aprueba casos, y la auditoría solo la lee: no puede alterar el rastro de sus propias acciones."],
        ["`ROL_SUPERVISOR`", "Repartir y dar seguimiento al trabajo", "`tickets:leer`, `tickets:escribir`, `solicitudes:leer`, `solicitudes:escribir`, `asignaciones:leer`, `asignaciones:escribir`, `aprobaciones:leer`, `comentarios:escribir`, `usuarios:leer`, `estadisticas:leer`, `catalogo:leer`", "Necesita ver todo para asignar. No aprueba accesos ni borra casos."],
        ["`ROL_TECNICO`", "Atender los casos asignados", "`tickets:leer`, `tickets:escribir`, `solicitudes:leer`, `solicitudes:escribir`, `asignaciones:leer`, `comentarios:escribir`, `estadisticas:leer_propios`, `catalogo:leer`", "Los scopes se limitan en la API a los casos asignados a él. No se asigna trabajo a sí mismo ni aprueba."],
        ["`ROL_JEFE_AREA`", "Decidir las solicitudes de acceso de su área", "`solicitudes:leer`, `tickets:leer`, `aprobaciones:leer`, `aprobaciones:escribir`, `comentarios:escribir`, `estadisticas:leer`, `catalogo:leer`", "Limitado a su área por el atributo `department`. No ejecuta el alta ni aprueba lo que él mismo pidió."],
        ["`ROL_AUDITOR`", "Revisar cumplimiento y trazabilidad", "`tickets:leer`, `solicitudes:leer`, `aprobaciones:leer`, `asignaciones:leer`, `usuarios:leer`, `auditoria:leer`, `estadisticas:leer`, `catalogo:leer`", "Solo lectura. Quien audita no opera ni modifica."],
        ["`ROL_EMPLEADO`", "Reportar problemas y pedir accesos", "`tickets:leer_propios`, `tickets:escribir_propios`, `solicitudes:leer_propios`, `solicitudes:escribir_propios`, `comentarios:escribir_propios`, `estadisticas:leer_propios`, `catalogo:leer`", "Control por propiedad: solo accede a registros donde su `sub` es el creador."],
        ["`ROL_INVITADO`", "Consultar información pública", "`catalogo:leer`", "Acceso mínimo, sin datos internos."],
    ],
    [2.6, 3.0, 5.9, 5.0],
    tam=8,
    titulo="Tabla 10. Scopes por rol",
)

# ---------------------------------------------------------- 7. contraseñas --
h1("7. Política de contraseñas del directorio")
p("La política se aplica en el dominio de Samba, que es la fuente única de identidades, y no en la aplicación.")
tabla(
    ["Parámetro", "Valor", "Origen"],
    [
        ["Longitud mínima", "12 caracteres", "Guía, sección 7.2."],
        ["Historial", "No reutilizar las últimas 5", "Guía, sección 7.2."],
        ["Bloqueo", "Tras 5 intentos fallidos, durante 15 minutos", "Guía, sección 7.2. NIST exige limitar los intentos fallidos y fija un máximo de 100 [5]."],
        ["Reglas de composición", "Ninguna (no se exigen mayúsculas ni símbolos)", "NIST SP 800-63B-4: no se deben imponer reglas de composición [5]."],
        ["Cambio periódico", "No se fuerza", "NIST SP 800-63B-4: no se debe exigir el cambio periódico; sí cuando hay evidencia de compromiso [5]."],
    ],
    [3.8, 5.6, 7.1],
    titulo="Tabla 11. Política de contraseñas",
)
p(
    "La versión vigente de NIST SP 800-63B (revisión 4) pide un mínimo de 15 caracteres cuando la contraseña es el "
    "único factor y permite 8 cuando forma parte de una autenticación multifactor [5]. Los 12 caracteres de la guía "
    "quedan entre ambos valores; en Cerberos los roles con más privilegio usan además TOTP. NIST también pide comparar "
    "las contraseñas nuevas con una lista de contraseñas comunes o filtradas; ese control no forma parte de este "
    "laboratorio y se anota como mejora para producción."
)

# ------------------------------------------------------------ referencias --
h1("Referencias")
refs = [
    "N. Sakimura, J. Bradley, M. Jones, B. de Medeiros y C. Mortimore, «OpenID Connect Core 1.0», OpenID Foundation, 2014. [En línea]. Disponible en: https://openid.net/specs/openid-connect-core-1_0.html",
    "D. Hardt, «The OAuth 2.0 Authorization Framework», RFC 6749, IETF, 2012. [En línea]. Disponible en: https://www.rfc-editor.org/rfc/rfc6749",
    "N. Sakimura, J. Bradley y N. Agarwal, «Proof Key for Code Exchange by OAuth Public Clients», RFC 7636, IETF, 2015. [En línea]. Disponible en: https://www.rfc-editor.org/rfc/rfc7636",
    "T. Lodderstedt, J. Bradley, A. Labunets y D. Fett, «Best Current Practice for OAuth 2.0 Security», RFC 9700, IETF, 2025. [En línea]. Disponible en: https://www.rfc-editor.org/rfc/rfc9700",
    "NIST, «Digital Identity Guidelines: Authentication and Authenticator Management», SP 800-63B-4, sec. 3.1.1.2 y 3.2.2. [En línea]. Disponible en: https://pages.nist.gov/800-63-4/sp800-63b/authenticators/",
    "Keycloak, «Documentation» y archivo de licencia del proyecto. [En línea]. Disponible en: https://www.keycloak.org/documentation y https://github.com/keycloak/keycloak/blob/main/LICENSE.txt",
    "Samba Team, «Setting up Samba as an Active Directory Domain Controller», SambaWiki. [En línea]. Disponible en: https://wiki.samba.org/index.php/Setting_up_Samba_as_an_Active_Directory_Domain_Controller",
    "Authlib, «Authlib Licenses». [En línea]. Disponible en: https://docs.authlib.org/en/latest/community/licenses.html",
    "Pallets, «Flask Documentation: License». [En línea]. Disponible en: https://flask.palletsprojects.com/en/stable/license/",
    "Podman, «What is Podman?». [En línea]. Disponible en: https://docs.podman.io/",
    "OWASP, «A01:2021 – Broken Access Control», OWASP Top 10:2021. [En línea]. Disponible en: https://owasp.org/Top10/A01_2021-Broken_Access_Control/",
    "NIST, «Role Based Access Control». [En línea]. Disponible en: https://csrc.nist.gov/projects/role-based-access-control",
    "J. Sermersheim, «Lightweight Directory Access Protocol (LDAP): The Protocol», RFC 4511, IETF, 2006. [En línea]. Disponible en: https://www.rfc-editor.org/rfc/rfc4511",
    "F. Valsorda, «mkcert». [En línea]. Disponible en: https://github.com/FiloSottile/mkcert",
    "Bruno, «Bruno: open-source API client». [En línea]. Disponible en: https://www.usebruno.com/",
    "ZAP, «Zed Attack Proxy». [En línea]. Disponible en: https://www.zaproxy.org/",
    "Wireshark Foundation, «Wireshark». [En línea]. Disponible en: https://www.wireshark.org/",
    "Git, «About: Free and Open Source». [En línea]. Disponible en: https://git-scm.com/about/free-and-open-source",
    "JGraph, «draw.io». [En línea]. Disponible en: https://www.drawio.com/",
]
for i, r in enumerate(refs, 1):
    par = doc.add_paragraph()
    par.paragraph_format.left_indent = Cm(1.0)
    par.paragraph_format.first_line_indent = Cm(-1.0)
    par.paragraph_format.space_after = Pt(4)
    run = par.add_run(f"[{i}]\t{r} (consultado: 15 de noviembre de 2026).")
    run.font.size = Pt(10)

cp = doc.core_properties
cp.author = "David Moreno"
cp.last_modified_by = "David Moreno"
cp.title = "Cerberos - Documento de diseño (E1)"
cp.comments = ""
doc.save(SALIDA)
print("Escrito", SALIDA)
