
import io, select, socket, time
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
    def __init__(self, ip_addr, port, st, remotefname='script.pcl', read=True, wnd=None):
        MyAIO.__init__(self)
        self.mode = 'octet'.encode('ascii')
        self.ip_addr = ip_addr
        self.port = port
        self.st = st
        self.wnd = wnd
        self.remotefname = remotefname
        self.read = read
        self.timeout = 2
        self.add(self.tftp_cb1, self.tftp_cb2, self.tftp_cb3, self.io_cb)

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

    def tftp_cb1(self):
        if not self.st:
            return False
        if self.read and not self.st.writable():
            raise io.UnsupportedOperation
        if not self.read and not self.st.readable():
            raise io.UnsupportedOperation
        self.ackn = 0
        self.s = self.create_socket()
        self.qo.queue.clear()
        if self.read:
            pkt = self.make_rq_pkt(TFTP_RRQ, self.remotefname)
            self.qo.put(pkt)
        else:
            pkt = self.make_rq_pkt(TFTP_WRQ, self.remotefname)
            self.qo.put(pkt)
            self.st.seek(0)
            while True:
                bb = self.st.read(SEG_SZ1)
                pkt = b''.join([pack('>HH', TFTP_DATA, self.qo.qsize() - 1), bb])
                self.qo.put(pkt)
                if len(bb) != SEG_SZ1:
                    break
        return True

    def tftp_cb2(self, obj, val):
        if self.read:
            if len(val) > 2:
                val = val[4:]
                self.st.write(val)
                if len(val) == SEG_SZ1:
                    pkt = pack('>HH', TFTP_ACK, self.ackn)
                    self.ackn += 1
                    self.qo.put(pkt)
                    return True
            else:
                self.na.append(self.ip_addr)
                return False
        else:
            if val:
                return True
            else:
                self.na.append(self.ip_addr)
                return False

    def tftp_cb3(self):
        self.s.close()
        self.st.close()
        self.wnd.ctrl_cb3()

    def io_cb(self, obj):
        self.s.send(obj)
        r,w,x = select.select([self.s], [], [], self.timeout)
        if r:
            data, addr = self.s.recvfrom(SEG_SZ)
            return data
        return ''

    def make_rq_pkt(self, opcode, name):
        lst = [pack(">H", opcode), name.encode('ascii'), b'\0', self.mode, b'\0']
        return b''.join(lst)

def main():
    import asyncio
    st = open('/tmp/test.pcl', 'rb')
    f = Tftp('192.168.0.1', 69, st, 'script.pcl', True)
    asyncio.get_event_loop().run_until_complete(f.start())

if __name__ == "__main__":
    main()

