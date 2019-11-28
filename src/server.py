#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 28.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

import curio
from src.database import SqliteStorageClient
from src.app_constants import *
from src.logger import logger

StorageClientRealization = SqliteStorageClient


async def client_handler(client, addr):
    print("Connection from", addr)

    storage_client = StorageClientRealization(SERVER_DATABASE)
    async with storage_client:
        try:
            async with client:
                client_stream = client.as_stream()
                await client_stream.write(b"Registration.\n")
                await client_stream.write(b"Please, enter your name:\n--> ")
                name = (await client_stream.readline()).strip()
                await client_stream.write(b"Please, enter your password:\n-->")
                password = (await client_stream.readline()).strip()

                await storage_client.new_user(str(name, encoding='utf-8'), password)

                await (client_stream.write(b"User successfully created.\n"))
                await (client_stream.write(b"Please, enter the name of user you want to delete.\n-->"))
                name = (await client_stream.readline()).strip()

                await storage_client.delete_user(str(name, encoding='utf-8'))
        except Exception as e:
            logger.error(e)
    # except Exception as e:
    #     logger.error(e)
    #     await storage_client.end()
    #     await client.close()


if __name__ == '__main__':
    curio.run(curio.tcp_server, '', 25000, client_handler, with_monitor=True)
