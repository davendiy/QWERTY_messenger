#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 02.12.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

from .constants import *
from .logger import logger
from .security import *

import threading
import socket
import pickle
import json
import time
from queue import Queue

TIMEOUT = 40

MAIN_SERVER_HOST = 'localhost'
MAIN_SERVER_PORT = 25000

DATA_SERVER_HOST = 'localhost'
DATA_SERVER_PORT = 25001


background_queue = Queue()


class ServerError(Exception):
    pass


def background_socket_receiving(client_aux_socket):
    logger.info(f"[*] Starting of background receiving...")
    logger.debug(f"[-->] Sending {READY_FOR_TRANSFERRING} to aux server...")
    client_aux_socket.sendall(READY_FOR_TRANSFERRING)

    while True:
        try:
            logger.debug(f"[<--] Fetching the json from aux server...")
            resp = client_aux_socket.recv(ATOM_LENGTH)
            if not resp:
                time.sleep(1)
                continue
            logger.debug(f"[*] Got {resp} from aux sever.")
            try:
                data = json.loads(str(resp, encoding='utf-8'))
            except (ValueError, TypeError):
                logger.error(BAD_JSON_FORMAT)
                continue
            content_type = data[CONTENT_TYPE]
            content_size = data[CONTENT_SIZE]
            if content_type != CHATS_LIST:
                chat_name = data[CHAT_NAME]
            else:
                chat_name = ''

            signature = data[SIGNATURE_OF_SERVER]
            client_aux_socket.sendall(READY_FOR_TRANSFERRING)
            res_data = b''
            logger.debug(f"[<--] Fetching {content_size} bytes from aux server...")
            for _ in range(0, content_size, CHUNK):
                res_data += client_aux_socket.recv(CHUNK)
            done = len(res_data)
            if content_size - done:
                res_data += client_aux_socket.recv(content_size - done)
            verify_control_message(res_data, bytes.fromhex(signature))
            tmp = pickle.loads(res_data)
            background_queue.put((content_type, chat_name, tmp))

        except socket.error:
            client_aux_socket.close()
            break
        except Exception as e:
            logger.exception(e)
            continue


