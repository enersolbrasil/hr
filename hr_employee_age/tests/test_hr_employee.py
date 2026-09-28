# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from freezegun import freeze_time

from odoo.exceptions import UserError

from odoo.addons.base.tests.common import BaseCommon


class TestHrEmployee(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee_admin = cls.env.ref("hr.employee_admin")
        cls.employee_admin.write({"birthday": "1990-05-15"})
        cls.employees = cls.env["hr.employee"].create(
            [
                # 33 years old on 2024-05-15
                {"name": "Born 1990-05-16", "birthday": "1990-05-16"},
                # 34 years old on 2024-05-15
                {"name": "Born 1990-05-15", "birthday": "1990-05-15"},
                # 35 years old on 2024-05-15
                {"name": "Born 1989-05-15", "birthday": "1989-05-15"},
                {"name": "Without birthday"},
            ]
        )
        cls.age_33, cls.age_34, cls.age_35, cls.no_birthday = cls.employees

    def _search_age(self, operator, value):
        return self.env["hr.employee"].search(
            [("id", "in", self.employees.ids), ("age", operator, value)]
        )

    @freeze_time("2024-05-15")
    def test_compute_age(self):
        self.employee_admin._compute_age()
        self.assertEqual(self.employee_admin.age, 34)

    @freeze_time("2024-05-15 12:00:00")
    def test_compute_age_without_birthday(self):
        self.assertEqual(self.no_birthday.age, 0)

    @freeze_time("2024-05-15 12:00:00")
    def test_search_age(self):
        self.assertEqual(self._search_age("=", 34), self.age_34)
        self.assertEqual(self._search_age(">=", 34), self.age_34 | self.age_35)
        self.assertEqual(self._search_age(">", 34), self.age_35)
        self.assertEqual(self._search_age("<=", 34), self.age_33 | self.age_34)
        self.assertEqual(self._search_age("<", 34), self.age_33)
        self.assertEqual(
            self._search_age("!=", 34), self.age_33 | self.age_35 | self.no_birthday
        )
        self.assertEqual(self._search_age("in", [33, 35]), self.age_33 | self.age_35)
        self.assertEqual(
            self._search_age("not in", [33, 35]), self.age_34 | self.no_birthday
        )
        self.assertEqual(self._search_age("=", False), self.no_birthday)

    @freeze_time("2024-05-15 12:00:00")
    def test_search_age_matches_compute(self):
        for age in (33, 34, 35):
            employees = self._search_age("=", age)
            self.assertEqual(employees.mapped("age"), [age])

    @freeze_time("2027-02-28 12:00:00")
    def test_search_age_born_on_leap_day(self):
        employee = self.env["hr.employee"].create(
            {"name": "Born on a leap day", "birthday": "2024-02-29"}
        )
        self.assertEqual(employee.age, 3)
        employees = self.env["hr.employee"].search(
            [("id", "=", employee.id), ("age", "=", 3)]
        )
        self.assertEqual(employees, employee)

    def test_search_age_unsupported_operator(self):
        with self.assertRaises(UserError):
            self._search_age("ilike", 34)
