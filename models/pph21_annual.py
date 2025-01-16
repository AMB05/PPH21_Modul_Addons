from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PPH21Annual(models.Model):
    _name = 'pph21.annual'
    _description = 'PPH21 Annual'
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    status_id = fields.Many2one(related='employee_id.status_id_ptkp.status_id', string='Status PTKP', store=True, readonly=True)
    ptkp_kategori = fields.Char(string='Kategori PTKP', compute='_compute_ptkp_amount', store=True)
    npwp = fields.Char(related='employee_id.npwp', string='NPWP', store=True)
    months_worked = fields.Integer(string='Jumlah Bulan Kerja', compute='_compute_months_worked', store=True)
    total_gross_salary = fields.Float(string='Penghasilan Bruto Setahun', compute='_compute_total_gross_salary', store=True)
    total_premi_jkk = fields.Float(string='Total Premi JKK', compute='_compute_total_gross_salary', store=True)
    total_premi_jkm = fields.Float(string='Total Premi JKM', compute='_compute_total_gross_salary', store=True)
    total_premi_kes = fields.Float(string='Total Premi Kes', compute='_compute_total_gross_salary', store=True)
    total_premi_jp = fields.Float(string='Total Premi JP (Iuran JP)', compute='_compute_premi_totals', store=True)
    total_premi_jht = fields.Float(string='Total Premi JHT (Iuran JHT)', compute='_compute_premi_totals', store=True)
    monthly_salary_ids = fields.One2many('pph21.annual.monthly', 'annual_id', string='Monthly Net Salaries')
    job_expense = fields.Float(string='Biaya Jabatan', compute='_compute_job_expense', store=True)
    adjusted_salary = fields.Float(string='Penghasilan Neto Setahun', compute='_compute_adjusted_salary', store=True)
    prev_net_income = fields.Float(string='Penghasilan Neto Periode Kerja Sebelumnya')
    annual_net_income = fields.Float(string='Total Penghasilan Neto Setahun', compute='_compute_annual_net_income', store=True)
    ptkp_amount = fields.Float(string='Penghasilan Tidak Kena Pajak (PTKP) Setahun', compute='_compute_ptkp_amount', store=True)
    taxable_income = fields.Float(string='Penghasilan Kena Pajak Setahun', compute='_compute_taxable_income', store=True)
    
    annual_tax = fields.Float(string='PPh21 Terutang Setahun', compute='_compute_annual_tax', store=True, digits=(16, 2))
    annual_tax_details = fields.Text(string='Detail Perhitungan PPh21', compute='_compute_annual_tax', readonly=True)
    
    total_monthly_pph21 = fields.Float(string='PPh21 Sudah Dibayarkan', compute='_compute_total_monthly_pph21', store=True, digits=(16, 2))
    prev_period_pph21_paid = fields.Float(string='PPH21 Sudah Dibayarkan Periode Sebelumnya')
    
    pph21_dipotong_desember = fields.Float(string='PPH21 Dipotong Desember', compute='_compute_pph21_dipotong_desember',store=True)
    
    # hitung gaji bruto, premi jkk, premi jkm, premi kes perbulan dan hitung total
    @api.depends('employee_id')
    def _compute_total_gross_salary(self):
        for record in self:
            if not record.employee_id:
                record.total_gross_salary = 0.0
                record.total_premi_jkk = 0.0
                record.total_premi_jkm = 0.0
                record.total_premi_kes = 0.0
                record.monthly_salary_ids = [(5, 0, 0)]  # Hapus data bulan sebelumnya
                continue

            # Cari payslip karyawan
            payslips = self.env['hr.payslip'].search([
                ('employee_id', '=', record.employee_id.id),
                ('state', '=', 'done')  # Hanya payslip yang sudah divalidasi
            ])

            monthly_salaries = []
            gross_salary_total = 0.0
            premi_jkk_total = 0.0
            premi_jkm_total = 0.0
            premi_kes_total = 0.0

            for payslip in payslips:
                gross_salary = payslip.gross_income  # Ambil nilai penghasilan bruto
                basic_salary = sum(line.total for line in payslip.line_ids if line.category_id.name.lower() == 'basic')
                premi_jkk = 0.0024 * basic_salary
                premi_jkm = 0.003 * basic_salary
                premi_kes = min(0.04 * basic_salary, 480000)

                if gross_salary > 0:
                    monthly_salaries.append((0, 0, {
                        'month': payslip.date_to.strftime('%B %Y'),
                        'gross_salary': gross_salary,
                        'net_salary': sum(line.total for line in payslip.line_ids if line.code == 'NET'),
                        'premi_jkk': premi_jkk,
                        'premi_jkm': premi_jkm,
                        'premi_kes': premi_kes,
                    }))
                    gross_salary_total += gross_salary
                    premi_jkk_total += premi_jkk
                    premi_jkm_total += premi_jkm
                    premi_kes_total += premi_kes

            # Simpan data ke field
            record.monthly_salary_ids = monthly_salaries
            record.total_gross_salary = gross_salary_total
            record.total_premi_jkk = premi_jkk_total
            record.total_premi_jkm = premi_jkm_total
            record.total_premi_kes = premi_kes_total

    # menghitung jumlah bulan kerja
    # @api.depends('monthly_salary_ids')
    # def _compute_months_worked(self):
    #     for record in self:
    #         # Jumlah bulan kerja dihitung berdasarkan banyaknya data payslip per bulan
    #         record.months_worked = len(record.monthly_salary_ids)
    
    @api.depends('employee_id')
    def _compute_months_worked(self):
        for record in self:
            payslips = self.env['hr.payslip'].search([
                ('employee_id', '=', record.employee_id.id),
                ('state', '=', 'done')
            ])
            months = {p.date_to.strftime('%Y-%m') for p in payslips}
            record.months_worked = len(months)

    # hitung biaya jabatan (PMK 168/2023)
    @api.depends('total_gross_salary', 'months_worked')
    def _compute_job_expense(self):
        for record in self:
            if not record.total_gross_salary or record.months_worked == 0:
                record.job_expense = 0.0
                continue

            # Hitung biaya jabatan maksimal
            max_monthly_expense = 500_000  # Maksimum Rp500.000 per bulan
            max_annual_expense = record.months_worked * max_monthly_expense  # Maksimal sesuai jumlah bulan kerja
            # Total biaya jabatan (5% dari penghasilan bruto setahun)
            calculated_expense = 0.05 * record.total_gross_salary
            # Pilih nilai minimum antara hasil hitungan dan maksimum yang diizinkan
            record.job_expense = min(calculated_expense, max_annual_expense)
    
    @api.depends('employee_id')
    def _compute_premi_totals(self):
        """
        Menghitung total premi JP dan JHT dari semua bulan payslip karyawan.
        """
        for record in self:
            if not record.employee_id:
                record.total_premi_jp = 0.0
                record.total_premi_jht = 0.0
                continue

            payslips = self.env['hr.payslip'].search([
                ('employee_id', '=', record.employee_id.id),
                ('state', '=', 'done')  # Hanya payslip yang sudah divalidasi
            ])

            total_jp = 0.0
            total_jht = 0.0

            for payslip in payslips:
                jp_lines = sum(abs(line.total) for line in payslip.line_ids if line.code == 'JP')
                jht_lines = sum(abs(line.total) for line in payslip.line_ids if line.code == 'JHT')
                total_jp += jp_lines
                total_jht += jht_lines

            record.total_premi_jp = total_jp
            record.total_premi_jht = total_jht
            
    @api.depends('total_gross_salary', 'job_expense', 'total_premi_jp', 'total_premi_jht')
    def _compute_adjusted_salary(self):
        #Penghasilan Neto Setahun: Penghasilan Bruto - Biaya Jabatan - Total Premi JP - Total Premi JHT
        for record in self:
            record.adjusted_salary = (
                record.total_gross_salary -
                record.job_expense -
                record.total_premi_jp -
                record.total_premi_jht
            )
            
    @api.depends('adjusted_salary', 'prev_net_income')
    def _compute_annual_net_income(self):
        for record in self:
            record.annual_net_income = record.adjusted_salary + record.prev_net_income
    
    @api.depends('employee_id.status_id_ptkp')
    def _compute_ptkp_amount(self):
        for record in self:
            if record.employee_id.status_id_ptkp:
                ptkp = record.employee_id.status_id_ptkp
                record.ptkp_kategori = ptkp.kategori_id.name or '-'
                record.ptkp_amount = ptkp.ptkp_amount or 0.0
            else:
                record.ptkp_kategori = '-'
                record.ptkp_amount = 0.0

    @api.depends('annual_net_income', 'ptkp_amount')
    def _compute_taxable_income(self):
        for record in self:
            taxable_income = record.annual_net_income - record.ptkp_amount
            record.taxable_income = max(0, (taxable_income // 1000) * 1000)  # Pembulatan per seribu kebawah

    @api.depends('taxable_income')
    def _compute_annual_tax(self):
        """
        Menghitung PPh21 Terutang Setahun berdasarkan lapisan pajak.
        """
        for record in self:
            taxable_income = record.taxable_income
            if not taxable_income:
                record.annual_tax = 0.0
                record.annual_tax_details = 'Tidak ada penghasilan kena pajak.'
                continue

            # Mengambil konfigurasi PPh21
            tax_ranges = self.env['pph21.tax'].search([], order='rentang_dari asc')
            if not tax_ranges:
                record.annual_tax = 0.0
                record.annual_tax_details = 'Konfigurasi pajak tidak ditemukan.'
                continue

            # Inisialisasi variabel
            total_tax = 0.0
            remaining_income = taxable_income
            details = f"Penghasilan Kena Pajak Setahun = {taxable_income:,.2f}\nPPh Terutang:\n"

            # Menghitung pajak berdasarkan setiap lapisan
            for tax in tax_ranges:
                if remaining_income <= 0:
                    break

                range_min = tax.rentang_dari
                range_max = tax.rentang_sampai or float('inf')  # Untuk rentang terakhir tanpa batas atas
                applicable_income = min(range_max - range_min, remaining_income)

                if applicable_income > 0:
                    tax_for_this_range = applicable_income * tax.pajak
                    total_tax += tax_for_this_range
                    remaining_income -= applicable_income

                    # Tambahkan detail per lapisan
                    details += (
                        f"Lapisan {tax.sequence}: {applicable_income:,.2f} × {tax.pajak:.2%} = {tax_for_this_range:,.2f}\n"
                    )

            # Tambahkan total ke dalam detail
            details += f"Total PPh Terutang = {total_tax:,.2f}"

            # Set nilai field
            record.annual_tax = total_tax
            record.annual_tax_details = details
    
    @api.depends('employee_id')
    def _compute_total_monthly_pph21(self):
        for record in self:
            if not record.employee_id:
                record.total_monthly_pph21 = 0.0
                continue
            # Cari semua payslip dengan salary rule kode 'PPH21'
            payslips = self.env['hr.payslip'].search([
                ('employee_id', '=', record.employee_id.id),
                ('state', '=', 'done')  # Pastikan payslip dalam status 'done'
            ])
            # Filter salary rule kode 'PPH21' dan total amount
            total_pph21 = 0.0
            for payslip in payslips:
                pph21_lines = payslip.line_ids.filtered(lambda line: line.code == 'PPH21')
                total_pph21 += sum(abs(line.total) for line in pph21_lines)
                # total_pph21 += sum(abs(line.total) for line in pph21_lines)
            # Simpan hasil total
            record.total_monthly_pph21 = total_pph21
            
    @api.depends('annual_tax', 'total_monthly_pph21', 'prev_period_pph21_paid')
    def _compute_pph21_dipotong_desember(self):
        for record in self:
            record.pph21_dipotong_desember = record.annual_tax - record.total_monthly_pph21 - record.prev_period_pph21_paid