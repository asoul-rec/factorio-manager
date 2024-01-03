import logging
import os
from unittest import TestCase

from grpc_server.daemon import FactorioServerDaemon
import grpc_server.daemon as daemon
import asyncio

logging.basicConfig(format='%(asctime)s [%(levelname).1s] [%(name)s] %(message)s', level=logging.INFO)


class TestFactorioServerDaemon(TestCase):
    loop: asyncio.AbstractEventLoop

    @classmethod
    def setUpClass(cls):
        cls.executable = os.environ['executable']
        cls.savefile = os.environ['savefile']
        cls.loop = asyncio.new_event_loop()
        super().setUpClass()

    # @classmethod
    # def tearDownClass(cls):
    #     cls.loop.run_until_complete(asyncio.sleep(1))

    def test_start_stop(self):
        factorio_help = "Path where server ID will be stored or read"

        async def error_exe():
            fac = FactorioServerDaemon(self.executable + "f4cT0r10")
            status = await fac.start(['--start-server', self.savefile])
            if os.name == 'nt':
                self.assertEqual(status["code"], daemon.EXIT_ERROR)
                self.assertRegex(status["message"],
                                 r"is not recognized as an internal or external command,\\r\\n"
                                 r"operable program or batch file.\\r\\n")
            else:
                self.assertEqual(status["code"], daemon.BAD_ARG)
                self.assertRegex(status["message"], "^Cannot start server. FileNotFoundError: ")

        async def finish_exe():
            fac = FactorioServerDaemon(self.executable)
            status = await fac.start(['--help'])
            self.assertEqual(status["code"], daemon.EXIT_UNEXPECT)
            self.assertIn("The server exited unexpectedly without error", status["message"])
            self.assertRegex(status["message"],
                             f"^The server exited unexpectedly without error, stdout='.*{factorio_help}.*', stderr=''$")

        async def wrong_fac_arg():
            fac = FactorioServerDaemon(self.executable)
            status = await fac.start(['--helphelp'])
            self.assertEqual(status["code"], daemon.EXIT_ERROR)
            self.assertRegex(status["message"],
                             f"^The server finished with exit_code=1, stdout='.*{factorio_help}.*', stderr=''$")

        async def correct():
            fac = FactorioServerDaemon(self.executable)
            status = await fac.start(['--start-server', self.savefile])
            self.assertDictEqual(status, {"code": daemon.SUCCESS, "message": None})
            status = await fac.start(['--start-server', self.savefile])
            self.assertDictEqual(status, {"code": daemon.SATISFIED, "message": "The server is already running."})

            fac2 = FactorioServerDaemon(self.executable)
            status = await fac2.start(['--start-server', self.savefile])
            self.assertEqual(status["code"], daemon.EXIT_ERROR)
            self.assertIn("exit_code=1", status["message"])
            self.assertIn("Is another instance already running?", status["message"])
            status = await fac2.stop()
            self.assertDictEqual(status, {"code": daemon.SATISFIED, "message": "The server is already stopped."})

            status = await fac.stop()
            self.assertDictEqual(status, {"code": daemon.SUCCESS, "message": None})
            status = await fac.stop()
            self.assertDictEqual(status, {"code": daemon.SATISFIED, "message": "The server is already stopped."})

            status = await fac2.start(['--start-server', self.savefile])
            self.assertDictEqual(status, {"code": daemon.SUCCESS, "message": None})
            status = await fac2.stop()
            self.assertDictEqual(status, {"code": daemon.SUCCESS, "message": None})

        self.loop.run_until_complete(error_exe())
        self.loop.run_until_complete(finish_exe())
        self.loop.run_until_complete(wrong_fac_arg())
        self.loop.run_until_complete(correct())

    def test_restart(self):
        async def restart():
            fac = FactorioServerDaemon(self.executable)
            status = await fac.restart()
            self.assertDictEqual(status, {"code": daemon.BAD_ARG,
                                          "message": "Must provide starting arguments at the beginning"})
            status = await fac.start(['--start-server', self.savefile])
            self.assertDictEqual(status, {"code": daemon.SUCCESS, "message": None})
            status = await fac.restart()
            self.assertDictEqual(status, {"code": daemon.SUCCESS, "message": None})
            status = await fac.restart()
            self.assertDictEqual(status, {"code": daemon.SUCCESS, "message": None})
            status = await fac.stop()
            self.assertDictEqual(status, {"code": daemon.SUCCESS, "message": None})
            status = await fac.restart()
            self.assertDictEqual(status, {"code": daemon.SUCCESS, "message": None})
            status = await fac.stop()
            self.assertDictEqual(status, {"code": daemon.SUCCESS, "message": None})

        self.loop.run_until_complete(restart())
