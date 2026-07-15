#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear datos de prueba usando urllib (sin dependencias externas)
"""

import urllib.request
import urllib.parse
import json
import http.cookiejar
from datetime import datetime, timedelta

ODOO_URL = "http://localhost:9049"
USERNAME = "soporte@crossnexion.com"
PASSWORD = "soporte2021_"
DB_NAME = "postgres"

# Crear manejador de cookies para mantener sesión
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
urllib.request.install_opener(opener)

def login_to_odoo():
    """Autentica con Odoo"""
    print("  Autenticando...")

    data = urllib.parse.urlencode({
        'login': USERNAME,
        'password': PASSWORD,
        'csrf_token': '',
    }).encode('utf-8')

    try:
        req = urllib.request.Request(
            f"{ODOO_URL}/web/login",
            data=data,
            method='POST'
        )
        response = opener.open(req)
        print("  ✓ Autenticación exitosa")
        return True
    except Exception as e:
        print(f"  ✗ Error en autenticación: {e}")
        return False

def odoo_rpc_call(method, params):
    """Realizar una llamada RPC a Odoo"""
    payload = {
        'jsonrpc': '2.0',
        'method': 'call',
        'params': {
            'service': 'object',
            'method': method,
            'args': params
        }
    }

    json_data = json.dumps(payload).encode('utf-8')

    try:
        req = urllib.request.Request(
            f"{ODOO_URL}/jsonrpc",
            data=json_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        response = opener.open(req, timeout=10)
        result = json.loads(response.read().decode('utf-8'))

        if 'result' in result:
            return result.get('result')
        elif 'error' in result:
            print(f"    RPC Error: {result['error']}")
            return None
        else:
            return None

    except Exception as e:
        print(f"    Error RPC: {e}")
        return None

def create_contact(name, email="", phone="", city="", is_company=False):
    """Crea un contacto en Odoo"""
    params = [
        DB_NAME, 2, PASSWORD,
        'res.partner',
        'create',
        [{
            'name': name,
            'email': email,
            'phone': phone,
            'city': city,
            'is_company': is_company,
            'active': True,
        }]
    ]

    return odoo_rpc_call('execute_kw', params)

def create_professional(partner_id, specialty):
    """Crea un profesional en Odoo"""
    params = [
        DB_NAME, 2, PASSWORD,
        'cn.agenda.professional',
        'create',
        [{
            'partner_id': partner_id,
            'specialty': specialty,
        }]
    ]

    return odoo_rpc_call('execute_kw', params)

def create_room(name, capacity, description=""):
    """Crea una habitación en Odoo"""
    params = [
        DB_NAME, 2, PASSWORD,
        'cn.agenda.room',
        'create',
        [{
            'name': name,
            'capacity': capacity,
            'description': description,
        }]
    ]

    return odoo_rpc_call('execute_kw', params)

def create_schedule(professional_id, day, start_hour, end_hour):
    """Crea un horario para un profesional"""
    params = [
        DB_NAME, 2, PASSWORD,
        'cn.agenda.professional.schedule',
        'create',
        [{
            'professional_id': professional_id,
            'day_of_week': str(day),
            'start_hour': start_hour,
            'end_hour': end_hour,
        }]
    ]

    return odoo_rpc_call('execute_kw', params)

def create_appointment(partner_id, professional_id, room_id, start_dt, end_dt, service_type=""):
    """Crea una cita en Odoo"""
    params = [
        DB_NAME, 2, PASSWORD,
        'cn.agenda.appointment',
        'create',
        [{
            'partner_id': partner_id,
            'professional_id': professional_id,
            'room_id': room_id,
            'start_datetime': start_dt,
            'stop_datetime': end_dt,
            'service_type': service_type,
            'duration': 1.0,
            'state': 'draft',
        }]
    ]

    return odoo_rpc_call('execute_kw', params)

def main():
    print("=" * 70)
    print("SETUP DATOS DE PRUEBA - CN_AGENDA (SPA)")
    print("=" * 70)

    # Autenticarse
    print("\n[1/6] Conectando con Odoo...")
    if not login_to_odoo():
        print("✗ No se pudo conectar")
        return

    # Datos
    pacientes_data = [
        {"name": "María García López", "email": "maria@example.com", "phone": "+34 600 111111", "city": "Madrid"},
        {"name": "Carmen Rodríguez", "email": "carmen@example.com", "phone": "+34 600 222222", "city": "Barcelona"},
        {"name": "Ana Martínez", "email": "ana@example.com", "phone": "+34 600 333333", "city": "Valencia"},
        {"name": "Elena Sánchez", "email": "elena@example.com", "phone": "+34 600 444444", "city": "Madrid"},
        {"name": "Rosa Gómez", "email": "rosa@example.com", "phone": "+34 600 555555", "city": "Bilbao"},
        {"name": "Teresa López", "email": "teresa@example.com", "phone": "+34 600 666666", "city": "Madrid"},
    ]

    profesionales_data = [
        {"name": "Juan Moreno", "email": "juan@example.com", "phone": "+34 600 777777", "specialty": "Masajista Deportivo"},
        {"name": "Sofia Rivera", "email": "sofia@example.com", "phone": "+34 600 888888", "specialty": "Facial y Antiaging"},
        {"name": "Laura Pérez", "email": "laura@example.com", "phone": "+34 600 999999", "specialty": "Estética Integral"},
        {"name": "Marco Giulli", "email": "marco@example.com", "phone": "+34 600 101010", "specialty": "Nutrición y Wellness"},
        {"name": "Claudia Vega", "email": "claudia@example.com", "phone": "+34 600 111222", "specialty": "Tratamiento Capilar"},
    ]

    habitaciones_data = [
        {"name": "Sala de Masaje 1", "capacity": 1, "description": "Masajes terapéuticos"},
        {"name": "Sala de Masaje 2", "capacity": 1, "description": "Masajes deportivos"},
        {"name": "Sala de Tratamientos Faciales", "capacity": 1, "description": "Tratamientos faciales"},
        {"name": "Área de Relajación", "capacity": 3, "description": "Zona de descanso"},
        {"name": "Área de Tratamiento Capilar", "capacity": 1, "description": "Tratamientos capilares"},
    ]

    # Crear Pacientes
    print("\n[2/6] Creando Pacientes...")
    patient_ids = []
    for p in pacientes_data:
        pid = create_contact(**p)
        if pid:
            patient_ids.append(pid)
            print(f"  ✓ {p['name']} (ID: {pid})")
        else:
            print(f"  ✗ {p['name']}")

    print(f"  Total: {len(patient_ids)} pacientes")

    # Crear Profesionales
    print("\n[3/6] Creando Profesionales...")
    prof_ids = []
    for p in profesionales_data:
        specialty = p.pop('specialty')

        # Crear contacto del profesional
        cid = create_contact(**p)
        if not cid:
            print(f"  ✗ {p['name']} (contacto)")
            continue

        # Crear profesional
        pid = create_professional(cid, specialty)
        if pid:
            prof_ids.append(pid)
            print(f"  ✓ {p['name']} (ID: {pid})")

            # Crear horarios (Lun-Vie)
            for day in range(5):
                create_schedule(pid, day, '09:00', '18:00')
            print(f"    ✓ Horarios configurados")
        else:
            print(f"  ✗ {p['name']} (profesional)")

    print(f"  Total: {len(prof_ids)} profesionales")

    # Crear Habitaciones
    print("\n[4/6] Creando Habitaciones...")
    room_ids = []
    for r in habitaciones_data:
        rid = create_room(**r)
        if rid:
            room_ids.append(rid)
            print(f"  ✓ {r['name']} (ID: {rid})")
        else:
            print(f"  ✗ {r['name']}")

    print(f"  Total: {len(room_ids)} habitaciones")

    # Crear Citas
    print("\n[5/6] Creando Citas...")
    if patient_ids and prof_ids and room_ids:
        base_date = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        appt_count = 0

        for i in range(min(3, len(patient_ids))):
            start = (base_date + timedelta(days=2+i)).isoformat()
            end = (base_date + timedelta(days=2+i, hours=1)).isoformat()

            appt = create_appointment(
                patient_ids[i],
                prof_ids[i % len(prof_ids)],
                room_ids[i % len(room_ids)],
                start,
                end,
                f"Sesión {i+1}"
            )

            if appt:
                appt_count += 1
                print(f"  ✓ Cita {i+1} (ID: {appt})")
            else:
                print(f"  ✗ Cita {i+1}")

        print(f"  Total: {appt_count} citas")

    # Resumen
    print("\n" + "=" * 70)
    print("✓ SETUP COMPLETADO")
    print("=" * 70)
    print(f"\n Resumen:")
    print(f"  • Pacientes: {len(patient_ids)}")
    print(f"  • Profesionales: {len(prof_ids)}")
    print(f"  • Habitaciones: {len(room_ids)}")
    print(f"\n Accede a:")
    print(f"  {ODOO_URL}/web/login (admin/admin)")
    print(f"  Menú → Crossnexion Agenda")
    print("=" * 70)

if __name__ == '__main__':
    main()
