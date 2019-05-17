# -*- coding: utf-8 -*-
#加密解密
import binascii
import hashlib
class enc(object):
    def __init__(self):
        self.key='' #密码
        self.original='' #原文
        self.ciphertext = '' #密文
        self.mkey=''
    def encrypt(self):
        self.mkey = hashlib.sha256 (self.key).hexdigest ()
        lkey=len(self.mkey)
        secret=''
        num=0
        for each in self.original:
            if num>=lkey:
                num=num%lkey
            secret+= chr( ord(each)^ord(self.mkey[num]) )
            num+=1
        self.ciphertext=binascii.b2a_base64(secret)
    def decrypt(self):
        self.mkey = hashlib.sha256 (self.key).hexdigest ()
        tips = binascii.a2b_base64(self.ciphertext)
        lkey=len(self.mkey)
        secret=''
        num=0
        for each in tips:
            if num>=lkey:
                num=num%lkey
            secret+= chr( ord(each)^ord(self.mkey[num]) )
            num+=1
        self.original= secret