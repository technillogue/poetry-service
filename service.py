import asyncio
import hashlib
from pathlib import Path
from aiohttp import web
import yaml


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

async def solve_deps(deps: str) -> Path:
    requirements = canonicalize(deps)
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
    return lock_path

async def requirements(req: web.Request) -> web.FileResponse:
    lock_path = solve_deps(await req.text())
    return web.FileResponse(lock_path)

async def yaml(req: web.Request) -> web.FileResponse:
    cog = yaml.load(await req.text(), Loader=yaml.CLoader)
    deps = "\n".join(cog["build"]["python_packages"])
    lock_path = solve_deps(deps)
    return web.FileResponse(lock_path)



app.add_routes([web.post("/requirements", route)])
if __name__ == "__main__":
    web.run_app(app, port=8080)
