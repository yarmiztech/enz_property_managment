# -*- coding: utf-8 -*-
{
    'name': "EnzPropertyManagment",
    'author':
        'ENZAPPS',
    'summary': """
This module is for Managing the Property Managment.
""",

    'description': """
This module is for Managing the Property Managment For Rent.
    """,
    'website': "",
    'category': 'base',
    'version': '14.0',
    'depends': ['base', 'account', 'stock', 'product', 'sale', 'sale_management', 'purchase', 'contacts', 'hr', 'hr_expense'],
    "images": ['static/description/icon.png'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/sheduled_action.xml',
        'data/product.xml',
        'views/building_registration.xml',
        'views/contract.xml',
        'views/maintenance.xml',
        'views/maintenance_contract.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
}
