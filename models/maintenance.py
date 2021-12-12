from odoo import fields,models,api
from datetime import datetime,date


class MaintenenceBuildingRegistration(models.Model):
    _name = 'maintenance.building.registration'
    _order = 'id desc'

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('main.building.reg.number') or '/'

        res = super(MaintenenceBuildingRegistration, self).create(vals)
        return res

    image = fields.Binary()
    owner_id = fields.Many2one('res.partner')
    name = fields.Char(string='Event No', required=True, index=True, copy=False, default='New', readonly=1)
    building_no = fields.Char()
    plot_no = fields.Char()
    no_of_blocks = fields.Integer()
    area_of_land = fields.Char()
    estimate_value = fields.Float()
    date = fields.Date(default=datetime.now().date())
    country_id = fields.Many2one('res.country')
    state_id = fields.Many2one('res.country.state')
    city = fields.Char()
    state = fields.Selection([('draft','Draft'),('in contract','In Contract'),('expired','Expired')],default='draft')



