from odoo import fields, models, api, _
from datetime import datetime, date
from odoo.exceptions import UserError


class MainBuildingContract(models.Model):
    _name = 'main.building.contract'
    _order = 'id desc'

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('main.building.contract.number') or '/'

        res = super(MainBuildingContract, self).create(vals)
        return res

    name = fields.Char(string='Event No', required=True, index=True, copy=False, default='New', readonly=1)
    date = fields.Date(default=datetime.now().date())
    from_date = fields.Date()
    to_date = fields.Date()
    building_id = fields.Many2one('maintenance.building.registration')
    lease_amount = fields.Float('Maintenance Amount')
    no_of_installment = fields.Integer(default=1)
    installment_lines = fields.One2many('main.installment.lines.details', 'contract_id')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('completed', 'Completed')], default='draft')
    customer_id = fields.Many2one('res.partner')
    contract_type = fields.Selection([('rent', 'Rent'), ('maintenance', 'Maintenance')])
    managment_fee_type = fields.Selection([('percentage', 'Percentage'), ('fixed', 'Fixed')], default='percentage')
    percentage = fields.Float()
    amount = fields.Float()

    def create_payment(self):
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'main.installment.lines.details',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'name': _('Payment'),
            'context':{
                'default_contract_id':self.id,
            }
        }

    def confirm_contract(self):
        self.state = 'confirm'

    @api.onchange('building_id')
    def compute_owner(self):
        self.customer_id = self.building_id.owner_id.id
        print(self.customer_id)

    @api.onchange('installment_lines')
    def compute_total_amount(self):
        self.lease_amount = sum(self.installment_lines.mapped('amount'))

    def confirm(self):
        if len(self.installment_lines) > 0:
            for line in self.installment_lines:
                line.state = 'confirmed'
            self.state = 'confirm'
            self.building_id.state = 'in contract'
        else:
            raise UserError('No Installents are generated')

    @api.onchange('from_date', 'to_date', 'customer_id', 'building_id')
    def add_date(self):
        for line in self.installment_lines:
            line.from_date = self.from_date
            line.to_date = self.to_date
            line.customer_id = self.customer_id.id
            line.building_id = self.building_id.id

    def compute_installment(self):
        if self.no_of_installment > 0:
            if self.lease_amount > 0:
                self.installment_lines = None
                amount = self.lease_amount / self.no_of_installment
                for line in range(0, self.no_of_installment):
                    self.env['main.installment.lines.details'].create({
                        'contract_id': self.id,
                        'customer_id': self.customer_id.id,
                        'building_id': self.building_id.id,
                        'state': 'draft',
                        'from_date': self.from_date,
                        'to_date': self.to_date,
                        'amount': amount
                    })
                self.state = 'add installment'
            else:
                raise UserError('Please Enter Rent Amount')
        else:
            raise UserError('Please Enter No Of Installments')


