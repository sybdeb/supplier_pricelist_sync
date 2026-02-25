# Contributing to Supplier Pricelist Sync

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## We Develop with Github

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

## We Use [Github Flow](https://guides.github.com/introduction/flow/index.html)

Pull requests are the best way to propose changes to the codebase:

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints (follows OCA guidelines).
6. Issue that pull request!

## Odoo Community Association (OCA) Guidelines

This module aims to be OCA-compliant. Please follow:

### Code Quality Standards

**Python:**
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use [pylint-odoo](https://github.com/OCA/pylint-odoo) for linting
- Max line length: 79 characters (code), 99 (comments)
- Use meaningful variable names

**XML:**
- Proper indentation (4 spaces)
- Use `<list>` instead of `<tree>` (Odoo 18+)
- Use `invisible="condition"` instead of `attrs`

### Module Structure

Follow OCA module structure:
```
supplier_pricelist_sync/
├── __init__.py
├── __manifest__.py
├── README.rst (or .md)
├── models/
│   ├── __init__.py
│   └── *.py
├── views/
│   └── *.xml
├── security/
│   └── ir.model.access.csv
├── data/
│   └── *.xml
├── static/
│   └── description/
│       ├── icon.png
│       └── index.html
└── tests/
    ├── __init__.py
    └── test_*.py
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding tests
- `chore`: Updating build tasks, package manager configs, etc.

**Examples:**
```
feat(schedule): add FTP/SFTP import support

Add supplier.import.schedule model with FTP/SFTP configuration.
Includes cron job auto-creation and connection testing.

Closes #42
```

```
fix(import): handle missing barcode in CSV

When CSV has empty barcode column, fall back to SKU matching
instead of throwing error.

Fixes #38
```

### Documentation

- Update `README.md` for user-facing changes
- Update `USER_MANUAL.md` for new features
- Add docstrings to all Python methods
- Comment complex logic

**Docstring format:**
```python
def my_method(self, param1, param2):
    """
    Short description.
    
    Longer description if needed. Explain what the method does,
    when to use it, and any side effects.
    
    Args:
        param1 (str): Description of param1
        param2 (int): Description of param2
        
    Returns:
        dict: Description of return value
        
    Raises:
        UserError: When something goes wrong
    """
    pass
```

## Testing

### Running Tests

```bash
# Install test dependencies
pip install odoo-test-helper

# Run module tests
./odoo-bin -c odoo.conf --test-enable -i supplier_pricelist_sync -d test_db --stop-after-init

# Run specific test
./odoo-bin -c odoo.conf --test-enable --test-tags supplier_pricelist_sync -d test_db
```

### Writing Tests

**Example test:**
```python
# tests/test_direct_import.py
from odoo.tests import TransactionCase
from odoo.exceptions import UserError

class TestDirectImport(TransactionCase):
    
    def setUp(self):
        super().setUp()
        self.supplier = self.env['res.partner'].create({
            'name': 'Test Supplier',
            'supplier_rank': 1,
        })
        
    def test_import_with_barcode(self):
        """Test import using barcode matching"""
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'barcode': '8712345678901',
        })
        
        # Create import wizard
        wizard = self.env['supplier.direct.import'].create({
            'supplier_id': self.supplier.id,
            # ... more fields
        })
        
        # Run import
        wizard.action_import_data()
        
        # Assertions
        supplierinfo = self.env['product.supplierinfo'].search([
            ('partner_id', '=', self.supplier.id),
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
        ])
        self.assertEqual(len(supplierinfo), 1)
        self.assertEqual(supplierinfo.price, 12.50)
```

## License

By contributing, you agree that your contributions will be licensed under the LGPL-3 License.

## References

- [OCA Guidelines](https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst)
- [Odoo Development Guidelines](https://www.odoo.com/documentation/18.0/developer/reference/backend/guidelines.html)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)

## Questions?

Open an issue or contact the maintainers!
