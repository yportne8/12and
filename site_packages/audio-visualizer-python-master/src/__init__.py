import sys
import os
import logging


__version__ = '2.0.0'


class Logger(logging.getLoggerClass()):
    '''
        Custom Logger class to handle custom VERBOSE log level.
        Levels used in this program are as follows:
            VERBOSE     Annoyingly frequent debug messages (e.g, in loops)
            DEBUG       Ordinary debug information
            INFO        Expected events that are expensive or irreversible
            WARNING     A non-fatal error or suspicious behaviour
            ERROR       Any error that would interrupt the user
            CRITICAL    Things that really shouldn't happen at all
    '''
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        logging.addLevelName(5, "VERBOSE")

    def verbose(self, msg, *args, **kwargs):
        pass
logging.setLoggerClass(Logger)
logging.VERBOSE = 5


if getattr(sys, 'frozen', False):
    # frozen
    wd = os.path.dirname(sys.executable)
else:
    # unfrozen
    wd = os.path.dirname(os.path.realpath(__file__))
