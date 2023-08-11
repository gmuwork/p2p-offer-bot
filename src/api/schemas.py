from marshmallow import fields
from marshmallow import schema


class Offer(schema.Schema):
    offer_id = fields.Str(required=True, data_key="offer_id")
    provider = fields.Str(required=True, data_key="provider")


class PatchOffer(schema.Schema):
    status = fields.Str(required=True, data_key="status")


class Config(schema.Schema):
    currency = fields.Str(required=True, data_key="currency")
    provider = fields.Str(required=True, data_key="provider")
    config_name = fields.Str(required=True, data_key="name")
    config_value = fields.Str(required=True, data_key="value")
