"""Whitelisted API methods for this app.

`echo` is the starter's living example of the
`require_type_annotated_api_methods` hook (see `hooks.py`): every whitelisted
method must annotate all of its arguments and its return type, and calls with
wrongly-typed arguments are rejected with `frappe.exceptions.FrappeTypeError`.
"""

import frappe


@frappe.whitelist()
def echo(message: str) -> str:
	"""Return *message* unchanged.

	:param message: The message to echo back.
	:return: The message, unchanged.
	"""
	return message
