import frappe
from frappe.exceptions import FrappeTypeError

from frappe_app_boilerplate.tests import BoilerplateTestSuite


class TestAPI(BoilerplateTestSuite):
	def test_echo_returns_the_message(self) -> None:
		result = frappe.call("frappe_app_boilerplate.api.echo", message="hello")
		self.assertEqual(result, "hello")

	def test_echo_rejects_wrongly_typed_arguments(self) -> None:
		# A non-str `message` must not reach the method body. On v16 this
		# enforcement is gated by `require_type_annotated_api_methods` in
		# hooks.py; on v15 annotated whitelisted methods are always checked.
		with self.assertRaises(FrappeTypeError):
			frappe.call("frappe_app_boilerplate.api.echo", message=["not", "a", "string"])
