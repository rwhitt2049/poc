import logging
import logging.config
import logging.handlers
from functools import wraps
import datetime
from multiprocessing import Manager, Queue
import os


class QueueLogging(object):

    def __init__(self, folder='logs', debug=True,
                 handler=_SimpleHandler(), respect_handler_level=False):
        self.q = Manager().Queue()
        config = _config_listener(folder, debug)
        logging.config.dictConfig(config)

        self.lp = logging.handlers.QueueListener(
            self.q, handler, respect_handler_level=respect_handler_level)
        self.lp.start()

    def shutdown(self):
        self.lp.stop()


class _SimpleHandler:
    """
    A simple handler for logging events.
    """

    def handle(self, record):
        logger = logging.getLogger(record.name)
        logger.handle(record)


class LoggingMixin(object):
    """
    Convenience super-class to have a logger configured with the class name.

    Idea from Airflow:
        https://github.com/apache/incubator-airflow/blob/master/airflow/utils/logging.py
    """

    @property
    def logger(self):
        try:
            return self._logger
        except AttributeError:
            name = '{}.{}'.format(self.__class__.__module__,
                                  self.__class__.__name__)
            self._logger = logging.root.getChild(name)
            self._logger.addHandler(logging.NullHandler())
            return self._logger


def logf(func):
    """
    Convenience decorator to have logger configured with function name.

    Adapted from Ankur Dedania's logging code for SC2 command center
    """
    @wraps(func)
    def inner(*args, **kwargs):
        name = '{}.{}'.format(func.__module__,
                              func.__name__)
        logger = logging.getLogger(name)
        logger.addHandler(logging.NullHandler())
        kwargs['logger'] = logger
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(e)
    return inner


class InfoOnlyFilter(object):
    def __init__(self):
        self.__level = logging.INFO

    def filter(self, logRecord):
        return logRecord.levelno <= self.__level


def _config_listener(folder, debug):
    level = 'DEBUG' if debug else 'INFO'
    path = os.path.join(os.getcwd(), folder)
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        finally:
            pass

    now = datetime.datetime.now()
    dtformat = '%Y%m%d%H%M%S'
    pre = os.path.join(path, now.strftime(dtformat))

    config = {
        'version': 1,
        'formatters': {
            'detailed': {
                'class': 'logging.Formatter',
                'format': '%(asctime)s [%(name)-20s] %(levelname)8s: %(message)s'
            },
            'simple': {
                'class': 'logging.Formatter',
                'format': '[%(name)-20s] %(levelname)8s: %(message)s',
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
            'master': {
                'class': 'logging.FileHandler',
                'filename': '%s_log.log' % pre,
                'mode': 'w',
                'formatter': 'detailed'
            },
            'summary': {
                'class': 'logging.FileHandler',
                'filename': '%s_summary.log' % pre,
                'mode': 'w',
                #'filters': InfoOnlyFilter,
                'formatter': 'detailed'
            },
            'errors': {
                'class': 'logging.FileHandler',
                'filename': '%s_errors.log' % pre,
                'mode': 'w',
                'level': 'ERROR',
                'formatter': 'detailed'
            },
        },
        'loggers': {
            'jetstream.workflow': {
                'handlers': ['summary']
            }
        },
        'root': {
            'level': level,
            'handlers': ['console', 'master', 'errors']
        },
    }
    return config
