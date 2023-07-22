from marshmallow import fields
from marshmallow import schema


class AuthenticationToken(schema.Schema):
    access_token = fields.Str(required=True, data_key="access_token")
    expires_in = fields.Integer(required=True, data_key="expires_in")


class Offer(schema.Schema):
    offer_id = fields.Str(required=True, data_key="offer_id")
    offer_type = fields.Str(required=True, data_key="offer_type")
    crypto_currency_code = fields.Str(required=True, data_key="crypto_currency_code")
    fiat_currency_code = fields.Str(required=True, data_key="fiat_currency_code")
    fiat_price_per_crypto = fields.Decimal(
        required=True, data_key="fiat_price_per_crypto"
    )
    payment_method_slug = fields.Str(required=True, data_key="payment_method_slug")
    last_seen_timestamp = fields.Decimal(required=False, data_key="last_seen_timestamp", missing=None)
