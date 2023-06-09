# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: logproto.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='logproto.proto',
  package='logproto',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x0elogproto.proto\x12\x08logproto\x1a\x1fgoogle/protobuf/timestamp.proto\"0\n\x0bPushRequest\x12!\n\x07streams\x18\x01 \x03(\x0b\x32\x10.logproto.Stream\":\n\x06Stream\x12\x0e\n\x06labels\x18\x01 \x01(\t\x12 \n\x07\x65ntries\x18\x02 \x03(\x0b\x32\x0f.logproto.Entry\"D\n\x05\x45ntry\x12-\n\ttimestamp\x18\x01 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x0c\n\x04line\x18\x02 \x01(\tb\x06proto3')
  ,
  dependencies=[google_dot_protobuf_dot_timestamp__pb2.DESCRIPTOR,])




_PUSHREQUEST = _descriptor.Descriptor(
  name='PushRequest',
  full_name='logproto.PushRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='streams', full_name='logproto.PushRequest.streams', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=61,
  serialized_end=109,
)


_STREAM = _descriptor.Descriptor(
  name='Stream',
  full_name='logproto.Stream',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='labels', full_name='logproto.Stream.labels', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='entries', full_name='logproto.Stream.entries', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=111,
  serialized_end=169,
)


_ENTRY = _descriptor.Descriptor(
  name='Entry',
  full_name='logproto.Entry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='logproto.Entry.timestamp', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='line', full_name='logproto.Entry.line', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=171,
  serialized_end=239,
)

_PUSHREQUEST.fields_by_name['streams'].message_type = _STREAM
_STREAM.fields_by_name['entries'].message_type = _ENTRY
_ENTRY.fields_by_name['timestamp'].message_type = google_dot_protobuf_dot_timestamp__pb2._TIMESTAMP
DESCRIPTOR.message_types_by_name['PushRequest'] = _PUSHREQUEST
DESCRIPTOR.message_types_by_name['Stream'] = _STREAM
DESCRIPTOR.message_types_by_name['Entry'] = _ENTRY
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

PushRequest = _reflection.GeneratedProtocolMessageType('PushRequest', (_message.Message,), dict(
  DESCRIPTOR = _PUSHREQUEST,
  __module__ = 'logproto_pb2'
  # @@protoc_insertion_point(class_scope:logproto.PushRequest)
  ))
_sym_db.RegisterMessage(PushRequest)

Stream = _reflection.GeneratedProtocolMessageType('Stream', (_message.Message,), dict(
  DESCRIPTOR = _STREAM,
  __module__ = 'logproto_pb2'
  # @@protoc_insertion_point(class_scope:logproto.Stream)
  ))
_sym_db.RegisterMessage(Stream)

Entry = _reflection.GeneratedProtocolMessageType('Entry', (_message.Message,), dict(
  DESCRIPTOR = _ENTRY,
  __module__ = 'logproto_pb2'
  # @@protoc_insertion_point(class_scope:logproto.Entry)
  ))
_sym_db.RegisterMessage(Entry)


# @@protoc_insertion_point(module_scope)
