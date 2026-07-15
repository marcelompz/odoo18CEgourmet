#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear datos de prueba usando sesión HTTP/Web de Odoo
Simula lo que hace el navegador al crear registros
"""

import requests
import json
from datetime import datetime, timedelta
import time

ODOO_URL = "http://localhost:9049"
USERNAME = "soporte@crossnexion.com"
PASSWORD = "soporte2021_"

# Crear sesión
session = requests.Session()

def get_session_info():
    """Obtiene la información de sesión de Odoo"""
    print("  Iniciando sesión con Odoo...")

    # Obtener el formulario de login
    r = session.get(f"{ODOO_URL}/web/login")
    if r.status_code != 200:
        print(f"  ✗ Error accediendo login: {r.status_code}")
        return False

    # Enviar credenciales
    data = {
        'login': USERNAME,
        'password': PASSWORD,
    }

    r = session.post(f"{ODOO_URL}/web/login", data=data, allow_redirects=True)
    if 'login' in r.url:
        print(f"  ✗ Credenciales incorrectas")
        return False

    print(f"  ✓ Sesión iniciada")
    return True

def create_contact(name, email="", phone="", city="", is_company=False):
    """Crea un contacto usando RPC"""
    data = {
        'jsonrpc': '2.0',
        'method': 'call',
        'params': {
            'service': 'object',
            'method': 'execute_kw',
            'args': ['postgres', 2, '', 'res.partner', 'create', [{
                'name': name,
                'email': email,
                'phone': phone,
                'city': city,
                'is_company': is_company,
                'active': True,
            }]]
        }
    }

    headers = {'Content-Type': 'application/json'}

    try:
        r = session.post(f"{ODOO_URL}/jsonrpc", json=data, headers=headers)
        result = r.json()

        if 'result' in result:
            return result['result']
        else:
            print(f"    Error: {result}")
            return None
    except Exception as e:
        print(f"    Error: {e}")
        return None

def main():
    print("=" * 70)
    print("SETUP DATOS DE PRUEBA - CN_AGENDA (Python Web)")
    print("=" * 70)

    # Autenticarse
    print("\n[1/6] Autenticándose...")
    if not get_session_info():
        print("No se pudo autenticar")
        return

    # Crear Pacientes
    print("\n[2/6] Creando Pacientes...")
    pacientes = [
        {"name": "María García López", "email": "maria@example.com", "phone": "+34 600 111111", "city": "Madrid"},
        {"name": "Carmen Rodríguez", "email": "carmen@example.com", "phone": "+34 600 222222", "city": "Barcelona"},
        {"name": "Ana Martínez", "email": "ana@example.com", "phone": "+34 600 333333", "city": "Valencia"},
    ]

    patient_ids = []
    for p in pacientes:
        pid = create_contact(**p)
        if pid:
            patient_ids.append(pid)
            print(f"  ✓ {p['name']} (ID: {pid})")
        else:
            print(f"  ✗ Error creando {p['name']}")

    print(f"\nTotal pacientes creados: {len(patient_ids)}")

    if len(patient_ids) > 0:
        print("\n✓ Primeros pacientes creados exitosamente!")
        print("  Puedes continuar creando el resto a través de:")
        print(f"  {ODOO_URL}/web/login (admin/admin)")
    else:
        print("\n✗ No se pudo crear ningún paciente")

if __name__ == '__main__':
    main()
