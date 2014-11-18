
import os, socket, sys, threading, time, pdb
from collections import OrderedDict as OD
from queue import Queue
from .server import proxy

class SocketIO:
    def __init__(self, ip_addr, port, fname, fsz=0, send=True):
        #self.DEV_TX_PORT = 8888
        #self.DEV_RX_PORT = 8889
        self.fsz = fsz
        self.ip_addr = ip_addr
        self.port = port
        self.send = send
        self.fname = fname

    def create_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.ip_addr, self.port))
        except socket.error:
            s.close()
            print('could not connect')
            return
        if s is None:
            print('could not open socket')
            return
        return s

    def open_file(self):
        if type(self.fname) == str:
            return open(self.fname, 'rb' if self.send else 'wb')
        elif type(self.fname) == Queue:
            return self.fname

    def close_file(self, f):
        if type(self.fname) == str:
            f.close()

    def write_data(self, f, d):
        if type(f) == Queue:
            f.put(d)
        else:
            f.write(d)

    def read_data(self, f, sz1):
        if type(f) == Queue:
            try:
                data = f.get_nowait()
                return data.encode('ascii')
            except:
                pass
        else:
            return f.read(sz1)

    def data_io_thread(self):
        fsz = self.fsz
        s = self.create_socket()
        if not s:
            return
        f = self.open_file()
        if not f:
            s.close()
            return
        sz1 = 512
        szo = 0
        while True:
            tmp = fsz - szo
            tmp = sz1 if tmp > sz1 else tmp
            if self.send:
                d = self.read_data(f, sz1)
                if d == None:
                    break
                s.send(d)
            else:
                d = s.recv(tmp)
                self.write_data(f, d)
            szo += len(d)
            self.caller_func.progress = int(100.*szo/fsz)
            update_progress(self.caller_func.progress)
            if szo >= fsz:
                break
        self.close_file(f)
        s.close()

    def data_io(self, caller_func=None):
        if not caller_func:
            return '0'
        if hasattr(caller_func, 't'):
            if caller_func.t.is_alive():
                return '0'
        if self.fsz:
            self.caller_func = caller_func
            self.caller_func.progress = 0
            caller_func.t = threading.Thread(target=self.data_io_thread)
            caller_func.t.start()
            return '0x%X' % self.fsz

def get_fsz(fname=None, fsz=0):
    if fsz:
        if type(fsz) == str:
            if fsz.lower()[:2] == '0x':
                fsz = int(fsz, 16)
            else:
                fsz = int(fsz)
    if not fsz and type(fname) == str:
        fsz = os.path.getsize(fname)
    return fsz

def update_progress(progress):
    s = '\r[{0}] {1}%'.format('#'*(int(progress/10)), '%d' % progress)
    try:
        sys.stdout.write(s)
        sys.stdout.flush()
    except:
        pass
    if progress == 100:
        print()

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield '0x' + str(l[i:i+n], 'ascii')

def send_data(ip_addr, port, fname, fsz=''):
    '''
    Отправить данные из файла в устройство
    @param ip_addr - ip-адрес устройства
    @param fname - имя файла
    @return fsz - хорошо, None - ошибка
    '''
    if not fsz:
        fsz = get_fsz(fname, fsz)
    if fsz:
        sktio = SocketIO(ip_addr, port, fname, fsz=fsz, send=True)
        return sktio.data_io(caller_func=send_data)

def recv_data(ip_addr, port, fname, fsz):
    '''
    Получить данные из устройства и записать в файл
    @param ip_addr - ip-адрес устройства
    @param fname - имя файла
    @param fsz - размер файла
    @return fsz - хорошо, None - ошибка
    '''
    if not fsz:
        fsz = get_fsz(fname, fsz)
    if fsz:
        myio = SocketIO(ip_addr, port, fname, fsz=fsz, send=False)
        return myio.data_io(caller_func=recv_data)

