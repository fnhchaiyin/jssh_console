# -*- coding: utf-8 -*-  
import pexpect
class server(object):
    def __init__(self,name='',ip = '',port = '',username = '',password = '',susername='',spassword='',comment=''):
        self.name=name
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.susername = susername
        self.spassword = spassword
        self.comment=comment
        self.send_file_status = 'false'
        self.get_file_status = 'false'
        self.result = ''
        self.err = ''
        self.connect_status=False
    def connect(self):
        if not self.connect_status:
            try:
                self.host=pexpect.spawn("ssh "+self.username+"@"+self.ip+' -p '+self.port)
                ex=self.host.expect(['(.*?)[>|#|$]','[P|p]assword:','(.*?)yes/no(.*?)'])
                if ex == 0:
                    self.connect_status = True
                elif ex == 1:
                    self.host.sendline(self.password)
                    if not self.host.expect('(.*?)[>|#|$]'):
                        self.connect_status=True
                elif ex==2:
                    self.host.sendline('yes')
                    self.host.sendline (self.password)
                    if not self.host.expect ('(.*?)[>|#|$]'):
                        self.connect_status = True
                else:
                    self.err='Login Failed!'
                if self.connect_status:
                    self.host.sendline('unset TMOUT')
                if self.susername:
                    self.host.sendline("LANG=;su - " + self.susername)
                    if not self.host.expect('[P|p]assword:'):
                        self.host.sendline(self.spassword)
                        if self.host.expect('(.*?)#'):
                            self.err='Change to super user failed!'
                        else:
                            self.host.sendline('unset TMOUT')
            except Exception as e:
                self.err=e
                self.err+=self.host.read_nonblocking (size=512, timeout=0.3)
    def exec_cmd(self,cmd=''):
        if self.connect_status:
            self.host.sendline(cmd)
            self.get_result()
        else:
            err = 'Not connected!\n'
            self.err = self.err + err
    def get_result(self):
        if self.connect_status:
            while True:
                if not self.host.isalive():
                    self.connect_status=False
                try:
                    self.result+=self.host.read_nonblocking(size=512,timeout=0.3)
                except:
                    break
    def FileTransfer(self,lo_path='',re_path='',FileSend = 0):
        if FileSend==1:
            self.filetransfer = pexpect.spawn ("scp -P "+self.port+' -r '+lo_path+' '+self.username+'@'+self.ip+':'+re_path)
        if FileSend==0:
            self.filetransfer = pexpect.spawn ("scp -P "+self.port+' -r '+self.username+'@'+self.ip+':'+re_path+' '+lo_path)
        ex = self.filetransfer.expect (['[P|p]assword:', '(.*?)yes/no(.*?)'])
        if ex == 0:
            self.filetransfer.sendline (self.password)
        elif ex == 1:
            self.filetransfer.sendline ('yes')
            self.filetransfer.sendline (self.password)
        else:
            self.err = 'file transfer failed!'
            self.filetransfer.close()
            return
        try:
            ex = self.filetransfer.expect (['(.*?)Permission denied','(.*?)No such file or directory'],timeout=1)
        except:
            ex=-1
        if ex == 0:
            self.err='Permission denied'
        elif ex == 1:
            self.err='No such file or directory'
    def close(self):
        if self.connect_status:
            self.host.close()
            self.connect_status=False
    def clear(self):
        self.send_file_status = 'false'
        self.get_file_status = 'false'
        self.result = ''
        self.err = ''
    def __str__(self):
        r=''
        if not self.connect_status:
            r+= '%s:%s\t\t\033[41;37mnot connected\033[0m' % (self.ip,self.comment)
        else:
            r+= '%s:%s\t\tconnected' % (self.ip,self.comment)
        return r
    def __del__(self):
        if self.connect_status:
            self.host.close()