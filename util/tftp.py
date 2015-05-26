
import select, socket, time
from struct import pack
try:
    from .myio import MyAIO
except:
    from myio import MyAIO
finally:
    pass
import pdb

TFTP_RRQ    = 1
TFTP_WRQ    = 2
TFTP_DATA   = 3
TFTP_ACK    = 4
TFTP_ERR    = 5
TFTP_OACK   = 6
SEG_SZ1     = 512
SEG_SZ      = SEG_SZ1 + 4

class Tftp(MyAIO):
    def __init__(self, ip_addr, port, remotefname='script.pcl', read=True):
        MyAIO.__init__(self)
        self.mode = 'octet'.encode('ascii')
        self.ip_addr = ip_addr
        self.port = port
        self.remotefname = remotefname
        self.read = read
        self.timeout = 0.5
        self.add(self.tftp_cb1, self.tftp_cb2, self.tftp_cb3, self.io_cb)
        self.data_cb = self.file_cb

    def create_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
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

    def get(self, fname, data_cb=None):
        self.s = self.create_socket()
        pkt = self.make_rq_pkt(TFTP_RRQ, fname)
        self.s.send(pkt)
        while True:
            d = s.recv(SEG_SZ)
            if not d:
                break
            if data_cb:
                data_cb(d)
            else:
                print(d)
            if len(d) != SEG_SZ:
                break
        self.s.close()

    def tftp_cb1(self):
        self.ackn = 0
        self.s = self.create_socket()
        self.qo.queue.clear()
        print(self.read)
        if self.read:
            pkt = self.make_rq_pkt(TFTP_RRQ, self.remotefname)
            self.qo.put(pkt)
        else:
            pkt = self.make_rq_pkt(TFTP_WRQ, self.remotefname)
            self.qo.put(pkt)
            data = self.data_cb()
            for i in range(0, int(len(data)/SEG_SZ1) + 1):
                pkt = b''.join([pack('>HH', TFTP_DATA, i), data[i*SEG_SZ1:(i+1)*SEG_SZ1]])
                self.qo.put(pkt)
        return True

    def tftp_cb2(self, obj, val):
        if self.read:
            if len(val) > 2:
                val = val[4:]
                ret = self.data_cb(val)
                if len(val) == SEG_SZ1:
                    pkt = pack('>HH', TFTP_ACK, self.ackn)
                    self.ackn += 1
                    self.qo.put(pkt)
                    return True
            return False
        else:
            print(val)
            '''
            ret = self.data_cb()
            if ret:
                pkt = b''.join([pack('>H', TFTP_DATA), ret])
                self.qo.put(pkt)
                return True
            '''
            return True

    def tftp_cb3(self):
        self.s.close()

    def io_cb(self, obj):
        self.s.send(obj)
        r,w,x = select.select([self.s], [], [], self.timeout)
        if r:
            data, addr = self.s.recvfrom(SEG_SZ)
            return data
        return ''

    def file_cb(self, bb=b''):
        if not getattr(self, 'fd', False):
            self.fd = open(self.localfname, 'wb' if self.read else 'rb')
        if self.read:
            if len(bb) > 0:
                self.fd.write(bb)
        else:
            bb = self.fd.read(SEG_SZ1)
        if len(bb) != SEG_SZ1:
            self.fd.close()
            delattr(self, 'fd')
        return bb

    def make_rq_pkt(self, opcode, name):
        lst = [pack(">H", opcode), name.encode('ascii'), b'\0', self.mode, b'\0']
        return b''.join(lst)

def main():
    import asyncio
    f = Tftp('192.168.0.1', 69, 'script.pcl', False)
    f.localfname = '/tmp/test.pcl'
    r = asyncio.get_event_loop().run_until_complete(f.start())

if __name__ == "__main__":
    main()

