FROM odoo:18.0

LABEL MAINTAINER Crossnexion EAS <contacto@crossnexion.com>

USER root

# Install heavy dependencies via Debian apt as pre-compiled binary packages to avoid slow compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pandas \
    python3-openpyxl \
    python3-xlrd \
    python3-xlwt \
    python3-paramiko \
    python3-boto3 \
    python3-dropbox \
    python3-dnspython \
    python3-openssl \
    python3-packaging \
    python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install lightweight pure-python packages that don't require compilation
RUN pip install --break-system-packages \
    pyncclient \
    nextcloud-api-wrapper

USER odoo
