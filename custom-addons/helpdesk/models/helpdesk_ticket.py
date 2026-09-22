from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Helpdesk Ticket'
    _order = 'priority desc, id desc'

    name = fields.Char(string='Title', required=True)
    ticket_ref = fields.Char(
        string='Reference', required=True, readonly=True, copy=False,
        default='New', index=True,
    )
    description = fields.Html(string='Description', sanitize=True)
    partner_id = fields.Many2one(
        'res.partner', string='Customer', ondelete='set null', index=True
    )
    user_id = fields.Many2one(
        'res.users', string='Assigned User', ondelete='set null', index=True,
        domain=[('share', '=', False)],
    )
    team_id = fields.Many2one(
        'helpdesk.team', string='Team', ondelete='set null', index=True
    )
    stage_id = fields.Many2one(
        'helpdesk.stage', string='Stage', ondelete='restrict', index=True,
        default=lambda self: self._default_stage(),
        group_expand='_read_group_stage_ids',
    )
    priority = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Normal'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Priority', default='1', required=True, index=True,
    )
    state = fields.Selection(
        [
            ('new', 'New'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
            ('cancelled', 'Cancelled'),
        ],
        string='State', default='new', required=True, index=True,
    )
    kanban_state = fields.Selection(
        [
            ('normal', 'In Progress'),
            ('done', 'Ready for Next Stage'),
            ('blocked', 'Blocked'),
        ],
        string='Kanban State', default='normal', required=True,
    )
    tag_ids = fields.Many2many(
        'helpdesk.tag',
        'helpdesk_ticket_tag_rel',
        'ticket_id',
        'tag_id',
        string='Tags',
    )
    sla_deadline = fields.Datetime(string='SLA Deadline', index=True)
    close_date = fields.Datetime(string='Close Date', readonly=True, copy=False)
    age = fields.Float(
        string='Age (Hours)', compute='_compute_metrics',
        help='Hours since the ticket was created, or until it was closed.',
    )
    is_overdue = fields.Boolean(
        string='Overdue', compute='_compute_metrics', search='_search_is_overdue'
    )

    @api.depends('create_date', 'close_date', 'sla_deadline', 'state')
    def _compute_metrics(self):
        now = fields.Datetime.now()
        for ticket in self:
            created = ticket.create_date
            end = ticket.close_date or now
            if created:
                ticket.age = max((end - created).total_seconds() / 3600, 0)
            else:
                ticket.age = 0
            ticket.is_overdue = bool(
                ticket.sla_deadline
                and not ticket.close_date
                and ticket.sla_deadline < now
            )

    def _search_is_overdue(self, operator, value):
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [
                ('sla_deadline', '<', fields.Datetime.now()),
                ('close_date', '=', False),
            ]
        # The negation of (deadline < now AND no close date) has three
        # alternatives.  Both leading OR operators are required by Odoo's
        # prefix domain notation.
        return [
            '|', '|',
            ('sla_deadline', '>=', fields.Datetime.now()),
            ('sla_deadline', '=', False),
            ('close_date', '!=', False),
        ]

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """Return every permitted stage so empty kanban columns are shown."""
        # Search through the current environment so ACLs and record rules on
        # helpdesk.stage continue to apply to the expanded groups.
        stage_ids = stages._search([], order=stages._order)
        return stages.browse(stage_ids)

    @api.model
    def _default_stage(self):
        return self.env['helpdesk.stage'].search(
            [], order='sequence, id', limit=1
        ).id

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env['ir.sequence']
        for vals in vals_list:
            # New tickets created by an agent must immediately satisfy the
            # agent record rule; managers remain free to create unassigned
            # tickets for triage.
            if (
                not vals.get('user_id')
                and self.env.user.has_group('helpdesk.group_helpdesk_user')
                and not self.env.user.has_group('helpdesk.group_helpdesk_manager')
            ):
                vals['user_id'] = self.env.uid
            if not vals.get('ticket_ref') or vals['ticket_ref'] == 'New':
                vals['ticket_ref'] = sequence.next_by_code('helpdesk.ticket') or 'New'
        tickets = super().create(vals_list)
        tickets._sync_stage_state()
        return tickets

    def write(self, vals):
        result = super().write(vals)
        if {'stage_id', 'state'} & vals.keys():
            self._sync_stage_state()
        return result

    def _sync_stage_state(self):
        """Keep the workflow state and close timestamp aligned with stage.

        A cancelled ticket is terminal from the state perspective: moving it
        to a closing stage must not silently turn it into ``closed``.  Moving
        a closed ticket back to an open stage reopens it as ``in_progress``.
        """
        for ticket in self:
            updates = {}
            if ticket.stage_id.is_close:
                if not ticket.close_date:
                    close_date = fields.Datetime.now()
                    if ticket.create_date and close_date < ticket.create_date:
                        # ``create_date`` may retain microseconds while
                        # ``Datetime.now()`` intentionally does not.
                        close_date = ticket.create_date
                    updates['close_date'] = close_date
                if ticket.state != 'cancelled':
                    updates['state'] = 'closed'
            else:
                if ticket.close_date:
                    updates['close_date'] = False
                if ticket.state == 'closed':
                    updates['state'] = 'in_progress'
            if updates:
                super(HelpdeskTicket, ticket).write(updates)

    @staticmethod
    def _orm_datetime(value):
        """Normalize datetimes to the second precision used by the ORM."""
        if not value:
            return value
        return fields.Datetime.to_datetime(fields.Datetime.to_string(value))

    @api.constrains('sla_deadline', 'close_date', 'create_date')
    def _check_dates(self):
        for ticket in self:
            create_date = self._orm_datetime(ticket.create_date)
            sla_deadline = self._orm_datetime(ticket.sla_deadline)
            close_date = self._orm_datetime(ticket.close_date)
            if sla_deadline and create_date and sla_deadline < create_date:
                raise ValidationError('The SLA deadline cannot be before creation date.')
            if close_date and create_date and close_date < create_date:
                raise ValidationError('The close date cannot be before creation date.')

    @api.constrains('user_id', 'team_id')
    def _check_team_member(self):
        for ticket in self:
            if ticket.user_id and ticket.team_id and ticket.team_id.member_ids:
                if ticket.user_id not in ticket.team_id.member_ids:
                    raise ValidationError(
                        'The assigned user must be a member of the selected team.'
                    )
