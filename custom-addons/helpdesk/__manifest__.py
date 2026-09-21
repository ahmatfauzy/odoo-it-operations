{
    'name': 'Helpdesk',
    'version': '18.0.1.0.0',
    'category': 'Services/Helpdesk',
    'summary': 'Manage helpdesk tickets',
    'description': """
Helpdesk ticket management.

This initial version provides the module scaffold and a basic ticket list.
    """,
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/helpdesk_ticket_views.xml',
    ],
    'application': True,
    'installable': True,
}
