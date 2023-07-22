import dataclasses
import datetime


@dataclasses.dataclass
class AuthenticationToken:
    token: str
    expires_at: datetime.datetime
