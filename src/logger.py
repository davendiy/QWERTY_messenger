#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 27.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

import logging
import inspect
import types
from abc import ABCMeta
from .constants.app_constants import *

ENABLE_LOGGER_METACLASS = True


# Create a custom logger
logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)

# Create handlers
i_handler = logging.FileHandler(LOG_SERVER_FILE)
s_handler = logging.StreamHandler()
f_handler = logging.FileHandler(CRITICAL_LOG_SERVER_FILE)

# all the information will be written to the LOG_SERVER_FILE
# all the warning and error will be written to the stdout
# all the error will be written to the error.log
i_handler.setLevel(logging.INFO)
s_handler.setLevel(logging.DEBUG)
f_handler.setLevel(logging.ERROR)

# Create formatters and add it to handlers
i_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
s_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

i_handler.setFormatter(i_format)
s_handler.setFormatter(s_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(i_handler)
logger.addHandler(s_handler)
logger.addHandler(f_handler)
#
# logger.info('This is an info')         # test
# logger.warning('This is a warning')
# logger.error('This is an error')


def logged(cls_name, function):
    logger.debug("[*] Creating logger wrapper for "
                "{:>25} from {:>25}".format(function.__name__, cls_name))
    if not inspect.iscoroutinefunction(function):
        def _fn(self, *args, **kwargs):
            logger.debug("[*] Starting {:>25} from {:25} "
                        "with params:\n{}, {}...".format(function.__name__,
                                                         cls_name,
                                                         args, kwargs))
            return function(self, *args, **kwargs)
        return _fn
    else:
        async def _async_fn(self, *args, **kwargs):
            logger.debug("[*] Awaiting {:>25} from {:25} "
                        "with params:\n{}, {}...".format(function.__name__,
                                                         cls_name,
                                                         args, kwargs))
            return await function(self, *args, **kwargs)
        return _async_fn


class DebugMetaclass(type):

    def __new__(mcs, name, bases, attrs):

        if ENABLE_LOGGER_METACLASS:

            for key, value in attrs.items():
                if type(value) == types.FunctionType or \
                        type(value) == types.MethodType:
                    attrs[key] = logged(name, value)

        return super(DebugMetaclass, mcs).__new__(mcs, name, bases, attrs)


class DebugMetaclassForAbstract(DebugMetaclass, ABCMeta):

    def __new__(mcs, *args, **kwargs):
        return DebugMetaclass.__new__(mcs, *args, **kwargs)
