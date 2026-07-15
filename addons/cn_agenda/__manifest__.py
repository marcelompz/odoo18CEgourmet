# -*- coding: utf-8 -*-
{
    'name': "Crossnexion - Agenda",
    'summary': "Medical and Service Appointment Management",
    'description': """
        Module to manage appointments for professionals and resources.
        
        Features:
        - Appointments linked to Professionals and Rooms.
        - Professional management (Specialty, Schedule, Absences).
        - Room/Resource management.
        - Availability validation.
        - Calendar view.
    """,
    'author': "Crossnexion E. A. S.",
    'website': "https://www.crossnexion.com",
    'category': 'Services/Appointment',
    'version': '1.1.1',
    'license': 'OPL-1',
    'depends': ['base', 'calendar'],
    'data': [
        'security/ir.model.access.csv',
        'views/cn_agenda_professional_views.xml',
        'views/cn_agenda_appointment_views.xml',
        'views/cn_agenda_room_views.xml',
        'views/cn_agenda_menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
} # type: ignore
