import logging

from ..protobuf.facmgr_pb2 import SaveNameList, SaveName, SaveStat, Status, GameUpdates, ManagerStat, OutputStreams
from ..protobuf.facmgr_pb2_grpc import ServerManagerServicer

from .save_explorer import SavesExplorer
from . import daemon


class ServerManager(ServerManagerServicer):
    def __init__(self, saves_dir, fac_exec, fac_timeout, welcome_message='welcome to Factorio server'):
        self.saves = SavesExplorer(saves_dir)
        self.daemon = daemon.FactorioServerDaemon(fac_exec, timeout=fac_timeout)
        self.welcome = welcome_message

    async def GetManagerStatus(self, request, context):
        is_running = self.daemon.is_running
        current_save = game_version = None
        if request.verbose:
            game_version = await self.daemon.get_game_version()
            if is_running:
                run_args = self.daemon.get_current_args()
                try:
                    current_save = SaveName(name=run_args[run_args.index('--start-server') + 1])
                except (ValueError, IndexError, AttributeError):
                    pass

        return ManagerStat(
            welcome=self.welcome,
            running=is_running,
            game_version=game_version,
            current_save=current_save
        )

    async def GetAllSaveName(self, request, context):
        result = SaveNameList()
        result.save_name.extend([SaveName(name=name) for name in await self.saves.get_names()])
        return result

    async def GetStatByName(self, request, context):
        return SaveStat(stat_json=await self.saves.load_json(request.name))

    async def StartServerByName(self, request, context):
        if not request.HasField("save_name"):
            return Status(code=daemon.BAD_ARG, message="Save name is required for starting a server")
        args = ['--start-server', request.save_name.name]
        args += request.extra_args
        result = await self.daemon.start(args)
        return Status(**result)

    async def StopServer(self, request, context):
        result = await self.daemon.stop()
        return Status(**result)

    async def RestartServer(self, request, context):
        args = []
        if request.HasField("save_name"):
            args += ['--start-server', request.save_name.name]
        args += request.extra_args
        if not args:
            args = None
        result = await self.daemon.restart(args)
        return Status(**result)

    async def InGameCommand(self, request, context):
        return Status(**self.daemon.in_game_command(request.cmd))

    async def WaitForUpdates(self, request, context):
        from_offset = None
        if request.HasField("from_offset"):
            from_offset = request.from_offset
        offset, messages = await self.daemon.get_message(from_offset)
        return GameUpdates(latest_offset=offset, updates=messages)

    async def GetOutputStreams(self, request, context):
        stdout, stderr = await self.daemon.get_output()
        return OutputStreams(stdout=stdout, stderr=stderr)

    async def UploadToTelegram(self, request, context):
        try:
            progress = await self.saves.upload_tg(
                request.save_name.name,
                request.client.session_string,
                request.client.chat_id,
                request.client.reply_id if request.client.HasField("reply_id") else None
            )
        except FileNotFoundError:
            yield Status(code=-1, message="Save file not found")
            return
        try:
            async for current, total in progress:
                yield Status(code=0, message=f"{current}/{total}")
        except Exception as e:
            logging.error(f"An error occurs during uploading: '{type(e).__name__}: {e}'")
            yield Status(code=-2, message=f"{type(e).__name__}: {e}")
