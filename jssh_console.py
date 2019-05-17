# -*- coding: utf-8 -*-
import re
import readline
from threading import Thread,Semaphore
from datetime import datetime
import gl
import os
from server import *
from progressbar import *
import json
import jenc
import getpass
from jgroup import jgroup
class Completer(object):
    def _listdir(self, root):
        "List directory 'root' appending the path separator to subdirs."
        res = []
        for name in os.listdir(root):
            path = os.path.join(root, name)
            if os.path.isdir(path):
                name += os.sep
            res.append(name)
        return res
    def _complete_path(self, path=None):
        "Perform completion of filesystem path."
        if not path:
            return self._listdir('.')
        dirname, rest = os.path.split(path)
        if dirname:
            tmp = dirname
        else:
            tmp = '.'
        res = [os.path.join(dirname, p) for p in self._listdir(tmp) if p.startswith(rest)]
        # more than one match, or single match which does not exist (typo)
        if len(res) > 1 or not os.path.exists(path):
            return res
        # resolved to a single directory, so return list of files below it
        if os.path.isdir(path):
            return [os.path.join(path, p) for p in self._listdir(path)]
        # exact file match terminates this completion
        return [path + ' ']
    def complete_group_import(self, args):
        if not args:
            return self._complete_path('.')
        # treat the last arg as a path and complete it
        return self._complete_path(args[-1])
    def complete_groups(self, args):
        if not args:
            return [c for c in gl.jssh['groups'].keys()]
        else:
            return [c+' ' for c in gl.jssh['groups'].keys() if c.startswith(args[-1])]
    def complete_join_hosts(self, args):
        if not args:
            return [c for c in gl.jssh['services'].keys()]
        else:
            return [c+' ' for c in gl.jssh['services'].keys() if c.startswith(args[-1]) and c not in gl.jssh['current_services']]
    def complete_remove_hosts(self, args):
        if not args:
            return [c for c in gl.jssh['current_services']]
        else:
            return [c+' ' for c in gl.jssh['current_services'] if c.startswith(args[-1])]
    def complete_new(self, args):
        return [c+' ' for c in new_cmd if c.startswith(args[-1])]
    # def complete_imp(self, args):
    #     if not args:
    #         return [c for c in imp_cmd]
    #     elif args[0] in imp_cmd:
    #         return self._complete_path(args[-1])
    #     else:
    #         return [c+' ' for c in imp_cmd if c.startswith(args[-1])]
    def complete_exp_log(self, args):
        return self._complete_path (args[-1])
    def complete_send_file(self, args):
        return self._complete_path (args[-1])
    def complete_get_file(self, args):
        return self._complete_path (args[-1])
    def complete_jset(self, args):
        if not args:
            return [c for c in set_cmd]
        else:
            return [c+' ' for c in set_cmd if c.startswith(args[-1])]
    def complete_delete(self, args):
        if not args:
            return [c for c in delete_cmd]
        elif args[0]=='hosts':
            return [c+' ' for c in gl.jssh['services'].keys () if c.startswith(args[-1])]
        elif args[0]=='groups':
            return [c+' ' for c in gl.jssh['groups'].keys () if c.startswith(args[-1])]
        else:
            return [c+' ' for c in delete_cmd if c.startswith(args[-1])]
    def complete_show(self, args):
        if not args:
            return [c for c in show_cmd]
        elif args[0] in ['hosts','result']:
            return [c+' ' for c in gl.jssh['services'].keys () if c.startswith(args[-1])]
        elif args[0]=='groups':
            return [c+' ' for c in gl.jssh['groups'].keys () if c.startswith(args[-1])]
        else:
            return [c+' ' for c in show_cmd if c.startswith(args[-1])]
    def complete_exec_cmd(self, args):
        if not args:
            return [c for c in gl.jssh['history'][-100:]]
        else:
            return [c + ' ' for c in gl.jssh['history'][-100:] if args[-1] in c.split ()]
    def complete_host(self, args):
        if not args:
            return [c for c in host_cmd]
        elif args[0] in host_cmd:
            return [c+' ' for c in gl.jssh['services'].keys() if c.startswith(args[-1])]
        else:
            return [c+' ' for c in host_cmd if c.startswith(args[-1])]
    def complete_comment(self, args):
        if not args:
            return [c for c in comment_cmd]
        elif args[0] == 'host':
            return [c+' ' for c in gl.jssh['services'].keys() if c.startswith(args[-1])]
        elif args[0] == 'group':
            return [c + ' ' for c in gl.jssh['groups'].keys () if c.startswith (args[-1])]
        else:
            return [c+' ' for c in comment_cmd if c.startswith(args[-1])]
    def complete(self, text, state):
        "Generic readline completion entry point."
        buffer = readline.get_line_buffer()
        line = readline.get_line_buffer().split()
        # show all commands
        if not line:
            return [c + ' ' for c in COMMANDS][state]
        # account for last argument ending in a space
        RE_SPACE = re.compile('.*\s+$', re.M)
        if RE_SPACE.match(buffer):
            line.append('')
        # resolve command to the implementation function
        cmd = line[0].strip()
        if cmd in COMMANDS:
            impl = getattr(self, 'complete_%s' % cmd)
            args = line[1:]
            if args:
                return (impl(args) + [None])[state]
            return [cmd + ' '][state]
        results = [c + ' ' for c in COMMANDS if c.startswith(cmd)] + [None]
        return results[state]

