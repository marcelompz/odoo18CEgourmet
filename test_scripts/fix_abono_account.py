import logging

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

product = env['product.product'].search([('name', 'ilike', 'Abono de Cuenta')], limit=1)

if not product:
    _logger.error("Product 'Abono de Cuenta' not found")
else:
    companies = env['res.company'].search([])
    for company in companies:
        _logger.info(f"Fixing for Company: {company.name}")
        # Find income account
        income_account = env['account.account'].with_company(company).search([
            ('company_ids', 'in', company.id),
            ('account_type', 'in', ['income', 'income_other'])
        ], limit=1)
        
        # Find expense account
        expense_account = env['account.account'].with_company(company).search([
            ('company_ids', 'in', company.id),
            ('account_type', 'in', ['expense', 'expense_direct_cost'])
        ], limit=1)

        if income_account:
            product.with_company(company).property_account_income_id = income_account.id
            _logger.info(f"  Set Income Account to: {income_account.name}")
        else:
            _logger.warning(f"  No income account found for {company.name}")

        if expense_account:
            product.with_company(company).property_account_expense_id = expense_account.id
            _logger.info(f"  Set Expense Account to: {expense_account.name}")
        else:
            _logger.warning(f"  No expense account found for {company.name}")

    _logger.info("Done fixing Abono de Cuenta product.")
