# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: grpc_server/server.proto
# Protobuf Python Version: 4.25.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x18grpc_server/server.proto\x12\x0f\x66\x61\x63torio_server\x1a\x1bgoogle/protobuf/empty.proto\"\x17\n\x04Ping\x12\x0f\n\x07verbose\x18\x01 \x01(\x08\"\x8c\x01\n\x0bManagerStat\x12\x0f\n\x07welcome\x18\x01 \x01(\t\x12\x0f\n\x07running\x18\x02 \x01(\x08\x12\x14\n\x0cgame_version\x18\x03 \x01(\t\x12\x34\n\x0c\x63urrent_save\x18\x04 \x01(\x0b\x32\x19.factorio_server.SaveNameH\x00\x88\x01\x01\x42\x0f\n\r_current_save\"<\n\x0cSaveNameList\x12,\n\tsave_name\x18\x01 \x03(\x0b\x32\x19.factorio_server.SaveName\"\x18\n\x08SaveName\x12\x0c\n\x04name\x18\x01 \x01(\t\"\x1d\n\x08SaveStat\x12\x11\n\tstat_json\x18\x01 \x01(\t\"d\n\rServerOptions\x12\x31\n\tsave_name\x18\x01 \x01(\x0b\x32\x19.factorio_server.SaveNameH\x00\x88\x01\x01\x12\x12\n\nextra_args\x18\x02 \x03(\tB\x0c\n\n_save_name\"\'\n\x06Status\x12\x0c\n\x04\x63ode\x18\x01 \x01(\x05\x12\x0f\n\x07message\x18\x02 \x01(\t\"\x16\n\x07\x43ommand\x12\x0b\n\x03\x63md\x18\x01 \x01(\t\"9\n\rUpdateInquiry\x12\x18\n\x0b\x66rom_offset\x18\x01 \x01(\x05H\x00\x88\x01\x01\x42\x0e\n\x0c_from_offset\"5\n\x0bGameUpdates\x12\x15\n\rlatest_offset\x18\x01 \x01(\x05\x12\x0f\n\x07updates\x18\x02 \x03(\x0c\"/\n\rOutputStreams\x12\x0e\n\x06stdout\x18\x01 \x01(\x0c\x12\x0e\n\x06stderr\x18\x02 \x01(\x0c\"]\n\x0eTelegramClient\x12\x16\n\x0esession_string\x18\x01 \x01(\t\x12\x0f\n\x07\x63hat_id\x18\x02 \x01(\x03\x12\x15\n\x08reply_id\x18\x03 \x01(\x03H\x00\x88\x01\x01\x42\x0b\n\t_reply_id\"s\n\x12UploadTelegramInfo\x12,\n\tsave_name\x18\x01 \x01(\x0b\x32\x19.factorio_server.SaveName\x12/\n\x06\x63lient\x18\x02 \x01(\x0b\x32\x1f.factorio_server.TelegramClient2\xf3\x05\n\rServerManager\x12G\n\x10GetManagerStatus\x12\x15.factorio_server.Ping\x1a\x1c.factorio_server.ManagerStat\x12G\n\x0eGetAllSaveName\x12\x16.google.protobuf.Empty\x1a\x1d.factorio_server.SaveNameList\x12\x45\n\rGetStatByName\x12\x19.factorio_server.SaveName\x1a\x19.factorio_server.SaveStat\x12=\n\nStopServer\x12\x16.google.protobuf.Empty\x1a\x17.factorio_server.Status\x12L\n\x11StartServerByName\x12\x1e.factorio_server.ServerOptions\x1a\x17.factorio_server.Status\x12H\n\rRestartServer\x12\x1e.factorio_server.ServerOptions\x1a\x17.factorio_server.Status\x12\x42\n\rInGameCommand\x12\x18.factorio_server.Command\x1a\x17.factorio_server.Status\x12N\n\x0eWaitForUpdates\x12\x1e.factorio_server.UpdateInquiry\x1a\x1c.factorio_server.GameUpdates\x12J\n\x10GetOutputStreams\x12\x16.google.protobuf.Empty\x1a\x1e.factorio_server.OutputStreams\x12R\n\x10UploadToTelegram\x12#.factorio_server.UploadTelegramInfo\x1a\x17.factorio_server.Status0\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'grpc_server.server_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_PING']._serialized_start=74
  _globals['_PING']._serialized_end=97
  _globals['_MANAGERSTAT']._serialized_start=100
  _globals['_MANAGERSTAT']._serialized_end=240
  _globals['_SAVENAMELIST']._serialized_start=242
  _globals['_SAVENAMELIST']._serialized_end=302
  _globals['_SAVENAME']._serialized_start=304
  _globals['_SAVENAME']._serialized_end=328
  _globals['_SAVESTAT']._serialized_start=330
  _globals['_SAVESTAT']._serialized_end=359
  _globals['_SERVEROPTIONS']._serialized_start=361
  _globals['_SERVEROPTIONS']._serialized_end=461
  _globals['_STATUS']._serialized_start=463
  _globals['_STATUS']._serialized_end=502
  _globals['_COMMAND']._serialized_start=504
  _globals['_COMMAND']._serialized_end=526
  _globals['_UPDATEINQUIRY']._serialized_start=528
  _globals['_UPDATEINQUIRY']._serialized_end=585
  _globals['_GAMEUPDATES']._serialized_start=587
  _globals['_GAMEUPDATES']._serialized_end=640
  _globals['_OUTPUTSTREAMS']._serialized_start=642
  _globals['_OUTPUTSTREAMS']._serialized_end=689
  _globals['_TELEGRAMCLIENT']._serialized_start=691
  _globals['_TELEGRAMCLIENT']._serialized_end=784
  _globals['_UPLOADTELEGRAMINFO']._serialized_start=786
  _globals['_UPLOADTELEGRAMINFO']._serialized_end=901
  _globals['_SERVERMANAGER']._serialized_start=904
  _globals['_SERVERMANAGER']._serialized_end=1659
# @@protoc_insertion_point(module_scope)
