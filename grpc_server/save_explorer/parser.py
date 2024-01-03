from typing import Any
from zipfile import ZipFile
from struct import Struct
import zlib
import io
import string
from warnings import warn
import json

STRICT_CHECK = True


class Deserializer:
    u16 = Struct('<H')
    u32 = Struct('<I')
    fp64 = Struct('<d')

    def __init__(self, stream):
        self.stream = stream

    def read(self, n):
        return self.stream.read(n)

    def read_fmt(self, fmt):
        return fmt.unpack(self.read(fmt.size))[0]

    def read_u8(self):
        return self.read(1)[0]

    def read_bool(self):
        return bool(self.read_u8())

    def read_u16(self):
        return self.read_fmt(self.u16)

    def read_u32(self):
        return self.read_fmt(self.u32)

    def read_fp64(self):
        return self.read_fmt(self.fp64)

    def read_str(self):
        length = self.read_u8()
        result: bytes = self.read(length)
        try:
            return result.decode('utf-8')
        except UnicodeDecodeError:
            if STRICT_CHECK:
                raise
            else:
                warn("cannot decode with 'utf-8' codec")
                return result

    def assert_byte_seq(self, desired: bytes, name=''):
        if not STRICT_CHECK:
            return
        magic = self.read(len(desired))
        if name:
            name = '[' + name + '] '
        if magic != desired:
            raise ValueError(rf"{name}{magic} != {desired}")

    @classmethod
    def load_save_zip(cls, zip_name, head_size=16384):
        zf = ZipFile(zip_name, 'r')
        for dat_filename in zf.namelist():
            if dat_filename.endswith('/level.dat0'):
                is_zlib = True
                break
            if dat_filename.endswith('/level.dat'):
                is_zlib = False
                break
        else:
            raise IOError("level.dat not found in save file")
        with zf.open(dat_filename) as f:
            raw_data = f.read(head_size)
            if is_zlib:
                raw_data = zlib.decompressobj().decompress(raw_data)
            return cls(io.BytesIO(raw_data))

    # def read_optim(self, dtype):
    #     byte = self.read_u8()
    #     if byte != 0xFF:
    #         return byte
    #     return self.read_fmt(dtype)
    #
    # def read_optim_u16(self):
    #     return self.read_optim(self.u16)
    #
    # def read_optim_u32(self):
    #     return self.read_optim(self.u32)
    #
    # def read_optim_str(self):
    #     length = self.read_optim_u32()
    #     return self.read(length)
    #
    # def read_optim_tuple(self, dtype, num):
    #     return tuple(self.read_optim(dtype) for i in range(num))


def version_to_str(ver):
    return '.'.join(str(x) for x in ver)


def ticks_to_formatted_time(ticks):
    second = ticks // 60
    h = second // 3600
    m = second % 3600 // 60
    s = second % 60
    return ':'.join(str(x) for x in [h, m, s])


def load_metadata(filename):
    ds = Deserializer.load_save_zip(filename)
    metadata = {'version': version_to_str(ds.read_u16() for _ in range(4)), 'unknowns': []}
    ds.assert_byte_seq(b'\x00', "after version")
    sce = [ds.read_str(), ds.read_str()]
    if sce[0]:
        metadata['scenario'] = '/'.join(sce)
    else:
        metadata['scenario'] = sce[1]
    metadata['unknowns'].append(
        [ds.read_str(), ds.read(8), version_to_str(ds.read_u8() for _ in range(3)), ds.read(3)]
    )
    mods_len = ds.read_u8()
    metadata['mods'] = [
        [ds.read_str(), version_to_str(ds.read_u8() for _ in range(3)), ds.read(4)]
        for _ in range(mods_len)
    ]
    metadata['unknowns'].append(ds.read(6))
    startup_len = ds.read_u32()
    metadata['startup_settings'] = startup = []
    for _ in range(startup_len):
        ds.assert_byte_seq(b'\x00', "before startup name")
        value = [ds.read_str()]
        startup.append(value)
        ds.assert_byte_seq(b'\x05\x00\x01\x00\x00\x00\x00\x05value', "after startup name")
        dtype = {1: 'bool', 2: 'double', 3: 'str'}[ds.read_u8()]
        value.append(dtype)
        if dtype == 'bool':
            ds.assert_byte_seq(b'\x00', "startup bool")
            value.append(ds.read_bool())
        elif dtype == 'double':
            ds.assert_byte_seq(b'\x00', "startup double")
            value.append(ds.read_fp64())
        elif dtype == 'str':
            ds.assert_byte_seq(b'\x00\x00', "startup str")
            value.append(ds.read_str())

    metadata["ticks"] = ticks = [ds.read_u32() for _ in range(3)]
    metadata["play_time"] = ticks_to_formatted_time(ticks[2])
    metadata["total_time"] = ticks_to_formatted_time(ticks[0])
    return metadata


class BytesEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, bytes):
            return str(o)
        return super().default(o)


def json_stringify(metadata):
    return json.dumps(metadata, cls=BytesEncoder)


if __name__ == '__main__':
    import sys

    for save in sys.argv[1:]:
        metadata = load_metadata(save)
        print('%s:' % save)
        print(metadata)
        print(f"play time: {metadata['time']}")
        print()
