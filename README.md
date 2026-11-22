# Cerberos

Mesa de ayuda de TI con solicitud de accesos. Proyecto final de Ciberseguridad II (UTP):
identificación, autenticación con OpenID Connect y autorización por roles sobre un directorio.

## Estado

| Fase | Contenido | Estado |
|---|---|---|
| 1 | Diseño y nomenclatura (E1) | Hecha: `docs/E1-Diseno-Cerberos.docx`, secciones 1 a 3 |
| 2 | Directorio Samba AD DC | Hecha: `directorio/`, `docs/evidencias/fase2/` y sección 4 del documento |
| 3 | Keycloak (IdP) | Pendiente |
| 4 | Login OIDC en la aplicación | Pendiente |
| 5 | Autorización en la API | Pendiente |
| 6 | Pruebas y evidencias | Pendiente |
| 7 | Informe y sustentación | Pendiente |

## Estructura

```
directorio/                    Samba AD DC en contenedor: imagen, compose, datos y scripts
  datos/                       ous.csv, grupos.csv y usuarios.csv (lo que se carga en el dominio)
docs/
  E1-Diseno-Cerberos.docx      Informe del proyecto (diseño y Fase 2)
  arquitectura.drawio / .png   Diagrama de arquitectura
  evidencias/fase2/            Salida de cada prueba del directorio (texto)
  evidencias/fase2/capturas/   Capturas de las pruebas (las figuras del informe)
```

## Documento del proyecto

`docs/E1-Diseno-Cerberos.docx` es el informe. Lo editamos a mano en Word, así que la versión
del repositorio es una copia del documento de trabajo del equipo.

El diagrama editable es `docs/arquitectura.drawio` (abrir con draw.io).

## Directorio (Fase 2)

Requisitos: Podman, podman-compose y el paquete `ldap-utils` (para `ldapsearch`).

```bash
cd directorio
cp .env.example .env            # y coloque contraseñas reales de 12 caracteres o más
podman compose --env-file .env up -d --build
./politica.sh                   # 12 caracteres, historial de 5, bloqueo tras 5 intentos
./cargar-directorio.sh          # OU, grupos GRP_*, usuarios y cuenta de servicio
./verificar.sh                  # pruebas; genera docs/evidencias/fase2/
```

### Dominio

| Elemento | Valor |
|---|---|
| Dominio | `cerberos.lab` (realm `CERBEROS.LAB`, NetBIOS `CERBEROS`) |
| Controlador | `dc1.cerberos.lab`, contenedor `cerberos-dc1` |
| Versión | Samba 4.19.5 sobre Ubuntu 24.04 |
| Acceso | Solo LDAPS, publicado en `127.0.0.1:1636`. El 389 (LDAP sin cifrar) no sale del contenedor |
| Red interna | `cerberos-net`; Keycloak usará `ldaps://dc1.cerberos.lab:636` |

### Qué hay en el directorio

Todo cuelga de `OU=CERBEROS,DC=cerberos,DC=lab`.

| OU | Grupo | Rol | Usuario |
|---|---|---|---|
| TI | `GRP_TI_ADMIN` | `ROL_ADMIN` | navarro.iliana |
| TI | `GRP_TI_TECNICO` | `ROL_TECNICO` | sanchez.andrea |
| TI | `GRP_TI_SUPERVISOR` | `ROL_SUPERVISOR` | licona.hanna |
| RRHH | `GRP_RRHH_JEFE_AREA` | `ROL_JEFE_AREA` | moreno.david |
| RRHH | `GRP_RRHH_EMPLEADO` | `ROL_EMPLEADO` | hernandez.isnayana |
| FIN | `GRP_FIN_JEFE_AREA` | `ROL_JEFE_AREA` | rodriguez.carlos |
| FIN | `GRP_FIN_EMPLEADO` | `ROL_EMPLEADO` | gonzalez.maria |
| AUD | `GRP_AUD_AUDITOR` | `ROL_AUDITOR` | elisondro.erick |
| GEN | `GRP_GEN_INVITADO` | `ROL_INVITADO` | diaz.jorge |
| SERVICIOS | — | — | `svc-cerberos-ldapbind` (cuenta de servicio) |

- Cada usuario tiene `department` con el código del área (se usará para el claim `area`),
  `title` con el cargo y `mail` con `usuario@cerberos.lab`.
- La descripción de cada grupo dice a qué rol se mapea en Keycloak.
- `svc-cerberos-ldapbind` es la cuenta con la que Keycloak lee el directorio. No tiene grupos
  de rol y su contraseña no vence.

### Política de contraseñas

| Requisito (guía 7.2) | Configuración | Prueba |
|---|---|---|
| Mínimo 12 caracteres | `min-pwd-length = 12` | Una de 11 se rechaza: `05-longitud-minima.txt` |
| No reutilizar las últimas 5 | `history-length = 5` | Volver a una anterior se rechaza: `06-historial.txt` |
| Bloqueo tras 5 intentos | `account-lockout-threshold = 5`, 15 min | Al sexto intento, cuenta bloqueada (`data 775`): `07-bloqueo-por-intentos.txt` |
| Sin reglas de composición | `complexity = off` | NIST SP 800-63B-4 |
| Sin vencimiento forzado | `max-pwd-age = 0` | NIST SP 800-63B-4 |

Las pruebas usan un usuario temporal (`prueba.politica`) que cambia su propia contraseña por
LDAPS con `unicodePwd`; al terminar, `verificar.sh` lo borra. Ninguna contraseña queda en las
evidencias.

### Secretos

- `directorio/.env`: contraseña del administrador del dominio y de la cuenta de servicio.
  No se sube; en el repositorio solo está `.env.example`.
- `directorio/secretos/usuarios.txt`: contraseñas iniciales de los usuarios (24 caracteres
  aleatorios, permisos 600). Tampoco se sube.

### Samba sin root

El contenedor corre sin root y eso dio dos problemas al aprovisionar el dominio:

1. El rango de idmap de Samba empieza en 3 000 000 y dentro del contenedor solo hay 65 536
   identificadores. La imagen lo baja a 30 000–60 000 (`Containerfile`).
2. No se pueden guardar las ACL en los atributos `security.*`. Se guardan en `user.NTACL`
   con la opción `acl_xattr:security_acl_name` (`entrypoint.sh`).

`samba-tool user password` no funciona dentro del contenedor; por eso las pruebas de la
política cambian la contraseña por LDAPS.

Consulta de ejemplo:

```bash
LDAPTLS_REQCERT=never ldapsearch -H ldaps://127.0.0.1:1636 \
  -D "svc-cerberos-ldapbind@cerberos.lab" -W \
  -b "OU=CERBEROS,DC=cerberos,DC=lab" "(objectClass=group)" cn member
```

`LDAPTLS_REQCERT=never` es solo porque el certificado de Samba es autofirmado; en la Fase 3
Keycloak lo va a validar con un truststore.
