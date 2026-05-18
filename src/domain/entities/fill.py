from dataclasses import dataclass, field
from decimal import Decimal
from uuid import uuid4


@dataclass
class Fill:
    oid: int  # FK -> orders.oid
    owner_address: str  # FK -> wallets.address
    px: Decimal  # executed price
    sz: Decimal  # executed size
    timestamp: int  # milliseconds epoch
    fill_id: str = field(default_factory=lambda: str(uuid4()))  # PK
