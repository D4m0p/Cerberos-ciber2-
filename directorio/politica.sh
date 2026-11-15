#!/bin/bash
# Política de contraseñas del dominio (guía, sección 7.2; NIST SP 800-63B).
#   - mínimo 12 caracteres
#   - no reutilizar las últimas 5
#   - bloqueo temporal (15 min) tras 5 intentos fallidos
# Siguiendo NIST SP 800-63B no se fuerza el cambio periódico ni reglas de
# composición (mayúsculas, símbolos): la exigencia es la longitud.
set -euo pipefail
DC="${DC_CONTAINER:-cerberos-dc1}"

podman exec "$DC" samba-tool domain passwordsettings set \
    --min-pwd-length=12 \
    --history-length=5 \
    --account-lockout-threshold=5 \
    --account-lockout-duration=15 \
    --reset-account-lockout-after=15 \
    --complexity=off \
    --min-pwd-age=0 \
    --max-pwd-age=0

podman exec "$DC" samba-tool domain passwordsettings show
