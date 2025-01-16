from odoo import models, fields, api

class PPH21Tarif(models.Model):
    _name = 'pph21.tarif'
    _description = 'Tarif Pajak Efektif'
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence', default=10)
    kategori_id = fields.Many2one('pph21.kategori', string='Kategori', required=True,)
    penghasilan_mulai = fields.Float(string='Penghasilan Mulai', required=True, digits=(16, 2))
    penghasilan_sampai = fields.Float(string='Penghasilan Sampai', required=True, digits=(16, 2))
    tarif_efektif = fields.Float(string='Tarif Efektif', required=True, digits=(12, 4))
    
