import logging
import logging.handlers
import threading

from logging_tree import printout

from multiprocessing import Pool, Manager

logging.basicConfig(level='DEBUG', filename='worker.log')

def func(a):
    if 0 <= a < 7:
        val = 2*a
    else:
        val = 1/0
    return val


def worker(x, args, rq, eq):
    qh = logging.handlers.QueueHandler(eq)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(qh)
    wlog = logging.getLogger('worker_process')
    try:
        print('in worker: ', x(*args))
        rq.put(x(*args))
    except Exception as e:
        print('error')
        wlog.exception(e)


def listener(rq):
    while True:
        result = rq.get()
        if result is None:
            print('listener break')
            break
        print('in listener: ', result)


def logger_thread(q):
    while True:
        record = q.get()
        if record is None:
            print('logger break')
            break
        print('logger', record)
        #logger = logging.getLogger(record.name)
        #logger.handle(record)


def main():
    m = Manager()
    results_q = m.Queue()
    exc_q = m.Queue()
    lp = threading.Thread(target=logger_thread, args=(exc_q,))
    lp.start()
    with Pool(processes=4) as pool:
        pool.apply_async(listener, args=(results_q, ))
        jobs = [pool.apply_async(worker, args=(func, [x], results_q, exc_q)) for x in range(10)]

        for job in jobs:
            job.get()

        results_q.put(None)
        exc_q.put(None)

        lp.join()
    printout()


if __name__ == '__main__':
    import sys; sys.exit(main())
