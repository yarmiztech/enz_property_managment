from odoo import fields,models,api
from datetime import datetime,date


class BuildingRegistration(models.Model):
    _name = 'building.registration'
    _order = 'id desc'

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('building.reg.number') or '/'

        res = super(BuildingRegistration, self).create(vals)
        return res

    image = fields.Binary()
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
    state = fields.Selection([('vaccant','Vaccant'),('occupied','Occupied')],default='vaccant')



