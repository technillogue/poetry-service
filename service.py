import asyncio
import hashlib
from pathlib import Path
from aiohttp import web


def sha256(_data: str) -> str:
    return hashlib.sha256(_data.encode()).hexdigest()


async def get_output(cmd: str, cwd: "str | Path", inp: str = "") -> str:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdin=-1, stdout=-1, stderr=-1, cwd=str(cwd), close_fds=True
    )
    stdout, stderr = await proc.communicate(inp.encode())
    return stdout.decode().strip() or stderr.decode().strip()


def canonicalize(requirements: str):
    return " ".join(sorted(requirements.replace(" ", "").split("\n")))


app = web.Application()
base = Path("/tmp/envs")


async def route(req: web.Request) -> web.FileResponse:
    requirements = canonicalize(await req.text())
    digest = sha256(requirements)
    poetry_path = base / digest
    lock_path = poetry_path / "poetry.lock"
    if lock_path.exists():
        return web.FileResponse(lock_path)
    poetry_path.mkdir(exist_ok=True)
    await get_output("poetry init --no-interaction", cwd=poetry_path)
    proc = await asyncio.create_subprocess_exec(
        "poetry", "add", *requirements.split(), cwd=poetry_path
    )
    await proc.wait()
    return web.FileResponse(lock_path)


app.add_routes([web.post("/poetry", route)])
if __name__ == "__main__":
    web.run_app(app, port=8080)