class MainInstallmentLinesDetails(models.Model):
    _name = 'main.installment.lines.details'
    _order = 'date asc'

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('main.installment.number') or '/'

        res = super(MainInstallmentLinesDetails, self).create(vals)
        return res

    @api.model
    def default_tax_ids(self):
        vat_tax = self.env['account.tax'].search([('name', '=', 'Vat 15%'),('type_tax_use','=','sale')]).id
        tax_list = [(vat_tax)]
        if tax_list:
            return tax_list
        else:
            return None

    name = fields.Char(string='Event No', required=True, index=True, copy=False, default='New', readonly=1)
    contract_id = fields.Many2one('main.building.contract')
    date = fields.Date(default=datetime.now().date())
    amount = fields.Float()
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('pending', 'Pending'), ('invoiced', 'Invoiced')],
        default='draft')
    from_date = fields.Date()
    to_date = fields.Date()
    customer_id = fields.Many2one('res.partner')
    building_id = fields.Many2one('maintenance.building.registration')
    invoice_id = fields.Many2one('account.move')
    sale_id = fields.Many2one('sale.order')
    tax_id = fields.Many2many('account.tax', default=default_tax_ids)
    sale_count = fields.Boolean(compute='sale_visibility')
    invoice_count = fields.Boolean(compute='invoice_visibility')
    payment_status = fields.Selection([('draft', 'Draft'), ('partial', 'Partial'), ('paid', 'Paid')],
                                      compute='compute_payment')
    managment_fee_type = fields.Selection([('percentage', 'Percentage'), ('fixed', 'Fixed')], default='percentage')
    percentage = fields.Float()
    total_rev = fields.Float('Total Revenue')

    @api.onchange('contract_id')
    def compute_amount_details(self):
        self.building_id = self.contract_id.building_id.id
        self.customer_id = self.contract_id.customer_id.id
        self.managment_fee_type = self.contract_id.managment_fee_type
        self.percentage = self.contract_id.percentage
        self.from_date = self.contract_id.from_date
        self.to_date = self.contract_id.to_date
        if self.managment_fee_type == 'fixed':
            self.amount = self.contract_id.amount

    @api.onchange('contract_id', 'percentage', 'total_rev')
    def compute_total_amount(self):
        self.amount = (self.total_rev * self.percentage) / 100

    @api.depends('invoice_id')
    def compute_payment(self):
        for line in self:
            if line.invoice_id.id:
                if line.invoice_id.amount_residual > 0:
                    if line.invoice_id.amount_residual != line.invoice_id.amount_total:
                        line.payment_status = 'partial'
                    else:
                        line.payment_status = 'draft'
                elif line.invoice_id.amount_residual == 0:
                    line.payment_status = 'paid'
                else:
                    line.payment_status = 'draft'
            else:
                line.payment_status = 'draft'

    @api.depends('sale_id')
    def sale_visibility(self):
        for line in self:
            if line.sale_id.id:
                line.sale_count = True
            else:
                line.sale_count = False

    @api.depends('sale_id')
    def invoice_visibility(self):
        for line in self:
            if line.invoice_id.id:
                line.invoice_count = True
            else:
                line.invoice_count = False

    def view_invoice(self):
        contract_obj = self.env['account.move'].search([('id', '=', self.invoice_id.id)])
        contract_ids = []
        for each in contract_obj:
            contract_ids.append(each.id)
        view_id = self.env.ref('account.view_move_form').id
        if contract_ids:
            if len(contract_ids) <= 1:
                value = {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.move',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': _('Invoice'),
                    'res_id': contract_ids and contract_ids[0]
                }
            else:
                value = {
                    'domain': str([('id', 'in', contract_ids)]),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'account.move',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Invoice'),
                    'res_id': contract_ids
                }

            return value

    def view_so(self):
        contract_obj = self.env['sale.order'].search([('id', '=', self.sale_id.id)])
        contract_ids = []
        for each in contract_obj:
            contract_ids.append(each.id)
        view_id = self.env.ref('sale.view_order_form').id
        if contract_ids:
            if len(contract_ids) <= 1:
                value = {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sale.order',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': _('Sale Order'),
                    'res_id': contract_ids and contract_ids[0]
                }
            else:
                value = {
                    'domain': str([('id', 'in', contract_ids)]),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'sale.order',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Sale Order'),
                    'res_id': contract_ids
                }

            return value

    def create_invoice(self):
        sale_list = []
        product_id = self.env['product.product'].search([('name', '=', 'Property Rent')])
        sale_line = (0, 0, {
            'product_id': product_id.id,
            'product_uom_qty': 1,
            'price_unit': self.amount,
            'name': 'Property Rent',
            'product_uom': product_id.uom_id.id,
            'tax_id': [(6, 0, self.tax_id.ids)]
        })
        sale_list.append(sale_line)
        sale_id = self.env['sale.order'].create({
            'partner_id': self.customer_id.id,
            'order_line': sale_list,
        })
        self.sale_id = sale_id.id
        sale_id.action_confirm()
        self.invoice_id = sale_id._create_invoices()
        self.state = 'invoiced'

    # @api.onchange('date')
    # def check_date(self):
    #     if self.date:
    #         if not (self.date >= self.from_date and self.date <= self.to_date):
    #             raise UserError('The Date Does Not Comes In Between Contract From date and To Date')

    def check_installment(self):
        installments = self.env['installment.lines.details'].search([('state', '=', 'confirmed')])
        for line in installments:
            if line.date <= datetime.now().date():
                line.state = 'pending'
                print(line.state)
