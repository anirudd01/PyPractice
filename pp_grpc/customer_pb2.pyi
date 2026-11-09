import datetime

from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Tier(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TIER_UNSPECIFIED: _ClassVar[Tier]
    TIER_FREE: _ClassVar[Tier]
    TIER_PREMIUM: _ClassVar[Tier]
TIER_UNSPECIFIED: Tier
TIER_FREE: Tier
TIER_PREMIUM: Tier

class Customer(_message.Message):
    __slots__ = ("id", "name", "email", "tier", "tags", "created_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    TIER_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    email: str
    tier: Tier
    tags: _containers.RepeatedScalarFieldContainer[str]
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., email: _Optional[str] = ..., tier: _Optional[_Union[Tier, str]] = ..., tags: _Optional[_Iterable[str]] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CreateCustomerRequest(_message.Message):
    __slots__ = ("name", "email", "tier", "tags")
    NAME_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    TIER_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    name: str
    email: str
    tier: Tier
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[str] = ..., email: _Optional[str] = ..., tier: _Optional[_Union[Tier, str]] = ..., tags: _Optional[_Iterable[str]] = ...) -> None: ...

class GetCustomerRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class UpdateCustomerRequest(_message.Message):
    __slots__ = ("id", "name", "email", "tier")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    TIER_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    email: str
    tier: Tier
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., email: _Optional[str] = ..., tier: _Optional[_Union[Tier, str]] = ...) -> None: ...

class ListCustomersRequest(_message.Message):
    __slots__ = ("page_size", "tier")
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    TIER_FIELD_NUMBER: _ClassVar[int]
    page_size: int
    tier: Tier
    def __init__(self, page_size: _Optional[int] = ..., tier: _Optional[_Union[Tier, str]] = ...) -> None: ...

class BulkCreateResponse(_message.Message):
    __slots__ = ("created_count", "ids")
    CREATED_COUNT_FIELD_NUMBER: _ClassVar[int]
    IDS_FIELD_NUMBER: _ClassVar[int]
    created_count: int
    ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, created_count: _Optional[int] = ..., ids: _Optional[_Iterable[str]] = ...) -> None: ...
