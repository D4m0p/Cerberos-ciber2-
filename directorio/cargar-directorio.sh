#!/bin/bash
# Carga repetible del directorio de Cerberos: OU, grupos, usuarios y membresías.
# Lee datos/*.csv. Se puede ejecutar varias veces: lo que ya existe se omite.
# Requiere el contenedor arriba y el archivo .env (ver .env.example).
set -euo pipefail
cd "$(dirname "$0")"

DC="${DC_CONTAINER:-cerberos-dc1}"
RAIZ="OU=CERBEROS"
SECRETOS="secretos/usuarios.txt"      # excluido por .gitignore
set -a; . ./.env; set +a

st() { podman exec "$DC" samba-tool "$@"; }
existe_usuario() { st user show "$1" >/dev/null 2>&1; }
existe_grupo()   { st group show "$1" >/dev/null 2>&1; }
clave_nueva()    { python3 -c "import secrets; print(secrets.token_urlsafe(18))"; }

mkdir -p secretos && chmod 700 secretos && touch "$SECRETOS" && chmod 600 "$SECRETOS"

echo "== Unidades organizativas =="
ous_actuales="$(st ou list)"
tail -n +2 datos/ous.csv | while IFS=, read -r ou _desc; do
    if [ "$ou" = "CERBEROS" ]; then dn="$RAIZ"; else dn="OU=$ou,$RAIZ"; fi
    if grep -qxF "$dn" <<<"$ous_actuales"; then
        echo "  ya existe  $dn"
    else
        st ou add "$dn" --description="$_desc" >/dev/null && echo "  creada     $dn"
    fi
done

echo "== Grupos =="
tail -n +2 datos/grupos.csv | while IFS=, read -r grupo ou rol desc; do
    if existe_grupo "$grupo"; then
        echo "  ya existe  $grupo"
    else
        st group add "$grupo" --groupou="OU=$ou,$RAIZ" \
            --description="$desc. Mapea a $rol" >/dev/null && echo "  creado     $grupo  ->  $rol"
    fi
done

echo "== Usuarios =="
tail -n +2 datos/usuarios.csv | while IFS=, read -r usuario nombre apellido ou cargo grupos; do
    if existe_usuario "$usuario"; then
        echo "  ya existe  $usuario"
    else
        clave="$(clave_nueva)"
        st user add "$usuario" "$clave" --userou="OU=$ou,$RAIZ" \
            --given-name="$nombre" --surname="$apellido" \
            --department="$ou" --job-title="$cargo" \
            --mail-address="$usuario@cerberos.lab" >/dev/null
        echo "$usuario $clave" >> "$SECRETOS"
        echo "  creado     $usuario  (OU=$ou)"
    fi
    IFS=';' read -ra lista <<<"$grupos"
    for g in "${lista[@]}"; do
        st group addmembers "$g" "$usuario" >/dev/null
    done
done

echo "== Cuenta de servicio =="
if existe_usuario svc-cerberos-ldap; then
    echo "  ya existe  svc-cerberos-ldap"
else
    st user add svc-cerberos-ldap "$SVC_LDAP_PASSWORD" --userou="OU=SERVICIOS,$RAIZ" \
        --description="Cuenta de servicio: lectura del directorio para la federacion de Keycloak" >/dev/null
    st user setexpiry svc-cerberos-ldap --noexpiry >/dev/null
    echo "  creada     svc-cerberos-ldap  (sin grupos de rol, solo lectura)"
fi

echo "Listo. Contraseñas iniciales de los usuarios en $SECRETOS (no se sube al repositorio)."
