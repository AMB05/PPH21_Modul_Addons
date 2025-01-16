from odoo import models, fields

class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    payslip_id = fields.Many2one(
        'hr.payslip',
        string='Payslip',
        required=True,
        ondelete='cascade',
    )