class ConnectionManager:


    def __init__(self, main_socket: socket.socket, aux_socket: socket.socket):
        self._main_socket = main_socket
        self._aux_socket = aux_socket
        self._logged_in = False
        self._logged_name = ""
        self._connected = False
        self._aux_connected = False

        self._user_chats = None

    def register(self, user_name, password):
        logger.info(f"[*] Starting process of registration...")
        logger.debug(f"[-->] Sending {REGISTRATION}...")
        self._main_socket.sendall(REGISTRATION)
        logger.debug(f"[<--] Getting answer from server...")
        resp = self._main_socket.recv(ATOM_LENGTH)
        logger.debug(f"[*] Got: {resp}.")
        if resp != READY_FOR_TRANSFERRING:
            raise ServerError(f"Incorrect server response: {resp}")
        self._confirm_server()
        data = JSON_REGISTRATION_TEMPLATE.copy()
        data[NAME] = user_name
        data[PASSWORD] = password
        logger.debug(f"[-->] Sending to the server {data}...")
        self._main_socket.sendall(bytes(json.dumps(data), encoding='utf-8'))
        logger.debug(f"[<--] Fetching response...")
        resp = self._main_socket.recv(ATOM_LENGTH)
        logger.debug(f"[*] Got {resp}.")
        if resp == READY_FOR_TRANSFERRING:
            self._aux_connection()
        else:
            raise ServerError(str(resp, encoding='utf-8'))
        logger.info(f'[*] Process of registration done.')
        threading.Thread(target=background_socket_receiving,
                         args=(self._aux_socket,), daemon=True).start()

    def _aux_connection(self):
        logger.info(f"[*] Starting the process of creating aux connection...")
        logger.debug(f"[-->] Sending {READY_FOR_TRANSFERRING}...")
        self._main_socket.sendall(READY_FOR_TRANSFERRING)
        logger.debug(f"[<--] Receiving the control phrase from the server...")
        check_phrase = self._main_socket.recv(ATOM_LENGTH)
        logger.debug(f"[*] Got {check_phrase}.")

        logger.debug(f"[*] Connecting to the server for data transferring...")
        self._aux_socket.connect((DATA_SERVER_HOST, DATA_SERVER_PORT))
        logger.debug(f"[-->] Sending {check_phrase} to the aux server...")
        self._aux_socket.sendall(check_phrase)

        logger.debug(f"[<--] Fetching the response from aux server...")
        resp = b""
        for i in range(TIMEOUT):
            resp = self._aux_socket.recv(ATOM_LENGTH)
            if resp:
                break
            time.sleep(1)

        if resp == READY_FOR_TRANSFERRING:
            self._aux_connected = True
        else:
            raise ServerError(str(resp, encoding='utf-8'))
        logger.info(f"[*] Process of creating aux connection done.")

    def _confirm_server(self):
        logger.info(f"[*] Starting process of server confirmation...")
        control_message = generate_control_message()
        logger.debug(f"[-->] Sending control message: {control_message}")
        self._main_socket.sendall(control_message)
        logger.debug(f"[<--] Getting response from the server...")
        resp = self._main_socket.recv(256)
        logger.debug(f"[*] Got: {resp}")
        verify_control_message(control_message, resp)
        logger.info(f"[*] Process of server confirmation done.")

    def log_in(self, user_name, password):
        logger.info(f"[*] Starting process of logging in...")
        logger.debug(f"[-->] Sending {SIGN_IN}...")
        self._main_socket.sendall(SIGN_IN)
        logger.debug(f"[<--] Getting answer from server...")
        resp = self._main_socket.recv(ATOM_LENGTH)
        logger.debug(f"[*] Got: {resp}.")
        if resp != READY_FOR_TRANSFERRING:
            raise ServerError(f"Incorrect server response: {resp}")
        self._confirm_server()
        data = JSON_SIGN_IN_TEMPLATE.copy()
        data[NAME] = user_name
        data[PASSWORD] = password
        logger.debug(f"[-->] Sending to the server {data}...")
        self._main_socket.sendall(bytes(json.dumps(data), encoding='utf-8'))
        logger.debug(f"[<--] Fetching response...")
        resp = self._main_socket.recv(ATOM_LENGTH)
        logger.debug(f"[*] Got {resp}.")
        if resp == READY_FOR_TRANSFERRING:
            self._aux_connection()
        else:
            raise ServerError(str(resp, encoding='utf-8'))
        logger.info(f'[*] Process of logging in done.')
        threading.Thread(target=background_socket_receiving,
                         args=(self._aux_socket,), daemon=True).start()

    def create_chat(self, chat_name, members):
        logger.info(f"[*] Starting process of chat creating...")
        logger.debug(f"[-->] Sending {CREATE_CHAT} to the main server.")
        self._main_socket.sendall(CREATE_CHAT)
        logger.debug(f"[<--] Fetching response from the main server...")
        resp = self._main_socket.recv(ATOM_LENGTH)
        logger.debug(f"[*] Got: {resp}.")
        if resp != READY_FOR_TRANSFERRING:
            raise ServerError(resp)

        data = pickle.dumps(members)
        metadata = JSON_CREATE_CHAT_FORMAT.copy()
        metadata[NAME] = chat_name
        metadata[CONTENT_TYPE] = CHAT_MEMBERS
        metadata[CONTENT_SIZE] = len(data)
        logger.debug(f"[-->] Sending {metadata} to the main server...")
        self._main_socket.sendall(bytes(json.dumps(metadata), encoding='utf-8'))

        logger.debug(f"[<--] Fetching response from the main server...")
        resp = self._main_socket.recv(ATOM_LENGTH)
        if resp != READY_FOR_TRANSFERRING:
            raise ServerError(resp)
        logger.debug(f"[-->] Sending all the members to the server...")
        self._main_socket.sendall(data)
        logger.info(f"[*] Process of chat creating is done")

    def open_chat(self):
        pass

    def find_chat(self, user_name):
        pass

    def start(self):
        logger.info("[*] Creating main connection...")
        self._main_socket.connect((MAIN_SERVER_HOST, MAIN_SERVER_PORT))
        self.log_in(f'test18', "test_password")

        # self.create_chat('test_chat', [])
        while True:
            print(background_queue.get())


_main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
_aux_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client = ConnectionManager(_main_socket, _aux_socket)
