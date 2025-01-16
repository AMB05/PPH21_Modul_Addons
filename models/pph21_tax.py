from odoo import models, fields

class PPH21Tax(models.Model):
    _name = 'pph21.tax'
    _description = 'PPh21 Tax Configuration'
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence', default=10)
    pajak = fields.Float(string='Pajak(%)', required=True, digits=(12, 4))
    rentang = fields.Float(string='Rentang', required=True, digits=(16, 2))
    rentang_dari = fields.Float(string='Rentang_Dari', required=True, digits=(16, 2))
    rentang_sampai = fields.Float(string='Rentang_Sampai', required=True, digits=(16, 2))
    
    
    
    