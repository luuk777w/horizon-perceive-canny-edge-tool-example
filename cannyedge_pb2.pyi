from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DetectEdgesRequest(_message.Message):
    __slots__ = ("image_chunk", "parameters")
    IMAGE_CHUNK_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    image_chunk: ImageChunk
    parameters: Parameters
    def __init__(self, image_chunk: _Optional[_Union[ImageChunk, _Mapping]] = ..., parameters: _Optional[_Union[Parameters, _Mapping]] = ...) -> None: ...

class ImageChunk(_message.Message):
    __slots__ = ("content",)
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    content: bytes
    def __init__(self, content: _Optional[bytes] = ...) -> None: ...

class Parameters(_message.Message):
    __slots__ = ("minThreshold", "maxThreshold")
    MINTHRESHOLD_FIELD_NUMBER: _ClassVar[int]
    MAXTHRESHOLD_FIELD_NUMBER: _ClassVar[int]
    minThreshold: int
    maxThreshold: int
    def __init__(self, minThreshold: _Optional[int] = ..., maxThreshold: _Optional[int] = ...) -> None: ...

class DetectEdgesResponse(_message.Message):
    __slots__ = ("image_chunk",)
    IMAGE_CHUNK_FIELD_NUMBER: _ClassVar[int]
    image_chunk: bytes
    def __init__(self, image_chunk: _Optional[bytes] = ...) -> None: ...
