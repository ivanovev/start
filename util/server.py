#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy

from inspect import getargspec
from socket import gethostbyaddr
from types import FunctionType

from .misc import app_srv, ping
from .cache import CachedDict
from .serial import query_serial, get_serials
from .version import get_version

import binascii, pickle
import os, subprocess, sys, time, urllib, pdb

acl_fname = 'acl.txt'

def start_process(pa, *args, echo=False):
    pr = pa.split() + list(args)
    if os.name == 'nt':
        if sys.argv[0].lower().find('.exe') == -1:
            pr.insert(0, 'python')
    else:
        if sys.argv[0].lower().find('.py') != -1:
            pr.insert(0, 'python3')
    if echo:
        print(' '.join(pr))
        pr.append('--echo')
    try:
        subprocess.Popen(pr)
        return 0
    except:
        return 1

class OutDevice():
    def __init__(self):
        self.output = ''
    def write(self, s):
        self.output += s

class MyServer(SimpleXMLRPCServer):
    def __init__(self, addr, extras, dfltbe='SAM7X'):
        SimpleXMLRPCServer.__init__(self, addr, MyHandler)
        self.src_ip = ''
        self.acl = ['*']
        self.echo = True
        self.idle = False
        self.verbose = True
        self.backends = set()
        self.register_function(self.alive, 'srv.alive')
        self.register_function(self.echo1, 'srv.echo')
        self.register_function(self.idle1, 'srv.idle')
        self.register_function(self.sleep, 'srv.sleep')
        self.register_function(self.verbose1, 'srv.verbose')
        self.register_function(self.stop_server, 'srv.stop')
        self.register_function(self.backend1, 'srv.backend')
        self.register_function(self.backends1, 'srv.backends')
        self.register_function(self.reload_acl, 'srv.reload_acl')
        self.register_function(self.start_process1, 'srv.start_process')
        self.register_function(get_version, 'srv.version')
        self.register_function(get_serials, 'srv.get_serials')
        self.register_function(query_serial, 'srv.query_serial')
        if extras == None: extras = {}
        self.extras = extras
        for k,v in extras.items():
            self.register_function(v, k)
            for k1 in ['spi', 'gpio', 'mdio', 'uart', 'telnet']:
                kk = k.split('.')
                if k1 in kk:
                    self.backends.add(kk[0])
        self.backend1(dfltbe)
        self.register_introspection_functions()
        self.allow_none = True
        self.logRequests = False

    def _dispatch(self, method, params):
        extras = self.extras.keys()
        if self.acl != None and method in extras:
            if '*' not in self.acl and self.src_ip not in self.acl:
                if self.verbose:
                    print('ACL error (%s)' % self.src_ip)
                return
        func = None
        if method not in self.funcs.keys():
            if self.verbose:
                print('Method lookup error (%s)' % method)
            return ''
        if self.idle and method in extras:
            self.verbose_msg(method, params, '0 (idle)')
            return '0'
        func = self.funcs[method]
        outdev = OutDevice()
        if not hasattr(func, 'stdout'):
            #sys.stdout = outdev
            pass
        try:
            result = func(*params)
            if result == None:
                print('result = None')
                result = ''
        except:
            print('Failed to call %s' % method, sys.exc_info())
            result = ''
        sys.stdout = sys.__stdout__
        if self.verbose:
            self.verbose_msg(method, params, result)
        if outdev.output != '':
            print(outdev.output, end='')
        return result

    def verbose_msg(self, method, params, result):
        max_msg_len = 79
        if self.verbose or (method == 'verbose' and len(params) == 1):
            m = ' '.join([str(self.src_ip), str(method), str(params)])
            if type(result) == str:
                rr = result.split()
                m = ' '.join([m, rr[0]])
                if len(m) > max_msg_len:
                    m = m[0:max_msg_len-3] + '...'
                else:
                    for i in range(1, len(rr)):
                        if len(m) + len(rr[i]) + 1 > max_msg_len:
                            m += '...'
                            break
                        m += ' ' + rr[i]
                print(m)
            else:
                print(m, result)

    def serve_forever(self):
        self.quit = 0
        self.reload_acl()
        while not self.quit:
            self.handle_request()

    @staticmethod
    def hexlify(s):
        b = pickle.dumps(s)
        h = binascii.hexlify(b)
        return str(h, 'ascii')

    @staticmethod
    def unhexlify(s):
        b = bytes(s, 'ascii')  
        uh = binascii.unhexlify(b)
        return pickle.loads(uh)

    def system_listMethods(self):
        """
        Вернуть список имён функций
        @return строка (имена функций через пробел)
        """
        ret = SimpleXMLRPCServer.system_listMethods(self)
        return ' '.join(ret)

    def system_methodSignature(self, method_name):
        """
        Вернуть сигнатуру вызова функции %method_name%
        @param method_name - имя функции
        @return строка (бинарное представление объекта)
        """
        if method_name not in self.funcs:
            return ''
        a = getargspec(self.funcs[method_name])
        return MyServer.hexlify(a)

    def system_methodHelp(self, method_name):
        """
        Вернуть __docstring__ функции %method_name%
        @param method_name - имя функции
        @return строка (бинарное представление unicode строки)
        """
        if method_name not in self.funcs:
            return ''
        ret = SimpleXMLRPCServer.system_methodHelp(self, method_name)
        return MyServer.hexlify(ret)

    def alive(self):
        """
        Функция для выяснения состояния сервера
        """
        return '1'

    def sleep(self, dt='3'):
        """
        time.sleep(dt)
        """
        print('sleep')
        time.sleep(int(dt))
        return dt

    def lfunc(self, attr, v):
        lret = lambda v: '1' if int(v) else '0'
        if not v:
            return lret(getattr(self, attr))
        try:
            setattr(self, attr, bool(int(v)))
            return lret(getattr(self, attr))
        except:
            pass

    def echo1(self, v=''):
        """
        Если echo == 1 выводить в консоль аргументы команд при запуске дочерних процессов
        @param v - 0, 1 или пустая строка
        """
        return self.lfunc('echo', v)

    def idle1(self, v=''):
        """
        Если idle == 1 выводить в консоли сервера сообщение f(...),
        саму функцию при этом не вызывать
        @param v - 0, 1 или пустая строка
        """
        return self.lfunc('idle', v)

    def verbose1(self, v=''):
        """
        Если verbose == 1 выводить в консоль сообщения вида f(...) при обращении к серверу
        @param v - 0, 1 или пустая строка
        """
        return self.lfunc('verbose', v)

    def backends1(self):
        """
        Вернуть список устройств, которые обеспечивают доступ к spi, gpio, uart...
        """
        ret = list(self.backends)
        ret.sort()
        return ' '.join(ret)

    def backend1(self, v=''):
        """
        Выбрать текущий набор функций для доступа к spi, gpio, uart...
        """
        if v in self.backends:
            kk = list(self.funcs.keys())
            for k in kk:
                if k.find('util') == 0:
                    self.funcs.pop(k)
            for k in kk:
                if k.find(v) == 0:
                    n = k.replace(v, 'util')
                    self.register_function(self.funcs[k], n)
            self.backend = v
            return v
        elif not v:
            if hasattr(self, 'backend'):
                return self.backend
        return ''

    def stop_server(self):
        """
        Остановить сервер
        """
        print('server shutdown')
        self.wait_threads()
        self.quit = 1
        return ''

    def wait_threads(self):
        for k,v in self.funcs.items():
            if hasattr(v, 't'):
                v.t.join()
            kk = k.split('.')
            if 'srv' not in kk:
                if 'stop' in kk:
                    a = getargspec(v)
                    if not len(a.args):
                        v()

    @staticmethod
    def load_acl():
        acl = []
        try:
            global acl_fname
            f = open(acl_fname)
            for l in f.readlines():
                l = l.replace('\n', '')
                l = l.replace('\r', '')
                if len(l) == 0:
                    continue
                acl.append(l)
            f.close()
        except:
            acl = ['*']
        return acl

    @staticmethod
    def save_acl(acl):
        try:
            global acl_fname
            f = open(acl_fname, 'w')
            for l in acl:
                f.write(l + '\n\r')
            f.close()
        except:
            pass

    def reload_acl(self):
        """
        Перезагрузить список доступа к серверу (access control list)
        """
        self.acl = MyServer.load_acl()
        print('Access control list:')
        for l in self.acl: print(l)
        return '0'

    def start_process1(self, pa, *args):
        """
        Запустить дочерний процесс с аргументами %pa%
        """
        return start_process(pa, *args, echo=self.echo)

