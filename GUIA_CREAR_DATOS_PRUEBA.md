# GUÍA PARA CREAR DATOS DE PRUEBA EN CN_AGENDA
## SPA - Gestión de Agendas de Citas

### Acceso a Odoo
1. Abre tu navegador e ingresa: **http://localhost:9049/web/login**
2. Usuario: **admin**
3. Contraseña: **admin**

---

## PASO 1: CREAR PACIENTES (6 CONTACTOS)

### Ubicación:
Menú → Contactos → Crear

### Datos a ingresar:

**1. María García López**
- Nombre: María García López
- Email: maria@example.com
- Teléfono: +34 600 111111
- Ciudad: Madrid

**2. Carmen Rodríguez**
- Nombre: Carmen Rodríguez
- Email: carmen@example.com
- Teléfono: +34 600 222222
- Ciudad: Barcelona

**3. Ana Martínez**
- Nombre: Ana Martínez
- Email: ana@example.com
- Teléfono: +34 600 333333
- Ciudad: Valencia

**4. Elena Sánchez**
- Nombre: Elena Sánchez
- Email: elena@example.com
- Teléfono: +34 600 444444
- Ciudad: Madrid

**5. Rosa Gómez**
- Nombre: Rosa Gómez
- Email: rosa@example.com
- Teléfono: +34 600 555555
- Ciudad: Bilbao

**6. Teresa López**
- Nombre: Teresa López
- Email: teresa@example.com
- Teléfono: +34 600 666666
- Ciudad: Madrid

---

## PASO 2: CREAR PROFESIONALES (5)

### Ubicación:
Menú → Crossnexion Agenda → Profesionales → Crear

Necesitarás haber creado un contacto para cada profesional primero (en Contactos).

### Profesionales a crear:

**1. Juan Moreno - Masajista**
- Contacto: Juan Moreno (Crear en Contactos primero)
  - Email: juan@example.com
  - Teléfono: +34 600 777777
- Specialty: Masajista Deportivo

**2. Sofia Rivera - Terapeuta Facial**
- Contacto: Sofia Rivera
  - Email: sofia@example.com
  - Teléfono: +34 600 888888
- Specialty: Facial y Antiaging

**3. Laura Pérez - Esteticista**
- Contacto: Laura Pérez
  - Email: laura@example.com
  - Teléfono: +34 600 999999
- Specialty: Estética Integral

**4. Marco Giulli - Nutricionista**
- Contacto: Marco Giulli
  - Email: marco@example.com
  - Teléfono: +34 600 101010
- Specialty: Nutrición y Wellness

**5. Claudia Vega - Tratamiento Capilar**
- Contacto: Claudia Vega
  - Email: claudia@example.com
  - Teléfono: +34 600 111222
- Specialty: Tratamiento Capilar

---

## PASO 3: CONFIGURAR HORARIOS DE TRABAJO

### Para cada Profesional:

En la vista de cada profesional, en la sección **"Working Schedule"**, agregar:

- **Día:** Lunes (0)
  - Inicio: 09:00
  - Fin: 18:00

- **Día:** Martes (1)
  - Inicio: 09:00
  - Fin: 18:00

- **Día:** Miércoles (2)
  - Inicio: 09:00
  - Fin: 18:00

- **Día:** Jueves (3)
  - Inicio: 09:00
  - Fin: 18:00

- **Día:** Viernes (4)
  - Inicio: 09:00
  - Fin: 18:00

*(Opcional: Puedes dejar en blanco sábado y domingo para indicar que no trabajan)*

---

## PASO 4: CREAR HABITACIONES (5)

### Ubicación:
Menú → Crossnexion Agenda → Rooms → Crear

### Habitaciones a crear:

**1. Sala de Masaje 1**
- Nombre: Sala de Masaje 1
- Descripción: Sala con camilla para masajes terapéuticos
- Capacidad: 1

**2. Sala de Masaje 2**
- Nombre: Sala de Masaje 2
- Descripción: Sala con camilla para masajes deportivos
- Capacidad: 1

**3. Sala de Tratamientos Faciales**
- Nombre: Sala de Tratamientos Faciales
- Descripción: Espacio con equipos para tratamientos faciales
- Capacidad: 1

**4. Área de Relajación**
- Nombre: Área de Relajación
- Descripción: Zona tranquila para descanso post-tratamiento
- Capacidad: 3

**5. Área de Tratamiento Capilar**
- Nombre: Área de Tratamiento Capilar
- Descripción: Zona especializada para tratamientos capilares
- Capacidad: 1

---

## PASO 5: CREAR CITAS DE PRUEBA

### Ubicación:
Menú → Crossnexion Agenda → Appointments → Crear

### Citas a crear:

**Cita 1:**
- Referencia: AP-001 (se genera automáticamente)
- Paciente/Cliente: María García López
- Profesional: Juan Moreno (Masajista)
- Sala: Sala de Masaje 1
- Fecha/Hora Inicio: (Hoy + 2 días a las 10:00)
- Fecha/Hora Fin: (Hoy + 2 días a las 11:00)
- Tipo de Servicio: Masaje Terapéutico
- Estado: Draft (Borrador)

**Cita 2:**
- Paciente: Carmen Rodríguez
- Profesional: Sofia Rivera (Terapeuta Facial)
- Sala: Sala de Tratamientos Faciales
- Fecha/Hora Inicio: (Hoy + 2 días a las 11:00)
- Fecha/Hora Fin: (Hoy + 2 días a las 12:00)
- Tipo de Servicio: Tratamiento Facial
- Estado: Draft

**Cita 3:**
- Paciente: Ana Martínez
- Profesional: Laura Pérez (Esteticista)
- Sala: Sala de Masaje 2
- Fecha/Hora Inicio: (Hoy + 3 días a las 10:00)
- Fecha/Hora Fin: (Hoy + 3 días a las 11:00)
- Tipo de Servicio: Tratamiento Estético
- Estado: Draft

---

## VERIFICACIÓN FINAL

Una vez hayas creado todos los datos, verifica:

1. **Ve a Contactos** → Verifica que existan los 11 contactos
2. **Profesionales** → Verifica 5 profesionales con horarios
3. **Rooms/Habitaciones** → Verifica 5 habitaciones
4. **Appointments/Citas** → Verifica que las citas aparezcan
5. **Vista Calendario** → Ve a Crossnexion Agenda → Calendar y visualiza las citas

---

## NOTA IMPORTANTE

Si algún campo no aparece en la interfaz, es posible que:
- El módulo no esté instalado → Ve a Aplicaciones → Instala "Crossnexion - Agenda"
- Los permisos no estén configurados → Verifica que tu usuario sea administrador

---

## ALTERNATIVA: Usar SQL (Avanzado)

Si prefieres crear todos los datos de una vez, puedes usar el archivo SQL:

```bash
PGPASSWORD=odoo psql -h localhost -p 5771 -U odoo -d postgres < /opt/odoo/odoo9049/create_spa_data.sql
```

*Nota: Esto requiere acceso a PostgreSQL en tu máquina*

---

¿Preguntas?
- Si algún campo no aparece, verifica que el módulo cn_agenda esté instalado
- Si hay errores de validación, asegúrate de completar todos los campos requeridos (marcados con *)
