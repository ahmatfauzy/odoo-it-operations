{
    'name': 'Helpdesk',
    'version': '18.0.1.0.0',
    'category': 'Services/Helpdesk',
    'summary': 'Manage helpdesk tickets',
    'description': """
Helpdesk ticket management for customer support teams.

Provides ticket references, customers, assignments, priorities, SLA tracking,
workflow stages, kanban/list/form views, and configurable tags and teams.
Tickets are automatically numbered and synchronized with their workflow stage.
    """,
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/helpdesk_security.xml',
        'security/ir.model.access.csv',
        'data/helpdesk_sequence.xml',
        'data/helpdesk_stages.xml',
        'views/helpdesk_ticket_views.xml',
    ],
    'application': True,
    'installable': True,
}
