import opcode
import time

from xrkutil import *
from xrkdsm import *
from thobfus import *
from xrkasm import *
from thvm import *
from __main__ import *


class FSEQ:
    tp = -1
    seq = ()
    def __init__(self, tp, seq):
        self.tp = tp
        self.seq = seq

class FKEY:
    koff1 = 0
    idx = 0
    flg1 = 0
    flg2 = 0
    oprID = 0
    ID = 0
    koff2 = 0

class FHNDL:
    idx1 = -1
    idxList = None
    f_5d8 = 0
    f_5dc = 0
    f_624 = 0
    f_628 = 0
    f_62c = 0
    hndlID = -1
    c024 = 0
    keys = None
    tp = -1
    f_530 = None

    def __init__(self, id = -1):
        self.idxList = []
        self.hndlID = id
        self.keys = []
        self.f_530 = []

class FISH(VM):
    jmpaddr = -1
    push1 = 0
    push1_2 = 0
    push2 = 0
    push2_2 = 0
    VMAddr = -1
    imageBase = 0
    val1 = 0
    vmImgBase = 0 # Add it to address
    vmOldBase = 0 # Sub it from address
    val4 = 0
    vmEIP = 0
    iatAddr = 0
    val7 = 0
    iatCount = 0
    f_c01a = 0
    f_c01c = 0
    f_c01e = 0
    f_c020 = 0
    f_c024 = 0

    hndl_tp0_fnd = 0

    f_2a = 0
    f_2c = 0

    fres = None
    frescnt = 0

    KVal = None
    KOff = None
    KEYNUM = 10

    hndl = None
    hndlCount = 0

    SeqData1 = ( FSEQ(8, (OP_MOV, OP_ADD, OP_MOV, OP_CMP, OP_JNZ, OP_MOV, OP_ADD, OP_MOV, OP_ADD, OP_MOV, OP_ADD, OP_MOV, OP_ADD, OP_MOV, OP_CMP, OP_JE, OP_CMP, OP_JE, OP_ADD, OP_MOV, OP_ADD)),
                FSEQ(5, (OP_MOV, OP_ADD, OP_MOV, OP_ADD, OP_MOV, OP_ADD, OP_MOV, OP_ADD, OP_MOV, OP_MOV, OP_POP, OP_POP, OP_POP, OP_POP, OP_POP, OP_POP, OP_POP, OP_RETN)),
                FSEQ(7, (OP_MOV, OP_ADD, OP_MOV, OP_SHL, OP_MOV, OP_ADD, OP_MOV, OP_MOV, OP_ADD, OP_MOV, OP_MOV, OP_AND, OP_CMP, OP_JE, OP_AND, OP_SUB, OP_JMP)),
                FSEQ(0xb, (OP_MOV, OP_MOV, OP_ADD, OP_MOV, OP_ADD, OP_MOV, OP_MOV, OP_ADD, OP_MOV, OP_CMP, OP_JE, OP_CMP, OP_JE, OP_CMP, OP_JNZ)),
                FSEQ(6, (OP_MOV, OP_MOV, OP_ADD, OP_MOV, OP_ADD, OP_MOV, OP_MOV, OP_ADD, OP_MOV, OP_CMP, OP_JE, OP_CMP, OP_JE, OP_CMP, OP_JNZ)),
                FSEQ(0xc, (OP_MOV, OP_ADD, OP_MOV, OP_ADD, OP_MOV, OP_MOV, OP_MOV, OP_ADD, OP_MOV, OP_ADD, OP_MOV, OP_MOV)),
                FSEQ(0xd, (OP_MOV, OP_ADD, OP_MOV, OP_ADD, OP_MOV, OP_MOV, OP_ADD, OP_MOV, OP_ADD, OP_MOV, OP_MOV)),
                FSEQ(9, (OP_MOV, OP_ADD, OP_MOV, OP_CMP, OP_JE, OP_CMP, OP_JE, OP_MOV, OP_ADD, OP_MOV, OP_ADD)),
                FSEQ(0x1f, (OP_MOV, OP_ADD, OP_MOV, OP_ADD, OP_MOV, OP_ADD, OP_MOV, OP_CMP, OP_JNZ)),
                FSEQ(0x23, (OP_MOV, OP_MOV, OP_MOV, OP_MOV, OP_MOV, OP_MOV, OP_MOV, OP_MOV)),
                FSEQ(0x21, (OP_MOV, OP_ADD, OP_MOVZX, OP_ADD, OP_MOV)),
                FSEQ(0x22, (OP_MOV, OP_ADD, OP_MOVZX, OP_ADD, OP_MOV)) )

    SeqData2 = (FSEQ(0, (OP_MOV, 0xfffe, OP_CMP, OP_JNZ, OP_MOV, 0xfffe, 0xfffe, OP_AND, OP_ADD, OP_MOV, 0xfffe, OP_MOV, OP_MOV, 0xfffe, OP_MOV, OP_CMP, OP_JNZ, OP_MOV, OP_CMP, OP_JNZ, OP_MOV, OP_CMP, OP_JNZ, OP_MOV, 0xfffe, 0xfffe, OP_MOV)),
                FSEQ(1, (OP_MOV, 0xfffe, OP_CMP, OP_JNZ, OP_MOV, 0xfffe, 0xfffe, OP_AND, OP_MOV, 0xfffe, OP_ADD, OP_MOV, OP_CMP, OP_JNZ, OP_MOV, OP_CMP, OP_JNZ, OP_MOV, OP_CMP, OP_JNZ, OP_MOV, 0xfffe, 0xfffe, OP_MOV)),
                FSEQ(2, (OP_MOV, 0xfffe, OP_CMP, OP_JNZ, OP_MOV, 0xfffe, 0xfffe, OP_AND, OP_MOV, 0xfffe, OP_ADD, OP_MOV, OP_MOV, 0xfffe, OP_MOV, OP_CMP, OP_JNZ, OP_MOV, OP_CMP, OP_JNZ, OP_MOV, OP_CMP, OP_JNZ, OP_MOV, 0xfffe, 0xfffe, OP_MOV)),
                FSEQ(3, (OP_MOV, 0xfffe, 0xfffe, OP_MOV, 0xffff, 0xffff, 0xffff, 0xfffe, OP_CMP, OP_JNZ, OP_CMP, OP_JNZ, OP_PUSH, OP_CMP, OP_JNZ, OP_MOV, 0xfffe, OP_CMP, OP_JNZ, OP_POP)),
                FSEQ(3, (OP_MOV, 0xfffe, 0xfffe, OP_MOV, 0xffff, 0xffff, 0xffff, OP_CMP, OP_JNZ, OP_CMP, OP_JNZ, OP_PUSH, OP_CMP, OP_JNZ, OP_MOV, 0xfffe, OP_CMP, OP_JNZ, OP_POP)),
                FSEQ(4, (OP_MOV, 0xfffe, OP_CMP, OP_JNZ, OP_MOV, 0xfffe, 0xfffe, OP_AND, OP_ADD, OP_MOV, 0xfffe, OP_MOV, OP_MOV, 0xfffe, 0xfffe, OP_MOV)),
                FSEQ(5, (OP_MOV, 0xfffe, OP_CMP, OP_JNZ, OP_MOV, 0xfffe, 0xfffe, OP_AND, OP_ADD, OP_MOV, 0xfffe, 0xfffe, OP_MOV)),
                FSEQ(6, (OP_MOV, OP_ADD, OP_MOVZX, OP_MOV, OP_AND, 0xfffe, 0xfffe, 0xfffe, 0xfffe, OP_MOV, OP_MOV)),
                FSEQ(7, (OP_MOV, 0xfffe, 0xfffe, OP_AND, OP_ADD, OP_MOV, OP_ADD)),
                FSEQ(8, (OP_MOV, OP_ADD, OP_MOV, 0xfffe, 0xfffe, OP_MOV)),
                FSEQ(9, (OP_MOV, OP_ADD, OP_MOVZX)),
                FSEQ(0xa, (OP_MOV,)))

    ## 7:
    ## MOV
    ## asx
    ## asx
    ## AND
    ## ADD
    ## MOV  ... , dword[  + vmImgBase]
    ## ADD

    ## 9:
    ## MOV
    ## ADD
    ## MOVZX  ... , byte/word[EBP + vmEIP]

    ## a:
    ## MOV byte/word[EBP + ???], 0

    def __init__(self, d):
        VM.__init__(self, 5, d)
        self.fres = []
        self.frescnt = 0

        self.KVal = [0] * self.KEYNUM
        self.KOff = [0] * self.KEYNUM

        self.hndl = dict()


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
        while i + addr < self.mblk.size + self.mblk.addr:

            m = self.GetMM(i + addr)
            if m[0] == 0xf3:
                i += 1
                continue

            sz, rk = XrkDecode(m)

            CMDSimpler.Add(rk, i + addr)

            if rk.ID == OP_JMP and rk.operand[0].TID() == 3:
                break

            i += sz

        f = open("{}/TXT/Fish_ZeroData_{:08x}.txt".format(self.WrkDir, self.VMAddr),"w")
        for l in CMDSimpler.GetListing(1, 1):
            f.write("{}\n".format(l))
        f.close()
        return True

    def FindImageBase(self, startn = 0, dbg = False):
        val = 0
        flg = [False, False, False]

        i = startn
        while i < CMDSimpler.count:
            cmd = CMDSimpler.heap[i]
            op = cmd.instr

            if op.ID == OP_CALL:
                val = cmd.addr + 5
                flg[0] = True
                if dbg:
                    print("FindImageBase OP_CALL {:08x}".format(val))

            elif flg[0] and IsOpClass(op.ID, 0, 0, 1) and op.operand[0].ID == 0x10 and\
                op.operand[0].value == 0x13 and op.operand[1].TID() == 2:
                _,val = ComputeVal(op.ID, op.operand[0].value & 0xF, val, op.operand[1].value)
                flg[0] = False
                flg[1] = True

                if dbg:
                    print("FindImageBase asx0 {:08x} = {:08x}".format(op.operand[1].value, val))

            elif flg[1] and IsOpClass(op.ID, 0, 0, 1) and op.operand[0].ID == 0x10 and\
                op.operand[0].value == 0x13 and op.operand[1].ID == 0x23:
                _,val = ComputeVal(op.ID, op.operand[0].value & 0xF, val, op.operand[1].value)
                flg[2] = True
                flg[1] = False

                if dbg:
                    print("FindImageBase asx1 {:08x} = {:08x}".format(op.operand[1].value, val))

            elif flg[2] and op.ID == OP_MOV and op.operand[0].ID == 0x10 and op.operand[0].value == 0x53 and\
                 op.operand[1].ID == 0x23:
                if dbg:
                    print("FindImageBase OP_MOV {:d} {:08x}".format(i, val))
                return (i, val)

            elif op.ID == OP_PUSH:
                if dbg:
                    print("FindImageBase OP_PUSH")
                break

            i += 1
        return (0, 0)

    def fn(self, startn = 0, dbg = False):
        reg = 0
        addr = 0
        flg = False

        i = startn
        while i < CMDSimpler.count:
            op = CMDSimpler.heap[i].instr

            if op.ID == OP_MOV and op.operand[0].ID == 0x10 and op.operand[0].value == 0x53 and\
                    op.operand[1].ID == 0x23:
                addr = op.operand[1].value
                reg = op.operand[0].GetB(0)
                flg = True
                if dbg:
                    print("FindImageBase OP_MOV {:08x}".format(val))

            elif flg and IsOpClass(op.ID, 0, 0, 1) and op.operand[0].ID == 0x10 and \
                    op.operand[0].GetB(0) == reg and op.operand[1].TID() == 1 and op.operand[1].GetB(0) == 0x13:

                if dbg:
                    print("FindImageBase asx0 {:08x} = {:08x}".format(op.operand[1].value, val))

                return (i + 1, UINT(self.imageBase + addr))

            elif op.ID == OP_PUSH:
                if dbg:
                    print("FindImageBase OP_PUSH")
                break
            i += 1

    def GetVmImgBase(self, startn):
        i = startn
        while i < CMDSimpler.count:
            op = CMDSimpler.heap[i].instr
            op1 = CMDSimpler.heap[i + 1].instr

            if op.ID == OP_MOV and op1.ID == OP_MOV and\
                op.operand[0].ID == 0x10 and op.operand[1].ID == 0x23 and\
                op1.operand[0].ID == 0x33 and op1.operand[1].ID == 0x10 and \
                (op.operand[0].GetB(0) == op1.operand[0].GetB(1) or op.operand[0].GetB(0) == op1.operand[0].GetB(2)):
                return (i + 2, op.operand[1].value)

            if op.ID == OP_CMP:
                break
            i += 1
        return (0, 0)

    def GetVmOldBase(self, startn):
        i = startn
        while i < CMDSimpler.count:
            op = CMDSimpler.heap[i].instr
            op1 = CMDSimpler.heap[i + 1].instr

            if op.ID == OP_MOV and op1.ID == OP_MOV and\
                op.operand[0].ID == 0x10 and op.operand[1].ID == 0x23 and\
                op1.operand[0].ID == 0x33 and op1.operand[1].ID == 0x23 and \
                (op.operand[0].GetB(0) == op1.operand[0].GetB(1) or op.operand[0].GetB(0) == op1.operand[0].GetB(2)):
                return (i + 1, op.operand[1].value)

            if op.ID == OP_CMP:
                break
            i += 1
        return (0, 0)

    def fn4(self, startn):
        i = startn
        while i < CMDSimpler.count:
            op = CMDSimpler.heap[i].instr

            if op.ID == OP_MOV and\
                op.operand[0].ID == 0x33 and\
                op.operand[0].GetB(1) != 0 and op.operand[0].GetB(2) != 0 and op.operand[0].GetB(3) == 0 and \
                op.operand[0].val2 == 0 and op.operand[1].ID == 0x23:
                return (i + 1, op.operand[1].value)

            if op.ID == OP_CMP:
                break
            i += 1
        return (0, 0)

    def GetVmEIPOff(self, startn):
        i = startn
        while i < CMDSimpler.count:
            op = CMDSimpler.heap[i].instr
            op1 = CMDSimpler.heap[i + 1].instr

            # MOV reg, val                       offset of vm "EIP"
            # MOV reg, dword ptr [ESP + 0x28]    get push(first)
            if op.ID == OP_MOV and op1.ID == OP_MOV and\
                op.operand[0].ID == ID_REG and op.operand[1].ID == ID_VAL32 and\
                op1.operand[0].ID == ID_REG and op1.operand[1].ID == ID_MEM32 and \
                op1.operand[0].GetB(0) != R_ESP and\
                op1.operand[1].GetB(1) == R_ESP and op1.operand[1].GetB(2) == 0 and op1.operand[1].GetB(3) == 0 and\
                op1.operand[1].val2 == 0x28:
                return (i + 1, op.operand[1].value)

            if op.ID == OP_CMP:
                break
            i += 1
        return (0, 0)

    def GetIatAddr(self, startn):
        flg = False
        i = startn
        while i < CMDSimpler.count:
            op = CMDSimpler.heap[i].instr

            if op.ID == OP_MOV and op.operand[0].ID == 0x10 and op.operand[0].GetB(0) != 0x43 and\
                op.operand[1].ID == 0x33 and op.operand[1].GetB(1) == 0x43 and \
                op.operand[1].GetB(2) == 0 and op.operand[1].GetB(3) == 0 and \
                op.operand[1].val2 == 0x28:
                flg = True

            elif flg and op.ID == OP_MOV and op.operand[0].ID == 0x10 and op.operand[0].GetB(0) != 0x43 and\
                op.operand[1].ID == 0x23 and op.operand[1].value != 0:
                return (i + 1, UINT(self.imageBase + op.operand[1].value))

            if op.ID == OP_CMP:
                break
            i += 1
        return (0, 0)

    def fn7(self, startn):
        i = startn
        while i < CMDSimpler.count:
            op = CMDSimpler.heap[i].instr
            op1 = CMDSimpler.heap[i + 1].instr

            if op.ID == OP_MOV and op1.ID == OP_MOV and\
                op.operand[0].ID == 0x10 and op.operand[1].ID == 0x23 and\
                op1.operand[0].ID == 0x10 and op1.operand[1].ID == 0x33 and \
                (op.operand[0].GetB(0) == op1.operand[1].GetB(1) or op.operand[0].GetB(0) == op1.operand[1].GetB(2)):
                return (i + 1, op.operand[1].value)

            if op.ID == OP_CMP:
                break
            i += 1
        return (0, 0)

    def GetIatCount(self, startn):
        i = CMDSimpler.NextOpPos(OP_PUSH, startn)
        if i == -1:
            return 0

        while i < CMDSimpler.count:
            op = CMDSimpler.heap[i].instr
            op1 = CMDSimpler.heap[i + 1].instr

            if op.ID == OP_PUSH and op1.ID == OP_MOV and\
                op.operand[0].ID == 0x10 and op1.operand[0].ID == 0x10 and\
                op1.operand[1].ID == 0x23 and \
                op.operand[0].GetB(0) == op1.operand[0].GetB(0):
                return op1.operand[1].value >> 2

            if op.ID == OP_PUSH:
                break
            i += 1
        return 0

    def Step2(self):
        i, self.imageBase = self.FindImageBase()
        if self.imageBase == 0:
            return False

        i, self.val1 = self.fn(i)
        if self.val1 == 0:
            return False

        popPos = CMDSimpler.NextOpPos(OP_POP, i)
        if popPos == -1:
            return False

        i, self.vmImgBase = self.GetVmImgBase(popPos)
        if self.vmImgBase == 0:
            return False

        i, self.vmOldBase = self.GetVmOldBase(i)
        if self.vmOldBase == 0:
            return False

        i, self.val4 = self.fn4(i)
        if self.val4 == 0:
            return False

        i, self.vmEIP = self.GetVmEIPOff(i)
        if self.vmEIP == 0:
            return False

        i, self.iatAddr = self.GetIatAddr(i)
        if self.iatAddr == 0:
            return False

        i, self.val7 = self.fn7(i)
        if self.val7 == 0:
            return False

        self.iatCount = self.GetIatCount(i)
        if self.iatCount == 0:
            return False

        self.push1_2 = UINT(self.push1_2 + self.imageBase)
        self.push1 = UINT(self.push1 + self.imageBase)

        print("v1 {:08x} pop {:d} v2 {:08x} v3 {:08x} v4 {:08x} vmEIP {:08x} iatAddr {:08x} v7 {:08x} iatCount {:08x}".format(self.val1, popPos, self.vmImgBase, self.vmOldBase, self.val4, self.vmEIP, self.iatAddr, self.val7, self.iatCount))
        return True

    def FUN_1005d540(self):
        i = CMDSimpler.count - 1
        op = CMDSimpler.heap[i].instr
        if op.ID == OP_CMP:
            return True
        elif op.ID == OP_TEST:
            return True
        elif op.ID == OP_OR and op.operand[0].TID() == TID_REG and op.operand[1].TID() == TID_REG and\
            op.operand[0].GetB(0) == op.operand[1].GetB(0):
            CMDSimpler.unk = 0
            return True
        return False


    def FUN_100412e0(self):
        if CMDSimpler.count < 7:
            return False

        op0 = CMDSimpler.heap[CMDSimpler.count - 6].instr
        op1 = CMDSimpler.heap[CMDSimpler.count - 5].instr
        op2 = CMDSimpler.heap[CMDSimpler.count - 4].instr
        op3 = CMDSimpler.heap[CMDSimpler.count - 3].instr
        op4 = CMDSimpler.heap[CMDSimpler.count - 2].instr
        op5 = CMDSimpler.heap[CMDSimpler.count - 1].instr

        ## CMP   REG8, VAL
        ## JE
        ## CMP   REG8, VAL
        ## JE
        ## CMP   REG8, VAL
        ## JNZ
        if op0.ID == OP_CMP and op0.operand[0].ID == ID_REG and op0.operand[1].TID() == TID_VAL and\
           op1.ID == OP_JE and\
           op2.ID == OP_CMP and op2.operand[0].ID == ID_REG and op2.operand[1].TID() == TID_VAL and\
           op3.ID == OP_JE and\
           op4.ID == OP_CMP and op4.operand[0].ID == ID_REG and op4.operand[1].TID() == TID_VAL and\
           op5.ID == OP_JNZ and\
           op0.operand[0].GetB(0) & 0xF == 1 and op0.operand[0].GetB(0) == op2.operand[0].GetB(0) and\
           op2.operand[0].GetB(0) == op4.operand[0].GetB(0):
            return True
        return False


    def DumpHandler(self, addr, J):
        CMDSimpler.Clear()
        self.f_c024 = 0
        self.fres = []

        loc4c = 0
        loc48 = -1
        loc50 = 0
        i = 0
        while UINT(i + addr) < self.mblk.addr + self.mblk.size:
            m = self.GetMM( UINT(i + addr) )
            sz, rk = XrkDecode(m)

            opAdr = UINT(i + addr)
            i = UINT(i + sz)

            if rk.ID == OP_CMP:
                CMDSimpler.Add(rk, opAdr)
                self.f_c024 += 1
            elif rk.ID == OP_JMP:
                if rk.operand[0].TID() == TID_VAL:
                    i = UINT(i + rk.operand[0].value)
                    if CMDSimpler.GetAddr( UINT(i + addr) ) != None:
                        break
                else:
                    CMDSimpler.Add(rk, opAdr)

                    if loc4c == 1 and loc48 != -1:
                        addr = loc48
                        i = 0
                        loc48 = -1
                    else:
                        break
            elif rk.ID == OP_RETN:
                CMDSimpler.Add(rk, opAdr)
                if loc4c == 1 and loc48 != -1:
                    addr = loc48
                    i = 0
                    loc48 = -1
                else:
                    break
            elif rk.ID >= OP_JA and rk.ID <= OP_JS:
                if self.FUN_1005d540():
                    CMDSimpler.Add(rk, opAdr)

                    if self.f_c024 == 3:
                        if self.FUN_100412e0():
                            loc4c = 1
                            loc50 = 0xF
                        else:
                            loc4c = 0

                    if loc4c == 1:
                        if loc50 > 0:
                            i = UINT(i + rk.operand[0].value)
                        if loc50 == 0:
                            loc48 = UINT(addr + i + rk.operand[0].value)
                        loc50 -= 1
                else:
                    b = 0
                    if J == 1:
                        a, b = CMDSimpler.EvaluateBranch(self, rk.ID, False, 'C')
                        if (a & 0xFF) == 0:
                            print("Follow Jump?")
                            b = False
                        self.fres.append(b)
                    else:
                        b = 1
                        self.fres.append(b)

                    if b == 1:
                        i = UINT(i + rk.operand[0].value)

                CMDSimpler.GetAddr( UINT(i + addr) )

            else:
                CMDSimpler.Add(rk, opAdr)

            if CMDSimpler.GetAddr( UINT(i + addr) ) != None:
                break

        CMDSimpler.Simple(self, 0xFFFF,'C')
        self.FUN_100436b0()
        self.FUN_10042a60()



    def FUN_100436b0(self):
        cmds = CMDSimpler.heap
        i = 0
        while i < CMDSimpler.count:
            op = cmds[i].instr
            #  MOV  reg(not ESP/EBP), EBP
            if op.ID == OP_MOV and op.operand[0].ID == ID_REG and op.operand[1].ID == ID_REG and\
               op.operand[0].GetB(0) not in (R_ESP, R_EBP) and op.operand[1].GetB(0) == R_EBP:
                loc1c = 1
                reg = op.operand[0].GetB(0)

                k = i + 1
                while k < CMDSimpler.count:
                    opk = cmds[k].instr

                    if opk.ID != 0:
                        # ADD   reg, const
                        if opk.ID == OP_ADD and\
                           opk.operand[0].ID == ID_REG and opk.operand[1].ID == ID_VAL32 and\
                           opk.operand[0].GetB(0) == reg:
                            loc1c += 1
                            for z in range(k + 1, CMDSimpler.count):
                                opz = cmds[z].instr
                                if opz.ID != 0:
                                    if opz.ID != OP_MOVS:
                                        if opz.operand[0].TID() == TID_MEM and\
                                           opz.operand[0].GetB(1) == reg and opz.operand[0].GetB(2) == 0 and opz.operand[0].GetB(3) == 0 and\
                                           opz.operand[0].val2 == 0 and loc1c == 2:
                                            opz.operand[0].SetB(1, R_EBP)
                                            opz.operand[0].val2 = opk.operand[1].value
                                            opk.ID = 0
                                            op.ID = 0
                                            loc1c = 3
                                        elif opz.operand[1].TID() == TID_MEM and\
                                             opz.operand[1].GetB(1) == reg and opz.operand[1].GetB(2) == 0 and opz.operand[1].GetB(3) == 0 and\
                                             opz.operand[1].val2 == 0 and loc1c == 2:
                                            opz.operand[1].SetB(1, R_EBP)
                                            opz.operand[1].val2 = opk.operand[1].value
                                            opk.ID = 0
                                            op.ID = 0
                                            loc1c = 3
                                        elif opz.operand[0].ID == ID_REG and opz.operand[0].GetB(0) == reg:
                                            loc1c += 1
                                    if loc1c > 2:
                                        break
                        elif opk.operand[0].ID == ID_REG and opk.operand[0].GetB(0) == reg:
                            loc1c += 1

                        if loc1c >= 2:
                            break

                    k += 1

            i += 1
        CMDSimpler.Cleaner()

        i = 0
        while i < CMDSimpler.count:
            op = cmds[i].instr
            # MOV reg, imm
            if op.ID == OP_MOV and op.operand[0].TID() == TID_REG and op.operand[1].TID() == TID_VAL:
                loc30 = 0
                reg = op.operand[0].GetB(0)
                j = i + 1
                while j < CMDSimpler.count:
                    opj = cmds[j].instr

                    ## break if change 'reg' to another value or place value into [reg]
                    ##  ...   reg, ...
                    ##  ...   [reg ], ...
                    if (opj.operand[0].TID() == TID_REG and opj.operand[0].GetB(0) == reg) or\
                       (opj.operand[0].TID() == TID_MEM and (opj.operand[0].GetB(1) == reg or opj.operand[0].GetB(2) == reg)):
                        break

                    ## ...   [ebp + ?], reg
                    ## change to
                    ## ...   [ebp + ?], imm
                    if opj.operand[1].TID() == TID_REG and opj.operand[1].GetB(0) == reg and \
                       opj.operand[0].TID() == TID_MEM and \
                       opj.operand[0].GetB(1) == R_EBP and opj.operand[0].GetB(2) == 0 and opj.operand[0].GetB(3) == 0:
                        opj.operand[1].ID = (opj.operand[1].GetB(0) & 0xf) | ID_VALx
                        opj.operand[1].value = op.operand[1].value
                        loc30 += 1
                    j += 1
                if loc30 > 0:
                    op.ID = 0
            ###  MOV   reg, [ebp + keyX]
            elif op.ID == OP_MOV and op.operand[0].TID() == TID_REG and op.operand[1].TID() == TID_MEM and\
                 self.IsIdxOpEbpKey(i, 1):
                reg = op.operand[0].GetB(0)
                j = i + 1
                while j < CMDSimpler.count:
                    opj = cmds[j].instr

                    ## break if change 'reg' to another value or place value into [reg]
                    ##  ...   reg, ...
                    ##  ...   [reg ], ...
                    if (opj.operand[0].TID() == TID_REG and opj.operand[0].GetB(0) == reg) or \
                       (opj.operand[0].TID() == TID_MEM and (opj.operand[0].GetB(1) == reg or opj.operand[0].GetB(2) == reg)):
                        break

                    ## write reg value into [key]
                    ## ...  [ebp + keyX], reg
                    if opj.operand[1].TID() == TID_REG and opj.operand[1].GetB(0) == reg and\
                       opj.operand[0].TID() == TID_MEM and\
                       opj.operand[0].GetB(1) == R_EBP and opj.operand[0].GetB(2) == 0 and opj.operand[0].GetB(3) == 0 and\
                       self.IsIdxOpEbpKey(j, 0):
                        CMDSimpler.heap[j].keyData = op.operand[1].val2 | 0x80000000
                    j += 1

            i += 1
        CMDSimpler.Cleaner()


    def IsIdxOpEbpKey(self, i, mv):
        op = CMDSimpler.heap[i].instr
        if IsOpClass(op.ID, mv, 0, 1):
            if op.operand[0].TID() == TID_MEM:
                if op.operand[0].GetB(1) == R_EBP and op.operand[0].GetB(2) == 0 and op.operand[0].GetB(3) == 0:
                    for v in self.KOff:
                        if v == op.operand[0].val2:
                            return True
            elif op.operand[1].TID() == TID_MEM:
                if op.operand[1].GetB(1) == R_EBP and op.operand[1].GetB(2) == 0 and op.operand[1].GetB(3) == 0:
                    for v in self.KOff:
                        if v == op.operand[1].val2:
                            return True
        return False

    def FUN_10042380(self, i, opt, p3, u3, p5, dbg = False):
        if p3 == -1:
            if p5 == 1 and i >= 0 and i < CMDSimpler.count:
                CMDSimpler.heap[i].index = u3

            op = CMDSimpler.heap[i].instr
            t = 0
            if op.operand[opt].TID() == TID_REG:
                t = op.operand[opt].GetB(0) >> 4
            if op.operand[opt].TID() == TID_MEM:
                t = op.operand[opt].GetB(1) >> 4

            # not xSP/xBP
            if t not in (4,5) and i > 0:
                bv2 = False
                j = i - 1
                while j > -1 and not bv2:
                    opj = CMDSimpler.heap[j].instr

                    if opj.ID in (OP_MOV, OP_MOVSX, OP_MOVZX):
                        if opj.operand[0].TID() == TID_REG and (opj.operand[0].GetB(0) >> 4) == t:
                            CMDSimpler.heap[j].index = u3
                            bv2 = True
                            if opj.operand[1].TID() == TID_REG and opj.operand[1].GetB(0) not in (R_ESP, R_EBP):
                                if opj.ID == OP_MOV and opj.operand[0].GetB(0) == opj.operand[1].GetB(0):
                                    CMDSimpler.heap[j].index = 0
                                    bv2 = False
                                else:
                                    self.FUN_10042380(j, 1, -1, u3, p5)
                    elif opj.ID == OP_POP:
                        if opj.operand[0].TID() == TID_REG and (opj.operand[0].GetB(0) >> 4) == t:
                            CMDSimpler.heap[j].index = u3
                            bv2 = True
                    else:
                        if opj.ID in (OP_CMP, OP_TEST):
                            opj1 = CMDSimpler.heap[j + 1].instr
                            if opj1.ID != OP_PUSHF and opj1.ID != 0 and (opj1.ID <= OP_JMP or opj1.ID >= OP_JCXZ):
                                j -= 1
                                continue

                        if opj.operand[0].TID() == TID_REG and (opj.operand[0].GetB(0) >> 4) == t:
                            CMDSimpler.heap[j].index = u3
                            if opj.operand[1].TID() == TID_REG and opj.operand[1].GetB(0) not in (R_ESP, R_EBP):
                                self.FUN_10042380(j, 1, -1, u3, p5)
                    j -= 1
        elif p3 == 1:
            print("FUN_10042380 InvalidInstructionException")

    def GetKValByOff(self, off):
        for i in range(self.KEYNUM):
            if self.KOff[i] != -1 and self.KOff[i] == off:
                return (1, self.KVal[i])
        return (0, 0)

    def SetKValByOff(self, off, val):
        for i in range(self.KEYNUM):
            if self.KOff[i] != -1 and self.KOff[i] == off:
                self.KVal = val
                return True
        return False

    def IsKOffValue(self, off):
        for i in range(self.KEYNUM):
            if self.KOff[i] != -1 and self.KOff[i] == off:
                return True
        return False


    def FUN_10042a60(self):
        locc = 0
        loc10 = -1
        i = 0
        while i < CMDSimpler.count:
            op = CMDSimpler.heap[i].instr

            if op.ID in (OP_CALL, OP_JMP):
                if op.operand[0].TID() != TID_VAL:
                    self.FUN_10042380(i, 0, -1, 1, 1)
            elif op.ID in (OP_CMP, OP_TEST):
                if loc10 != -1 and loc10 + 1 == i:
                    CMDSimpler.heap[i].index = 1
                else:
                    op1 = CMDSimpler.heap[i + 1].instr
                    if op1.ID == OP_PUSHF or op1.ID == 0 or (op1.ID > OP_JMP and op1.ID < OP_JCXZ):
                        self.FUN_10042380(i, 0, -1, 1, 1)
                        if op.operand[1].TID() != TID_VAL:
                            self.FUN_10042380(i, 1, -1, 1, 1)
            elif op.ID in range(OP_JA, OP_JCXZ):
                CMDSimpler.heap[i].index = 1
                if i > 0:
                    self.FUN_10042380(i  - 1, 0, -1, 1, 1)
                    if  CMDSimpler.heap[i - 1].instr.operand[1].TID() == TID_REG:
                        self.FUN_10042380(i - 1, 1, -1, 1, 1)
            elif op.ID == OP_MOVS:
                CMDSimpler.heap[i].index = 1
                self.FUN_10042380(i, 0, -1, 1, 1)
                self.FUN_10042380(i, 1, -1, 1, 1)
            elif op.ID == OP_POP:
                CMDSimpler.heap[i].index = 1
                if op.operand[0].TID() == TID_MEM:
                    self.FUN_10042380(i, 0, -1, 1, 1)
            elif op.ID == OP_PUSHF:
                CMDSimpler.heap[i].index = 1
                if loc10 + 2 != i:
                    op1 = CMDSimpler.heap[i - 1].instr
                    if op1.operand[0].TID() == TID_REG:
                        self.FUN_10042380(i - 1, 0, -1, 1, 1)
                    if op1.operand[0].TID() == TID_MEM:
                        self.FUN_10042380(i - 1, 0, -1, 1, 1)
                    if op1.operand[1].TID() == TID_REG:
                        self.FUN_10042380(i - 1, 1, -1, 1, 1)
            elif op.ID == OP_RETN:
                CMDSimpler.heap[i].index = 1
            elif op.ID != 0:
                if op.ID == OP_NOT:
                    loc10 = i

                if locc == 1 and self.f_2c == 0 and IsOpClass(op.ID, 0, 0, 1) and\
                       op.operand[0].ID == ID_MEM32 and op.operand[1].ID == ID_REG and\
                       op.operand[0].GetB(1) == R_EBP and op.operand[0].GetB(2) == 0 and op.operand[0].GetB(3) == 0 and\
                       self.IsKOffValue(op.operand[0].val2) == False and op.operand[0].val2 != self.vmEIP:
                    self.f_2c = 1
                    self.f_2a = op.operand[0].val2 & 0xFFFF
                    op.ID = 0
                elif locc == 1 and self.f_2c == 1 and IsOpClass(op.ID, 0, 0, 1) and\
                        op.operand[0].ID == ID_MEM32 and op.operand[1].ID == ID_REG and \
                        op.operand[0].GetB(1) == R_EBP and op.operand[0].GetB(2) == 0 and op.operand[0].GetB(3) == 0 and\
                        op.operand[0].val2 == self.f_2a:
                    op.ID = 0
                else:
                    if locc == 0 and op.ID == OP_MOV and op.operand[0].ID == ID_REG and op.operand[1].ID == ID_MEM32 and\
                       op.operand[1].GetB(1) == R_EBP and op.operand[1].GetB(2) == 0 and op.operand[1].GetB(3) == 0 and\
                       op.operand[1].val2 == self.val7:
                        locc = 1
                    if op.operand[0].ID == 0:
                        CMDSimpler.heap[i].index = 1
                    elif op.operand[0].TID() == TID_VAL:
                        CMDSimpler.heap[i].index = 1
                    elif op.operand[0].TID() == TID_MEM:
                        CMDSimpler.heap[i].index = 1
                        self.FUN_10042380(i, 0, -1, 1, 1)
                        if op.operand[1].TID() == TID_REG:
                            CMDSimpler.heap[i].index = 1
                            self.FUN_10042380(i, 1, -1, 1, 1)
                    elif op.operand[1].TID() == TID_MEM:
                        CMDSimpler.heap[i].index = 1
                        self.FUN_10042380(i, 1, -1, 1, 1)
                    else:
                        if op.ID == OP_PUSH and op.operand[0].TID() == TID_REG:
                            CMDSimpler.heap[i].index = 1
                            self.FUN_10042380(i, 0, -1, 1, 1)
                        if op.operand[0].TID() == TID_REG and (op.operand[0].GetB(0) >> 4) == 4: # xSP
                            CMDSimpler.heap[i].index = 1
            i += 1

        for i in range(CMDSimpler.count):
            if CMDSimpler.heap[i].index == 0:
                CMDSimpler.heap[i].instr.ID = 0

        CMDSimpler.Cleaner()

    def SetKVOff(self, id, off, val):
        self.KVal[id] = val
        self.KOff[id] = off

    def CheckForKeysHandle(self):
        if CMDSimpler.count < 8:
            return False

        for i in range(self.KEYNUM):
            op = CMDSimpler.heap[i].instr

            if op.ID != OP_MOV:
                return False

            ##Added 7
            if i not in (5,6,7) and op.operand[0].ID != ID_MEM32:
                return False

            if i == 5 and op.operand[0].ID != ID_MEM16:
                return False

            ##Added ID_MEM16
            if i == 6 and op.operand[0].ID not in (ID_MEM8, ID_MEM16):
                return False

            ##New
            if i == 7 and op.operand[0].ID not in (ID_MEM8, ID_MEM16):
                return False

            if op.operand[0].GetB(1) != R_EBP or op.operand[0].GetB(2) != 0 or op.operand[0].GetB(3) != 0:
                return False

            if op.operand[1].TID() != TID_VAL:
                return False

            if op.operand[1].value != 0:
                return False

            #print("Add key", hex(op.operand[0].val2))
            self.SetKVOff(i, op.operand[0].val2, 0)
        return True

    def ProcessToNextHndl(self):
        if CMDSimpler.count <= 2:
            return False

        cmds = CMDSimpler.heap
        op1 = cmds[CMDSimpler.count - 2].instr
        op2 = cmds[CMDSimpler.count - 1].instr

        ## ADD dword[ebp + vmEIP], imm
        ## JMP
        if op1.ID == OP_ADD and op1.operand[0].ID == ID_MEM32 and\
           op1.operand[0].GetB(1) == R_EBP and op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and\
           op1.operand[0].val2 == self.vmEIP and op1.operand[1].TID() == TID_VAL and\
           op2.ID == OP_JMP:
            N = op1.operand[1].value
            j = CMDSimpler.count - 3
            flg = False
            while j > -1 and flg == False:
                opj = CMDSimpler.heap[j].instr

                ## search up for
                ## MOV reg(not esp/ebp), dword[ebp + vmEIP]
                if opj.ID == OP_MOV and opj.operand[0].ID == ID_REG and opj.operand[0].GetB(0) not in (R_ESP, R_EBP) and\
                   opj.operand[1].ID == ID_MEM32 and\
                   opj.operand[1].GetB(1) == R_EBP and opj.operand[1].GetB(2) == 0 and opj.operand[1].GetB(3) == 0 and\
                   opj.operand[1].val2 == self.vmEIP:
                    flg = True
                    ## ADD  reg, imm
                    opj1 = CMDSimpler.heap[j + 1].instr
                    if opj1.ID == OP_ADD and opj1.operand[0].ID == ID_REG and\
                       opj1.operand[0].GetB(0) == opj.operand[0].GetB(0) and\
                       opj1.operand[1].TID() == TID_VAL and N < 0x32:
                        m = self.GetMM( UINT(self.push1 + opj1.operand[1].value) )
                        #print("{:08x} ".format(UINT(self.push1 + opj1.operand[1].value)))
                        self.push2_2 = GetWORD(m)
                        self.push1 = UINT(self.push1 + N)
                        return True
                j -= 1

            print(j)
        return False

    def KeyWalk(self):
        b = GetBytes(UINT(self.val1 + self.val7), 4)
        if not b:
            return False

        ibase = GetDWORD(b)
        if self.iatAddr == ibase:
            ibase = 0
        else:
            ibase = self.imageBase

        print("[AntiFISH] Searching for keys...")

        for i in range(self.KEYNUM):
            self.KVal[i] = 0
            self.KOff[i] = -1

        f = open("{}/TXT/Fish_KeyWalk_{:08x}.txt".format(self.WrkDir, self.VMAddr),"w")

        for i in range(5):
            m = self.GetMM(UINT(self.iatAddr + self.push2_2 * 4))
            haddr = GetDWORD(m)

            self.DumpHandler(UINT(ibase + haddr), 1)

            print("Process handle at {:08x}".format( UINT(ibase + haddr) ))

            f.write("//////////////////////////////////////////////\r\n// FISH Virtual Handler {:04x} {:08X}\r\n".format(i, UINT(ibase + haddr) ))
            for l in CMDSimpler.GetListing(True, False):
                f.write("{}\n".format(l))

            if self.CheckForKeysHandle():
                f.close()
                print("Key found")
                return True

            if not self.ProcessToNextHndl():
                f.close()
                return False
        f.close()
        return False


    def IsVmEipOp(self, op):
        if op.operand[0].ID == ID_REG and op.operand[1].ID == ID_MEM32 and\
            op.operand[1].GetB(1) == R_EBP and op.operand[1].GetB(2) == 0 and op.operand[1].GetB(3) == 0 and\
            op.operand[1].val2 == self.vmEIP:
            return True
        elif op.operand[0].ID == ID_MEM32 and \
             op.operand[0].GetB(1) == R_EBP and op.operand[0].GetB(2) == 0 and op.operand[0].GetB(3) == 0 and \
             op.operand[0].val2 == self.vmEIP:
            return True
        return False

    def GetVmEipReadOpLastIndex(self):
        i = CMDSimpler.count - 1
        while i >= 0:
            op = CMDSimpler.heap[i].instr
            if op.ID == OP_MOV and op.operand[0].ID == ID_REG and self.IsVmEipOp(op):
                return i
            i -= 1
        return -1

    def RecoverJumpData(self, h):
        cmds = CMDSimpler.heap
        if cmds[CMDSimpler.count - 1].instr.ID != OP_JMP:
            return True

        i = self.GetVmEipReadOpLastIndex()
        if i == -1:
            print("EIP")
            return False

        h.flowReadIndex = i
        reg = cmds[i].instr.operand[0].GetB(0)

        while True:
            i += 1
            if i >= CMDSimpler.count:
                return False

            ## ADD  reg, imm
            op = cmds[i].instr
            if op.ID == OP_ADD and op.operand[0].ID == ID_REG and op.operand[0].GetB(0) == reg and \
               op.operand[1].TID() == TID_VAL:
                break

        i += 1
        if cmds[CMDSimpler.count - 2].instr.ID == OP_ADD:
            h.f_62c = 5
            h.f_628 = 0
            h.f_624 = 0
            h.idxList = []

            while True:
                if i >= CMDSimpler.count:
                    return False

                op = cmds[i].instr

                if op.ID == OP_MOVZX and op.operand[0].ID == ID_REG and op.operand[1].ID == ID_MEM16 and\
                   op.operand[1].GetB(1) == reg and op.operand[1].GetB(2) == 0 and op.operand[1].GetB(3) == 0 and\
                   op.operand[1].val2 == 0:
                    h.f_5d8 = i
                    reg = op.operand[0].GetB(0)
                    break

                if op.ID == OP_MOV and op.operand[0].ID == ID_REG and op.operand[1].ID == ID_MEM16 and\
                   op.operand[1].GetB(1) == reg and op.operand[1].GetB(2) == 0 and op.operand[1].GetB(3) == 0 and \
                   op.operand[1].val2 == 0:
                    h.f_5d8 = i
                    return True
                i += 1

            i += 1
            while True:
                if i >= CMDSimpler.count:
                    return False

                op = cmds[i].instr

                if op.ID == OP_AND and op.operand[0].ID == ID_REG and op.operand[1].TID() == TID_VAL and\
                   op.operand[0].GetB(0) == reg and op.operand[1].value == 0xFFFF:
                    return True

                if IsOpClass(op, 0, 0, 1):
                    if self.IsIdxOpEbpKey(i, 0):
                        if op.operand[0].ID == ID_REG and op.operand[0].GetB(0) == reg:
                            h.idxList.append( i )
                        elif op.operand[1].ID == ID_REG and op.operand[1].GetB(0) == reg:
                            h.idxList.append(i)
                    if op.operand[0].ID == ID_REG and op.operand[1].TID() == TID_VAL and op.operand[0].GetB(0) == reg:
                        h.f_624 = i
                        h.f_62c = op.ID
                        h.f_628 = op.operand[1].value
                i += 1

        elif cmds[CMDSimpler.count - 2].instr.ID == OP_SUB:
            h.f_62c = 5
            h.f_628 = 0
            h.f_624 = 0
            h.idxList = []

            while True:
                if i >= CMDSimpler.count:
                    return False

                op = cmds[i].instr

                if op.ID == OP_MOV and op.operand[0].ID == ID_REG and op.operand[1].ID == ID_MEM32 and\
                   op.operand[1].GetB(1) == reg and op.operand[1].GetB(2) == 0 and op.operand[1].GetB(3) == 0 and \
                   op.operand[1].val2 == 0:
                    h.f_5d8 = i
                    reg = op.operand[0].GetB(0)
                    return True
                i += 1

            i += 1
            while True:
                if i >= CMDSimpler.count:
                    return False

                op = cmds[i].instr

                if op.ID == OP_AND and op.operand[0].ID == ID_REG and op.operand[1].TID() == TID_VAL and \
                   op.operand[0].GetB(0) == reg and op.operand[1].value == 0x80000000:
                    return True
                i += 1

        return True

    def RecoverKeyData(self, h):
        for i in range(CMDSimpler.count):
            if not self.IsIdxOpEbpKey(i, 0):
                continue

            ## ADD/SUB/XOR/AND/OR/SHL/SHR     not MOV

            cmd = CMDSimpler.heap[i]
            op = cmd.instr

            key = FKEY()
            if cmd.keyData & 0x80000000 == 0x80000000:
                if op.operand[0].TID() == TID_MEM:
                    key.flg1 = 0
                    key.flg2 = 1
                    key.koff1 = op.operand[0].val2 & 0xFFFF
                    key.ID = op.ID
                    key.idx = cmd.index
                    key.oprID = (op.operand[1].ID & 0xF0) | (op.operand[0].ID & 0xF)
                    key.koff2 = cmd.keyData & 0x7FFFFFFF
                else:
                    key.flg1 = 1
                    key.flg2 = 0
                    key.koff1 = op.operand[1].val2 & 0xFFFF
                    key.ID = op.ID
                    key.idx = cmd.index
                    key.oprID = (op.operand[0].ID & 0xF0) | (op.operand[1].ID & 0xF)
                    key.koff2 = cmd.keyData & 0x7FFFFFFF
                cmd.keyData = 0
            else:
                if op.operand[0].TID() == TID_MEM:
                    key.flg1 = 0
                    key.flg2 = 0
                    key.koff1 = op.operand[0].val2 & 0xFFFF
                    key.ID = op.ID
                    key.idx = cmd.index
                    key.oprID = (op.operand[1].ID & 0xF0) | (op.operand[0].ID & 0xF)
                    key.koff2 = op.operand[1].value
                else:
                    key.flg1 = 1
                    key.flg2 = 0
                    key.koff1 = op.operand[1].val2 & 0xFFFF
                    key.ID = op.ID
                    key.idx = cmd.index
                    key.oprID = (op.operand[0].ID & 0xF0) | (op.operand[1].ID & 0xF)
                    key.koff2 = op.operand[0].value

            op.ID = 0
            h.keys.append(key)

        CMDSimpler.Cleaner()
        return True

    def CheckHndl1E(self):
        n = 0
        idx1 = -1
        idx2 = -1
        val1 = 0
        val2 = 0

        for i in range(10):
            if i >= CMDSimpler.count or n >= 2:
                break
            op = CMDSimpler.heap[i].instr
            if n == 0:
                if self.IsVmEipOp(op):
                    val1 = op.operand[0].GetB(0)
                    idx1 = i
                    n += 1
            elif n == 1:
                if self.IsVmEipOp(op):
                    val2 = op.operand[0].GetB(0)
                    idx2 = i
                    n += 1

        if n < 2:
            return False

        for j in range(2):
            i = 0
            reg = 0
            if j == 0:
                i = idx1
                reg = val1
            else:
                i = idx2
                reg = val2

            ri, rcmd = CMDSimpler.NextOp0Reg(i + 1, reg)
            if rcmd == None or rcmd.instr.ID != OP_ADD:
                return False

            ri, rcmd = CMDSimpler.NextOp1MemReg(ri + 1, reg)
            if rcmd == None or rcmd.instr.ID != OP_MOVZX:
                return False

            reg = rcmd.instr.operand[0].GetB(0)

            ri, rcmd = CMDSimpler.NextOp0Reg(ri + 1, reg)
            if rcmd == None or rcmd.instr.ID != OP_ADD or\
               rcmd.instr.operand[1].ID != ID_REG or rcmd.instr.operand[1].GetB(0) != R_EBP:
                return False

            ri, rcmd = CMDSimpler.NextOp1MemReg(ri + 1, reg)
            if rcmd == None or ri > 10:
                return False

            if rcmd.instr.ID == OP_ADD:
                if rcmd.instr.operand[1].TID != TID_VAL or rcmd.instr.operand[1].value != 4:
                    return False
            else:
                if rcmd.instr.ID != OP_POP:
                    return False
                if rcmd.instr.operand[0].TID() != TID_MEM:
                    return False
        return True

    def CheckHndl1D(self):
        n = 0
        idx1 = -1
        idx2 = -1
        val1 = 0
        val2 = 0

        for i in range(25):
            if i >= CMDSimpler.count or n >= 2:
                break
            op = CMDSimpler.heap[i].instr
            if n == 0:
                if self.IsVmEipOp(op):
                    val1 = op.operand[0].GetB(0)
                    idx1 = i
                    n += 1
            elif n == 1:
                if self.IsVmEipOp(op):
                    val2 = op.operand[0].GetB(0)
                    idx2 = i
                    n += 1

        if n < 2:
            return False

        for j in range(2):
            i = 0
            reg = 0
            if j == 0:
                i = idx1
                reg = val1
            else:
                i = idx2
                reg = val2

            ## find ADD  reg, ...
            ri, rcmd = CMDSimpler.NextOp0Reg(i + 1, reg)
            if rcmd == None or rcmd.instr.ID != OP_ADD:
                return False

            ## find MOVZX  ..., [reg]
            ri, rcmd = CMDSimpler.NextOp1MemReg(ri + 1, reg)
            if rcmd == None or rcmd.instr.ID != OP_MOVZX:
                return False

            ## change reg
            reg = rcmd.instr.operand[0].GetB(0)

            ## find ADD  reg, ebp
            ri, rcmd = CMDSimpler.NextOp0Reg(ri + 1, reg)
            if rcmd == None or rcmd.instr.ID != OP_ADD or\
               rcmd.instr.operand[1].ID != ID_REG or rcmd.instr.operand[1].GetB(0) != R_EBP:
                return False

            ## find  ...  [reg], ...
            ri, rcmd = CMDSimpler.NextOp0MemReg(ri + 1, reg)
            if rcmd == None or ri > 25:
                return False

            ##  is   SUB [reg], 4
            if rcmd.instr.ID == OP_SUB:
                if rcmd.instr.operand[1].TID != TID_VAL or rcmd.instr.operand[1].value != 4:
                    return False
            ## or is  PUSH [reg]
            elif rcmd.instr.ID != OP_PUSH or rcmd.instr.operand[0].TID() != TID_MEM:
                    return False
        print("1D")
        return True

    def CheckHndl20(self):
        for i in range(3, 9):
            if i >= CMDSimpler.count:
                break
            op = CMDSimpler.heap[i].instr
            ## ADD  esp, REG(not esp)
            if op.ID == OP_ADD and op.operand[0].ID == ID_REG and op.operand[1].ID == ID_REG and\
               op.operand[0].GetB(0) == R_ESP and op.operand[1].GetB(0) != R_ESP:
                return True
                print("20")
        return False

    def CheckHndlPUSHF(self, h):
        cmds = CMDSimpler.heap
        if CMDSimpler.count > 16 and cmds[11].instr.ID == OP_SUB and cmds[12].instr.ID == OP_PUSHF:
            i = CMDSimpler.NextOpPos(OP_CMP, 13)
            if i != -1:
                op0 = cmds[i].instr
                op1 = cmds[i + 1].instr
                op2 = cmds[i + 2].instr
                op3 = cmds[i + 3].instr

                if op0.operand[1].TID() == TID_VAL and op0.operand[1].value == 0 and\
                   op1.ID == OP_JE and op2.ID == OP_SUB and op3.ID == OP_SUB and\
                   op2.operand[1].TID() == TID_VAL:
                    if op2.operand[1].value == 4:
                        h.tp = 0x13
                        return True
                    if op2.operand[1].value == 2:
                        h.tp = 0x12
                        return True
                    if op2.operand[1].value == 1:
                        h.tp = 0x11
                        return True

        if CMDSimpler.count > 16 and cmds[11].instr.ID == OP_CMP and cmds[12].instr.ID == OP_PUSHF:
            i = CMDSimpler.NextOpPos(OP_CMP, 13)
            if i != -1:
                op0 = cmds[i].instr
                op1 = cmds[i + 1].instr
                op2 = cmds[i + 2].instr
                op3 = cmds[i + 3].instr

                if op0.operand[1].TID() == TID_VAL and op0.operand[1].value == 0 and\
                   op1.ID == OP_JE and op2.ID == OP_SUB and op3.ID == OP_SUB and\
                   op2.operand[1].TID() == TID_VAL:
                    if op2.operand[1].value == 4:
                        h.tp = 0x16
                        return True
                    if op2.operand[1].value == 2:
                        h.tp = 0x15
                        return True
                    if op2.operand[1].value == 1:
                        h.tp = 0x14
                        return True

        if CMDSimpler.count > 27 and cmds[11].instr.ID == OP_CMP and cmds[26].instr.ID == OP_CMP and cmds[27].instr.ID == OP_JE:
            i = CMDSimpler.NextOpPos(OP_CMP, 11)
            if i != -1:
                op0 = cmds[i].instr
                op1 = cmds[i + 1].instr
                op2 = cmds[i + 2].instr
                op3 = cmds[i + 3].instr

                if op0.operand[1].TID() == TID_VAL and op0.operand[1].value == 0 and\
                   op1.ID == OP_JE and op2.ID == OP_SUB and op3.ID == OP_SUB and\
                   op3.operand[1].TID() == TID_VAL:
                    if op3.operand[1].value == 4:
                        h.tp = 0x1c
                        return True
                    if op3.operand[1].value == 2:
                        h.tp = 0x1b
                        return True
                    if op3.operand[1].value == 1:
                        h.tp = 0x1a
                        return True

        if CMDSimpler.count > 21 and cmds[11].instr.ID == OP_MOV and cmds[17].instr.ID == OP_AND and cmds[18].instr.ID == OP_POP:
            i = CMDSimpler.NextOpPos(OP_PUSH, 2)
            if i != -1 and i < 11 and cmds[i].instr.operand[0].TID() == TID_REG:
                j = -1
                for k in range(i, 16):
                    if cmds[k].instr.ID == OP_MOV and cmds[k].instr.operand[0].TID() == TID_MEM:
                        j = k
                        break

                if j != -1 and cmds[19].instr.ID == OP_CMP and cmds[19].instr.operand[1].TID() == TID_VAL and \
                   cmds[19].instr.operand[1].value == 0 and cmds[20].instr.ID == OP_JE and cmds[21].instr.ID == OP_SUB:

                    if cmds[j].instr.operand[0].GetB(1) == cmds[i].instr.operand[0].GetB(0):
                        if cmds[21].instr.operand[1].value == 4:
                            h.tp = 0x19
                            return True
                        if cmds[21].instr.operand[1].value == 2:
                            h.tp = 0x18
                            return True
                        if cmds[21].instr.operand[1].value == 1:
                            h.tp = 0x17
                            return True
                    else:
                        if cmds[21].instr.operand[1].value == 4:
                            h.tp = 0x10
                            return True
                        if cmds[21].instr.operand[1].value == 2:
                            h.tp = 0xf
                            return True
                        if cmds[21].instr.operand[1].value == 1:
                            h.tp = 0xe
                            return True
        return False

    def CheckHndl24(self):
        cmds = CMDSimpler.heap
        if CMDSimpler.count < 6:
            return False

        flg = 0
        reg = 0
        for i in range(5):
            op = cmds[i].instr
            if op.operand[0].TID() == TID_MEM:
                return False
            if op.ID == OP_MOV and op.operand[1].TID() == TID_MEM:
                if self.IsVmEipOp(op):
                    flg += 1
                elif op.operand[0].ID == ID_REG and (op.operand[0].GetB(0) & 0xF) == 3 and \
                     op.operand[1].GetB(1) == R_EBP and not self.IsKOffValue(op.operand[1].val2):
                    reg = op.operand[0].GetB(0)
        if flg == 1 and cmds[5].instr.operand[0].ID == ID_MEM32 and cmds[5].instr.operand[1].ID == ID_REG and \
                        cmds[5].instr.operand[1].GetB(0) == reg:
            return True
        return False

    def CheckSeq1(self, fsq):
        cmds = CMDSimpler.heap
        flg = 0
        res = True

        if CMDSimpler.count < len(fsq.seq):
            return False

        if fsq.tp == 0xb and (CMDSimpler.count < 25 or CMDSimpler.NextOpPos(OP_RETN, CMDSimpler.count - 25) == -1):
            return False

        for i in range(len(fsq.seq)):
            op = cmds[i].instr

            sid = fsq.seq[i]
            if sid == 0xFFFF:
                continue
            elif sid == 0xFFFE:
                if not IsOpClass(op.ID, 0, 0, 1):
                    return False
            else:
                if op.ID != sid:
                    return False

                if fsq.tp == 5:
                    if i == 7 and (op.operand[1].ID != ID_REG or op.operand[1].GetB(0) != R_ESP):
                        return False
                elif fsq.tp == 0xc:
                    if i == 5:
                        if cmds[3].instr.operand[0].GetB(0) != cmds[4].instr.operand[1].GetB(1) or \
                           cmds[4].instr.operand[0].GetB(0) != op.operand[1].GetB(1):
                            return False
                elif fsq.tp == 0xd:
                    if i == 9:
                        if cmds[3].instr.operand[0].GetB(0) != cmds[4].instr.operand[1].GetB(1) or \
                           cmds[4].instr.operand[0].GetB(0) != op.operand[1].GetB(1):
                            return False
                elif fsq.tp == 0x1f:
                    if i == 3:
                        if op.operand[1].ID != ID_REG:
                            return False
                elif fsq.tp == 0x20:
                    if i == 6:
                        if op.operand[0].ID != ID_REG or (op.operand[0].GetB(0) & 0xF) != 3 or op.operand[1].ID not in(ID_MEM8, ID_MEM16):
                            return False
                    elif i == 7:
                        if op.operand[0].ID != ID_REG or op.operand[0].GetB(0) != R_ESP:
                            return False
                elif fsq.tp == 0x21:
                    if i == 4:
                        if op.operand[0].ID != ID_REG or op.operand[0].GetB(0) != R_ESP:
                            return False
                elif fsq.tp == 0x22:
                    if i == 4:
                        if op.operand[1].ID != ID_REG or op.operand[1].GetB(0) != R_ESP:
                            return False
        return True

    def CheckSeq2(self, off, fsq):
        for i, sid in enumerate(fsq.seq):
            op = CMDSimpler.heap[off + i].instr
            #sid = fsq.seq[i]
            if sid == 0xFFFF:
                continue
            elif sid == 0xFFFE:
                if not IsOpClass(op.ID, 0, 0, 1):
                    return False
            elif op.ID != sid:
                return False

        cmds = CMDSimpler.heap
        if fsq.tp == 9:
            if not self.IsVmEipOp(cmds[off].instr):
                return False
            if cmds[off + 2].instr.operand[1].ID not in(ID_MEM8, ID_MEM16):
                return False
        elif fsq.tp == 7:
            if cmds[off + 5].instr.operand[1].ID != ID_MEM32:
                return False

            if cmds[off + 5].instr.operand[1].val2 != self.vmImgBase:
                return False
        elif fsq.tp == 0xa:
            op = cmds[off + len(fsq.seq) - 1].instr
            if op.ID != OP_MOV or op.operand[0].ID not in(ID_MEM8, ID_MEM16) or\
               op.operand[0].GetB(1) != R_EBP or op.operand[0].GetB(2) != 0  or op.operand[0].GetB(3) != 0 or\
               op.operand[1].ID not in (ID_VAL8, ID_VAL16) or op.operand[1].value != 0:
                return False
        return True


    def CheckSeq2_2(self, lst):
        tp_cnt = [0] * 12
        for v in lst:
            if v <= 10:
                tp_cnt[v] += 1

        if len(lst) >= 10 and tp_cnt[9] == 1 and tp_cnt[8] == 2 and tp_cnt[6] == 2 and tp_cnt[5] == 1 and\
                tp_cnt[4] == 1 and tp_cnt[3] == 0 and tp_cnt[1] == 1 and tp_cnt[0] == 1:
            return 2
        elif len(lst) >= 8 and tp_cnt[9] == 0 and tp_cnt[8] == 2 and tp_cnt[6] == 2 and tp_cnt[5] == 0 and \
                tp_cnt[4] == 2 and tp_cnt[3] == 0 and tp_cnt[2] == 1 and tp_cnt[1] == 0 and tp_cnt[0] == 1:
            return 4
        elif len(lst) >= 4 and tp_cnt[9] == 1 and tp_cnt[8] == 1 and tp_cnt[6] == 1 and tp_cnt[5] == 0 and \
                tp_cnt[4] == 1 and tp_cnt[3] == 0 and tp_cnt[1] == 0 and tp_cnt[0] == 1 and \
                CMDSimpler.NextOpPos(OP_PUSHF, 10) != -1:
            return 1
        elif len(lst) >= 6 and tp_cnt[9] == 1 and tp_cnt[8] == 1 and tp_cnt[6] == 1 and \
                tp_cnt[4] == 1 and tp_cnt[3] == 1 and tp_cnt[0] == 1:
            return 0
        elif len(lst) >= 2 and tp_cnt[9] == 0 and tp_cnt[8] == 1 and tp_cnt[7] == 1 and tp_cnt[6] == 0 and \
                tp_cnt[4] == 0 and tp_cnt[3] == 0 and tp_cnt[0] == 0:
            return 3

        return -1

    def GetTpSeq2Len(self, tp):
        for sq in self.SeqData2:
            if sq.tp == tp:
                return len(sq.seq)
        return -1

    def RecoveryHandleType(self, h):
        cmds = CMDSimpler.heap
        if self.CheckHndl1E():
            h.tp = 0x1e
        elif self.CheckHndl1D():
            h.tp = 0x1d
        elif self.CheckHndl1D():
            h.tp = 0x20
        elif self.CheckHndlPUSHF(h):
            return
        elif self.CheckHndl24():
            h.tp = 0x24
        elif CMDSimpler.count > 8 and (cmds[8].instr.ID == OP_STD or cmds[9].instr.ID == OP_STD):
            h.tp = 0xa
        else:
            for fsq in self.SeqData1:
                if self.CheckSeq1(fsq):
                    h.tp = fsq.tp
                    return

            off = 0
            h.f_530 = []
            i = 0
            while i < len(self.SeqData2):
                fsq = self.SeqData2[i]
                if self.CheckSeq2(off, fsq):
                    h.f_530.append( fsq.tp )
                    off += len(fsq.seq)
                    i = 0
                    if fsq.tp == 3:
                        break
                else:
                    i += 1

            print(h.f_530)
            h.tp = self.CheckSeq2_2(h.f_530)

            if h.tp == 0:
                if self.hndl_tp0_fnd == 0:
                    off = 0
                    for v in h.f_530:
                        if v == 6:
                            self.f_c01c = cmds[off + 9].instr.operand[0].val2 & 0xFFFF
                        elif v == 8:
                            self.f_c01a = cmds[off + 5].instr.operand[0].val2 & 0xFFFF

                        l = self.GetTpSeq2Len(v)
                        if l > 0:
                            off += l
                    self.hndl_tp0_fnd = 1
            elif h.tp == 2:
                if self.hndl_tp2_fnd == 0 and self.hndl_tp0_fnd == 1:
                    off = 0
                    for v in h.f_530:
                        if v == 6:
                            self.f_c020 = cmds[off + 9].instr.operand[0].val2 & 0xFFFF
                        elif v == 8 and (cmds[off + 5].instr.operand[0].val2 & 0xFFFF) != self.f_c01a:
                            self.f_c01e = cmds[off + 5].instr.operand[0].val2 & 0xFFFF

                        l = self.GetTpSeq2Len(v)
                        if l > 0:
                            off += l
                    self.hndl_tp2_fnd = 1




    def RecoverHandle(self, h, fdbg = None):
        if not self.RecoverJumpData(h):
            print("Error while recover jump data")
            return False

        if not self.RecoverKeyData(h):
            print("Error while recover key data")
            return False

        if fdbg != None:
            if CMDSimpler.count > 0:
                fdbg.write("//////////////////////////////////////////////\r\n// FISH Virtual Handler {:04x} {:08x}\r\n".format(h.hndlID, CMDSimpler.heap[0].addr))
                for l in CMDSimpler.GetListing(1, 1):
                    fdbg.write("{}\n".format(l))

        if h.hndlID == 8:
            for l in CMDSimpler.GetListing(1, 1):
                print(l)

        self.RecoveryHandleType(h)

        if h.tp == -1:
            print("Error while recover handler type")
            return False
        else:
            print("Handler {:x}".format(h.tp))

        return True






    def EnumOps(self):
        for i in range(CMDSimpler.count):
            CMDSimpler.heap[i].index = i


    def DeofusVM(self):
        b = GetBytes(UINT(self.val1 + self.val7), 4)
        if not b:
            return False

        ibase = GetDWORD(b)
        if self.iatAddr == ibase:
            ibase = 0
        else:
            ibase = self.imageBase

        self.f_6f038 = 0

        f = open("{}/TXT/Fish_Machine_{:08x}.txt".format(self.WrkDir, self.VMAddr), "w")
        f2 = open("{}/TXT/Fish_Machine_dbg_{:08x}.txt".format(self.WrkDir, self.VMAddr), "w")
        for i in range(self.iatCount):
            m = self.GetMM( UINT(self.iatAddr + i * 4) )
            haddr = GetDWORD(m)

            self.DumpHandler( UINT(ibase + haddr), 1 )

            ####
            print("\tHandler {:04x} {:08x}".format(i, UINT(ibase + haddr)))
            f.write("//////////////////////////////////////////////\r\n// FISH Virtual Handler {:04x} {:08x}\r\n".format(i, UINT(ibase + haddr)))
            for l in CMDSimpler.GetListing(1, 1):
                f.write("{}\n".format(l))

            self.EnumOps()

            h = FHNDL(i)
            h.c024 = self.f_c024
            if not self.RecoverHandle(h, f2):
                #time.sleep(1.5)
                pass

            self.hndl[i] = h
            self.hndlCount += 1


