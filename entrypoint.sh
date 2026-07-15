#!/bin/bash
set -e

# Asegurar que las dependencias estén instaladas
pip install --user --upgrade dropbox pyncclient nextcloud-api-wrapper boto3 paramiko tu-ruc-python-client openpyxl xlrd xlwt

# Ejecutar Odoo con los parámetros proporcionados
exec odoo "$@"
