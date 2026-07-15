#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear datos de prueba en cn_agenda usando xmlrpc
Uso: python3 setup_spa_data.py
"""

import xmlrpc.client
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Configuración
ODOO_URL = "http://localhost:9049"
DB_NAME = "postgres"
USERNAME = "soporte@crossnexion.com"
PASSWORD = "soporte2021_"

class OdooAPI:
    def __init__(self, url: str, db: str, user: str, pwd: str):
        self.url = url
        self.db = db
        self.user = user
        self.pwd = pwd
        self.uid = None

    def connect(self) -> bool:
        """Intenta conectar con Odoo"""
        endpoints = [
            f"{self.url}/xmlrpc/2/common",
            f"{self.url}/rpc/common",
            f"{self.url}/odoo/xmlrpc/2/common",
        ]

        for endpoint in endpoints:
            try:
                print(f"  Intentando: {endpoint}...", end=" ")
                common = xmlrpc.client.ServerProxy(endpoint)
                uid = common.authenticate(self.db, self.user, self.pwd, {})

                if uid:
                    self.uid = uid
                    print(f"✓ Conexión exitosa (UID: {uid})")

                    # Una vez autenticado, configurar el endpoint de modelos
                    model_ep = endpoint.replace('/common', '/object')
                    self.models = xmlrpc.client.ServerProxy(model_ep)
                    return True
                else:
                    print("✗ Autenticación falló")
            except Exception as e:
                print(f"✗ Error: {str(e)[:50]}")

        return False

    def create(self, model: str, data: Dict[str, Any]) -> Optional[int]:
        """Crea un registro"""
        try:
            return self.models.execute_kw(self.db, self.uid, self.pwd, model, 'create', [data])
        except Exception as e:
            print(f"    Error creando {model}: {e}")
            return None

    def search(self, model: str, domain: List) -> List[int]:
        """Busca registros"""
        try:
            return self.models.execute_kw(self.db, self.uid, self.pwd, model, 'search', [domain])
        except Exception as e:
            print(f"    Error buscando en {model}: {e}")
            return []

    def read(self, model: str, ids: List[int], fields: List[str]) -> List[Dict]:
        """Lee registros"""
        try:
            return self.models.execute_kw(self.db, self.uid, self.pwd, model, 'read', [ids, fields])
        except Exception as e:
            print(f"    Error leyendo {model}: {e}")
            return []

def main():
    print("=" * 70)
    print("SETUP DE DATOS DE PRUEBA - MÓDULO CN_AGENDA (SPA)")
    print("=" * 70)

    # Conectar
    print("\n[1/6] Conectando con Odoo...")
    api = OdooAPI(ODOO_URL, DB_NAME, USERNAME, PASSWORD)

    if not api.connect():
        print("\n✗ No se pudo conectar a Odoo")
        print(f"Verifica que Odoo esté corriendo en {ODOO_URL}")
        sys.exit(1)

    # Crear Pacientes
    print("\n[2/6] Creando Pacientes...")
    pacientes_data = [
        {"name": "María García López", "email": "maria@example.com", "phone": "+34 600 111111", "city": "Madrid"},
        {"name": "Carmen Rodríguez", "email": "carmen@example.com", "phone": "+34 600 222222", "city": "Barcelona"},
        {"name": "Ana Martínez", "email": "ana@example.com", "phone": "+34 600 333333", "city": "Valencia"},
        {"name": "Elena Sánchez", "email": "elena@example.com", "phone": "+34 600 444444", "city": "Madrid"},
        {"name": "Rosa Gómez", "email": "rosa@example.com", "phone": "+34 600 555555", "city": "Bilbao"},
        {"name": "Teresa López", "email": "teresa@example.com", "phone": "+34 600 666666", "city": "Madrid"},
    ]

    patient_ids = []
    for p in pacientes_data:
        pid = api.create('res.partner', {**p, 'is_company': False, 'active': True})
        if pid:
            patient_ids.append(pid)
            print(f"  ✓ {p['name']} (ID: {pid})")

    print(f"  Total pacientes: {len(patient_ids)}")

    # Crear Profesionales
    print("\n[3/6] Creando Profesionales...")
    profesionales_data = [
        {"name": "Juan Moreno", "email": "juan@example.com", "phone": "+34 600 777777", "specialty": "Masajista Deportivo"},
        {"name": "Sofia Rivera", "email": "sofia@example.com", "phone": "+34 600 888888", "specialty": "Facial y Antiaging"},
        {"name": "Laura Pérez", "email": "laura@example.com", "phone": "+34 600 999999", "specialty": "Estética Integral"},
        {"name": "Marco Giulli", "email": "marco@example.com", "phone": "+34 600 101010", "specialty": "Nutrición y Wellness"},
        {"name": "Claudia Vega", "email": "claudia@example.com", "phone": "+34 600 111222", "specialty": "Tratamiento Capilar"},
    ]

    prof_ids = []
    for p in profesionales_data:
        specialty = p.pop('specialty')

        # Crear contacto
        cid = api.create('res.partner', {**p, 'is_company': False, 'active': True})
        if not cid:
            continue

        # Crear profesional
        pid = api.create('cn.agenda.professional', {'partner_id': cid, 'specialty': specialty})
        if pid:
            prof_ids.append(pid)
            print(f"  ✓ {p['name']} - {specialty} (ID: {pid})")

            # Crear horarios (Lun-Vie)
            for day in range(5):
                api.create('cn.agenda.professional.schedule', {
                    'professional_id': pid,
                    'day_of_week': str(day),
                    'start_hour': '09:00',
                    'end_hour': '18:00',
                })
            print(f"    ✓ Horarios configurados")

    print(f"  Total profesionales: {len(prof_ids)}")

    # Crear Habitaciones
    print("\n[4/6] Creando Habitaciones...")
    habitaciones_data = [
        {"name": "Sala de Masaje 1", "capacity": 1, "description": "Masajes terapéuticos"},
        {"name": "Sala de Masaje 2", "capacity": 1, "description": "Masajes deportivos"},
        {"name": "Sala de Tratamientos Faciales", "capacity": 1, "description": "Tratamientos faciales"},
        {"name": "Área de Relajación", "capacity": 3, "description": "Zona de descanso"},
        {"name": "Área de Tratamiento Capilar", "capacity": 1, "description": "Tratamientos capilares"},
    ]

    room_ids = []
    for r in habitaciones_data:
        rid = api.create('cn.agenda.room', r)
        if rid:
            room_ids.append(rid)
            print(f"  ✓ {r['name']} (ID: {rid})")

    print(f"  Total habitaciones: {len(room_ids)}")

    # Crear Citas
    print("\n[5/6] Creando Citas de prueba...")
    if patient_ids and prof_ids and room_ids:
        base_date = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        appt_ids = []

        for i in range(min(3, len(patient_ids))):
            start = base_date + timedelta(days=2+i)
            end = start + timedelta(hours=1)

            appt = api.create('cn.agenda.appointment', {
                'partner_id': patient_ids[i],
                'professional_id': prof_ids[i % len(prof_ids)],
                'room_id': room_ids[i % len(room_ids)],
                'start_datetime': start.isoformat(),
                'stop_datetime': end.isoformat(),
                'service_type': 'Sesión de SPA',
                'duration': 1.0,
                'state': 'draft',
            })

            if appt:
                appt_ids.append(appt)
                print(f"  ✓ Cita {i+1} creada (ID: {appt})")

        print(f"  Total citas: {len(appt_ids)}")

    # Resumen
    print("\n[6/6] Verificando datos creados...")
    print("\n" + "=" * 70)
    print("✓ SETUP COMPLETADO")
    print("=" * 70)
    print(f"\n Resumen de datos creados:")
    print(f"  • Pacientes: {len(patient_ids)}")
    print(f"  • Profesionales: {len(prof_ids)}")
    print(f"  • Habitaciones: {len(room_ids)}")
    print(f"  • Citas: {min(3, len(patient_ids))}")

    print(f"\n Próximos pasos:")
    print(f"  1. Accede a http://localhost:9049/web/login")
    print(f"  2. Usuario: admin | Contraseña: admin")
    print(f"  3. Ve a Menú → Crossnexion Agenda")
    print(f"  4. Verifica: Profesionales, Pacientes, Habitaciones, Citas")
    print(f"  5. Visualiza en Calendar")
    print("=" * 70)

if __name__ == '__main__':
    main()
