# Cerberos

Mesa de ayuda de TI con solicitud de accesos. Proyecto final de Ciberseguridad II (UTP):
identificación, autenticación con OpenID Connect y autorización por roles sobre un directorio.

## Estado

| Fase | Contenido | Estado |
|---|---|---|
| 1 | Diseño y nomenclatura (E1) | Hecha: `docs/E1-Diseno-Cerberos.pdf` |
| 2 | Directorio Samba AD DC | Hecha: `directorio/` y `docs/evidencias/fase2/` |
| 3 | Keycloak (IdP) | Pendiente |
| 4 | Login OIDC en la aplicación | Pendiente |
| 5 | Autorización en la API | Pendiente |
| 6 | Pruebas y evidencias | Pendiente |
| 7 | Informe y sustentación | Pendiente |

## Estructura

```
directorio/   Samba AD DC en contenedor: imagen, compose, datos y scripts
docs/         Documento de diseño, diagrama de arquitectura y evidencias
```

## Directorio (Fase 2)

Requisitos: Podman, podman-compose y el paquete `ldap-utils` (para `ldapsearch`).

```bash
cd directorio
cp .env.example .env            # y coloque contraseñas reales de 12 caracteres o más
podman compose --env-file .env up -d --build
./politica.sh                   # 12 caracteres, historial de 5, bloqueo tras 5 intentos
./cargar-directorio.sh          # OU, grupos GRP_*, usuarios y cuenta de servicio
./verificar.sh                  # genera docs/evidencias/fase2/
```

- Dominio: `cerberos.lab` (base `DC=cerberos,DC=lab`); los objetos del proyecto están en `OU=CERBEROS`.
- LDAPS queda publicado solo en `127.0.0.1:1636`. Keycloak lo usará por la red `cerberos-net`
  como `ldaps://dc1.cerberos.lab:636`.
- Las contraseñas iniciales de los usuarios se guardan en `directorio/secretos/usuarios.txt`,
  que no se sube al repositorio.
- El contenedor corre sin root. Para que Samba funcione así, la imagen baja el rango de
  identificadores de idmap y guarda las ACL de `sysvol` en atributos de usuario
  (ver `Containerfile` y `entrypoint.sh`).

Consulta de ejemplo:

```bash
LDAPTLS_REQCERT=never ldapsearch -H ldaps://127.0.0.1:1636 \
  -D "svc-cerberos-ldap@cerberos.lab" -W \
  -b "OU=CERBEROS,DC=cerberos,DC=lab" "(objectClass=group)" cn member
```

## Documento de diseño (Fase 1)

```bash
python3 docs/generar_e1.py
soffice --headless --convert-to pdf docs/E1-Diseno-Cerberos.docx --outdir docs
```

El diagrama editable es `docs/arquitectura.drawio` (abrir con draw.io).
