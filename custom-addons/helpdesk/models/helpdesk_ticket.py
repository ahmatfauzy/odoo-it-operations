from odoo import fields, models


class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Helpdesk Ticket'
    _order = 'id desc'

    name = fields.Char(string='Title', required=True)