class MyHandler(SimpleXMLRPCRequestHandler):
    def setup(self):
        SimpleXMLRPCRequestHandler.setup(self)
        try:
            self.server.src_ip = gethostbyaddr(self.address_string())[-1][0]
        except:
            self.server.src_ip = self.address_string()

class MyProxy:
    def __init__(self):
        self.cd = CachedDict()
        self.port = 8888

    def start_server_process(self):
        if self.alive(): return
        pr = []
        pr.append(sys.argv[0])
        pr.extend(['--mode', 'srv'])
        pr.extend(['--port', '%d' % self.port])
        start_process(*pr)

    def ping_srv(self, srv):
        try:
            ipaddr,port = urllib.parse.splitport(srv)
            if ping(ipaddr):
                return True
        except:
            pass
        return False

    def call_method(self, srv, *args):
        method = args[0]
        args = args[1:]
        return self.call_method2(srv, method, *args)

    def call_method2(self, srv, method, *args):
        if not srv:
            srv = self.get_local_srv()
        if not self.ping_srv(srv):
            print('Failed to ping srv', srv)
            return
        ms = self.get_methods(srv)
        if ms:
            if method in ms:
                pxy = self.get_proxy(srv)
                m = getattr(pxy, method)
                if m:
                    try:
                        return m(*args)
                    except:
                        pass
                else:
                    print('Server %s has no method %s' % (pxy, method))
        elif hasattr(self, 'srv'):
            m = self.find_method(method, self.srv.funcs.keys())
            if m:
                m = self.srv.funcs[m]
                try:
                    return m(*args)
                except:
                    pass
            

    def find_method(self, m, lst):
        if lst == None:
            return
        if m in lst:
            return m
        for i in lst:
            if m in i.split('.'):
                return i

    def get_argspec_raw(self, srv, m):
        s = self.call_method(srv, 'system.methodSignature', m)
        try:
            return MyServer.unhexlify(s)
        except:
            pass

    def get_argspec(self, srv, m):
        if srv == None:
            srv = self.get_local_srv()
        return self.cd.get(lambda: self.get_argspec_raw(srv, m), srv, m, 'argspec')

    def call(self, dev, *args, rec=1):
        cmd = ' '.join(list(args))
        srv = dev['server'] if dev else self.get_local_srv()
        cc = cmd.split(' ', 1)
        ms = self.get_methods(srv)
        if ms == None:
            return
        m = self.find_method(cc[0], ms)
        if m == None:
            if rec > 0 and len(cc) > 1:
                return self.call(dev, cc[1], rec=rec-1)
            else:
                return
        if self.get_argspec(srv, m) == None:
            return
        args = cmd.split(' ')
        if len(args) > 1:
            if args[0] == args[1]:
                args.pop(0)
        args.pop(0)
        return self.call_method(srv, m, *args)

    def get_local_srv(self):
        return '127.0.0.1:%d' % self.port

    def get_proxy(self, srv=None):
        if srv == None:
            srv = self.get_local_srv()
        pxy = self.cd.get(lambda: ServerProxy('http://%s' % srv, allow_none=True), srv, 'proxy')
        return pxy

    def get_methods(self, srv=None):
        if srv == None:
            srv = self.get_local_srv()
        pxy = self.get_proxy(srv)
        return self.cd.get(lambda: pxy.system.listMethods().split(), srv, 'methods')

    def call_telnet(self, dev, *args):
        srv = dev['server'] if dev else self.get_local_srv()
        if dev:
            srv = dev['server']
            ip_addr = dev['ip_addr']
        else:
            srv = self.get_local_srv()
            args = list(args)
            ip_addr = args.pop(0)
        return self.call_method(srv, 'util.telnet', ip_addr, *args)

    def alive(self, srv=None):
        return self.call(None, 'srv.alive')

    def stop(self, srv=None):
        return self.call(None, 'srv.stop')

    def echo(self, *args):
        return self.call(None, 'srv.echo', *args)

    def idle(self, *args):
        return self.call(None, 'srv.idle', *args)

    def reload_acl(self, *args):
        return self.call(None, 'srv.reload_acl', *args)

    def verbose(self, *args):
        return self.call(None, 'srv.verbose', *args)

    def backend(self, *args):
        return self.call(None, 'srv.backend', *args)

    def backends(self, *args):
        return self.call(None, 'srv.backends', *args)

    def start_process(self, *args, srvalive=None):
        if self.alive() if srvalive == None else False:
            return self.call(None, 'start_process', *args)
        else:
            return start_process(*args)

    def get_server(self, apps):
        if hasattr(self, 'srv'):
            return self.srv
        else:
            extras = app_srv(apps)
            self.srv = MyServer(('', self.port), extras)
            return self.srv

    def start_server(self, apps):
        print('server startup (port %d)' % self.port)
        try:
            srv = self.get_server(apps)
            srv.serve_forever()
        except:
            print('failed to start server at port', self.port)

    def call_server(self, *args, apps=None):
        srv = self.get_server(apps)
        args = list(args)
        m = args.pop(0)
        ret = None
        if m in srv.funcs:
            ret = srv.funcs[m](*tuple(args))
            srv.wait_threads()
        return ret

proxy = MyProxy()

