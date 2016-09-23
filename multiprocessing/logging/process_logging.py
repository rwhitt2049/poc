import logging
import logging.config
import logging.handlers
from multiprocessing import Process, Queue
import random
import threading
import time
import logging_tree as lt

#logging.basicConfig(level='DEBUG', filename='worker.log')


def func(a):
    if 1 < a < 4:
        1 / 0
    else:
        print(2 * a)


def logger_thread(q):
    while True:
        record = q.get()
        if record is None:
            break
        print(record.name)
        logger = logging.getLogger('worker_process.logger_thread')
        logger.info('logged')


def worker_process(afunc, arg, q):
    # QueueHandler needs to go on the worker
    qh = logging.handlers.QueueHandler(q)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(qh)
    # Because the QueueHandler exists on the root, it doesn't need to be
    # specified again for the wlog
    wlog = logging.getLogger('worker_process')
    # wlog.addHandler(qh)
    try:
        afunc(arg)
    except Exception as e:
        wlog.exception(e)
        # wlog.debug('huh')

    '''
    levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR,
              logging.CRITICAL]
    loggers = ['foo', 'foo.bar', 'foo.bar.baz',
               'spam', 'spam.ham', 'spam.ham.eggs']
    for i in range(10):
        lvl = random.choice(levels)
        logger = logging.getLogger(random.choice(loggers))
        logger.log(lvl, 'Message no. %d', i)
    '''


if __name__ == '__main__':
    q = Queue()
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.info('main')
    #h1 = logging.StreamHandler()
    #h1.setLevel(logging.ERROR)
    h2 = logging.FileHandler('process_logging.log')
    h2.setLevel(logging.DEBUG)
    #root.addHandler(h1)
    #root.addHandler(h2)
    workers = []
    for i in range(5):
        wp = Process(target=worker_process, name='worker %d' % (i + 1),
                     args=(func, i, q,))
        workers.append(wp)
        wp.start()
    # logging.config.dictConfig(d)
    lp = threading.Thread(target=logger_thread, args=(q,))
    lp.start()
    # At this point, the main process could do some useful work of its own
    # Once it's done that, it can wait for the workers to terminate...
    for wp in workers:
        wp.join()
    # And now tell the logging thread to finish up, too
    q.put(None)
    lp.join()
    lt.printout()