def help(ri):
    sys.stdout.write('''
        add host:
            add a new host :
                new host 192.168.0.3 22 user pass root rootpwd
                new host 192.168.0.4 22 user pass
            add hosts from file:
                imp host list_file
                list_file:
                    192.168.2.3 22 user password root superpasswd
                    192.168.2.4 22 user password
        add new group:
            new groups groupa groupb groupc
        switch groups:
            groups groupname
        join hosts to currentgroups:
            join_hosts 192.168.2.3 192.168.2.4
        remove hosts from currentgroups:
            remove_hosts 192.168.2.3 192.168.2.4
        add a new group and join hosts from file:
            imp group group_file
                group_file:
                    192.168.2.3
                    192.168.2.4
        connect to the current hosts:
            connect
        diconnect from the current hosts:
            disconnect
        exec_cmd:
            exec_cmd df -h
        get_file:
            Get a file from hosts
        send_file:
            Send a file to hosts
        host:
			operate one host
				like: host 192.168.2.3
        show:
            Display state
            show err:Display the last error message
            show result:Display the last result
            show history_cmd:Display history command
            show hosts_status:show hosts status
        set thread numbers:
            jset threads_num 10 
        set login password:
            jset password
    \n''')
def connect(ri):
    if gl.jssh['current_services']:
        semaphore= Semaphore(gl.jssh['thread_num'])
        def connect_do(i):
            if semaphore.acquire():
                i.connect()
            semaphore.release()
        save_log('Connecting,Please wait ...')
        threads = []
        for n in gl.jssh['current_services']:
            t = Thread(target=connect_do,args=(gl.jssh['services'][n],))
            t.start()
            threads.append(t)
        bar = ProgressBar(total=len(threads))
        bar.show()
        while True:
            for a in threads:
                if not a.isAlive():
                    bar.move()
                    bar.show()
                    threads.remove(a)
            if not threads:
                for n in gl.jssh['current_services']:
                    if not gl.jssh['services'][n].connect_status:
                        save_log(log="--------------------------------------%s" % n)
                        save_log (log=gl.jssh['services'][n].err)
                save_log ('Connect completed')
                break
def disconnect(ri):
    semaphore= Semaphore(gl.jssh['thread_num'])
    def disconnect_do(i):
        if semaphore.acquire():
            i.close()
        semaphore.release()
    threads = []
    for n in gl.jssh['current_services']:
        t = Thread(target=disconnect_do,args=(gl.jssh['services'][n],))
        t.start()
        threads.append(t)
    for a in threads:
        a.join()
