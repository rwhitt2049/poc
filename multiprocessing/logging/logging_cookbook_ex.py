import logging
import logging.config
import logging.handlers
from multiprocessing import Process, Queue
import random
import threading
import time
from logging_tree import printout

FMT = '%(asctime)s %(name)-15s %(levelname)-8s %(processName)-10s %(message)s'

"""
Example from: https://docs.python.org/3/howto/logging-cookbook.html
"""

d = {
    'version': 1,
    'formatters': {
        'detailed': {
            'class': 'logging.Formatter',
            'format': '%(asctime)s %(name)-15s %(levelname)-8s %(processName)-10s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'mplog.log',
            'mode': 'w',
            'formatter': 'detailed',
        },
        'foofile': {
            'class': 'logging.FileHandler',
            'filename': 'mplog-foo.log',
            'mode': 'w',
            'formatter': 'detailed',
        },
        'errors': {
            'class': 'logging.FileHandler',
            'filename': 'mplog-errors.log',
            'mode': 'w',
            'level': 'ERROR',
            'formatter': 'detailed',
        },
    },
    'loggers': {
        'foo': {
            'handlers': ['foofile']
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file', 'errors']
    },
}


def logger_thread(q):
    while True:
        record = q.get()
        if record is None:
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)


def worker_process(q):
    qh = logging.handlers.QueueHandler(q)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(qh)
    foo = logging.getLogger('foo')
    foobar = logging.getLogger('foo.bar')
    foobarbaz = logging.getLogger('foo.bar.baz')

    foo.debug('worker_proces foo debug')
    foobar.info('worker_proces foobar info')
    foobarbaz.error('worker_proces foobarbaz error')

    spam = logging.getLogger('spam')
    spamham = logging.getLogger('spam.ham')
    spamhameggs = logging.getLogger('spam.ham.eggs')

    spam.debug('worker_proces spam debug')
    spamham.info('worker_proces spamham info')
    spamhameggs.error('worker_proces spamhameggs error')


if __name__ == '__main__':
    q = Queue()
    workers = []
    for i in range(5):
        wp = Process(target=worker_process, name='worker %d' % (i + 1), args=(q,))
        workers.append(wp)
        wp.start()

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sfmt = logging.Formatter(FMT)
    sh.setFormatter(sfmt)

    foo = logging.getLogger('foo')
    fh = logging.FileHandler('mplog-foo.log')
    ft = logging.Formatter(FMT)
    fh.setFormatter(ft)
    foo.addHandler(fh)

    spam = logging.getLogger('spam')
    mpl = logging.FileHandler('mplog.log')
    mpl.setFormatter(ft)

    mple = logging.FileHandler('mplog-errors.log')
    mple.setLevel(logging.ERROR)
    mple.setFormatter(ft)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(sh)
    root.addHandler(mpl)
    root.addHandler(mple)

    # Messages to the logger need to come after you add their handlers
    # to the root
    spam.info('spam info in the main')
    foo.info('foo info in the main')

    #logging.config.dictConfig(d)
    lp = threading.Thread(target=logger_thread, args=(q,))
    lp.start()
    # At this point, the main process could do some useful work of its own
    # Once it's done that, it can wait for the workers to terminate...
    for wp in workers:
        wp.join()
    # And now tell the logging thread to finish up, too
    q.put(None)
    lp.join()
    printout()
