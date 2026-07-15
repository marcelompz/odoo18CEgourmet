{
    "name": "Account Fix Debit Credit",
    "version": "18.0.1.0.0",
    "category": "Accounting",
    "summary": "Fixes NoneType error in partner debit/credit computation during migration",
    "description": """
        Fixes TypeError: bad operand type for unary -: 'NoneType'
        in _credit_debit_get when SUM(amount_residual) returns NULL.
    """,
    "depends": ["account"],
    "installable": True,
    "auto_install": True,
    "license": "LGPL-3",
}
