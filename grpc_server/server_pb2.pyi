from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ManagerStat(_message.Message):
    __slots__ = ("welcome", "running")
    WELCOME_FIELD_NUMBER: _ClassVar[int]
    RUNNING_FIELD_NUMBER: _ClassVar[int]
    welcome: str
    running: bool
    def __init__(self, welcome: _Optional[str] = ..., running: bool = ...) -> None: ...

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

class Command(_message.Message):
    __slots__ = ("cmd",)
    CMD_FIELD_NUMBER: _ClassVar[int]
    cmd: str
    def __init__(self, cmd: _Optional[str] = ...) -> None: ...

class UpdateInquiry(_message.Message):
    __slots__ = ("from_offset",)
    FROM_OFFSET_FIELD_NUMBER: _ClassVar[int]
    from_offset: int
    def __init__(self, from_offset: _Optional[int] = ...) -> None: ...

class GameUpdates(_message.Message):
    __slots__ = ("latest_offset", "updates")
    LATEST_OFFSET_FIELD_NUMBER: _ClassVar[int]
    UPDATES_FIELD_NUMBER: _ClassVar[int]
    latest_offset: int
    updates: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, latest_offset: _Optional[int] = ..., updates: _Optional[_Iterable[bytes]] = ...) -> None: ...
