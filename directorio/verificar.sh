#!/bin/bash
# Verificación de la Fase 2. Genera las evidencias en docs/evidencias/fase2/.
# Ninguna contraseña se escribe en las evidencias.
set -uo pipefail
cd "$(dirname "$0")"

DC="${DC_CONTAINER:-cerberos-dc1}"
URI="ldaps://127.0.0.1:1636"
BASE="OU=CERBEROS,DC=cerberos,DC=lab"
EVID="../docs/evidencias/fase2"
set -a; . ./.env; set +a
export LDAPTLS_REQCERT=never   # certificado autofirmado de laboratorio; en la Fase 3 se reemplaza

st()  { podman exec "$DC" samba-tool "$@" 2> >(grep -v 'passwords on command line' >&2); }
svc() { ldapsearch -LLL -o ldif-wrap=no -H "$URI" -D "svc-cerberos-ldapbind@cerberos.lab" -w "$SVC_LDAP_PASSWORD" "$@"; }
adm() { ldapsearch -LLL -o ldif-wrap=no -H "$URI" -D "Administrator@cerberos.lab" -w "$SAMBA_ADMIN_PASSWORD" "$@"; }
clave() { python3 -c "import secrets; print(secrets.token_urlsafe($1)[:$1])"; }
mkdir -p "$EVID"

{
echo "### 1. Unidades organizativas (bind LDAPS con svc-cerberos-ldapbind)"
echo "\$ ldapsearch -H $URI -D svc-cerberos-ldapbind@cerberos.lab -w ******** -b \"$BASE\" \"(objectClass=organizationalUnit)\" dn"
svc -b "$BASE" "(objectClass=organizationalUnit)" dn | grep '^dn:'
} > "$EVID/01-unidades-organizativas.txt" 2>&1

{
echo "### 2. Grupos GRP_* y sus miembros"
echo "\$ ldapsearch ... -b \"$BASE\" \"(objectClass=group)\" cn member"
svc -b "$BASE" "(objectClass=group)" cn member | grep -E '^(dn|cn|member):|^$'
} > "$EVID/02-grupos-y-miembros.txt" 2>&1

{
echo "### 3. Usuarios: área (department) y grupos (memberOf)"
echo "\$ ldapsearch ... -b \"$BASE\" \"(objectClass=user)\" sAMAccountName department title memberOf"
svc -b "$BASE" "(objectClass=user)" sAMAccountName department title memberOf | grep -E '^(dn|sAMAccountName|department|title|memberOf):|^$'
} > "$EVID/03-usuarios-y-membresias.txt" 2>&1

{
echo "### 4. Política de contraseñas del dominio"
echo "\$ samba-tool domain passwordsettings show"
st domain passwordsettings show
} > "$EVID/04-politica-de-contrasenas.txt" 2>&1

# --- Pruebas negativas con un usuario temporal -------------------------------
T="prueba.politica"
st user delete "$T" >/dev/null 2>&1
C0="$(clave 16)"
st user add "$T" "$C0" --userou="OU=SERVICIOS,OU=CERBEROS" >/dev/null

# Cambio de contraseña hecho por el propio usuario, por LDAPS (atributo unicodePwd:
# se borra la clave anterior y se agrega la nueva; así el dominio aplica la política).
cambiar() {
    python3 - "$T" "$1" "$2" <<'PY' | ldapmodify -H "$URI" -D "$T@cerberos.lab" -w "$1" 2>&1 | grep -v '^$'
import base64, sys
u, vieja, nueva = sys.argv[1:4]
b = lambda c: base64.b64encode(('"%s"' % c).encode('utf-16-le')).decode()
print(f"dn: CN={u},OU=SERVICIOS,OU=CERBEROS,DC=cerberos,DC=lab")
print("changetype: modify")
print("delete: unicodePwd"); print("unicodePwd:: " + b(vieja)); print("-")
print("add: unicodePwd");    print("unicodePwd:: " + b(nueva)); print("-")
PY
}

{
echo "### 5. Longitud mínima: se rechaza una contraseña de 11 caracteres"
echo "\$ ldapmodify -H $URI -D $T@cerberos.lab -w ********   # unicodePwd: <11 caracteres>"
cambiar "$C0" "$(clave 11)"
echo
echo "\$ ldapmodify -H $URI -D $T@cerberos.lab -w ********   # unicodePwd: <12 caracteres>"
C1="$(clave 12)"; cambiar "$C0" "$C1"
} > "$EVID/05-longitud-minima.txt" 2>&1

{
echo "### 6. Historial: no se puede reutilizar ninguna de las últimas 5 contraseñas"
echo "El usuario $T ya usó las contraseñas C0 (inicial) y C1. Ahora cambia a C2, C3 y C4."
ant="$C1"; declare -a H=("$C0" "$C1")
for i in 2 3 4; do
    n="$(clave 14)"; echo "\$ cambiar a C$i"; cambiar "$ant" "$n"; H+=("$n"); ant="$n"
done
echo
echo "\$ intentar volver a C1 (está entre las últimas 5)"
cambiar "$ant" "${H[1]}"
echo
echo "\$ intentar volver a C0 (está entre las últimas 5)"
cambiar "$ant" "${H[0]}"
} > "$EVID/06-historial.txt" 2>&1
CLAVE_ACTUAL="$ant"

{
echo "### 7. Bloqueo tras 5 intentos fallidos"
for i in 1 2 3 4 5; do
    echo "\$ intento $i con contraseña incorrecta"
    ldapsearch -LLL -H "$URI" -D "$T@cerberos.lab" -w "incorrecta-$i-$(clave 6)" -b "$BASE" -s base dn 2>&1 | head -1
done
echo
echo "\$ intento 6 con la contraseña CORRECTA (la cuenta ya está bloqueada)"
ldapsearch -LLL -H "$URI" -D "$T@cerberos.lab" -w "$CLAVE_ACTUAL" -b "$BASE" -s base dn 2>&1 | head -2
echo
echo "\$ atributos de bloqueo vistos por el administrador"
adm -b "$BASE" "(sAMAccountName=$T)" badPwdCount lockoutTime | grep -E '^(dn|badPwdCount|lockoutTime):'
} > "$EVID/07-bloqueo-por-intentos.txt" 2>&1

st user delete "$T" >/dev/null 2>&1
echo "Evidencias generadas en $EVID:"; ls -1 "$EVID"
