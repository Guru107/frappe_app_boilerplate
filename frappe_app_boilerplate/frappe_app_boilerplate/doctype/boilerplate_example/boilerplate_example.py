# Copyright (c) 2026, Gurudatt Kulkarni and contributors
# For license information, please see license.txt

# DELETE ME AFTER RENAME: this is the starter's example DocType. Delete this
# whole folder once you have run the rename script and started building your
# own DocTypes.

# import frappe
from frappe.model.document import Document


class BoilerplateExample(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.SmallText | None
		enabled: DF.Check
		title: DF.Data
	# end: auto-generated types
