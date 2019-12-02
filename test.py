#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 27.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

import socket
import threading


host = ""
port = 25000


def client_handler(client_socket, addr):
    print(f"connected from {addr}")
    client_socket.close()


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((host, port))

server.listen(5)

while True:
    client, address = server.accept()
    threading.Thread(target=client_handler, args=(client, address), daemon=True).start()
