#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
import re
import scoring
from typing import Dict, Tuple, Any
from weakref import WeakKeyDictionary

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class FieldValidationError(ValueError):
    pass


class BaseField(metaclass=abc.ABCMeta):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable
        self.data = WeakKeyDictionary()

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        self.data[instance] = value

    def __get__(self, instance, owner):
        return self.data.get(instance)

    @abc.abstractmethod
    def check_field(self, value):
        pass


class IntField(BaseField):
    def check_field(self, value):
        if not isinstance(value, int):
            raise FieldValidationError('Incorrect field type. Field is not a int. Value %s' % value)


class ListField(BaseField):
    def check_field(self, value):
        if not isinstance(value, list):
            raise FieldValidationError('Incorrect field type. Field is not a list')


class CharField(BaseField):
    def check_field(self, value):
        if not isinstance(value, str):
            raise FieldValidationError('Incorrect field type. Field is not a string. Value %s' % value)


class DateField(CharField):
    def check_field(self, value):
        super(DateField, self).check_field(value)
        try:
            datetime.datetime.strptime(value, '%d.%m.%Y')
        except (ValueError, TypeError):
            raise FieldValidationError('Date field format error. Format must be DD.MM.YYYY. Value %s' % value)


class ArgumentsField(BaseField):
    def check_field(self, value):
        if not isinstance(value, dict):
            raise FieldValidationError('Incorrect field type. Field is not a dict. Value %s' % value)


class EmailField(CharField):
    def check_field(self, value):
        super(EmailField, self).check_field(value)
        if not re.match(r'^[\w\.-]+@[\w\.-]+[.]\w{2,3}$', value):
            raise FieldValidationError('Email field format error. Symbol @ not found. Value %s' % value)


class PhoneField(BaseField):
    def check_field(self, value):
        if not re.match(r'^7[0-9]{10}$', str(value)):
            raise FieldValidationError(
                'Phone field format error. The length must be equal to 11 symbols and start with 7. Value %s' % value
            )


class BirthDayField(DateField):
    MAX_AGE = 70

    def check_field(self, value):
        super(BirthDayField, self).check_field(value)
        date_birthday = datetime.datetime.strptime(value, '%d.%m.%Y')
        if datetime.datetime.now().year - date_birthday.year > self.MAX_AGE:
            raise FieldValidationError('Birthday field error. The age cannot be more than 70. Value %s' % value)
        if date_birthday > datetime.datetime.now():
            raise FieldValidationError('Birthday field error. Date can\'t be in future. Value %s' % value)


class GenderField(IntField):
    def check_field(self, value):
        super(GenderField, self).check_field(value)
        if value not in GENDERS.keys():
            raise FieldValidationError('Gender field error. The value must be 0, 1 or 2. Value %s' % value)


class ClientIDsField(ListField):
    def check_field(self, value):
        super(ClientIDsField, self).check_field(value)
        for v in value:
            if not isinstance(v, int):
                raise FieldValidationError('Incorrect field type. Field must be a list of int')


class BaseRequest(object):
    def __new__(cls, *args, **kwargs):
        cls.fields = [
            field_name for field_name, field_value in cls.__dict__.items() if isinstance(field_value, BaseField)
        ]
        return super(BaseRequest, cls).__new__(cls)

    def __init__(self, **kwargs):
        for field in self.fields:
            setattr(self, field, kwargs.get(field))

    def validate_request(self):
        errors_string = ''
        for name in self.fields:
            field = self.__class__.__dict__.get(name)
            value = getattr(self, name)

            if field.required:
                if value is None:
                    errors_string += 'Field validation error. Field %s is required.' % name
                    continue
            if not field.nullable:
                if value in ("", (), [], {}):
                    errors_string += 'Field validation error. Field %s can\'t be empty.' % name
                    continue

            if value not in (None, "", (), [], {}):
                try:
                    field.check_field(value)
                except FieldValidationError as e:
                    errors_string += 'Field validation error. Field %s. Error:  %s.' % (name, str(e))

        if errors_string != '':
            raise FieldValidationError(errors_string)


class ClientsInterestsRequest(BaseRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(BaseRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate_request(self):
        super(OnlineScoreRequest, self).validate_request()
        if not (
            (self.phone and self.email)
            or (self.first_name and self.last_name)
            or (self.gender in GENDERS.keys() and self.birthday)
        ):
            raise FieldValidationError('phone-email or first_name-last_name or gender-birthday must be not empty')


class MethodRequest(BaseRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login + SALT).encode('utf-8')).hexdigest()
    if digest == request.token:
        return True
    return False


def clients_interest_handler(request: Dict[str, Dict], ctx: Dict[str, Any], store) -> Tuple[Dict[str, Any], int]:
    ci_req = ClientsInterestsRequest(**request.arguments)
    ci_req.validate_request()

    ctx['nclients'] = len(ci_req.client_ids)

    response = {x: scoring.get_interests(store, x) for x in ci_req.client_ids}
    return response, OK


def online_score_handler(request: Dict[str, Dict], ctx: Dict[str, Any], store) -> Tuple[Dict[str, Any], int]:
    os_req = OnlineScoreRequest(**request.arguments)
    os_req.validate_request()

    ctx['has'] = [name for name in os_req.fields if getattr(os_req, name) is not None]

    if request.is_admin:
        response, code = dict(score=42), OK
    else:
        score = scoring.get_score(
            store=store,
            phone=os_req.phone,
            email=os_req.email,
            birthday=os_req.birthday,
            gender=os_req.gender,
            first_name=os_req.first_name,
            last_name=os_req.last_name,
        )
        response, code = dict(score=score), OK
    return response, code


def method_handler(request, ctx, store):
    handlers = {'online_score': online_score_handler, 'clients_interests': clients_interest_handler}
    request_dict = request.get('body')
    if not isinstance(request_dict, dict):
        return 'Request body must be a valid dictionary', INVALID_REQUEST

    try:
        method_request = MethodRequest(**request_dict)
        method_request.validate_request()
    except FieldValidationError as e:
        logging.exception(e)
        return str(e), INVALID_REQUEST

    if not check_auth(method_request):
        return None, FORBIDDEN

    if method_request.method not in handlers:
        return 'Unknown method %s' % str(method_request.method), INVALID_REQUEST
    else:
        handler = handlers[method_request.method]

    try:
        return handler(request=method_request, ctx=ctx, store=store)
    except FieldValidationError as e:
        logging.exception(e)
        return str(e), INVALID_REQUEST


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {"method": method_handler}
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode('utf_8'))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(
        filename=opts.log,
        level=logging.INFO,
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S',
    )
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
