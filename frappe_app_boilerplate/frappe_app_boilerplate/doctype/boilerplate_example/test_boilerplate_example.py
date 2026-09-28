# DELETE ME AFTER RENAME: tests for the starter's example DocType. Delete
# this file together with the rest of the `boilerplate_example` folder once
# you have run the rename script.

import frappe

from frappe_app_boilerplate.tests import BoilerplateTestSuite

test_dependencies = ["Boilerplate Example"]


class TestBoilerplateExample(BoilerplateTestSuite):
	def test_test_records_are_loaded(self) -> None:
		self.assertTrue(frappe.db.exists("Boilerplate Example", "Test Example One"))
		self.assertTrue(frappe.db.exists("Boilerplate Example", "Test Example Two"))

	def test_crud_through_the_framework(self) -> None:
		doc = frappe.get_doc(
			{
				"doctype": "Boilerplate Example",
				"title": "CRUD Example",
				"description": "Created by the test suite.",
			}
		).insert()
		self.assertEqual(doc.name, "CRUD Example")
		self.assertEqual(doc.enabled, 1)

		doc.enabled = 0
		doc.save()
		reloaded = frappe.get_doc("Boilerplate Example", "CRUD Example")
		self.assertEqual(reloaded.enabled, 0)

		reloaded.delete()
		self.assertFalse(frappe.db.exists("Boilerplate Example", "CRUD Example"))
