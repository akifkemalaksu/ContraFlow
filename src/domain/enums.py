from enum import Enum


class AccountType(str, Enum):
    MASTER = "master"
    SUB_ACCOUNT = "sub_account"
    VAULT = "vault"


class Direction(str, Enum):
    FORWARD = "forward"
    REVERSE = "reverse"


class Operator(str, Enum):
    GT = "GT"
    LT = "LT"


class OrderStatus(str, Enum):
    OPEN = "open"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"