def exec_cmd(ri):
    semaphore= Semaphore(gl.jssh['thread_num'])
    def gexe_do(i,cmd):
        if semaphore.acquire():
            i.exec_cmd(cmd)
        semaphore.release()
    for i in ri[1:]:
        if i in ['rm','mv','reboot','shutdown','sed','dd','chmod','chown']:
            com=raw_input('Dangerous operation,input "Yes" to continue:')
            if com !='Yes':
                save_log('canceled')
                return
    gcmd = ' '.join(ri[1:])
    if gcmd:
        gl.jssh['history'].append (gcmd)
        gl.jssh['history'].reverse()
        del gl.jssh['history'][1000:]
        gl.jssh['history'].reverse ()
        threads = []
        for n in gl.jssh['current_services']:
            gl.jssh['services'][n].err=''
            gl.jssh['services'][n].result=''
            a = Thread(target=gexe_do,kwargs={'i':gl.jssh['services'][n],'cmd':gcmd})
            a.start()
            threads.append(a)
        bar = ProgressBar(total=len(threads))
        host_count=len(threads)
        bar.show()
        while True:
                for a in threads:
                    if not a.isAlive():
                        bar.move()
                        bar.show()
                        threads.remove(a)
                if not threads:
                    for n in gl.jssh['current_services']:
                        save_log (log="--------------------------------------%s" % n)
                        if gl.jssh['services'][n].result:
                            save_log (log=gl.jssh['services'][n].result)
                        if gl.jssh['services'][n].err:
                            save_log (log=gl.jssh['services'][n].err)
                    break
        err_count=0
        resoult_count=0
        for n in gl.jssh['current_services']:
            if gl.jssh['services'][n].err:
                err_count+=1
            if gl.jssh['services'][n].result:
                resoult_count+=1
        save_log("######################all the servers finished execcmd:%s (%s)" % (gcmd,datetime.now()))
        save_log("host:%s\nerr:%s\nresoult:%s" %(host_count,err_count,resoult_count))
    else:
        save_log("Entry a command to exec!")
def get_result(ri):
    semaphore = Semaphore (gl.jssh['thread_num'])
    threads=[]
    def do(i):
        if semaphore.acquire():
            i.get_result ()
        semaphore.release ()
    for n in gl.jssh['current_services']:
        a = Thread(target=do,kwargs={'i':gl.jssh['services'][n]})
        a.start ()
        threads.append (a)
    bar = ProgressBar (total=len (threads))
    bar.show ()
    while True:
        for a in threads:
            if not a.isAlive ():
                bar.move ()
                bar.show ()
                threads.remove (a)
        if not threads:
            for n in gl.jssh['current_services']:
                save_log (log="--------------------------------------%s" % n)
                if gl.jssh['services'][n].result:
                    save_log (log=gl.jssh['services'][n].result)
                if gl.jssh['services'][n].err:
                    save_log (log=gl.jssh['services'][n].err)
            break
def get_file(ri):
    try:
        re_path = ri[1]
        lo_path = ri[2]
    except:
        save_log('usage:get_file remote_path local_path')
        return
    semaphore = Semaphore (gl.jssh['thread_num'])
    threads=[]
    def do(i):
        if semaphore.acquire():
            lopath = os.path.join (lo_path, i.ip)
            if not os.path.exists(lopath):
                os.mkdir(lopath)
            i.FileTransfer (lo_path=lopath,re_path=re_path,FileSend = 0)
        semaphore.release ()
    for n in gl.jssh['current_services']:
        a = Thread(target=do,kwargs={'i':gl.jssh['services'][n]})
        a.start ()
        threads.append (a)
    bar = ProgressBar (total=len (threads))
    bar.show ()
    while True:
        for a in threads:
            if not a.isAlive ():
                bar.move ()
                bar.show ()
                threads.remove (a)
        if not threads:
            for n in gl.jssh['current_services']:
                save_log (log="--------------------------------------%s" % n)
                if gl.jssh['services'][n].err:
                    save_log (log=gl.jssh['services'][n].err)
            break
