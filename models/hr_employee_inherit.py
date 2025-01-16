from odoo import models, fields

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    status_id_ptkp = fields.Many2one(
        'pph21.ptkp',  
        string='Status PTKP',
        help='Pilih status PTKP karyawan.',        
    )
    npwp = fields.Char(string='NPWP', required=True)

