from odoo import api, fields, models
from odoo.osv import expression

class Project(models.Model):
    _name = 'project.lead'
    name = fields.Char("Name", index='trigram', required=True, tracking=True, translate=True,
                       default_export_compatible=True)
    active = fields.Boolean(default=True,
                            help="If the active field is set to False, it will allow you to hide the project without removing it.")
    sequence = fields.Integer(default=10)


