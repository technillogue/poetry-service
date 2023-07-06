FROM python:3.10
RUN pip install poetry "aiohttp[speedups]" pyyaml
RUN mkdir /envs/
