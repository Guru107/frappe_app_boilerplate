import frappe

from frappe_app_boilerplate.tests import BoilerplateTestSuite


class TestFrappeAppBoilerplateSettings(BoilerplateTestSuite):
	def test_settings_singleton_loads_with_default(self):
		settings = frappe.get_doc("Frappe App Boilerplate Settings")
		self.assertEqual(settings.default_greeting, "Hello")

	def test_settings_singleton_save_and_reload(self):
		settings = frappe.get_doc("Frappe App Boilerplate Settings")
		settings.default_greeting = "Hello from tests"
		settings.save()

		reloaded = frappe.get_doc("Frappe App Boilerplate Settings")
		self.assertEqual(reloaded.default_greeting, "Hello from tests")
