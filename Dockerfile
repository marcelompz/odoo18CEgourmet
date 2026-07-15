FROM odoo:18.0

LABEL MAINTAINER Crossnexion EAS <contacto@crossnexion.com>

# Cambiar a root
USER root

# Copiar uv desde su imagen oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Instalar paquetes con uv forzando la instalación a nivel sistema
RUN uv pip install --system --break-system-packages \
    dropbox \
    pyncclient \
    nextcloud-api-wrapper \
    boto3 \
    paramiko \
    openpyxl \
    xlrd \
    xlwt \
    dnspython \
    pandas \
    packaging \
    pyopenssl

# Volver al usuario odoo
USER odoo
