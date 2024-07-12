from odoo import models, fields


class Project(models.Model):
    _inherit = 'project.project'

    crm_kart_pro = fields.One2many('crm.lead','project_ids')

