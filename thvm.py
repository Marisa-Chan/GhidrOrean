from __main__ import *
from xrkutil import *


class VM:
    tp = 0
    WrkDir = ""
    mblk = None

    def __init__(self, t, d):
        self.tp = t
        self.mblk = MMBlock()
        self.WrkDir = d

    def InBlock(self, addr):
        if UINT(addr) >= self.mblk.addr and UINT(addr) < self.mblk.addr + self.mblk.size:
            return True
        return False

    def GetMM(self, addr):
        if UINT(addr) >= self.mblk.addr and UINT(addr) < self.mblk.addr + self.mblk.size:
            return ROSlice(self.mblk.data, UINT(addr) - self.mblk.addr)
        #return self.mblk.data[UINT(addr) - self.mblk.addr:]
        return None


class CLABEL:
    addr = 0xFFFFFFFF
    size = 0
    used = 0
    pushVal = 0
    fld1 = 0
    proceed = 0
    printed = 0
    idx = 0

class CLABELS:
    arr = None
    sz = 0

    def Init(self):
        self.arr = [None] * 0x1000
        for i in range(len(self.arr)):
            self.arr[i] = CLABEL()

    def FindLabel(self, addr):
        for l in self.arr:
            if l.used == 1 and l.addr == addr:
                return l
        return None

    def GetLabel(self, addr, pushvl):
        lbl = self.FindLabel(addr)
        if lbl:
            return lbl

        for l in self.arr:
            if l.used == 0:
                l.used = 1
                l.addr = addr
                l.pushVal = pushvl
                l.size = 0
                l.fld1 = 0
                l.proceed = 0
                l.fld3 = 0
                l.idx = 0
                return l
        return None

    def GetNextToProceed(self):
        for l in self.arr:
            if l.used == 1 and l.proceed == 0:
                return l
        return None

    def FindContain(self, addr):
        for l in self.arr:
            if l.used == 1 and l.size != 0 and addr >= l.addr and addr < l.addr + l.size:
                return l
        return None

    def IsUsed(self, addr):
        if self.FindContain(addr):
            return True
        return False

    def Sort(self):
        self.arr.sort(key = lambda x: x.addr, reverse=False)

    def GetLabelNotPrinted(self, addr):
        for l in self.arr:
            if l.used == 1 and l.printed == 0 and addr >= l.addr:
                return l
        return None

LABELS = CLABELS()


def vid_22_d7(vid):
    return vid in range(0x22, 0xd7)

def vid_2c_2d_bb_ca(vid):
    if vid in (0x2c, 0x2d):
        return True
    if vid in range(0xbb, 0xca):
        return True
    return False