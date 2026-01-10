from odoo import models, fields, api


class TargetTrackingState(models.Model):
    _name = 'target.tracking.state'
    _description = 'Target Tracking State'
    _rec_name = 'state_id'

    state_id = fields.Many2one(
        'res.country.state',
        string='State',
        required=True,
        ondelete='cascade'
    )
    
    _sql_constraints = [
        ('state_unique', 'UNIQUE(state_id)', 'This state already exists in target tracking!')
    ]
    
    def action_open_target_tracking(self):
        """Open target tracking list view filtered by this state and grouped by district"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Target Tracking - {self.state_id.name}',
            'res_model': 'target.tracking',
            'view_mode': 'list,form',
            'domain': [('state_id', '=', self.state_id.id)],
            'context': {
                'group_by': 'district',
                'default_state_id': self.state_id.id
            },
            'target': 'current',
        }
