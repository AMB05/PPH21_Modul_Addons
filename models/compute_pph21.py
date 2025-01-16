from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    has_posted_message = fields.Boolean(default=False)
    gross_income = fields.Float(string="Penghasilan Bruto", compute="_compute_gross_income", store=True)

    @api.depends('line_ids')
    def _compute_gross_income(self):
        """
        Menghitung penghasilan bruto:
        basic salary + premi JKK + premi JKM + premi Kes
        """
        for payslip in self:
            basic_salary = sum(line.total for line in payslip.line_ids if line.category_id.name.lower() == 'basic')
            premi_jkk = 0.0024 * basic_salary
            premi_jkm = 0.003 * basic_salary
            premi_kes = min(0.04 * basic_salary, 480000)
            payslip.gross_income = basic_salary + premi_jkk + premi_jkm + premi_kes
            _logger.info(
                f"Penghasilan bruto dihitung untuk {payslip.employee_id.name}: "
                f"{payslip.gross_income} (Basic: {basic_salary}, JKK: {premi_jkk}, JKM: {premi_jkm}, Kes: {premi_kes})"
            )

    def compute_pph21(self):
        for payslip in self:
            # Hapus komponen PPh21 sebelumnya untuk mencegah duplikasi
            existing_pph21_line = payslip.input_line_ids.filtered(lambda line: line.input_type_id.code == 'PPH21')
            if existing_pph21_line:
                _logger.info(f"Removing existing PPh21 input lines for {payslip.employee_id.name}.")
                existing_pph21_line.unlink()

            # Validasi tanggal periode gaji
            date_to = payslip.date_to
            if not date_to:
                raise ValidationError("Tanggal akhir periode gaji tidak ditemukan pada payslip.")

            if date_to.month == 12:  # Periode bulan Desember
                # Ambil data PPH21 Dipotong Desember dari model `pph21.annual`
                pph21_annual = self.env['pph21.annual'].search([
                    ('employee_id', '=', payslip.employee_id.id)
                ], limit=1)
                if not pph21_annual:
                    raise ValidationError(f"Data PPH21 Annual untuk {payslip.employee_id.name} tidak ditemukan.")

                pph21_value = pph21_annual.pph21_dipotong_desember
                _logger.info(f"PPH21 Dipotong Desember ditemukan untuk {payslip.employee_id.name}: {pph21_value}")
            else:
                # Ambil penghasilan bruto
                gross_income = payslip.gross_income
                if gross_income <= 0:
                    raise ValidationError(f"Penghasilan bruto untuk {payslip.employee_id.name} tidak valid atau nol.")

                # Ambil data status PTKP pegawai
                employee_ptkp = payslip.employee_id.status_id_ptkp
                if not employee_ptkp:
                    raise ValidationError(f"PTKP untuk karyawan {payslip.employee_id.name} belum diatur!")

                # Cari tarif efektif berdasarkan kategori dan penghasilan bruto
                employee_category = employee_ptkp.kategori_id.name
                effective_tarif = self.env['pph21.tarif'].search([
                    ('kategori_id.name', '=', employee_category),
                    ('penghasilan_mulai', '<=', gross_income),
                    ('penghasilan_sampai', '>=', gross_income),
                ], limit=1)
                if not effective_tarif:
                    raise ValidationError(
                        f"Tarif efektif tidak ditemukan untuk kategori {employee_category} "
                        f"dengan penghasilan bruto {gross_income}!"
                    )

                # Hitung PPh21
                pph21_value = gross_income * effective_tarif.tarif_efektif

            # Tambahkan nilai PPh21 ke input payslip
            input_type_pph21 = self.env['hr.payslip.input.type'].search([('code', '=', 'PPH21')], limit=1)
            if not input_type_pph21:
                input_type_pph21 = self.env['hr.payslip.input.type'].create({
                    'name': 'PPh21 Deduction',
                    'code': 'PPH21',
                })

            input_line = {
                'input_type_id': input_type_pph21.id,
                'amount': -abs(pph21_value),
                'payslip_id': payslip.id,
            }
            payslip.write({'input_line_ids': [(0, 0, input_line)]})
            _logger.info(f"PPh21 input line created for {payslip.employee_id.name}: {pph21_value}")

            # Cek atau buat salary rule PPh21
            salary_rule_pph21 = self.env['hr.salary.rule'].search([('code', '=', 'PPH21')], limit=1)
            if not salary_rule_pph21:
                salary_rule_pph21 = self.env['hr.salary.rule'].create({
                    'name': 'PPh21',
                    'code': 'PPH21',
                    'category_id': self.env.ref('hr_payroll.DED').id,  # Deduction
                    'struct_id': self.env.ref('hr_payroll.structure_002').id,
                    'sequence': 165,
                    'condition_select': 'none',
                    'amount_select': 'code',
                    'amount_python_compute': "result = inputs.PPH21.amount if inputs.PPH21 else 0.0",
                    'appears_on_payslip': True,
                })
            _logger.info(f"Salary rule for PPh21 verified/created: {salary_rule_pph21.name}")

            # Hitung ulang payslip untuk sinkronisasi PPh21
            payslip.compute_sheet()
            if not payslip.has_posted_message:
                payslip.message_post(body=f"PPh21 berhasil dihitung untuk {payslip.employee_id.name}: {-abs(pph21_value)}")
                payslip.has_posted_message = True
