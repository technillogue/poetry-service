FROM python:3.10
RUN pip install poetry "aiohttp[speedups]"
RUN mkdir /envs/
