# -*- coding: utf-8 -*-

import unittest
import datetime
from api import (
    IntField,
    CharField,
    EmailField,
    PhoneField,
    GenderField,
    DateField,
    BirthDayField,
    ArgumentsField,
    ListField,
    ClientIDsField,
    FieldValidationError,
)
from tests.helper import cases


class TestCharField(unittest.TestCase):
    def setUp(self):
        self.field = CharField()

    @cases(
        [
            '',
            'short',
            'looooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooong',
            "12345678",
        ]
    )
    def test_char_field_successful_validate(self, value):
        self.assertIsNone(self.field.check_field(value))

    @cases([None, 12345678, []])
    def test_char_field_unsuccessful_validate(self, value):
        with self.assertRaises(FieldValidationError):
            self.field.check_field(value)


class TestIntField(unittest.TestCase):
    def setUp(self):
        self.field = IntField()

    @cases([0, 12345678, -1])
    def test_int_field_successful_validate(self, value):
        self.assertIsNone(self.field.check_field(value))

    @cases([None, '12345678', 1.1])
    def test_int_field_unsuccessful_validate(self, value):
        with self.assertRaises(FieldValidationError):
            self.field.check_field(value)


class TestDateField(unittest.TestCase):
    def setUp(self):
        self.field = DateField()

    @cases(['31.12.2021', '01.01.2022'])
    def test_date_field_successful_validate(self, value):
        self.assertIsNone(self.field.check_field(value))

    @cases([None, '', 12345678, 'short', {}, [], '32.12.2021', '01.13.2022'])
    def test_date_field_unsuccessful_validate(self, value):
        with self.assertRaises(FieldValidationError):
            self.field.check_field(value)


class TestEmailField(unittest.TestCase):
    def setUp(self):
        self.field = EmailField()

    @cases(['login@doma.in'])
    def test_email_field_successful_validate(self, value):
        self.assertIsNone(self.field.check_field(value))

    @cases([None, 'login', '@', 'doma.in', 'login@doma' 'login@doma.'])
    def test_email_field_unsuccessful_validate(self, value):
        with self.assertRaises(FieldValidationError):
            self.field.check_field(value)


class TestGenderField(unittest.TestCase):
    def setUp(self):
        self.field = GenderField()

    @cases(
        [
            0,
            1,
            2,
        ]
    )
    def test_gender_field_successful_validate(self, value):
        self.assertIsNone(self.field.check_field(value))

    @cases(
        [
            None,
            '',
            3,
            'short',
            '0',
        ]
    )
    def test_gender_field_unsuccessful_validate(self, value):
        with self.assertRaises(FieldValidationError):
            self.field.check_field(value)


class TestPhoneField(unittest.TestCase):
    def setUp(self):
        self.field = PhoneField()

    @cases(['71234567890', 71234567890])
    def test_phone_field_successful_validate(self, value):
        self.assertIsNone(self.field.check_field(value))

    @cases(
        [
            None,
            '',
            [],
            {},
            7123456789,
            11234567890,
            712345678900,
            '7123456789K',
            '+7123456789',
            '7(123)45678',
            '7-123-456-7',
        ]
    )
    def test_phone_field_unsuccessful_validate(self, value):
        with self.assertRaises(FieldValidationError):
            self.field.check_field(value)


class TestBirthDayField(unittest.TestCase):
    def setUp(self):
        self.field = BirthDayField()

    @cases(
        [
            datetime.datetime.today().strftime('%d.%m.%Y'),
            (datetime.datetime.today() - datetime.timedelta(365 * 70)).strftime('%d.%m.%Y'),
        ]
    )
    def test_birthday_field_successful_validate(self, value):
        self.assertIsNone(self.field.check_field(value))

    @cases(
        [
            (datetime.datetime.today() - datetime.timedelta(365 * 71)).strftime('%d.%m.%Y'),
            (datetime.datetime.today() + datetime.timedelta(1)).strftime('%d.%m.%Y'),
        ]
    )
    def test_birthday_field_unsuccessful_validate(self, value):
        with self.assertRaises(FieldValidationError):
            self.field.check_field(value)


class TestListField(unittest.TestCase):
    def setUp(self):
        self.field = ListField()

    @cases([[], [1, 2], ['q', 'w'], [1, 'w']])
    def test_list_field_successful_validate(self, value):
        self.assertIsNone(self.field.check_field(value))

    @cases([None, '', 12345678, 'short', {}])
    def test_list_field_unsuccessful_validate(self, value):
        with self.assertRaises(FieldValidationError):
            self.field.check_field(value)


class TestClientIDsField(unittest.TestCase):
    def setUp(self):
        self.field = ClientIDsField()

    @cases([[0], [1, 2, 3]])
    def test_client_ids_field_successful_validate(self, value):
        self.assertIsNone(self.field.check_field(value))

    @cases([['1', '2'], [1, 'q'], [1.1]])
    def test_client_ids_field_unsuccessful_validate(self, value):
        with self.assertRaises(FieldValidationError):
            self.field.check_field(value)


class TestArgumentField(unittest.TestCase):
    def setUp(self):
        self.field = ArgumentsField()

    @cases([{}, {"short": "short", "short": 12345678}])
    def test_argument_field_successful_validate(self, value):
        self.assertIsNone(self.field.check_field(value))

    @cases([None, '', 12345678, 'short', []])
    def test_argument_field_unsuccessful_validate(self, value):
        with self.assertRaises(FieldValidationError):
            self.field.check_field(value)


if __name__ == '__main__':
    unittest.main()
