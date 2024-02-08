import os
import re
from django.conf import settings
import json
import base64
from Cryptodome.Cipher import AES

def core_encrypt(string_to_encrypt):
    try:    
        key = settings.SECRET_KEY[:16]
        key = key.encode("utf-8")

        key = key.ljust(16, b'\x00')
        cipher = AES.new(key, AES.MODE_EAX)

        data = string_to_encrypt.encode("utf-8")

        ciphertext, tag = cipher.encrypt_and_digest(data)

        combined_data = cipher.nonce + tag + ciphertext

        encrypted_string = base64.b64encode(combined_data).decode("utf-8")
        return encrypted_string
    except Exception:
        return string_to_encrypt


def core_decrypt(encrypted_string):
    try:
        combined_data = base64.b64decode(encrypted_string)
        nonce = bytes(combined_data[:16])
        tag = combined_data[16:32]
        ciphertext = combined_data[32:]
        
        key = settings.SECRET_KEY[:16]
        key = key.encode("utf-8")

        key = key.ljust(16, b'\x00')
        cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)

        decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)

        decrypted_string = decrypted_data.decode("utf-8")
        return decrypted_string
    except Exception:
        return encrypted_string

def format(string,pattern):  # pragma: no cover
    if string:
        return f'{string[1:]}.xxjhaskjdhka?????klajslkdx.{string[:-1]}'

def format_longtext(string):  # pragma: no cover
    if string:
        return f'{string[3:3]}.xxx.{string[:-3]}'
    
def format_email(string):  # pragma: no cover
    return string