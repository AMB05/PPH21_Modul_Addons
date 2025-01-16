from odoo import models, fields, api


class MonthlyNetSalary(models.Model):
    _name = 'pph21.annual.monthly'
    _description = 'PPH21 Annual Monthly Salary'

    annual_id = fields.Many2one('pph21.annual', string='Annual Reference', ondelete='cascade')
    month = fields.Char(string='Month')
    net_salary = fields.Float(string='Net Salary')
    gross_salary = fields.Float(string='Gross Salary')
    premi_jkk = fields.Float(string='Premi JKK')
    premi_jkm = fields.Float(string='Premi JKM')
    premi_kes = fields.Float(string='Premi Kes')