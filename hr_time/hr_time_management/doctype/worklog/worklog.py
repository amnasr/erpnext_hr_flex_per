# Copyright (c) 2024, AtlasAero GmbH and contributors
# For license information, please see license.txt

from datetime import datetime
import frappe
from frappe.model.document import Document
from frappe.model.docstatus import DocStatus
from hr_time.api.shared.utils.frappe_utils import FrappeUtils
from hr_time.api.shared.constants.messages import Messages


class Worklog(Document):
    def before_save(self):
        if not self.log_time:
            # Set the time field to the current datetime
            self.log_time = datetime.now()

        # Set the employee field to the current user's corresponding Employee record
        if not self.employee:
            self.set_employee_from_user()

    def set_employee_from_user(self):
        # Fetch the employee record linked to the current user
        user_id = frappe.session.user

        # Get the Employee document where the user_id matches the current user
        employee = frappe.get_value("Employee", {"user_id": user_id}, "name")

        if employee:
            self.employee = employee
        else:
            FrappeUtils.throw_error_msg(Messages.Employee.NOT_FOUND_EMPLOYEE)
