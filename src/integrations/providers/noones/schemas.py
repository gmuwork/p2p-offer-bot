from marshmallow import fields
from marshmallow import schema


class AuthenticationToken(schema.Schema):
    access_token = fields.Str(required=True, data_key="access_token")
    expires_in = fields.Str(required=True, data_key="expires_in")
