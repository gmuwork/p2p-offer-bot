from marshmallow import fields
from marshmallow import schema


class Offer(schema.Schema):
    offer_id = fields.Str(required=True, data_key="offer_id")


class PatchOffer(schema.Schema):
    status = fields.Str(required=True, data_key="status")
