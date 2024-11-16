from xrkutil import *
from xrkdsm import *
from thobfus import *
from xrkasm import *
from thvm import *
from __main__ import *


class FISH(VM):
    jmpaddr = -1
    push1 = 0
    push1_2 = 0
    push2 = 0
    push2_2 = 0
    VMAddr = -1

    def __init__(self, d):
        VM.__init__(self, 5, d)


    def Step0(self, addr):

        bs = GetBytes(addr, 5)
        if UB(bs[0]) not in (0xe8, 0xe9):
            print("Not JMP or CALL at: {:08x}".format(addr))
            return False

        self.jmpaddr = addr
        vl = GetSInt(bs[1:6])

        vma = UINT(addr + 5 + vl)

        mblock = GetMemBlockInfo(vma)
        if not mblock:
            print("Can't get mem block at {:08X}".format(vma))
            return False

        print("Getting section {:08X} - {:08X}".format(mblock.addr, mblock.addr + mblock.size))

        self.mblk.data = GetBytes(mblock.addr, mblock.size)
        self.mblk.addr = mblock.addr
        self.mblk.size = mblock.size

        pushA = vma
        for i in range(2):
            m = self.GetMM(pushA)
            sz, rk = XrkDecode(m)

            if rk.ID != OP_PUSH:
                print("Instruction at {:08X} not a PUSH".format(pushA))
                return False

            if i == 0:
                self.push1 = rk.operand[0].value
                self.push1_2 = rk.operand[0].value
            else:
                self.push2 = rk.operand[0].value
                self.push2_2 = rk.operand[0].value

            pushA += sz

        m = self.GetMM(pushA)
        sz, rk = XrkDecode(m)

        if rk.ID != OP_JMP:
            print("Instruction at {:08X} not a JMP".format(pushA))
            return False

        maddr = UINT(pushA + sz + rk.operand[0].value)

        mblock = GetMemBlockInfo(maddr)
        if not mblock:
            print("Can't get mem block at {:08X}".format(maddr))
            return False

        print("Getting section {:08X} - {:08X}".format(mblock.addr, mblock.addr + mblock.size))
        self.mblk.data = GetBytes(mblock.addr, mblock.size)
        self.mblk.addr = mblock.addr
        self.mblk.size = mblock.size

        self.VMAddr = maddr
        return True

    def Step1(self, addr):
        CMDSimpler.Clear()
        i = 0
        while i + addr < self.mblk.size:

            m = self.GetMM(i + addr)
            if m[0] == 0xf3:
                i += 1
                continue

            sz, rk = XrkDecode(m)

            CMDSimpler.Add(rk, i + addr)
            if rk.ID == OP_JMP and rk.operand[0].TID() == 3:
                break

            i += sz
        return True

   # def fn43b0(self, i, ):