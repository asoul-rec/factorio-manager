from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SaveNameList(_message.Message):
    __slots__ = ("save_name",)
    SAVE_NAME_FIELD_NUMBER: _ClassVar[int]
    save_name: _containers.RepeatedCompositeFieldContainer[SaveName]
    def __init__(self, save_name: _Optional[_Iterable[_Union[SaveName, _Mapping]]] = ...) -> None: ...

class SaveName(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class SaveStat(_message.Message):
    __slots__ = ("stat_json",)
    STAT_JSON_FIELD_NUMBER: _ClassVar[int]
    stat_json: str
    def __init__(self, stat_json: _Optional[str] = ...) -> None: ...

class ServerOptions(_message.Message):
    __slots__ = ("save_name", "extra_args")
    SAVE_NAME_FIELD_NUMBER: _ClassVar[int]
    EXTRA_ARGS_FIELD_NUMBER: _ClassVar[int]
    save_name: SaveName
    extra_args: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, save_name: _Optional[_Union[SaveName, _Mapping]] = ..., extra_args: _Optional[_Iterable[str]] = ...) -> None: ...

class Status(_message.Message):
    __slots__ = ("code", "message")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    code: int
    message: str
    def __init__(self, code: _Optional[int] = ..., message: _Optional[str] = ...) -> None: ...
