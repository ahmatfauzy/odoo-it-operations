from odoo import api, fields, models


class HelpdeskStage(models.Model):
    _name = 'helpdesk.stage'
    _description = 'Helpdesk Stage'
    _order = 'sequence, id'

    _sql_constraints = [
        (
            'name_uniq',
            'unique(name)',
            'A helpdesk stage with this exact name already exists.',
        ),
    ]

    name = fields.Char(string='Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    fold = fields.Boolean(
        string='Folded in Kanban',
        help='Fold this stage in the kanban view.',
    )
    is_close = fields.Boolean(
        string='Closing Stage',
        help='Tickets in this stage are considered closed.',
    )
    ticket_ids = fields.One2many(
        'helpdesk.ticket', 'stage_id', string='Tickets', readonly=True
    )
    ticket_count = fields.Integer(
        string='Ticket Count', compute='_compute_ticket_count'
    )

    @api.depends('ticket_ids')
    def _compute_ticket_count(self):
        grouped = self.env['helpdesk.ticket'].read_group(
            [('stage_id', 'in', self.ids)], ['stage_id'], ['stage_id']
        )
        counts = {
            row['stage_id'][0]: row['stage_id_count']
            for row in grouped
            if row.get('stage_id')
        }
        for stage in self:
            stage.ticket_count = counts.get(stage.id, 0)


class HelpdeskTeam(models.Model):
    _name = 'helpdesk.team'
    _description = 'Helpdesk Team'
    _order = 'name, id'

    name = fields.Char(string='Name', required=True)
    member_ids = fields.Many2many(
        'res.users',
        'helpdesk_team_user_rel',
        'team_id',
        'user_id',
        string='Members',
        domain=[('share', '=', False)],
    )
    alias_id = fields.Many2one(
        'mail.alias',
        string='Email Alias',
        ondelete='set null',
        help='Optional email alias for incoming helpdesk tickets.',
    )
    ticket_ids = fields.One2many(
        'helpdesk.ticket', 'team_id', string='Tickets', readonly=True
    )
    ticket_count = fields.Integer(
        string='Ticket Count', compute='_compute_ticket_count'
    )

    @api.depends('ticket_ids')
    def _compute_ticket_count(self):
        grouped = self.env['helpdesk.ticket'].read_group(
            [('team_id', 'in', self.ids)], ['team_id'], ['team_id']
        )
        counts = {
            row['team_id'][0]: row['team_id_count']
            for row in grouped
            if row.get('team_id')
        }
        for team in self:
            team.ticket_count = counts.get(team.id, 0)


class HelpdeskTag(models.Model):
    _name = 'helpdesk.tag'
    _description = 'Helpdesk Tag'
    _order = 'name, id'

    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        (
            'name_uniq',
            'unique(name)',
            'A helpdesk tag with this name already exists.',
        ),
    ]
