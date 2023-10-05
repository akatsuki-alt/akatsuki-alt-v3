import logging.handlers
import logging
import config
import gzip
import sys
import os


class ColorFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    cyan = "\x1b[96m"
    reset = "\x1b[0m"

    format_prefix = "[%(asctime)s] - <%(name)s> "
    format = "%(levelname)s: %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_prefix + format + reset,
        logging.INFO: grey + format_prefix + cyan + format + reset,
        logging.WARNING: grey + format_prefix + yellow + format + reset,
        logging.ERROR: grey + format_prefix + red + format + reset,
        logging.CRITICAL: grey + format_prefix + bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class GZipRotator:
    def __call__(self, source, dest):
        os.rename(source, dest)
        with open(dest, "rb") as f_in:
            f_out = gzip.open(f"{dest}.gz", "wb")
            f_out.writelines(f_in)
            f_out.close()
        os.remove(dest)


os.makedirs(config.BASE_PATH+"/logs", exist_ok=True)

type = sys.argv[1] if len(sys.argv) > 1 else "debug"
file_handler = logging.handlers.TimedRotatingFileHandler(
    filename=f"{config.BASE_PATH}/logs/{type}.log",
    when="midnight",
    interval=1,
    backupCount=5,
)
file_handler.rotator = GZipRotator()
file_handler.setFormatter(ColorFormatter())

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ColorFormatter())

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] - <%(name)s> %(levelname)s: %(message)s",
    handlers=[file_handler, console_handler],
)

logger = logging.getLogger(type)
logger.setLevel(logging.DEBUG)


def get_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    return logger
