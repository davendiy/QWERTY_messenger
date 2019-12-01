#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 30.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

from Crypto.PublicKey import RSA
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import bcrypt, bcrypt_check
from base64 import b64encode

from .constants.app_constants import RSA_PRIVATE_KEY_PATH, RSA_PUBLIC_KEY_PATH

RSA_KEY = None
RSA_SIGNER = None

passphrase = "ThE s3Cre1 pa$$w0rd 4 RSA."


def generate_keys():

    global RSA_KEY
    global RSA_SIGNER

    RSA_KEY = RSA.generate(2048)
    encrypted_key = RSA_KEY.export_key(passphrase=passphrase, pkcs=8,
                                       protection="scryptAndAES128-CBC")
    with open(RSA_PRIVATE_KEY_PATH, 'wb') as file:
        file.write(encrypted_key)

    with open(RSA_PUBLIC_KEY_PATH, 'wb') as file:
        file.write(RSA_KEY.publickey().export_key())

    RSA_SIGNER = PKCS115_SigScheme(RSA_KEY)


def read_keys():
    global RSA_KEY, RSA_SIGNER
    with open(RSA_PRIVATE_KEY_PATH, 'rb') as file:
        RSA_KEY = RSA.import_key(file.read(), passphrase)


def sign_message(message):
    tmp = SHA256.new(message)
    signature = RSA_SIGNER.sign(tmp)
    return signature


# noinspection PyTypeChecker
def verify(message, signature):
    tmp = SHA256.new(message)
    with open(RSA_PUBLIC_KEY_PATH, 'rb') as file:
        key = RSA.import_key(file.read())
    signer = PKCS115_SigScheme(key)
    signer.verify(tmp, signature)


def hash_password(password):
    b64pwd = b64encode(SHA256.new(password).digest())
    bcrypt_hash = bcrypt(b64pwd, 12)
    return bcrypt_hash


def check_password(user_password, password_hash):
    b64pwd = b64encode(SHA256.new(user_password).digest())
    bcrypt_check(b64pwd, password_hash)


if RSA_KEY is None:
    read_keys()
