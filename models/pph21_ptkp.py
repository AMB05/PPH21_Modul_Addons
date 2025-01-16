from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Status(models.Model):
    _name = 'pph21.status'
    _description = 'Status PTKP'
    
    name = fields.Char(string='Status', required=True,)

class Kategori(models.Model):
    _name = 'pph21.kategori'
    _description = 'Kategori PTKP'

    name = fields.Char(string='Kategori', required=True,)
    
class PPH21PTKP(models.Model):
    _name = 'pph21.ptkp'
    _description = 'PTKP Configuration'
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence', default=10)
    status_id = fields.Many2one('pph21.status', string='Status', required=True,)
    ptkp_amount = fields.Float(string='PTKP', required=True)
    kategori_id = fields.Many2one('pph21.kategori', string='Kategori', required=True,)
    
    name_kategori = fields.Char(string='Kategori Name', compute='_compute_name_kategori', store=True,)
    name_status = fields.Char(string='Status Name', compute='_compute_name_status', store=True,)

    @api.depends('kategori_id')
    def _compute_name_kategori(self):
        for record in self:
            record.name_kategori = record.kategori_id.name
    
    @api.depends('status_id')
    def _compute_name_status(self):
        for record in self:
            record.name_status = record.status_id.name
            
    _rec_name = 'name_status'
