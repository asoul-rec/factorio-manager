import asyncio
import json
import logging
import os
import re
import shutil
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Optional

from ..protobuf.error_code import BAD_ARG, EXIT_ERROR, NOT_AVAILABLE, SATISFIED, SUCCESS


LATEST_RELEASES_URL = "https://factorio.com/api/latest-releases"
DOWNLOAD_URL = "https://factorio.com/get-download/{version}/headless/linux64"
USER_AGENT = "factorio-manager/0.1.1"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


@dataclass(frozen=True)
class UpdateEvent:
    stage: str
    code: int = SUCCESS
    message: Optional[str] = None
    progress: Optional[float] = None
    version: Optional[str] = None


class FactorioHeadlessUpdater:
    def __init__(self, update_dir: str | os.PathLike[str] | None, *,
                 timeout: float = 30, strict_version_output: bool = True):
        self.update_dir = None if update_dir is None else Path(update_dir)
        self.timeout = timeout
        self.strict_version_output = strict_version_output

    @property
    def enabled(self) -> bool:
        return self.update_dir is not None

    @property
    def releases_dir(self) -> Path:
        return self.update_dir / "releases"

    @property
    def downloads_dir(self) -> Path:
        return self.update_dir / "downloads"

    @property
    def current_link(self) -> Path:
        return self.update_dir / "current"

    @property
    def current_executable(self) -> Path:
        return self.current_link / "bin" / "x64" / "factorio"

    def _current_target(self) -> Optional[Path]:
        if self.current_link.is_symlink():
            return Path(os.readlink(self.current_link))
        return None

    async def update(self, daemon, channel: str | None = None,
                     version: str | None = None) -> AsyncIterator[UpdateEvent]:
        if not self.enabled:
            yield UpdateEvent(
                "unsupported", NOT_AVAILABLE,
                "Headless update is disabled. Start the manager with --update-dir to enable it."
            )
            return
        if os.name == "nt":
            yield UpdateEvent("unsupported", NOT_AVAILABLE, "Headless update is only supported on Linux.")
            return

        channel = channel or "stable"
        if channel not in ("stable", "experimental"):
            yield UpdateEvent("failed", BAD_ARG, "Channel must be stable or experimental.")
            return
        if version and not VERSION_RE.fullmatch(version):
            yield UpdateEvent("failed", BAD_ARG, f"Invalid Factorio version: {version}")
            return

        try:
            self.update_dir.mkdir(parents=True, exist_ok=True)
            self.releases_dir.mkdir(parents=True, exist_ok=True)
            self.downloads_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            yield UpdateEvent("failed", BAD_ARG, f"Cannot prepare update directory: {type(e).__name__}: {e}")
            return

        yield UpdateEvent("checking", message=f"Checking {channel} headless release.")
        if version is None:
            try:
                version = await asyncio.to_thread(self._fetch_latest_version, channel)
            except Exception as e:
                yield UpdateEvent("failed", EXIT_ERROR, f"Cannot fetch latest release: {type(e).__name__}: {e}")
                return

        current_version = await daemon.get_game_version()
        current_short = self._parse_version(current_version)
        if current_short == version:
            yield UpdateEvent("complete", SATISFIED, f"Factorio headless is already {version}.", version=version)
            return

        release_dir = self.releases_dir / f"factorio-{version}"
        if not (release_dir / "bin" / "x64" / "factorio").is_file():
            archive = self.downloads_dir / f"factorio_headless_x64_{version}.tar.xz"
            yield UpdateEvent("downloading", message=f"Downloading Factorio headless {version}.", version=version)
            try:
                async for event in self._download(version, archive):
                    yield event
            except Exception as e:
                yield UpdateEvent("failed", EXIT_ERROR, f"Download failed: {type(e).__name__}: {e}", version=version)
                return

            yield UpdateEvent("extracting", message=f"Extracting Factorio headless {version}.", version=version)
            try:
                await asyncio.to_thread(self._extract_release, archive, release_dir)
            except Exception as e:
                shutil.rmtree(release_dir, ignore_errors=True)
                yield UpdateEvent("failed", EXIT_ERROR, f"Extraction failed: {type(e).__name__}: {e}", version=version)
                return

        candidate = release_dir / "bin" / "x64" / "factorio"
        yield UpdateEvent("verifying", message=f"Verifying Factorio headless {version}.", version=version)
        verified_version = await self._get_binary_version(candidate)
        if verified_version != version:
            yield UpdateEvent(
                "failed", EXIT_ERROR,
                f"Downloaded binary reports {verified_version or 'unknown version'}, expected {version}.",
                version=version,
            )
            return

        old_args = daemon.get_current_args()
        was_running = daemon.is_running
        old_executable = daemon.executable
        old_release = self._current_target()
        if was_running:
            yield UpdateEvent("stopping", message="Stopping the running server before switching binary.", version=version)
            status = await daemon.stop()
            if status["code"]:
                yield UpdateEvent("failed", status["code"], "Cannot stop server: " + (status["message"] or ""),
                                  version=version)
                return

        yield UpdateEvent("switching", message=f"Switching to Factorio headless {version}.", version=version)
        try:
            await asyncio.to_thread(self._switch_current, release_dir)
        except Exception as e:
            if was_running:
                await self._restore_previous_release(daemon, old_release, old_executable, old_args)
            yield UpdateEvent("failed", EXIT_ERROR, f"Cannot switch release: {type(e).__name__}: {e}", version=version)
            return
        daemon.executable = str(self.current_executable)

        if was_running:
            yield UpdateEvent("starting", message="Restarting the server with the updated binary.", version=version)
            status = await daemon.start(old_args)
            if status["code"]:
                await self._restore_previous_release(daemon, old_release, old_executable, old_args)
                yield UpdateEvent("failed", status["code"], "Cannot restart server: " + (status["message"] or ""),
                                  version=version)
                return

        yield UpdateEvent("complete", SUCCESS, f"Updated Factorio headless to {version}.", version=version)

    def _fetch_latest_version(self, channel: str) -> str:
        if channel not in ("stable", "experimental"):
            raise ValueError("Channel must be stable or experimental.")
        request = urllib.request.Request(LATEST_RELEASES_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.load(response)
        version = payload[channel]["headless"]
        if not VERSION_RE.fullmatch(version):
            raise ValueError(f"Unexpected release version: {version}")
        return version

    async def _download(self, version: str, destination: Path) -> AsyncIterator[UpdateEvent]:
        queue: asyncio.Queue[UpdateEvent | None] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def put(event: UpdateEvent | None):
            loop.call_soon_threadsafe(queue.put_nowait, event)

        def worker():
            try:
                url = DOWNLOAD_URL.format(version=version)
                request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(request, timeout=30) as response:
                    total = int(response.headers.get("Content-Length") or 0)
                    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as tmp:
                        tmp_path = Path(tmp.name)
                        downloaded = 0
                        while chunk := response.read(1024 * 1024):
                            tmp.write(chunk)
                            downloaded += len(chunk)
                            if total:
                                put(UpdateEvent(
                                    "downloading", message=f"Downloaded {downloaded}/{total} bytes.",
                                    progress=downloaded / total, version=version
                                ))
                tmp_path.replace(destination)
            except BaseException as e:
                if "tmp_path" in locals():
                    tmp_path.unlink(missing_ok=True)
                put(UpdateEvent("failed", EXIT_ERROR, f"{type(e).__name__}: {e}", version=version))
            finally:
                put(None)

        task = asyncio.create_task(asyncio.to_thread(worker))
        while True:
            event = await queue.get()
            if event is None:
                break
            if event.code:
                await task
                raise RuntimeError(event.message)
            yield event
        await task

    def _extract_release(self, archive: Path, release_dir: Path):
        parent = release_dir.parent
        with tempfile.TemporaryDirectory(dir=parent) as tmp:
            tmp_path = Path(tmp)
            with tarfile.open(archive) as tar:
                self._safe_extract(tar, tmp_path)
            extracted = tmp_path / "factorio"
            executable = extracted / "bin" / "x64" / "factorio"
            if not executable.is_file():
                raise FileNotFoundError("archive does not contain factorio/bin/x64/factorio")
            if release_dir.exists():
                shutil.rmtree(release_dir)
            extracted.replace(release_dir)

    @staticmethod
    def _safe_extract(tar: tarfile.TarFile, destination: Path):
        destination = destination.resolve()
        for member in tar.getmembers():
            target = (destination / member.name).resolve()
            if not str(target).startswith(str(destination) + os.sep):
                raise ValueError(f"Unsafe path in archive: {member.name}")
        tar.extractall(destination, filter="data")

    def _switch_current(self, release_dir: Path):
        tmp_link = self.update_dir / ".current.new"
        tmp_link.unlink(missing_ok=True)
        os.symlink(release_dir, tmp_link, target_is_directory=True)
        os.replace(tmp_link, self.current_link)

    async def _restore_previous_release(self, daemon, old_release: Optional[Path],
                                        old_executable: str, old_args: Optional[list[str]]):
        if old_release is not None:
            try:
                await asyncio.to_thread(self._switch_current, old_release)
                daemon.executable = str(self.current_executable)
            except Exception as e:
                logging.error(f"Cannot restore previous Factorio release. {type(e).__name__}: {e}")
                daemon.executable = old_executable
        else:
            daemon.executable = old_executable

        if old_args is not None and not daemon.is_running:
            status = await daemon.start(old_args)
            if status["code"]:
                logging.error(f"Cannot restart previous Factorio release: {status}")

    async def _get_binary_version(self, executable: Path) -> Optional[str]:
        try:
            process = await asyncio.create_subprocess_exec(
                str(executable), "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                await asyncio.wait_for(process.wait(), timeout=self.timeout)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return None
            stdout = await process.stdout.read()
            stderr = await process.stderr.read()
        except OSError as e:
            logging.error(f"Fail to start downloaded Factorio binary. {type(e).__name__}: {e}")
            return None

        if process.returncode != 0 or not stdout:
            logging.error(f"Downloaded Factorio binary fails version check: stdout={stdout!r}, stderr={stderr!r}")
            return None
        if self.strict_version_output and stderr:
            logging.error(f"Downloaded Factorio binary produced unexpected stderr: {stderr!r}")
            return None
        return self._parse_version(stdout.decode(errors="replace"))

    @staticmethod
    def _parse_version(output: str | None) -> Optional[str]:
        if not output:
            return None
        match = re.search(r"^Version: ([0-9]+\.[0-9]+\.[0-9]+)", output, re.MULTILINE)
        return None if match is None else match.group(1)
