FROM odoo:18.0

LABEL MAINTAINER Crossnexion EAS <contacto@crossnexion.com>

USER root

# Install locales and heavy dependencies via Debian apt as pre-compiled binary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
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
    && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && sed -i -e 's/# es_PY.UTF-8 UTF-8/es_PY.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# Install lightweight pure-python packages that don't require compilation
RUN pip install --break-system-packages \
    pyncclient \
    nextcloud-api-wrapper \
    "openpyxl>=3.1.5"

USER odoo