def send_file(ri):
    try:
        re_path = ri[2]
        lo_path = ri[1]
    except:
        save_log('usage:send_file local_path remote_path')
        return
    semaphore = Semaphore (gl.jssh['thread_num'])
    threads=[]
    def do(i):
        if semaphore.acquire():
            i.FileTransfer (lo_path=lo_path, re_path=re_path, FileSend=1)
        semaphore.release ()
    for n in gl.jssh['current_services']:
        a = Thread(target=do,kwargs={'i':gl.jssh['services'][n]})
        a.start ()
        threads.append (a)
    bar = ProgressBar (total=len (threads))
    bar.show ()
    while True:
        for a in threads:
            if not a.isAlive ():
                bar.move ()
                bar.show ()
                threads.remove (a)
        if not threads:
            for n in gl.jssh['current_services']:
                save_log (log="--------------------------------------%s" % n)
                if gl.jssh['services'][n].err:
                    save_log (log=gl.jssh['services'][n].err)
            break
def clear_result(ri):
    for n in gl.jssh['current_services']:
        gl.jssh['services'][n].result=''
        gl.jssh['services'][n].err=''
def save_log(log=''):
    print log
    gl.jssh['log'].append(log)
# def imp(ri):
#     def hosts(arg):
#         if arg:
#             try:
#                 server_list = open(arg[0])
#             except:
#                 server_list=None
#                 save_log("open file failed !")
#                 return
#             if server_list:
#                 for (num, value) in enumerate(server_list):
#                     if len(value) > 4 and not value.startswith('#'):
#                         try:
#                             ip_addr = value.split()[0]
#                         except:
#                             save_log('get ip addr failed!')
#                             continue
#                         if gl.jssh['services'].has_key(ip_addr):
#                             err='ERROR,At line %s:Duplicate ipaddr %s' % (num,ip_addr)
#                             save_log(log=err)
#                             continue
#                         try:
#                             port = value.split()[1]
#                             username = value.split()[2]
#                         except:
#                             continue
#                         try:
#                             password = value.split()[3]
#                         except IndexError:
#                             password=''
#                         try:
#                             susername=value.split()[4]
#                             spassword=value.split()[5]
#                         except:
#                             susername=''
#                             spassword=''
#                         new(['new','host',ip_addr,port,username,password,susername,spassword])
#                 server_list.close()
#     def group(arg):
#         if arg:
#             try:
#                 file = arg[0]
#             except Exception,e:
#                 save_log("Give the group file!")
#             if file:
#                 group_name=os.path.split(file)[-1]
#                 try:
#                     server_list = open(file)
#                 except:
#                     server_list=None
#                     save_log("open file failed !")
#                     return
#                 new(['new','groups',group_name])
#                 groups(['groups',group_name])
#                 for i in server_list:
#                     ip=i.split()[0]
#                     join_hosts(['join_host',ip])
#                 server_list.close()
#     try:
#         cmd=ri[1]
#     except:
#         cmd=''
#     try:
#         arg=ri[2:]
#     except:
#         arg=''
#     if cmd in imp_cmd:
#         eval(cmd)(arg)
#     else:
#         save_log("\033[41;37mWrong option!\033[0m")
def new(ri):
    def host(arg):
       try:
            ip=arg[0]
            port=arg[1]
            username=arg[2]
            password=arg[3]
            try:
                susername=arg[4]
                spassword=arg[5]
            except:
                susername=''
                spassword=''
            gl.jssh['services'][ip]=server(ip=ip,port=port,username=username,password=password,susername=susername,spassword=spassword)
            save_log('add host %s success!' % ip)
       except:
            save_log('add host failed! eg: 192.168.3.23 22 user password root rootpassword')
    def groups(arg):
        if arg:
            if not gl.jssh['current_groups']:
                gl.jssh['current_groups']=['root']
            for group in arg:
                if  gl.jssh['groups'].has_key(group):
                    save_log("\033[41;37mgroup %s exist!\033[0m" % group)
                    continue
                gl.jssh['groups'][group]=jgroup(name=group,child_groups=[], hosts = [],comment='')
                gl.jssh['groups'][gl.jssh['current_groups'][0]].child_groups.append(group)
                save_log('add group %s success!' % group)
    try:
        cmd=ri[1]
    except:
        cmd=''
    try:
        arg=ri[2:]
    except:
        arg=''
    if cmd in new_cmd:
        eval(cmd)(arg)
    else:
        save_log("\033[41;37mWrong option!\033[0m")
