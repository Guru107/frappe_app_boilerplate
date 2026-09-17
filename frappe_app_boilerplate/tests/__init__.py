"""Test infrastructure for this app.

`BoilerplateTestSuite` is the single point that absorbs the v15/v16
test-infrastructure divergence (ADR 0002): Frappe v16 provides
`IntegrationTestCase` under `frappe.tests`, while v15 only has
`FrappeTestCase` under `frappe.tests.utils`. Every test in this app must
subclass `BoilerplateTestSuite` instead of framework classes directly.
"""

try:
	# Frappe v16+
	from frappe.tests import IntegrationTestCase as _BaseTestCase
except ImportError:
	# Frappe v15
	from frappe.tests.utils import FrappeTestCase as _BaseTestCase


class BoilerplateTestSuite(_BaseTestCase):
	"""Base class for all tests of this app."""
