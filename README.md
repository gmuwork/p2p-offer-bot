## Overview

This project creates autonomous trading bot for p2p crypto trading platforms, NOONES and PAXFUL.
The bot functions on the principle of searching for the best competitor offers based on currency, payment method, owner
last seen time, market price.
Best competitor offer is then improved for a specific margin, such that we always provide best offer on the market.

## RUNNING BOT LOCALLY

### AUTHENTICATION TOKENS

In order to run bot locally we first need to issue commands that create and maintain auth token for desired platform.
The commands should be run periodically, so that the expired token is immediately refreshed with the new one.

```bash
python manage.py maintain_active_auth_token  --provider=<PROVIDER_NAME>

# examples
python manage.py maintain_active_auth_token  --provider=PAXFUL
python manage.py maintain_active_auth_token  --provider=NOONES
```

### CONFIGURATION AND OFFERS

After we create authentication tokens for desired platforms, we should set configs and our internal offers that we want
to create. Configs and offers are managed through our API.

#### OFFER MANAGEMENT

Offers are managed through two API endpoints:

**Get all offers**

`Request`

```python
Endpoint: GET
"http://<base_url>/api/offers"
```

`Response`

```python
{
    "data": [
        {
            "id": 3,
            "attributes": {
                "offer_id": "o6CCPpzfZor",
                "provider": "PAXFUL",
                "status": "ACTIVE",
                "type": "BUY",
                "currency": "BTC",
                "fiat_currency": "ZAR",
                "payment_method": "international-wire-transfer-swift"
            }
        },
        {
            "id": 4,
            "attributes": {
                "offer_id": "ukVEPHNRvLi",
                "provider": "NOONES",
                "status": "ACTIVE",
                "type": "BUY",
                "currency": "BTC",
                "fiat_currency": "ZAR",
                "payment_method": "visa-debitcredit-card"
            }
        }
    ]
}
```

**Save new offer**

`Request`

```python
Endpoint: POST
"http://<base_url>/api/offers"
Payload:
{
    "offer_id": "ukVEPHNRvLi",
    "provider": "NOONES"
}
```

`Response`

```python
{
    "data": {
        "attributes": {
            "offer_id": "ukVEPHNRvLi",
            "provider": "NOONES"
        }
    }
}
```

#### CONFIG MANAGEMENT

Configuration for offer improvement and search is managed through two API endpoints.
Following configuration can be managed:

- `amount_to_increase_offer`
- `search_price_upper_margin`
- `search_price_lower_margin`
- `owner_last_seen_max_time`

**Get all configs**
`Request`

```python
Endpoint: GET
"http://<base_url>/api/configs"
```

`Response`

```python
{
    "data": [
        {
            "id": 2,
            "attributes": {
                "currency": "BTC",
                "provider": "PAXFUL",
                "name": "search_price_upper_margin",
                "value": "5"
            }
        },
        {
            "id": 3,
            "attributes": {
                "currency": "BTC",
                "provider": "PAXFUL",
                "name": "search_price_lower_margin",
                "value": "5"
            }
        },
        {
            "id": 4,
            "attributes": {
                "currency": "BTC",
                "provider": "PAXFUL",
                "name": "owner_last_seen_max_time",
                "value": "30"
            }
        },
        {
            "id": 5,
            "attributes": {
                "currency": "BTC",
                "provider": "NOONES",
                "name": "amount_to_increase_offer",
                "value": "20"
            }
        },
        {
            "id": 1,
            "attributes": {
                "currency": "BTC",
                "provider": "PAXFUL",
                "name": "amount_to_increase_offer",
                "value": "20"
            }
        },
        {
            "id": 6,
            "attributes": {
                "currency": "BTC",
                "provider": "NOONES",
                "name": "search_price_upper_margin",
                "value": "5"
            }
        },
        {
            "id": 7,
            "attributes": {
                "currency": "BTC",
                "provider": "NOONES",
                "name": "search_price_lower_margin",
                "value": "5"
            }
        },
        {
            "id": 8,
            "attributes": {
                "currency": "BTC",
                "provider": "NOONES",
                "name": "owner_last_seen_max_time",
                "value": "30"
            }
        }
    ]
}
```

**Save new config**

`Request`

```python
Endpoint: POST
"http://<base_url>/api/configs"
Payload:
{
    "currency": "BTC",
    "provider": "PAXFUL",
    "name": "amount_to_increase_offer",
    "value": "30"
}
```

`Response`

```python
{
    "data": {
        "id": 1,
        "attributes": {
            "currency": "BTC",
            "provider": "PAXFUL",
            "name": "amount_to_increase_offer",
            "value": "30"
        }
    }
}
```

### OFFER IMPROVEMENT

Scripts for offer improvement are supposed to be run periodically. The scripts search for best competitor offers and
improve
our internal offers based on the competition.

```bash
python manage.py improve_active_offers --provider=PAXFUL
python manage.py improve_active_offers --provider=NOONES
```