def delete(ri):
    def hosts(arg):
        if arg:
            for ip in arg:
                if gl.jssh['services'].has_key(ip):
                    del gl.jssh['services'][ip]
                    fresh_current_host()
                    save_log('delete host %s success!' % ip)
                else:
                    save_log('\033[41;37mno such host!\033[0m')
    def groups(arg):
        if arg:
            for group in arg:
                if gl.jssh['groups'].has_key(group):
                    if group in gl.jssh['current_groups']:
                        gl.jssh['current_groups'].remove(group)
                    for i in gl.jssh['groups'].keys():
                        if group in gl.jssh['groups'][i].child_groups:
                            gl.jssh['groups'][i].child_groups.remove(group)
                    del gl.jssh['groups'][group]
                    fresh_current_host()
                    save_log('success!')
                else:
                    save_log('\033[41;37mno such group!\033[0m')
    try:
        cmd=ri[1]
    except:
        cmd=''
    try:
        arg=ri[2:]
    except:
        arg=''
    if cmd in delete_cmd:
        eval(cmd)(arg)
    else:
        save_log("\033[41;37mWrong option!\033[0m")
def show(ri):
    def err(arg):
        for n in gl.jssh['current_services']:
            if gl.jssh['services'][n].err:
                save_log( "--------------------------------------%s" % n)
                save_log(gl.jssh['services'][n].err)
        save_log('END')
    def result(arg):
        if arg:
            for n in arg:
                if gl.jssh['services'][n].result:
                    save_log( "--------------------------------------%s" % n)
                    save_log(gl.jssh['services'][n].result)
            save_log('END')
        else:
            for n in gl.jssh['current_services']:
                if gl.jssh['services'][n].result:
                    save_log( "--------------------------------------%s" % n)
                    save_log(gl.jssh['services'][n].result)
            save_log('END')
    def log(arg):
        for i in gl.jssh['log']:
            print(i)
    def thread_num(arg):
        save_log("thread_num = %s" % gl.jssh['thread_num'])
    def history(arg):
        for i in gl.jssh['history']:
            save_log(i)
    def status(arg):
        for host in gl.jssh['current_services']:
            save_log(gl.jssh['services'][host])
        save_log ('total:%s' % gl.jssh['current_services'].__len__())
    def hosts(arg):
        if arg:
            for host in arg:
                if host in gl.jssh['services'].keys():
                    save_log (gl.jssh['services'][host])
                else:
                    save_log ("\033[41;37mNo such host!\033[0m")
        else:
            for host in gl.jssh['services']:
                save_log (gl.jssh['services'][host])
            save_log ('total:%s' % gl.jssh['services'].__len__ ())
    def groups(arg):
        if arg:
            for i in arg:
                if i in gl.jssh['groups'].keys():
                    save_log(gl.jssh['groups'][i])
                else:
                    save_log("\033[41;37mNo such group!\033[0m")
        else:
             save_log(gl.jssh['groups']['root'])
    try:
        option=ri[1]
        arg=ri[2:]
    except:
        option=''
    if option in show_cmd:
        eval(option)(arg)
    else:
        save_log("\033[41;37mWrong option!\033[0m")
def groups(ri):
    groups = ri[1:]
    groups = list(set(groups))
    for group in groups:
        if group not in gl.jssh['groups'].keys ():
            save_log("\033[41;37mNo such group!\033[0m")
            return
    gl.jssh['current_groups']=groups
    fresh_current_host()
    save_log("%s host selected" % len(gl.jssh['current_services']))
def fresh_current_host():
    servers=[]
    gl.jssh['current_services'] = []
    for group in gl.jssh['current_groups']:
        servers+=gl.jssh['groups'][group].get_child_hosts()
    servers=list(set(servers))
    for i in servers:
        if gl.jssh['services'].has_key(i):
            gl.jssh['current_services'].append(i)
