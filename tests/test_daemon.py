import asyncio
import logging
import os
from unittest import TestCase

from facmgr.server.daemon import FactorioServerDaemon
from facmgr.protobuf.error_code import *

logging.basicConfig(format='%(asctime)s [%(levelname).1s] [%(name)s] %(message)s', level=logging.INFO)


class TestFactorioServerDaemon(TestCase):
    loop: asyncio.AbstractEventLoop

    @classmethod
    def setUpClass(cls):
        cls.executable = os.environ['executable']
        cls.savefile = os.environ['savefile']
        cls.loop = asyncio.new_event_loop()
        super().setUpClass()

    @staticmethod
    def available_stop_strategies():
        if os.name == 'nt':
            return ['quit']
        return ['quit', 'interrupt']

    def test_error_exe(self):
        async def error_exe():
            fac = FactorioServerDaemon(self.executable + "f4cT0r10")
            status = await fac.start(['--start-server', self.savefile])
            if os.name == 'nt':
                self.assertEqual(status["code"], EXIT_ERROR)
                self.assertRegex(status["message"],
                                 r"is not recognized as an internal or external command,\\r\\n"
                                 r"operable program or batch file.\\r\\n")
            else:
                self.assertEqual(status["code"], BAD_ARG)
                self.assertRegex(status["message"], "^Cannot start server. FileNotFoundError: ")

        self.loop.run_until_complete(error_exe())

    def test_finish_exe(self):
        factorio_help = "Path where server ID will be stored or read"

        async def finish_normally():
            fac = FactorioServerDaemon(self.executable)
            status = await fac.start(['--help'])
            self.assertEqual(status["code"], EXIT_UNEXPECT)
            self.assertIn("The server exited unexpectedly without error", status["message"])
            self.assertRegex(status["message"],
                             f"^The server exited unexpectedly without error, stdout='.*{factorio_help}.*', stderr=''$")

        async def finish_with_error():
            fac = FactorioServerDaemon(self.executable)
            status = await fac.start(['--helphelp'])
            self.assertEqual(status["code"], EXIT_ERROR)
            self.assertRegex(status["message"],
                             f"^The server finished with exit_code=1, stdout='.*{factorio_help}.*', stderr=''$")

        self.loop.run_until_complete(finish_normally())
        self.loop.run_until_complete(finish_with_error())

    def test_start_stop(self):
        async def start_stop(stop_strategy):
            # normal and repeated start
            fac = FactorioServerDaemon(self.executable, stop_strategy=stop_strategy)
            status = await fac.start(['--start-server', self.savefile])
            self.assertDictEqual(status, {"code": SUCCESS, "message": None})
            status = await fac.start(['--start-server', self.savefile])
            self.assertDictEqual(status, {"code": SATISFIED, "message": "The server is already running."})

            # fail to start if factorio is running externally already, but do not keep error after reporting it
            fac2 = FactorioServerDaemon(self.executable)
            status = await fac2.start(['--start-server', self.savefile])
            self.assertEqual(status["code"], EXIT_ERROR)
            self.assertIn("exit_code=1", status["message"])
            self.assertIn("Is another instance already running?", status["message"])
            status = await fac2.stop()
            self.assertDictEqual(status, {"code": SATISFIED, "message": "The server is already stopped."})

            # normal and repeated stop
            status = await fac.stop()
            self.assertDictEqual(status, {"code": SUCCESS, "message": None})
            status = await fac.stop()
            self.assertDictEqual(status, {"code": SATISFIED, "message": "The server is already stopped."})

        for ss in self.available_stop_strategies():
            self.loop.run_until_complete(start_stop(ss))

    def test_unexpected_exit(self):
        async def unexpected_exit(stop_strategy):
            fac = FactorioServerDaemon(self.executable, stop_strategy=stop_strategy)
            # unexpected exit is reported when trying to stop later, but not reported if trying to start
            # stop part
            status = await fac.start(['--start-server', self.savefile])
            self.assertDictEqual(status, {"code": SUCCESS, "message": None})
            self.assertEqual(fac.in_game_command('/quit')["code"], SUCCESS)
            fac.process.stdin.write_eof()
            await fac._process_info.daemon
            status = await fac.stop()
            self.assertEqual(status["code"], EXIT_UNEXPECT)
            self.assertIn("The server exited unexpectedly without error", status["message"])
            # start part
            status = await fac.start(['--start-server', self.savefile])
            self.assertDictEqual(status, {"code": SUCCESS, "message": None})
            self.assertEqual(fac.in_game_command('/quit')["code"], SUCCESS)
            fac.process.stdin.write_eof()
            await fac._process_info.daemon
            status = await fac.start(['--start-server', self.savefile])
            self.assertDictEqual(status, {"code": SUCCESS, "message": None})
            status = await fac.stop()
            self.assertDictEqual(status, {"code": SUCCESS, "message": None})

            # process do terminate but not exit normally when stop
            status = await fac.start(['--start-server', self.savefile])
            self.assertDictEqual(status, {"code": SUCCESS, "message": None})
            status = asyncio.create_task(fac.stop())
            await fac._kill()  # mimic bad thing happens during stopping
            self.assertDictEqual(await status, {"code": EXIT_UNEXPECT, "message": "Server did not stop normally."})

        for ss in self.available_stop_strategies():
            self.loop.run_until_complete(unexpected_exit(ss))

    def test_timeout(self):
        async def timeout():
            fac = FactorioServerDaemon(self.executable, timeout=0.1)
            status = await fac.start(['--start-server', self.savefile])
            self.assertDictEqual(status, {"code": EXIT_TIMEOUT, "message": "Starting is aborted after 0.1s."})
            fac.global_timeout = 30
            status = await fac.start(['--start-server', self.savefile])
            self.assertDictEqual(status, {"code": SUCCESS, "message": None})
            fac.global_timeout = 0.1
            status = await fac.stop()
            self.assertDictEqual(status, {"code": EXIT_TIMEOUT, "message": "Force stopping after 0.1s."})
            # Should not affect the normal operation
            fac.global_timeout = 30
            status = await fac.start(['--start-server', self.savefile])
            self.assertDictEqual(status, {"code": SUCCESS, "message": None})
            status = await fac.stop()
            self.assertDictEqual(status, {"code": SUCCESS, "message": None})

        self.loop.run_until_complete(timeout())

    def test_state_change(self):
        async def state_change():
            fac = FactorioServerDaemon(self.executable)
            status1 = asyncio.create_task(fac.start(['--start-server', self.savefile]))
            status2 = asyncio.create_task(fac.start(['--start-server', self.savefile]))
            status3 = asyncio.create_task(fac.stop())
            self.assertDictEqual(await status1, {"code": SUCCESS, "message": None})
            self.assertDictEqual(await status2, {"code": STARTING, "message": "The server is starting."})
            self.assertDictEqual(await status3, {"code": STARTING, "message": "The server is starting."})
            status1 = asyncio.create_task(fac.stop())
            status2 = asyncio.create_task(fac.stop())
            status3 = asyncio.create_task(fac.start(['--start-server', self.savefile]))
            self.assertDictEqual(await status1, {"code": SUCCESS, "message": None})
            self.assertDictEqual(await status2, {"code": STOPPING, "message": "The server is stopping."})
            self.assertDictEqual(await status3, {"code": STOPPING, "message": "The server is stopping."})

        self.loop.run_until_complete(state_change())

    def test_restart(self):
        async def restart():
            # restart at the beginning with no arg
            fac = FactorioServerDaemon(self.executable)
            status = await fac.restart()
            self.assertDictEqual(
                status, {"code": BAD_ARG, "message": "Must provide starting arguments at the beginning."})

            # normal test: can restart successfully no matter the server is running or not
            status = await fac.restart(['--start-server', self.savefile])
            self.assertDictEqual(status, {"code": SUCCESS, "message": None})
            status = await fac.restart()
            self.assertDictEqual(status, {"code": SUCCESS, "message": None})
            status = await fac.stop()
            self.assertDictEqual(status, {"code": SUCCESS, "message": None})
            status = await fac.restart()
            self.assertDictEqual(status, {"code": SUCCESS, "message": None})

            # inherit the error during starting
            fac2 = FactorioServerDaemon(self.executable)
            status = await fac2.restart(['--start-server', self.savefile])
            self.assertEqual(status["code"], EXIT_ERROR)
            self.assertIn("exit_code=1", status["message"])
            self.assertIn("Is another instance already running?", status["message"])

            # abort restarting if an error occurs during stopping
            status1 = asyncio.create_task(fac.stop())
            status2 = asyncio.create_task(fac.restart())
            self.assertDictEqual(await status1, {"code": SUCCESS, "message": None})
            self.assertDictEqual(await status2, {
                "code": STOPPING, "message": "Encountered an error while stopping: The server is stopping."
            })

        self.loop.run_until_complete(restart())

    def test_get_message(self):
        async def _helper(put_messages, delay=0.):
            if delay:
                await asyncio.sleep(delay)
            logging.info(f"put: {put_messages}")
            for m in put_messages:
                fac.message_buffer.append((next(fac.message_count), m))
            fac.message_new.set()

        async def get(start_init, expected):
            start_from = start_init
            while True:
                mess = await fac.get_message(start_from)
                self.assertEqual(next(expected), mess)
                logging.info(f"get message: {mess}")
                start_from = mess[0] + 1

        async def test():
            await _helper([b'a'])
            get_1 = asyncio.create_task(get(0, exp1))
            # Normally 'b' and 'c' should come at the same time? Note that async.sleep() is not accurate
            await asyncio.gather(_helper([b'b'], 0.1), _helper([b'c'], 0.1), _helper([b'd'], 0.2))
            get_2 = asyncio.create_task(get(2, exp2))  # they must come at the same time
            await _helper([b'e', b'f'], 0.1)
            await asyncio.sleep(0.1)
            if get_1.done():
                await get_1
            else:
                get_1.cancel()
            if get_2.done():
                await get_2
            else:
                get_2.cancel()
            await asyncio.sleep(0.01)

        fac = FactorioServerDaemon(self.executable)
        exp1 = iter([(0, [b'a']), (2, [b'b', b'c']), (3, [b'd']), (5, [b'e', b'f'])])
        exp2 = iter([(3, [b'c', b'd']), (5, [b'e', b'f'])])
        self.loop.run_until_complete(test())
        self.assertIsNone(next(exp1, None))
        self.assertIsNone(next(exp2, None))

    def test_get_version(self):
        async def test():
            fac = FactorioServerDaemon(self.executable)
            version_str = await fac.get_game_version()
            str_list = version_str.splitlines()
            self.assertRegex(str_list[0], r"^Version: \d\.\d\.\d+ \(build \d+, \w+, \w+\)$")
            self.assertEqual(len(str_list), 4)
            await fac.start(['--start-server', self.savefile])
            self.assertEqual(await fac.get_game_version(), version_str)
            await fac.stop()
            self.assertEqual(await fac.get_game_version(), version_str)

        self.loop.run_until_complete(test())

    def test_get_current_args(self):
        async def test():
            fac = FactorioServerDaemon(self.executable)
            self.assertIsNone(fac.get_current_args())
            input_args = ['--start-server', self.savefile]
            await fac.start(input_args)
            self.assertEqual(fac.get_current_args(), input_args)
            await fac.get_game_version()  # should not change the current args
            self.assertEqual(fac.get_current_args(), input_args)
            await fac.stop()
            self.assertIsNone(fac.get_current_args())
            await fac.start(['--version'])
            self.assertIsNone(fac.process)  # should be terminated automatically
            self.assertIsNone(fac.get_current_args())

        self.loop.run_until_complete(test())
