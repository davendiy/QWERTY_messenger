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

lock = threading.RLock()

background_queue = Queue()


class ServerError(Exception):
    pass


def background_socket_receiving(client_aux_socket):
    logger.info(f"[*] Starting of background receiving...")
    logger.debug(f"[-->] Sending {READY_FOR_TRANSFERRING} to aux server...")
    # client_aux_socket.sendall(READY_FOR_TRANSFERRING)

    while True:
        try:
            logger.debug(f"[<--] Fetching {READY_FOR_TRANSFERRING} from aux server...")
            resp = client_aux_socket.recv(ATOM_LENGTH)
            if not resp:
                time.sleep(1)
                continue
            elif resp != READY_FOR_TRANSFERRING:
                logger.error(f'[*] Got {resp} from aux server.')
                continue
            client_aux_socket.sendall(READY_FOR_TRANSFERRING)
            logger.debug(f"[<--] Fetching json from aux server...")
            resp = client_aux_socket.recv(ATOM_LENGTH)
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
            logger.debug(f'[-->] Sending {READY_FOR_TRANSFERRING} to the aux server...')
            client_aux_socket.sendall(READY_FOR_TRANSFERRING)
            res_data = b''
            logger.debug(f"[<--] Fetching {content_size} bytes from aux server...")
            for _ in range(0, content_size, CHUNK):
                res_data += client_aux_socket.recv(CHUNK)
            done = len(res_data)
            if (content_size - done) > 0:
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


def background_printer():
    while True:
        tmp = background_queue.get()
        with lock:
            print(tmp)

class ConnectionManager:


    def __init__(self, main_socket: socket.socket, aux_socket: socket.socket):
        self._main_socket = main_socket
        self._aux_socket = aux_socket
        self._logged_in = False
        self._logged_name = ""
        self._in_chat = None

        self._connected = False
        self._aux_connected = False
        self._current_messages = []
        self._current_chats = []
        self._current_chat_members = []

        self._user_chats = None

    def background_worker(self):
        while True:
            content_type, chat_name, value = background_queue.get()
            logger.debug(f"[*] Got from queue: {content_type}, {chat_name}, {value}.")
            if content_type == NEW_MESSAGE:
                with lock:
                    self._current_messages.append(value)
            elif content_type == CHATS_LIST:
                with lock:
                    self._current_chats = value
            elif content_type == CHAT_MEMBERS:
                with lock:
                    self._current_chat_members = value
            elif content_type == CHAT_MESSAGES:
                with lock:
                    self._current_messages = value
            elif content_type == NEW_USER:
                with lock:
                    self._current_chat_members.add(value)
            else:
                logger.error(f"Unknown type from queue: {content_type}.")

    def register(self, user_name, password):
        assert not self._logged_in
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
        self._logged_in = True
        self._logged_name = user_name
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
        resp = self._aux_socket.recv(ATOM_LENGTH)

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
        assert not self._logged_in
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
        self._logged_in = True
        self._logged_name = user_name
        logger.info(f'[*] Process of logging in done.')
        threading.Thread(target=background_socket_receiving,
                         args=(self._aux_socket,), daemon=True).start()

    def create_chat(self, chat_name, members):
        assert self._logged_in
        assert self._in_chat is None
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
        self._in_chat = chat_name

    def open_chat(self, chat: Chat):
        assert self._logged_in
        assert self._in_chat is None
        logger.info(f"[*] Starting process of opening {chat}...")
        logger.debug(f"[-->] Sending {OPEN_CHAT} to the main server.")
        self._main_socket.sendall(OPEN_CHAT)
        logger.debug(f"[<--] Fetching response from the main server...")
        resp = self._main_socket.recv(ATOM_LENGTH)
        logger.debug(f"[*] Got: {resp}.")
        if resp != READY_FOR_TRANSFERRING:
            raise ServerError(resp)

        data = JSON_OPEN_CHAT_FORMAT.copy()
        data[NAME] = chat.name
        data[CONTENT_TYPE] = CHAT
        logger.debug(f'[*] Sending {data} to the main server...')
        self._main_socket.sendall(bytes(json.dumps(data), encoding='utf-8'))
        resp = self._main_socket.recv(ATOM_LENGTH)
        if resp != READY_FOR_TRANSFERRING:
            raise ServerError(resp)
        self._in_chat = chat.name

    def exit_chat(self):
        assert self._logged_in
        assert self._in_chat
        self._main_socket.sendall(EXIT_FROM_CHAT)
        resp = self._main_socket.recv(ATOM_LENGTH)
        if resp != READY_FOR_TRANSFERRING:
            raise ServerError(resp)
        self._in_chat = None
        self._current_messages = []
        self._current_chat_members = set()

    def message(self, message: Message):
        assert self._logged_in
        assert self._in_chat
        self._main_socket.sendall(MESSAGE)
        resp = self._main_socket.recv(ATOM_LENGTH)
        if resp != READY_FOR_TRANSFERRING:
            raise ServerError(resp)
        self._confirm_server()
        content = message.content.encode('utf-8')
        metadata = JSON_MESSAGE_TEMPLATE.copy()
        metadata[CONTENT_TYPE] = message.content_type
        metadata[CONTENT_SIZE] = len(content)
        self._main_socket.sendall(bytes(json.dumps(metadata), encoding='utf-8'))
        resp = self._main_socket.recv(ATOM_LENGTH)
        if resp != READY_FOR_TRANSFERRING:
            raise ServerError(resp)
        self._main_socket.sendall(content)

        resp = self._main_socket.recv(ATOM_LENGTH)
        if resp != READY_FOR_TRANSFERRING:
            raise ServerError(resp)

    def find_chat(self, user_name):
        pass

    def start(self, username='test18', password='test_password', register=False):
        logger.info("[*] Creating main connection...")
        self._main_socket.connect((MAIN_SERVER_HOST, MAIN_SERVER_PORT))
        if register:
            self.register(username, password)
        else:
            self.log_in(username, password)
        threading.Thread(target=self.background_worker, daemon=True).start()
        time.sleep(2)
        while True:
            # time.sleep(2)
            command = input("Please, enter the command:\n--> ")
            if command == 'open chat':
                with lock:
                    name = input("Please, enter the chat name:\n--> ")
                self.open_chat(Chat(name, '', ''))
            elif command == 'create chat':
                with lock:
                    name = input("Please, enter the name of new chat:\n--> ")
                self.create_chat(name, [])
            elif command == 'members':
                with lock:
                    for row in self._current_chat_members:
                        print(row)
            elif command == 'exit':
                if self._in_chat:
                    self.exit_chat()
                else:
                    exit(0)
            elif command == 'message':
                with lock:
                    text = input("Text:\n")
                self.message(Message(self._logged_name, '', '', TEXT, text))
            elif command == "status":
                with lock:
                    print(f"Logged as {self._logged_name}, \n"
                          f"Opened chat: {self._in_chat}, \n")
            elif command == "chats":
                with lock:
                    for row in self._current_chats:
                        print(row)
            elif command == 'messages':
                with lock:
                    for row in self._current_messages:
                        print(row)
            else:
                print("Bad command")

_main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
_aux_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client = ConnectionManager(_main_socket, _aux_socket)