def join_hosts(ri):
    if gl.jssh['current_groups']:
        hosts = ri[1:]
        for group in gl.jssh['current_groups']:
            for host in hosts:
                if host not in gl.jssh['services']:
                    save_log('the host %s not exist' % host)
                    continue
                if host in gl.jssh['groups'][group].hosts:
                    save_log('host %s is aready in group %s' % (host,group))
                else:
                    gl.jssh['groups'][group].hosts.append(host)
        fresh_current_host()
    else:
        save_log('select a group frist! eg: group group_name')
def remove_hosts(ri):
    if gl.jssh['current_groups']:
        hosts = ri[1:]
        for group in gl.jssh['current_groups']:
            for host in hosts:
                gl.jssh['groups'][group].hosts.remove(host)
        fresh_current_host()
    else:
        save_log('select a group frist! eg: group group_name')
def host(ri):
    def connect():
        gl.jssh['services'][ip].connect()
    def disconnect():
        gl.jssh['services'][ip].close()
    def info():
        save_log('ip=%s port=%s username=%s password=%s superuser=%s superpassword=%s' % (gl.jssh['services'][ip].ip,gl.jssh['services'][ip].port,gl.jssh['services'][ip].username,gl.jssh['services'][ip].password,gl.jssh['services'][ip].susername,gl.jssh['services'][ip].spassword))
    def console():
        save_log('back command:!back')
        while True:
            ra = raw_input ('\033[;32mjssh[%s]#\033[0m' % gl.prompt)
            if ra=='!back':
                break
            elif ra:
                gl.jssh['services'][ip].exec_cmd(ra)
                if gl.jssh['services'][ip].result:
                    save_log(gl.jssh['services'][ip].result)
                if gl.jssh['services'][ip].err:
                    save_log(gl.jssh['services'][ip].err)
                gl.jssh['services'][ip].result=''
                gl.jssh['services'][ip].err = ''
    try:
        cmd=ri[1]
    except:
        cmd=''
    if cmd in host_cmd:
        try:
            ip = ri[2]
        except:
            save_log ('\033[41;37mWrong option!\033[0m')
            return
        gl.prompt = ip
        if not gl.jssh['services'].has_key (ip):
            save_log ("\033[41;37mNo such host %s !\033[0m" % ip)
            return
        eval(cmd)()
    else:
        save_log("\033[41;37mWrong option!\033[0m")
def comment(ri):
    def group(name,com):
        if gl.jssh['groups'].has_key(name):
            gl.jssh['groups'][name].comment = com
            save_log('comment group %s : %s' %(name,com))
        else:
            save_log ("\033[41;37mNo such group %s !\033[0m" % name)
    def host(name,com):
        if gl.jssh['services'].has_key (name):
            gl.jssh['services'][name].comment=com
            save_log ('comment host %s : %s' % (name, com))
        else:
            save_log ("\033[41;37mNo such host %s !\033[0m" % name)
    try:
        cmd=ri[1]
    except:
        cmd=''
    if cmd in comment_cmd:
        try:
            name = ri[2]
            com = ''.join(ri[3:])
        except:
            com = ''
            return
        eval(cmd)(name,com)
    else:
        save_log("\033[41;37mWrong option!\033[0m")
def init_db():
    gl.jssh['log'] = []
    gl.jssh['history'] = []
    gl.jssh['groups'] = {'root':jgroup(name='root',child_groups=[], hosts = [],comment='')}
    gl.jssh['current_groups'] = ['root']
    gl.jssh['thread_num'] = 10
    gl.jssh['password'] = ''
    gl.jssh['services']={}
    gl.jssh['current_services']=[]
def jset(ri):
    def password(arg):
        password1 = getpass.getpass ("New password:")
        password2 = getpass.getpass ("Retpye new password:")
        if password1==password2:
            gl.jssh['password']=password2
            save_log ("Succesed!")
        else:
            save_log ("Change password failed!")
    def threads_num(arg):
        try:
            num=int(arg[0])
        except:
            save_log("\033[41;37mWrong option!\033[0m")
            return
        gl.jssh['thread_num']=int(arg[0])
    try:
        cmd=ri[1]
    except:
        cmd=''
    try:
        arg=ri[2:]
    except:
        arg=''
    if cmd in set_cmd:
        eval(cmd)(arg)
    else:
        save_log("\033[41;37mWrong option!\033[0m")
