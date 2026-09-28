# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase

# a transparent 1x1 PNG image
SIGNATURE = (
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42"
    b"mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


class TestHREmployeePPE(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product_employee_ppe_expirable = self.env["product.template"].create(
            {
                "name": "Product Test Employee PPE",
                "is_personal_equipment": True,
                "is_ppe": True,
                "indications": "Test indications",
                "expirable_ppe": True,
                "ppe_interval_type": "days",
                "ppe_duration": 3,
            }
        )
        self.product_employee_ppe_no_expirable = self.env["product.template"].create(
            {
                "name": "Product Test Employee No PPE",
                "is_personal_equipment": True,
                "is_ppe": True,
                "indications": "Test indications",
                "expirable_ppe": False,
            }
        )
        self.user = (
            self.env["res.users"]
            .sudo()
            .create(
                {
                    "name": "Test User",
                    "login": "user@test.com",
                    "email": "user@test.com",
                    "groups_id": [
                        (4, self.env.ref("base.group_user").id),
                        (4, self.env.ref("hr.group_hr_user").id),
                    ],
                }
            )
        )
        self.employee = self.env["hr.employee"].create(
            {"name": "Employee Test", "user_id": self.user.id}
        )
        product_exp = self.product_employee_ppe_expirable.product_variant_id
        product_no_exp = self.product_employee_ppe_no_expirable.product_variant_id
        lines = [
            {
                "name": "Personal Equipment PPE Expirable",
                "product_id": product_exp.id,
                "quantity": 3,
            },
            {
                "name": "Personal Equipment No Expirable",
                "product_id": product_no_exp.id,
                "quantity": 2,
            },
        ]

        self.personal_equipment_request = (
            self.env["hr.personal.equipment.request"]
            .with_user(self.user.id)
            .create(
                {
                    "name": "Personal Equipment Request Test",
                    "line_ids": [(0, 0, line) for line in lines],
                }
            )
        )

        self.hr_employee_ppe_expirable = self.personal_equipment_request.line_ids[0]
        self.hr_employee_ppe_no_expirable = self.personal_equipment_request.line_ids[1]

    def _create_request(self, product_template):
        return (
            self.env["hr.personal.equipment.request"]
            .with_user(self.user)
            .create(
                {
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": product_template.product_variant_id.id,
                                "quantity": 1,
                            },
                        )
                    ],
                }
            )
        )

    def test_ppe_data_from_product(self):
        self.assertTrue(self.hr_employee_ppe_expirable.is_ppe)
        self.assertTrue(self.hr_employee_ppe_expirable.expire_ppe)
        self.assertEqual(
            self.hr_employee_ppe_expirable.indications,
            self.product_employee_ppe_expirable.indications,
        )
        self.assertTrue(self.hr_employee_ppe_no_expirable.is_ppe)
        self.assertFalse(self.hr_employee_ppe_no_expirable.expire_ppe)

    def test_ppe_data_follows_product_changes(self):
        allocation = self.hr_employee_ppe_expirable
        self.product_employee_ppe_expirable.write(
            {"is_ppe": False, "indications": "New indications"}
        )
        self.assertFalse(allocation.is_ppe)
        self.assertEqual(allocation.indications, "New indications")
        # whether the allocation expires can still be decided per allocation
        allocation.expire_ppe = False
        self.assertFalse(allocation.expire_ppe)

    def test_certification_copied_from_product(self):
        product = self.product_employee_ppe_expirable
        product.ppe_certification = "12345"
        allocation = self._create_request(product).line_ids
        self.assertEqual(allocation.certification, "12345")
        # the allocation keeps the certification of the delivered PPE
        product.ppe_certification = "67890"
        self.assertEqual(allocation.certification, "12345")
        # but it can still be changed on the allocation
        allocation.certification = "54321"
        self.assertEqual(allocation.certification, "54321")
        self.assertEqual(product.ppe_certification, "67890")

    def test_expired_certification_blocks_delivery(self):
        today = fields.Date.context_today(self.hr_employee_ppe_expirable)
        self.product_employee_ppe_expirable.ppe_certification_expiry_date = (
            today - timedelta(days=1)
        )
        with self.assertRaises(UserError):
            self.personal_equipment_request.accept_request()
        with self.assertRaises(UserError):
            self.hr_employee_ppe_expirable.validate_allocation()
        self.assertEqual(self.hr_employee_ppe_expirable.state, "draft")

    def test_expired_certification_allowed(self):
        today = fields.Date.context_today(self.hr_employee_ppe_expirable)
        self.product_employee_ppe_expirable.ppe_certification_expiry_date = (
            today - timedelta(days=1)
        )
        self.employee.company_id.ppe_block_expired_certification = False
        self.personal_equipment_request.accept_request()
        self.hr_employee_ppe_expirable.validate_allocation()
        self.assertEqual(self.hr_employee_ppe_expirable.state, "valid")

    def test_certification_valid_until_its_expiry_date(self):
        today = fields.Date.context_today(self.hr_employee_ppe_expirable)
        self.product_employee_ppe_expirable.ppe_certification_expiry_date = today
        self.personal_equipment_request.accept_request()
        self.hr_employee_ppe_expirable.validate_allocation()
        self.assertEqual(self.hr_employee_ppe_expirable.state, "valid")

    def test_accept_allocation(self):
        self.assertFalse(self.hr_employee_ppe_expirable.issued_by)
        self.personal_equipment_request.with_user(self.user).accept_request()
        self.assertTrue(self.hr_employee_ppe_expirable.issued_by)
        self.assertEqual(self.hr_employee_ppe_expirable.issued_by, self.user)

    def test_validate_allocation_with_start_date(self):
        self.assertFalse(self.hr_employee_ppe_expirable.expiry_date)
        self.hr_employee_ppe_expirable.start_date = "2020-01-01"
        self.hr_employee_ppe_expirable.validate_allocation()
        self.assertTrue(self.hr_employee_ppe_expirable.expiry_date)
        self.assertEqual(str(self.hr_employee_ppe_expirable.expiry_date), "2020-01-04")

    def test_validate_allocation_without_start_date(self):
        self.assertFalse(self.hr_employee_ppe_expirable.expiry_date)
        self.assertFalse(self.hr_employee_ppe_expirable.start_date)
        self.hr_employee_ppe_expirable.validate_allocation()
        self.assertEqual(
            self.hr_employee_ppe_expirable.expiry_date,
            self.hr_employee_ppe_expirable.start_date
            + relativedelta(days=self.product_employee_ppe_expirable.ppe_duration),
        )

    def test_validate_allocation_duration_in_years(self):
        self.product_employee_ppe_expirable.write(
            {"ppe_interval_type": "years", "ppe_duration": 2}
        )
        allocation = self.hr_employee_ppe_expirable
        allocation.start_date = "2020-02-29"
        allocation.validate_allocation()
        self.assertEqual(allocation.expiry_date, date(2022, 2, 28))

    def test_validate_allocation_expirable_without_expiry_date(self):
        allocation = self.hr_employee_ppe_no_expirable
        allocation.expire_ppe = True
        allocation.validate_allocation()
        self.assertEqual(allocation.state, "valid")
        self.assertFalse(allocation.expiry_date)

    def test_validate_allocation_without_interval_type(self):
        self.product_employee_ppe_expirable.ppe_interval_type = False
        allocation = self.hr_employee_ppe_expirable
        allocation.validate_allocation()
        self.assertEqual(allocation.state, "valid")
        self.assertFalse(allocation.expiry_date)

    def test_cron_ppe_expiry_verification_expired_product(self):
        self.hr_employee_ppe_expirable.start_date = "2020-01-01"
        self.hr_employee_ppe_expirable.expiry_date = "2020-12-31"
        self.hr_employee_ppe_expirable.validate_allocation()
        self.assertEqual(self.hr_employee_ppe_expirable.state, "valid")
        self.hr_employee_ppe_expirable.cron_ppe_expiry_verification()
        self.assertEqual(self.hr_employee_ppe_expirable.state, "expired")

    def test_cron_ppe_expiry_verification_no_expired_product(self):
        self.hr_employee_ppe_expirable.expiry_date = (
            datetime.now() + timedelta(days=1)
        ).strftime("%Y-%m-%d")
        self.hr_employee_ppe_expirable.validate_allocation()
        self.assertEqual(self.hr_employee_ppe_expirable.state, "valid")
        self.hr_employee_ppe_expirable.cron_ppe_expiry_verification()
        self.assertNotEqual(self.hr_employee_ppe_expirable.state, "expired")

    def test_cron_ppe_expiry_verification_no_expirable_product(self):
        self.hr_employee_ppe_no_expirable.validate_allocation()
        self.assertEqual(self.hr_employee_ppe_no_expirable.state, "valid")
        self.hr_employee_ppe_no_expirable.cron_ppe_expiry_verification()
        self.assertNotEqual(self.hr_employee_ppe_no_expirable.state, "expired")

    def test_cron_ppe_expiry_verification_only_valid_allocations(self):
        allocation = self.hr_employee_ppe_expirable
        allocation.expiry_date = "2020-12-31"
        allocation.cron_ppe_expiry_verification()
        self.assertEqual(allocation.state, "draft")
        self.personal_equipment_request.cancel_request()
        allocation.cron_ppe_expiry_verification()
        self.assertEqual(allocation.state, "cancelled")

    def _deliver_expiring_ppe(self, days):
        """Deliver the expirable PPE with an expiry date in ``days`` days."""
        allocation = self.hr_employee_ppe_expirable
        self.personal_equipment_request.accept_request()
        today = fields.Date.context_today(allocation)
        allocation.write(
            {"start_date": today, "expiry_date": today + timedelta(days=days)}
        )
        allocation.validate_allocation()
        return allocation

    def test_cron_schedules_renewal_activity(self):
        allocation = self._deliver_expiring_ppe(10)
        allocation.cron_ppe_expiry_verification()
        activity = allocation.activity_ids
        self.assertEqual(len(activity), 1)
        self.assertEqual(
            activity.activity_type_id,
            self.env.ref("hr_employee_ppe.mail_activity_type_ppe_renewal"),
        )
        self.assertEqual(activity.date_deadline, allocation.expiry_date)
        # the user who accepted the request is in charge by default
        self.assertEqual(activity.user_id, self.user)
        self.assertTrue(allocation.expiry_notice_sent)
        # the activity is not scheduled again once done
        activity.action_done()
        allocation.cron_ppe_expiry_verification()
        self.assertFalse(allocation.activity_ids)

    def test_cron_renewal_activity_responsible(self):
        responsible = self.env["res.users"].create(
            {"name": "PPE Responsible", "login": "ppe.responsible@test.com"}
        )
        self.employee.company_id.ppe_expiry_responsible_id = responsible
        allocation = self._deliver_expiring_ppe(10)
        allocation.cron_ppe_expiry_verification()
        self.assertEqual(allocation.activity_ids.user_id, responsible)

    def test_cron_renewal_activity_outside_notice_period(self):
        self.employee.company_id.ppe_expiry_notice_days = 5
        allocation = self._deliver_expiring_ppe(10)
        allocation.cron_ppe_expiry_verification()
        self.assertFalse(allocation.activity_ids)
        self.assertFalse(allocation.expiry_notice_sent)

    def test_cron_renewal_activity_disabled(self):
        self.employee.company_id.ppe_expiry_notice_days = 0
        allocation = self._deliver_expiring_ppe(10)
        allocation.cron_ppe_expiry_verification()
        self.assertFalse(allocation.activity_ids)

    def test_new_expiry_date_resets_renewal_notice(self):
        allocation = self._deliver_expiring_ppe(10)
        allocation.cron_ppe_expiry_verification()
        self.assertTrue(allocation.expiry_notice_sent)
        allocation.expiry_date = allocation.expiry_date + timedelta(days=365)
        self.assertFalse(allocation.expiry_notice_sent)

    def test_signature_date(self):
        allocation = self.hr_employee_ppe_expirable
        allocation.employee_signature = SIGNATURE
        self.assertTrue(allocation.signed_on)
        allocation.employee_signature = False
        self.assertFalse(allocation.signed_on)

    def test_request_signature_copied_to_ppe(self):
        request = self.personal_equipment_request
        request.employee_signature = SIGNATURE
        self.assertTrue(request.signed_on)
        request.accept_request()
        allocation = self.hr_employee_ppe_expirable
        allocation.validate_allocation()
        self.assertEqual(allocation.employee_signature, request.employee_signature)
        self.assertEqual(allocation.signed_on, request.signed_on)

    def test_signature_required(self):
        self.employee.company_id.ppe_require_signature = True
        self.personal_equipment_request.accept_request()
        allocation = self.hr_employee_ppe_expirable
        with self.assertRaises(UserError):
            allocation.validate_allocation()
        allocation.employee_signature = SIGNATURE
        allocation.validate_allocation()
        self.assertEqual(allocation.state, "valid")

    def test_signature_locked_once_delivered(self):
        allocation = self.hr_employee_ppe_expirable
        allocation.employee_signature = SIGNATURE
        allocation.validate_allocation()
        with self.assertRaises(UserError):
            allocation.employee_signature = False

    def test_check_dates(self):
        with self.assertRaises(ValidationError):
            self.hr_employee_ppe_expirable.start_date = "2020-01-01"
            self.hr_employee_ppe_expirable.expiry_date = "2019-12-31"
            self.hr_employee_ppe_expirable.validate_allocation()

    def test_compute_contains_ppe(self):
        # Without ppes
        product_employee_no_ppe = self.env["product.template"].create(
            {
                "name": "Product Test Employee No PPE",
                "is_personal_equipment": True,
                "is_ppe": False,
            }
        )
        product = product_employee_no_ppe.product_variant_id
        lines = [
            {
                "name": "Personal Equipment PPE Expirable",
                "product_id": product.id,
                "quantity": 3,
            }
        ]

        personal_equipment_request = (
            self.env["hr.personal.equipment.request"]
            .with_user(self.user.id)
            .create(
                {
                    "name": "Personal Equipment Request Test",
                    "line_ids": [(0, 0, line) for line in lines],
                }
            )
        )
        personal_equipment_request._compute_contains_ppe()
        self.assertFalse(personal_equipment_request.contains_ppe)

        # With ppes
        product = self.product_employee_ppe_expirable.product_variant_id
        lines.append(
            {
                "name": "Personal Equipment PPE Expirable",
                "is_ppe": True,
                "product_id": product.id,
                "quantity": 3,
            }
        )
        personal_equipment_request["line_ids"] = [(0, 0, line) for line in lines]
        personal_equipment_request._compute_contains_ppe()
        self.assertTrue(personal_equipment_request.contains_ppe)

    def test_action_view_ppe_report(self):
        self.env.company.external_report_layout_id = self.env.ref(
            "web.external_layout_standard"
        ).id
        action = self.personal_equipment_request.action_view_ppe_report()
        self.assertEqual(action["name"], "Receipt of Personal protection Equipment")
        self.assertEqual(len(action["context"]["active_ids"]), 1)
        self.assertEqual(
            action["context"]["active_ids"][0], self.personal_equipment_request.id
        )
        self.assertEqual(action["report_type"], "qweb-pdf")
