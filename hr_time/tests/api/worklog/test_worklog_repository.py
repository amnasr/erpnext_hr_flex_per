import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from hr_time.api.worklog.repository import WorklogRepository, Worklog
from hr_time.api.shared.constants.messages import Messages


class TestWorklogRepository(unittest.TestCase):
    def setUp(self):
        self.repo = WorklogRepository()

    @patch('frappe.get_all')
    def test_get_worklogs(self, mock_get_all):
        # Arrange
        mock_data = [{"employee": "EMP001", "log_time": "2023-01-01 10:00:00",
                      "task_desc": "Test Task", "task": "Task1"}]
        # Define the mock method (lambda) to handle all fields defined in frappe framework
        mock_get_all.side_effect = lambda doctype, fields=None, filters=None, **kwargs: mock_data
        filters = {"employee": "EMP001"}

        # Act
        worklogs = self.repo.get_worklogs(filters)

        # Assert
        self.assertEqual(worklogs, mock_data)
        mock_get_all.assert_called_once_with("Worklog", fields=self.repo._doc_fields, filters=filters)


@patch('frappe.get_all')
def test_get_worklogs_of_employee_on_date(self, mock_get_all):
    # Arrange
    interested_emp_id = 'EMP001'
    interested_date = datetime(2024, 10, 10).date()
    mock_data = [
        {'employee': interested_emp_id, 'log_time': datetime(
            2024, 10, 10, 10, 10, 10), 'task_desc': 'Worked on task 1', 'task': 'TASK001'},
        {'employee': interested_emp_id, 'log_time': datetime(
            2024, 10, 11, 10, 0, 0), 'task_desc': 'Worked on task 2', 'task': 'TASK002'},
    ]

    # Mocking frappe.get_all to simulate filtering by date
    mock_get_all.side_effect = lambda doctype, fields=None, filters=None: [
        entry for entry in mock_data
        if filters['employee'] == interested_emp_id
        and filters['log_time'][1][0] <= entry['log_time'] <= filters['log_time'][1][1]
    ]

    # Act
    worklogs = self.repo.get_worklogs_of_employee_on_date(interested_emp_id, interested_date)

    # Assert
    self.assertEqual(len(worklogs), 1)  # Expecting only one log entry for 2024-10-10
    self.assertIsInstance(worklogs[0], Worklog)
    self.assertEqual(worklogs[0].employee_id, interested_emp_id)
    self.assertEqual(worklogs[0].task_desc, 'Worked on task 1')
    self.assertEqual(worklogs[0].task_desc, 'TASK001')
    # Verifying if correct filters are applied
    mock_get_all.assert_called_once_with(
        "Worklog", fields=self.repo.doc_fields,
        filters={
            "employee": interested_emp_id,
            "log_time": ["between", [
                datetime.combine(interested_date, datetime.min.time()), datetime.combine(
                    interested_date, datetime.max.time())
            ]]
        }
    )

    @patch('hr_time.api.worklog.repository.frappe.new_doc')
    def test_create_worklog_success(self, mock_new_doc):
        # Arrange
        mock_worklog_doc = MagicMock()
        mock_new_doc.return_value = mock_worklog_doc
        employee_id = 'EMP001'
        log_time = datetime(2024, 10, 10, 9, 0)
        worklog_text = 'Completed task'
        task = 'TASK001'

        # Act
        result = self.repo.create_worklog(employee_id, log_time, worklog_text, task)

        # Assert
        mock_new_doc.assert_called_once_with("Worklog")
        mock_worklog_doc.save.assert_called_once()
        self.assertEqual(result, {'status': 'success', 'message': Messages.Worklog.SUCCESS_WORKLOG_CREATION})

    @patch('hr_time.api.worklog.repository.frappe.new_doc')
    @patch('hr_time.api.worklog.repository.frappe.db.rollback')
    def test_create_worklog_failure(self, mock_rollback, mock_new_doc):
        # Arrange
        mock_new_doc.side_effect = Exception(Messages.Common.ERR_DB)
        employee_id = 'EMP001'
        log_time = datetime(2024, 10, 10, 9, 0)
        worklog_text = 'Completed task'
        task = 'TASK001'

        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.repo.create_worklog(employee_id, log_time, worklog_text, task)
        # Ensure the exception contains the ERR_DB message
        self.assertEqual(str(context.exception), Messages.Common.ERR_DB)
        # Ensure rollback is called on failure
        mock_rollback.assert_called_once()