def get_password():
    is_login=False
    t = 3
    while t:
        password = getpass.getpass ("Please input your password:")
        enc.key=password
        enc.ciphertext = open(db_file).read()
        enc.decrypt()
        try:
            gl.jssh=json.loads(enc.original,object_hook=json_2_server)
            is_login=True
            break
        except:
            t-=1
            continue
    return is_login
def save(ri):
    enc.key=gl.jssh['password']
    enc.original=json.dumps(gl.jssh,default=server_2_json)
    enc.encrypt()
    f=open(db_file,'wb')
    f.write(enc.ciphertext)
    f.flush()
    f.close()
def clear_log(ri):
    gl.jssh['log']=[]
def exp_log(ri):
    file=open(ri[1],'wb')
    for i in gl.jssh['log']:
        file.write(i+'\n')
    file.close()
def server_2_json(d):
    if type(d)==type(server()):
        return {
            'ip': d.ip,
            'port': d.port,
            'username': d.username,
            'password': d.password,
            'susername': d.susername,
            'spassword': d.spassword,
            'comment' : d.comment
        }
    elif type(d)==type(jgroup()):
        return {
        'name':d.name,
        'child_groups':d.child_groups,
        'hosts':d.hosts,
        'comment':d.comment
    }
    else:
        return d
def json_2_server(d):
    if d.has_key('ip') and d.has_key('port') and d.has_key('username') and d.has_key('password') and d.has_key('susername') and d.has_key('spassword'):
        return server(ip=d['ip'], port=d['port'], username=d['username'], password=d['password'],susername=d['susername'], spassword=d['spassword'],comment=d['comment'])
    elif d.has_key('name') and d.has_key('child_groups') and d.has_key('hosts') and d.has_key('comment'):
        return jgroup(name=d['name'],child_groups=d['child_groups'],hosts=d['hosts'],comment=d['comment'])
    else:
        return d
if __name__=='__main__':
    reload (sys)
    sys.setdefaultencoding ('utf8')
    enc = jenc.enc ()
    COMMANDS = ['show','new','comment','delete','groups','join_hosts','remove_hosts','host','connect', 'exec_cmd','get_result','clear_result','get_file','send_file','disconnect','jset','clear_log','exp_log','save','quit','help']
    show_cmd=['status','history','thread_num','result','err','groups','hosts','log']
    new_cmd=['groups','host']
    # imp_cmd = ['group', 'hosts']
    delete_cmd=['groups','hosts']
    set_cmd=['password','threads_num']
    host_cmd=['connect','disconnect','console','info']
    comment_cmd=['group','host']
    is_login = False
    db_file=os.path.join(sys.path[0],'jssh_console.db')
    if not os.path.exists(db_file):
        init_db()
        is_login=True
    else:
        is_login=get_password()
    if is_login:
        comp = Completer()
        readline.set_completer_delims(' \t\n;')
        readline.parse_and_bind("tab: complete")
        readline.set_completer(comp.complete)
        gl.prompt=','.join(gl.jssh['current_groups'])
        while True:
            try:
                ri=raw_input('\033[;32mjssh[%s]#\033[0m' % gl.prompt)
                if ri:
                    gl.jssh['log'].append ('%s\tjssh_console[%s]#%s' % (datetime.now (),gl.prompt,ri))
                rc = ri.split (' ')
                ri=ri.split()
                if ri:
                    cmdstr=ri[0]
                    if cmdstr in COMMANDS:
                        if cmdstr=='quit':
                            disconnect(ri)
                            break
                        elif cmdstr=='exec_cmd':
                            exec_cmd(rc)
                        else:
                            eval(cmdstr)(ri)
                            gl.prompt = ','.join (gl.jssh['current_groups'])
                    else:
                        save_log('\033[41;37m Unnkown command! \033[0m')
            except (IOError,EOFError,KeyboardInterrupt),e:
                save_log (str(e))
        save('')
