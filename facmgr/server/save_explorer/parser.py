import zipfile
from struct import Struct
import zlib
import io
from warnings import warn
import json

STRICT_CHECK = True


class Deserializer:
    u16 = Struct('<H')
    u32 = Struct('<I')
    u64 = Struct('<Q')
    fp32 = Struct('<f')
    fp64 = Struct('<d')

    @staticmethod
    def optim_read(func):
        def wrapper(self, optim=False):
            if optim:
                byte = self.read_u8()
                if byte != 0xFF:
                    return byte
            return func(self)

        return wrapper

    def __init__(self, stream):
        self.stream = stream

    def read(self, n):
        return self.stream.read(n)

    def read_fmt(self, fmt):
        return fmt.unpack(self.read(fmt.size))[0]

    def read_u8(self):
        return self.read(1)[0]

    def read_bool(self):
        byte = self.read_u8()
        if byte in [0, 1]:
            return bool(byte)
        raise ValueError(f"invalid bool value: {byte}")

    @optim_read
    def read_u16(self):
        return self.read_fmt(self.u16)

    @optim_read
    def read_u32(self):
        return self.read_fmt(self.u32)

    @optim_read
    def read_u64(self):
        return self.read_fmt(self.u64)

    def read_fp32(self):
        return self.read_fmt(self.fp32)

    def read_fp64(self):
        return self.read_fmt(self.fp64)

    def read_str(self):
        length = self.read_u32(optim=True)
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
        zf = zipfile.ZipFile(zip_name, 'r')
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
    version_str = '.'.join(str(x) for x in ver[:3])
    build_str = '.'.join(str(x) for x in ver[3:])
    if build_str:
        version_str += '-' + build_str
    return version_str


def ticks_to_formatted_time(ticks) -> str:
    second = ticks // 60
    h = second // 3600
    m = second % 3600 // 60
    s = second % 60
    return ':'.join(str(x) for x in [h, m, s])


def load_metadata(filename) -> dict:
    try:
        ds = Deserializer.load_save_zip(filename)
    except (zipfile.BadZipFile, zlib.error):
        return {}
    map_version = [ds.read_u16() for _ in range(4)]
    is_v2map = map_version[0] >= 2
    metadata = {'version': version_to_str(map_version), 'unknowns': []}
    ds.assert_byte_seq(b'\x00', "after version")
    sce = [ds.read_str(), ds.read_str()]
    if sce[0]:
        metadata['scenario'] = '/'.join(sce)
    else:
        metadata['scenario'] = sce[1]
    metadata['base_mod'] = ds.read_str()
    metadata['flags'] = {
        'difficulty':                    ds.read_u8(),
        'finished':                      ds.read_bool(),
        'player_won':                    ds.read_bool(),
        'next_level':                    ds.read_str(),
        'can_continue':                  ds.read_bool(),
        'finished_but_continuing':       ds.read_bool(),
        'saving_replay':                 ds.read_bool(),
        'allow_non_admin_debug_options': ds.read_bool(),
        'loaded_from':                   version_to_str([ds.read_u8() for _ in range(3)]),
        'build_number':                  ds.read_u32() if is_v2map else ds.read_u16(),
        'allowed_commands':              ds.read_u8()
    }
    if is_v2map:
        ds.assert_byte_seq(b'\x00\x00\xa0\x00', "after flags, before mods")
    mods_len = ds.read_u8()
    metadata['mods'] = [
        {'name': ds.read_str(), 'version': version_to_str([ds.read_u8() for _ in range(3)]), 'crc32': ds.read(4)}
        for _ in range(mods_len)
    ]
    metadata['unknowns'].append(ds.read(6))
    startup_len = ds.read_u32()
    metadata['mods_startup_settings'] = startup = []
    for _ in range(startup_len):
        ds.assert_byte_seq(b'\x00', "before startup name")
        value = [ds.read_str()]
        startup.append(value)
        ds.assert_byte_seq(b'\x05\x00\x01\x00\x00\x00\x00\x05value', "after startup name")
        dtype = {1: 'bool', 2: 'double', 3: 'str', 6: 'uint64'}[ds.read_u8()]
        value.append(dtype)
        if dtype == 'bool':
            ds.assert_byte_seq(b'\x00', "startup bool")
            value.append(ds.read_bool())
        elif dtype == 'double':
            ds.assert_byte_seq(b'\x00', "startup double")
            value.append(ds.read_fp64())
        elif dtype == 'uint64':
            ds.assert_byte_seq(b'\x00', "startup uint64")
            value.append(ds.read_u64())
        elif dtype == 'str':
            ds.assert_byte_seq(b'\x00\x00', "startup str")
            value.append(ds.read_str())
    if is_v2map:
        metadata['game_finish'] = []
        for i in range(2):
            finish_msg = []
            ds.assert_byte_seq(b'\x01', f"before game finish type {i}")
            finish_msg.append(ds.read_str())
            ds.assert_byte_seq(b'\x00', f"after game finish type {i}")
            if ds.read_bool():
                finish_msg.append(ds.read_str())
                ds.assert_byte_seq(b'\x00', f"after game finish type {i} message 1")
            bullet_point_len = ds.read_u8()
            bullet_point = []
            for _ in range(bullet_point_len):
                ds.assert_byte_seq(b'\x01', f"before finish type {i} bullet point")
                bullet_point.append(ds.read_str())
                ds.assert_byte_seq(b'\x00', f"after finish type {i} bullet point")
            finish_msg.append(bullet_point)
            if ds.read_bool():
                finish_msg.append(ds.read_str())
                ds.assert_byte_seq(b'\x00', f"after finish type {i} victory final message")
            finish_msg.append(ds.read_str())
            metadata['game_finish'].append(finish_msg)
        metadata['game_finish'].append(ds.read_bool())

    metadata["ticks"] = ticks = tuple(ds.read_u64() if is_v2map else ds.read_u32() for _ in range(3))
    metadata["play_time"] = ticks_to_formatted_time(ticks[2])
    metadata["total_time"] = ticks_to_formatted_time(ticks[0])
    if not is_v2map:
        metadata['unknowns'].append([ds.read_fp32(), ds.read_fp32()])
    map_setting_len = ds.read_u8()
    metadata['map_settings'] = map_settings = []
    for _ in range(map_setting_len):
        map_settings.append([ds.read_str(), [ds.read_fp32() for _ in range(3)]])
    ds.assert_byte_seq(b'\x00\x01', "before map seed")
    metadata['map_seed'] = ds.read_u32()
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
        info = load_metadata(save)
        print('%s:' % save)
        print(info)
        print(f"play time: {info['time']}")
        print()
