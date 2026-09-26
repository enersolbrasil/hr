from dateutil.relativedelta import relativedelta

from odoo import fields

from odoo.addons.base.tests.common import BaseCommon


class TestHrEmployee(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee_admin = cls.env.ref("hr.employee_admin")
        cls.birthday_34 = fields.Date.today() - relativedelta(years=34)
        cls.employee_admin.write({"birthday": cls.birthday_34})

    def test_compute_age(self):
        self.employee_admin._compute_age()
        self.assertEqual(self.employee_admin.age, 34)

    def test_compute_age_no_birthday(self):
        self.employee_admin.birthday = False
        self.employee_admin._compute_age()
        self.assertFalse(self.employee_admin.age)

    def test_search_age(self):
        self.employee_admin.birthday = self.birthday_34
        employees = self.env["hr.employee"].search([("age", ">=", 30)])
        self.assertIn(self.employee_admin, employees)
