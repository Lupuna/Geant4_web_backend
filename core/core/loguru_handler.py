from logging import __file__, Handler, LogRecord, currentframe
from loguru import logger


class InterceptHandler(Handler):
    def emit(self, record: LogRecord):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        message = record.getMessage()
        status_code = getattr(record, 'status_code', None)

        if status_code:
            message = f"{status_code} | {message}"

        frame, depth = currentframe(), 2
        while frame.f_code.co_filename == __file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, message)
