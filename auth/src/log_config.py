import time

from uvicorn.logging import AccessFormatter, DefaultFormatter


def _microsecond_time(record):
    ct = time.gmtime(record.created)
    t = time.strftime("%Y-%m-%d %H:%M:%S", ct)
    us = int(round((record.created - int(record.created)) * 1_000_000))
    return f"{t}.{us:06d}+00:00"


class MicrosecondFormatter(DefaultFormatter):
    def formatTime(self, record, datefmt=None):
        return _microsecond_time(record)


class MicrosecondAccessFormatter(AccessFormatter):
    def formatTime(self, record, datefmt=None):
        return _microsecond_time(record)
