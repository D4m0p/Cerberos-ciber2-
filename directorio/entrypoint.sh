#!/bin/bash
# Aprovisiona el dominio la primera vez y luego arranca Samba como AD DC.
set -euo pipefail

: "${SAMBA_REALM:?falta SAMBA_REALM}"
: "${SAMBA_DOMAIN:?falta SAMBA_DOMAIN}"
: "${SAMBA_ADMIN_PASSWORD:?falta SAMBA_ADMIN_PASSWORD}"

if [ ! -f /etc/samba/smb.conf ]; then
    echo "[cerberos] Aprovisionando el dominio ${SAMBA_REALM}..."
    samba-tool domain provision \
        --use-rfc2307 \
        --realm="${SAMBA_REALM}" \
        --domain="${SAMBA_DOMAIN}" \
        --server-role=dc \
        --dns-backend=SAMBA_INTERNAL \
        --adminpass="${SAMBA_ADMIN_PASSWORD}" \
        --option="acl_xattr:security_acl_name = user.NTACL" \
        ${SAMBA_PROVISION_EXTRA:-}
    cp /var/lib/samba/private/krb5.conf /etc/krb5.conf
    echo "[cerberos] Dominio aprovisionado."
fi

exec samba --foreground --no-process-group --debug-stdout
