import datetime
import logging
import logging.config
import logging.handlers

from logging_tree import printout

from multiprocessing import Process, Queue, Manager

now = datetime.datetime.now()
dtformat = '%Y%m%d%H%M%S'
FMT = '%(asctime)s %(name)-15s %(levelname)-8s %(processName)-10s %(message)s'
pre = now.strftime(dtformat)


class _SimpleHandler:
    """
    A simple handler for logging events.
    """

    def handle(self, record):
        logger = logging.getLogger(record.name)
        logger.handle(record)


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
            'filename': pre + '_mplog.log',
            'mode': 'w',
            'formatter': 'detailed',
        },
        'foofile': {
            'class': 'logging.FileHandler',
            'filename': pre + '_mplog-foo.log',
            'mode': 'w',
            'formatter': 'detailed',
        },
        'errors': {
            'class': 'logging.FileHandler',
            'filename': pre + '_mplog-errors.log',
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

'''
Create a queue
Configure all loggers
    either one by one
    or using dictConfig()
Add the q and handlers to logging.handlers.QueueListener
Start the queue listener
.... do everything
Stop the queue listener
'''

def main():
    q = Manager().Queue()
    workers = []
    for i in range(5):
        wp = Process(target=worker_process, name='worker %d' % (i + 1),
                     args=(q,))
        workers.append(wp)
        wp.start()

    logging.config.dictConfig(d)
    # Messages to the logger need to come after you add their handlers
    # to the root
    foo = logging.getLogger('foo')
    spam = logging.getLogger('spam')
    spam.info('spam info in the main')
    foo.info('foo info in the main')

    lp = logging.handlers.QueueListener(q, _SimpleHandler(),
                                        respect_handler_level=False)
    lp.start()

    # At this point, the main process could do some useful work of its own
    # Once it's done that, it can wait for the workers to terminate...
    for wp in workers:
        wp.join()
    # And now tell the logging thread to finish up, too
    # q.put(None)
    # lp.join()
    lp.stop()
    printout()


if __name__ == '__main__':
    main()