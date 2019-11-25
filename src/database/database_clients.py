#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 25.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

"""
TODO
    - Complete all the interface StoreClient
    - Implement descendant SQLiteStoreClient
    - Add config constants
    - Add documentation
    - Create unit tests
"""


from abc import ABC, abstractmethod
import datetime
from .constants import *


class StoreClient(ABC):

    # -------------------------- users -----------------------------------------
    @abstractmethod
    async def get_user(self, Id: int):
        pass

    @abstractmethod
    async def new_user(self, Name: str, PasswordHash: bytes):
        pass

    @abstractmethod
    async def del_user(self, Id: int):
        pass

    @abstractmethod
    async def find_users(self, Name: str):
        pass

    # ------------------------- channels/chats ---------------------------------
    @abstractmethod
    async def new(self, Name: str, Created: datetime, Type=CHANNEL):
        pass

    @abstractmethod
    async def delete(self, Id: int, Type=CHANNEL):
        pass

    @abstractmethod
    async def find(self, Name: str, Type=CHANNEL):
        pass

    @abstractmethod
    async def get(self, Id: int, Type=CHANNEL):
        pass

    # ------------------------ messages ----------------------------------------

    @abstractmethod
    async def new_message(self, ChatID: int,
                          Created: datetime, Status: int,
                          Type: str, Content):
        pass

    @abstractmethod
    async def get_message(self, Id: int):
        pass

    @abstractmethod
    async def find_message(self, text):
        pass

    @abstractmethod
    async def delete_message(self, Id: int):
        pass
