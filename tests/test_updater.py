import asyncio
import os
import tarfile
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from facmgr.protobuf.error_code import NOT_AVAILABLE, SATISFIED, SUCCESS
from facmgr.server.updater import FactorioHeadlessUpdater


class FakeDaemon:
    def __init__(self, version="2.0.76", running=False, start_failures=0):
        self.version = version
        self.is_running = running
        self.executable = "/old/factorio"
        self.stop_called = False
        self.start_args = None
        self.args = ["--start-server", "save.zip"] if running else None
        self.start_failures = start_failures

    async def get_game_version(self):
        return f"Version: {self.version} (build 1, linux64, headless)\n"

    def get_current_args(self):
        return self.args

    async def stop(self):
        self.stop_called = True
        self.is_running = False
        return {"code": SUCCESS, "message": None}

    async def start(self, args):
        if self.start_failures:
            self.start_failures -= 1
            return {"code": 122, "message": "boom"}
        self.start_args = args
        self.is_running = True
        return {"code": SUCCESS, "message": None}


def write_fake_factorio(path: Path, version: str):
    path.parent.mkdir(parents=True)
    path.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        f"  printf 'Version: {version} (build 1, linux64, headless)\\n'\n"
        "  printf 'Binary version: 64\\n'\n"
        "  printf 'Map input version: 0\\n'\n"
        "  printf 'Map output version: 0\\n'\n"
        "fi\n",
    )
    path.chmod(0o755)


def create_factorio_archive(path: Path, version: str):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "factorio"
        write_fake_factorio(root / "bin" / "x64" / "factorio", version)
        with tarfile.open(path, "w:xz") as tar:
            tar.add(root, arcname="factorio")


def make_fake_download(archive: Path):
    async def fake_download(_, destination):
        os.replace(archive, destination)
        for event in ():
            yield event

    return fake_download


class TestFactorioHeadlessUpdater(TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()

    def tearDown(self):
        self.loop.close()

    def test_disabled(self):
        async def run():
            events = [event async for event in FactorioHeadlessUpdater(None).update(FakeDaemon())]
            self.assertEqual(events[-1].code, NOT_AVAILABLE)

        self.loop.run_until_complete(run())

    def test_already_latest(self):
        async def run():
            with tempfile.TemporaryDirectory() as tmp:
                updater = FactorioHeadlessUpdater(tmp)
                events = [event async for event in updater.update(FakeDaemon(version="2.0.77"), version="2.0.77")]
                self.assertEqual(events[-1].code, SATISFIED)

        self.loop.run_until_complete(run())

    def test_update_switches_release_and_restarts(self):
        async def run():
            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                archive = tmp_path / "factorio_headless_x64_2.0.77.tar.xz"
                create_factorio_archive(archive, "2.0.77")
                daemon = FakeDaemon(running=True)
                updater = FactorioHeadlessUpdater(tmp_path)

                with patch.object(updater, "_download", make_fake_download(archive)):
                    events = [event async for event in updater.update(daemon, version="2.0.77")]

                self.assertEqual(events[-1].code, SUCCESS)
                self.assertEqual(events[-1].stage, "complete")
                self.assertTrue((tmp_path / "current" / "bin" / "x64" / "factorio").is_file())
                self.assertEqual(daemon.executable, str(tmp_path / "current" / "bin" / "x64" / "factorio"))
                self.assertTrue(daemon.stop_called)
                self.assertEqual(daemon.start_args, ["--start-server", "save.zip"])

        self.loop.run_until_complete(run())

    def test_update_rolls_back_when_new_release_does_not_start(self):
        async def run():
            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                old_release = tmp_path / "releases" / "factorio-2.0.76"
                write_fake_factorio(old_release / "bin" / "x64" / "factorio", "2.0.76")
                updater = FactorioHeadlessUpdater(tmp_path)
                updater._switch_current(old_release)

                archive = tmp_path / "factorio_headless_x64_2.0.77.tar.xz"
                create_factorio_archive(archive, "2.0.77")
                daemon = FakeDaemon(running=True, start_failures=1)
                daemon.executable = str(tmp_path / "current" / "bin" / "x64" / "factorio")

                with patch.object(updater, "_download", make_fake_download(archive)):
                    events = [event async for event in updater.update(daemon, version="2.0.77")]

                self.assertNotEqual(events[-1].code, SUCCESS)
                self.assertEqual(os.readlink(tmp_path / "current"), str(old_release))
                self.assertEqual(daemon.executable, str(tmp_path / "current" / "bin" / "x64" / "factorio"))

        self.loop.run_until_complete(run())
