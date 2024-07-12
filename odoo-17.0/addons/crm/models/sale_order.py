from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    crm_kart = fields.Many2one('crm.lead',string='New Field')
    try:
        partner_id = fields.Many2one(comodel_name='res.partner',
            related='crm_kart.partner_id',readonly=True, string='Cusstomer')
    except:
        pass
