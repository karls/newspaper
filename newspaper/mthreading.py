# -*- coding: utf-8 -*-
"""
Anything that has to do with threading in this library
must be abstracted in this file. If we decide to do gevent
also, it will deserve its own gevent file.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

import Queue
from threading import Thread

import requests
from PIL import Image
from StringIO import StringIO

class Worker(Thread):
    """
    Thread executing tasks from a given tasks queue.
    """
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            try:
                func, args, kargs = self.tasks.get()
            except Queue.Empty:
                print 'thread breaking b/c queue is empty'
                break
            try:
                func(*args, **kargs)
            except Exception, e:
                print 'critical multi-thread err %s' % e

            self.tasks.task_done()


class ThreadPool:
    """
    Pool of threads consuming tasks from a queue.
    """
    def __init__(self, num_threads):
        self.tasks = Queue.Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """
        Add a task to the queue.
        """
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """
        Wait for completion of all the tasks in the queue.
        """
        self.tasks.join()

    def clear_threads(self):
        """
        """
        pass


class NewsPool(object):

    def __init__(self):
        """
        Abstraction of a threadpool. A newspool can accept any number of
        source OR article objects together in a list. It allocates one
        thread to every source and then joins.

        We allocate one thread per source to avoid rate limiting.
        5 sources = 5 threads, one per source.

        >>> import newspaper
        >>> from newspaper import news_pool

        >>> cnn_paper = newspaper.build('http://cnn.com')
        >>> tc_paper = newspaper.build('http://techcrunch.com')
        >>> espn_paper = newspaper.build('http://espn.com')

        >>> papers = [cnn_paper, tc_paper, espn_paper]
        >>> news_pool.set(papers)
        >>> news_pool.join()

        # All of your papers should have their articles html all populated now.
        >>> cnn_paper.articles[50].html
        u'<html>blahblah ... '
        """
        self.papers = []
        self.pool = None

    def join(self):
        """
        Runs the mtheading and returns when all threads have joined
        resets the task.
        """
        if self.pool is None:
            print 'Call set(..) with a list of source objects before .join(..)'
            raise
        self.pool.wait_completion()
        self.papers = []
        self.pool = None

    def set(self, paper_list, threads_per_source=1):
        """
        Sets the job batch.
        """
        self.papers = paper_list
        num_threads = threads_per_source * len(self.papers)
        self.pool = ThreadPool(num_threads)

        for paper in self.papers:
            self.pool.add_task(paper.download_articles)


class ImagePool(object):

    def __init__(self):
        self.urls = []
        self.pool = None
        self.img_sizes = {}

    def join(self):
        """
        Runs the mtheading and returns when all threads have joined
        resets the task.
        """
        if self.pool is None:
            print 'Call set(..) with a list of source objects before .join(..)'
            raise
        self.pool.wait_completion()
        self.urls = []
        self.pool = None


    def calculate_size(self, url):
        resp = requests.get(url)
        i = Image.open(StringIO(resp.content))
        total_pixels = int(i.size[0]) * int(i.size[1])
        if total_pixels > 8000:
            self.img_sizes[url] = i.size


    def set(self, url_list, threads_per_source=1):
        """
        Sets the job batch.
        """
        self.urls = url_list
        num_threads = threads_per_source * len(self.urls)
        self.pool = ThreadPool(num_threads)

        for url in self.urls:
            self.pool.add_task(self.calculate_size, url)

# def test_image_pool():
#     from newspaper import Article
#     # a = Article(url="http://www.theguardian.com/world/2014/aug/12/russian-convoy-heads-for-ukraine")
#     a = Article(url="http://www.bbc.co.uk/news/uk-england-manchester-28755375")
#     a.build()
#     pool = ImagePool()
#     pool.set(a.images)
#     pool.join()
#     return pool.img_sizes
