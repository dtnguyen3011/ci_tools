""" See https://docs.python.org/3/howto/logging.html for usage. """
import logging
from logging import StreamHandler
from os.path import splitext, basename
import sys
from colorama import init, Fore, Back, Style

init()

class ColorStreamHandler(StreamHandler):
    """ A colorized output SteamHandler """
    colors = {
        'DEBUG': Fore.LIGHTCYAN_EX,
        'INFO': Fore.LIGHTGREEN_EX,
        'WARN': Fore.LIGHTYELLOW_EX,
        'WARNING': Fore.LIGHTYELLOW_EX,
        'ERROR': Fore.LIGHTRED_EX,
        'CRIT': Back.RED + Fore.WHITE,
        'CRITICAL': Back.RED + Fore.WHITE
    }

    def emit(self, record):
        try:
            message = self.format(record)
            self.stream.write(self.colors[record.levelname] + message + Style.RESET_ALL)
            self.stream.write(getattr(self, 'terminator', '\n'))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException:
            self.handleError(record)


def get_logger(filename=''):
    logger_name = splitext(basename(filename))[0]
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # explicitly resetting already established handlers
    # this avoids having multiple outputs if getLogger
    # gets called multiple times with the same name
    if logger.handlers:
        logger.handlers = []

    console_handler = ColorStreamHandler(sys.stdout)

    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(name)s |%(levelname)-8s| %(message)s', '%Y-%m-%d %H:%M:%S')

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

def demo(logger):
    """ Just some demo. """
    logger.info('##### LOGGER DEMO #####')
    logger.error('Errors will always be printed.')
    logger.critical('Critical is always printed.')
    logger.info('Info is not printed with -q.')
    logger.warning('Warning is only printed unless -q is given.')
    logger.debug('Debug is only printed if -d is set.')
    logger.info('#######################')
