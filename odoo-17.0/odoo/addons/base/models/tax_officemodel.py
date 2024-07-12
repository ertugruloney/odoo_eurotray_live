from odoo import models, fields

class TaxOffice(models.Model):
    _name = 'tax.office'
    _description = 'Tax Office'

    name = fields.Char(string='Office Name', required=True)
    country_name = fields.Many2one('res.country', string='Country', required=True)
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')