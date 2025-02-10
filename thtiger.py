import opcode
import time
from operator import truediv

import xrkdsm
from xrkutil import *
from xrkdsm import *
from thobfus import *
from xrkasm import *
from thvm import *
from thwild import *
from __main__ import *


TKEY_OPR1_32 = 3  #VM register index for operator 1 (32bit)
TKEY_OPR1_16 = 5  #VM register index for operator 1 (16bit)
TKEY_OPR0 = 6  #VM register index for operator 0

TKEY_OPERAND0 = (TKEY_OPR0, )
TKEY_OPERAND1 = (TKEY_OPR1_16, TKEY_OPR1_32)

TH_NOP = 0x2000 #

TH_PUSH = 0x2001
TH_POP = 0x2002 #

TH_INC = 0x2003 #
TH_DEC = 0x2004 #
TH_NOT = 0x2005 #
TH_NEG = 0x2006 #

TH_MOV = 0x2007 #
TH_MOVSX = 0x2008 #
TH_MOVZX = 0x2009 #

TH_ADD = 0x200a #
TH_SUB = 0x200b #
TH_AND = 0x200c #
TH_XOR = 0x200d #
TH_OR = 0x200e #

TH_SHL = 0x200f #
TH_SHR = 0x2010 #
TH_RCL = 0x2011 #
TH_RCR = 0x2012 #
TH_ROL = 0x2013 #
TH_ROR = 0x2014 #

TH_CMP = 0x2015 #
TH_TEST = 0x2016 #

TH_IMUL = 0x2017

TH_COUNT = 0x2018

TH_UNSHUFLE = 0x2019

TH_IMGBASE = 0x201A


THOP_UNSHUFFLE = 0x1100


TIGER_OPTXT = {THOP_UNSHUFFLE: "UNSHUFFLE"}

class REGTRACE:
    Key = -1
    Off = -1
    KeySz = 0
    DataTp = 0
    VmImg = False
    # 1 - reg
    # 2 - val
    # 3 - valmem
    # 4 - regmem



class TG_CTX_OP:
    isFound = False
    data = 0
    info = 0

class TG_OP_DEC:
    mnem = 0
    sz = 0
    data = 0

    def __init__(self, a=0, b=0, c=0):
        self.mnem = a
        self.sz = b
        self.data = c

class TG_OP:
    tp = 0
    sz = 0
    wrksz = 0
    idx = 0
    decoders = None
    tkey = -1
    flags = 0
    usei = -1
    useopr = -1

    def __init__(self):
        self.decoders = []

class THNDL(WHNDL):
    operands = None
    addr = 0
    opidx = -1

    def __init__(self, id = -1):
        WHNDL.__init__(self, id)
        self.operands = [TG_OP(), TG_OP()]

class TIGER(WILD):
    tigerOperands = None

    def __init__(self, d):
        WILD.__init__(self, WILD_TIGER, d)
        self.HANDLER = THNDL

        self.tigerOperands = [TG_CTX_OP(), TG_CTX_OP()]


    def CheckForKeysHandle(self):
        if CMDSimpler.count < 8:
            return False

        types = (ID_MEM32, ID_MEM32, ID_MEM32, ID_MEM32, ID_MEM32, ID_MEM16, ID_MEM16, ID_MEM16, ID_MEM32, ID_MEM32)

        for i in range(len(types)):
            op = CMDSimpler.heap[i].instr

            if op.ID == OP_MOV and op.operand[0]. ID == types[i] and\
               op.operand[0].GetB(1) == R_EBP and op.operand[0].GetB(2) == 0 and op.operand[0].GetB(3) == 0 and\
               op.operand[1].TID() == TID_VAL and op.operand[1].value == 0:
                self.AddKey(op.operand[0].val2)
            else:
                return False
        return True

    def FindOperandKeyReadIns(self, opkey, idx):
        for i in range(idx, CMDSimpler.count):
            op = CMDSimpler.heap[i].instr

            for opk in opkey:
                if (op.ID == OP_MOVZX or (opk == TKEY_OPR1_32 and op.ID == OP_MOV))  and op.operand[0].ID == ID_REG and \
                   op.operand[1].TID() == TID_MEM and \
                   op.operand[1].Base() == R_EBP and \
                   op.operand[1].GetB(2) == 0 and \
                   op.operand[1].GetB(3) == 0 and \
                   op.operand[1].val2 == self.GetKeyOffset(opk):
                    return (i, op)
        return (-1, None)

    def MapUnaryOperation(self, h, opid):

        i = 0
        while i < CMDSimpler.count:
            (ti, top) = self.FindOperandKeyReadIns( TKEY_OPERAND0, i)
            isop1 = False
            if ti == -1:
                if opid == OP_PUSH:
                    (ti, top) = self.FindOperandKeyReadIns(TKEY_OPERAND1, i)
                    isop1 = True

                if ti == -1:
                    i += 1
                    continue

            i = ti
            optp = TH_OPR_REG
            stg = 0
            for j in range(i + 1, CMDSimpler.count):
                jop = CMDSimpler.heap[j].instr
                if stg == 0 and \
                    jop.ID == OP_ADD and \
                    jop.operand[0].IsReg( top.operand[0].Base() ) and \
                    jop.operand[1].IsReg(R_EBP):
                    stg += 1
                elif stg == 1:
                    if jop.ID == OP_MOV and \
                        jop.operand[0].IsReg( top.operand[0].Base() ):
                        if jop.operand[1].IsMem32Base( top.operand[0].Base() ):
                            optp = TH_OPR_MEM_IMM
                        else:
                            break
                    elif jop.ID == opid and \
                        jop.operand[0].TID() == TID_MEM and\
                        jop.operand[0].Base() == top.operand[0].Base():
                        h.addr = CMDSimpler.heap[j].addr
                        h.operands[0].tp = optp
                        h.operands[0].sz = jop.operand[0].Size()
                        h.operands[0].idx = ti
                        h.operands[0].tkey = TKEY_OPR0

                        return j

                elif isop1 and stg == 0 and opid == OP_PUSH and \
                    jop.ID == opid and \
                    jop.operand[0].TID() == TID_REG and \
                    jop.operand[0].Base() == top.operand[0].Base():
                    h.addr = CMDSimpler.heap[j].addr
                    h.operands[0].tp = TH_OPR_MEM_IMM
                    h.operands[0].sz = jop.operand[0].Size()
                    h.operands[0].idx = ti
                    if isop1:
                        if top.operand[1].val2 == self.GetKeyOffset(TKEY_OPR1_32):
                            h.operands[0].tkey = TKEY_OPR1_32
                        else:
                            h.operands[0].tkey = TKEY_OPR1_16
                    else:
                        h.operands[0].tkey = TKEY_OPR0

                    return j

            i += 1
        return -1


    def FindOperand1VMSource(self, i, opt):
        op = CMDSimpler.heap[i].instr
        reg = op.operand[opt].XBase()

        # not xSP/xBP
        if reg in (R_xSP, R_xBP) or i <= 0:
            return (-1, 0, 0, 0)

        j = i - 1
        tp = TH_OPR_IMM
        cnt = 0
        movop = 0
        while j > -1:
            opj = CMDSimpler.heap[j].instr

            if opj.ID in (OP_MOV, OP_MOVSX, OP_MOVZX):
                if opj.operand[0].TID() == TID_REG and opj.operand[0].XBase() == reg:
                    if opj.operand[1].TID() == TID_REG:
                        if opj.operand[1].Base() not in (R_ESP, R_EBP):
                            reg = opj.operand[1].XBase()
                            if cnt == 0 and opj.ID in (OP_MOVSX, OP_MOVZX):
                                movop = opj.ID
                        else:
                            xlog("Something wrong! It's must not happen.")
                            return (-1, 0, 0, 0)
                    elif opj.operand[1].TID() == TID_MEM:
                        if opj.operand[1].Base() == R_EBP:
                            if opj.operand[1].val2 == self.GetKeyOffset(TKEY_OPR1_16):
                                return (j, tp, movop, TKEY_OPR1_16)
                            elif opj.operand[1].val2 == self.GetKeyOffset(TKEY_OPR1_32):
                                return (j, tp, movop, TKEY_OPR1_32)
                            else:
                                return (-1, 0, 0, 0)
                        else:
                            reg = opj.operand[1].XBase()
                            cnt += 1
                            if cnt >= 2:
                                tp = TH_OPR_MEM_IMM
                            elif movop == 0:
                                movop = opj.ID
            elif opj.ID == OP_ADD and\
                cnt == 1 and\
                opj.operand[0].ID == ID_REG and\
                opj.operand[0].Size() == 3 and\
                opj.operand[0].XBase() == reg and\
                opj.operand[1].ID == ID_REG and\
                opj.operand[1].Base() == R_EBP:
                tp = TH_OPR_REG

            j -= 1
        return (-1, 0, 0, 0)

    def MapBinOperation(self, h, idx, opid, dbg = False):
        opKeyIns = None
        i = 0
        while i < CMDSimpler.count:
            (ti, top) = self.FindOperandKeyReadIns(TKEY_OPERAND0, i)
            if ti == -1:
                i += 1
                continue

            topreg = top.operand[0].Base()

            i = ti
            op0tp = TH_OPR_REG
            stg = 0
            sepidx = -1
            sepreg = -1
            mreg = -1
            for j in range(i + 1, CMDSimpler.count):
                jop = CMDSimpler.heap[j].instr
                if stg == 0 and \
                   jop.ID == OP_ADD and \
                   jop.operand[0].IsReg( topreg ) and \
                   jop.operand[1].IsReg(R_EBP):
                    stg += 1
                    if dbg:
                        xlog("stg +1 at {:x}".format(CMDSimpler.heap[j].addr))
                elif stg == 1:
                    if jop.ID == OP_MOV and jop.operand[0].IsReg( topreg ):
                        if jop.operand[1].IsMem32Base( topreg ):
                            op0tp = TH_OPR_MEM_IMM
                        else:
                            break
                    elif jop.ID == OP_MOV and jop.operand[0].ID == ID_REG and jop.operand[1].IsMem32Roff( topreg, 0, 0, 0 ):
                        sepreg = jop.operand[0].XBase()
                        if dbg:
                            xlog("sepreg", sepreg)
                    elif jop.ID == OP_MOV and jop.operand[0].TID() == TID_REG and jop.operand[0].XBase() == (topreg >> 4):
                        if dbg:
                            xlog("break MOV reg at {:x}".format(CMDSimpler.heap[j].addr))
                        break
                    elif jop.ID == OP_MOV and jop.operand[0].ID == ID_REG and jop.operand[1].IsReg(topreg):
                        topreg = jop.operand[0].Base()
                    elif jop.ID == opid and \
                        jop.operand[0].TID() == TID_MEM and\
                        jop.operand[0].Base() == topreg:

                        (op1i, op1tp, movop, t1key) = self.FindOperand1VMSource(j, 1)

                        #if opid == OP_RCR:
                        #    xlog("RCR", op1i, op1tp, movop, t1key)

                        if op1i == -1:
                            break

                        h.addr = CMDSimpler.heap[j].addr
                        h.operands[0].tp = op0tp
                        h.operands[0].sz = jop.operand[0].Size()
                        h.operands[0].idx = i
                        h.operands[0].tkey = TKEY_OPR0
                        h.operands[1].tp = op1tp
                        h.operands[1].sz = jop.operand[1].Size()
                        h.operands[1].wrksz = CMDSimpler.heap[op1i].instr.operand[1].Size()
                        h.operands[1].idx = op1i
                        h.operands[1].tkey = t1key

                        return j
                    elif sepreg != -1 and jop.ID == opid and \
                         jop.operand[0].TID() == TID_REG and \
                         jop.operand[0].XBase() == sepreg:
                        sepidx = j
                    elif sepreg != -1 and sepidx != -1 and \
                         j - sepidx < 5 and\
                        jop.ID == OP_MOV and \
                        jop.operand[0].TID() == TID_MEM and\
                        jop.operand[0].Base() == topreg:

                        (op1i, op1tp, movop, t1key) = self.FindOperand1VMSource(sepidx, 1)
                        if op1i == -1:
                            break

                        h.addr = CMDSimpler.heap[j].addr
                        h.operands[0].tp = op0tp
                        h.operands[0].sz = jop.operand[0].Size()
                        h.operands[0].idx = i
                        h.operands[0].tkey = TKEY_OPR0
                        h.operands[1].tp = op1tp
                        h.operands[1].sz = jop.operand[1].Size()
                        h.operands[1].wrksz = CMDSimpler.heap[op1i].instr.operand[1].Size()
                        h.operands[1].idx = op1i
                        h.operands[1].tkey = t1key

                        return j
                    elif jop.ID == OP_MOV and opid in (OP_MOVSX, OP_MOVZX) and jop.operand[0].TID() == TID_MEM and \
                            jop.operand[0].Base() == topreg:

                        jj = j - 1
                        while jj > -1:
                            jjop = CMDSimpler.heap[jj].instr
                            if jjop.ID == opid and \
                               jjop.operand[0].ID == ID_REG and jjop.operand[0].XBase() == jop.operand[1].XBase():
                                break
                            jj -= 1

                        (op1i, op1tp, movop, t1key) = self.FindOperand1VMSource(j, 1)

                        if op1i == -1 or movop != opid:
                            break

                        h.addr = CMDSimpler.heap[j].addr
                        h.operands[0].tp = op0tp
                        h.operands[0].sz = jop.operand[1].Size()
                        h.operands[0].idx = i
                        h.operands[0].tkey = TKEY_OPR0
                        h.operands[1].tp = op1tp
                        h.operands[1].sz = CMDSimpler.heap[jj].instr.operand[1].Size()
                        h.operands[1].wrksz = CMDSimpler.heap[op1i].instr.operand[1].Size()
                        h.operands[1].idx = op1i
                        h.operands[1].tkey = t1key
                        if jj != -1:
                            h.operands[1].usei = jj
                            h.operands[1].useopr = 1

                        return j
            i += 1
        return -1


    # def FindReaders(self, h):
    #     lst = list()
    #     reg = -1
    #     off = -1
    #     for i in range(CMDSimpler.count):
    #         op = CMDSimpler.heap[i].instr
    #         if op.ID == OP_MOV and self.IsVmEipOp(op) and op.operand[0].ID == ID_REG:
    #             reg = op.operand[0].Base()
    #             off = -1
    #         elif reg != -1 and op.ID == OP_ADD and op.operand[0].IsReg(reg) and \
    #             op.operand[1].TID() == TID_VAL:
    #             off = op.operand[1].value
    #         elif op.ID == OP_MOV op.operand[0]

    def FindSourceReadOff(self, i, xbase):
        lst = self.BacktraceReg(i, xbase)
        if len(lst) == 0:
            xlog("ESP backtrace not found")
            return (-1, -1)

        bi = lst[-1]
        sop = CMDSimpler.heap[bi].instr
        if sop.ID not in (OP_MOV, OP_MOVZX):
            xlog("not get offsrc")
            return (-1, -1)

        lst = self.BacktraceReg(bi, sop.operand[1].XBase())
        if len(lst) == 0:
            xlog("no offsrc backtrace found")
            return (-1, -1)

        if len(lst) < 2:
            return (-1, -1)

        fop = CMDSimpler.heap[lst[-1]].instr
        if fop.ID not in (OP_MOV, OP_MOVZX) or not self.IsVmEipOp(fop):
            return (-1, -1)

        for j in lst:
            jop = CMDSimpler.heap[j].instr
            if jop.ID == OP_ADD and \
                jop.operand[1].TID() == TID_VAL:
                off = jop.operand[1].value
                if off > 0x100:
                    xlog("ERROR off > 0x100")
                    return (-1, -1)
                return (off, sop.operand[0].Size())
        return (-1, -1)

    def TraceListAddr(self, i, opid):
        lst = list()
        xbase = CMDSimpler.heap[i].instr.operand[opid].XBase()
        i -= 1
        while i >= 0:
            op = CMDSimpler.heap[i].instr

            if IsOpClass(op.ID, 0, 0, 1) and \
                op.operand[0].ID == ID_REG and op.operand[0].XBase() == xbase and \
                op.operand[1].TID() == TID_VAL:
                lst.append((i, op))
            elif op.ID == OP_ADD and \
               op.operand[0].ID == ID_REG and op.operand[0].XBase() == xbase:
                if op.operand[1].IsReg(R_EBP):
                    lst.append((i, op))
                elif op.operand[1].ID == ID_MEM32 and \
                     op.operand[1].Base() == R_EBP and op.operand[1].val2 == self.vmImgBaseOffset:
                    lst.append((i, op))
            elif op.ID in (OP_MOV, OP_MOVZX) and \
               op.operand[0].ID == ID_REG and op.operand[0].XBase() == xbase:
                if op.operand[1].ID == ID_REG:
                    xbase = op.operand[1].XBase()
                    lst.append((i, op))
                elif op.operand[1].TID() == TID_MEM:
                    if op.operand[1].Base() == R_EBP:
                        lst.append((i, op))
                        break
                    elif op.operand[1].Base() != R_ESP and \
                         op.operand[1].GetB(2) == 0 and op.operand[1].GetB(3) == 0 and op.operand[1].val2 == 0:
                        xbase = op.operand[1].XBase()
                        lst.append((i, op))
                    else:
                        break
                else:
                    break
            i -= 1
        return lst


    def TraceAddr(self, i, opid):
        xbase = CMDSimpler.heap[i].instr.operand[opid].XBase()
        isreg = False
        useImgBase = False
        off = -1
        deref = 0
        keyval = -1
        lastSz = 0
        i -= 1
        while i >= 0:
            op = CMDSimpler.heap[i].instr

            if op.ID == OP_ADD and \
               op.operand[0].ID == ID_REG and op.operand[0].XBase() == xbase:
                if op.operand[1].IsReg(R_EBP):
                    isreg = True
                elif op.operand[1].ID == ID_MEM32 and \
                     op.operand[1].Base() == R_EBP and op.operand[1].val2 == self.vmImgBaseOffset:
                    useImgBase = True
                elif op.operand[1].TID() == TID_VAL:
                    off = op.operand[1].value
            elif op.ID in (OP_MOV, OP_MOVZX) and \
               op.operand[0].ID == ID_REG and op.operand[0].XBase() == xbase:
                if op.operand[1].ID == ID_REG:
                    xbase = op.operand[1].XBase()
                    lastSz = op.operand[1].Size()
                elif op.operand[1].TID() == TID_MEM:
                    if op.operand[1].Base() == R_EBP:
                        keyval = op.operand[1].val2
                        break
                    elif op.operand[1].Base() != R_ESP and \
                         op.operand[1].GetB(2) == 0 and op.operand[1].GetB(3) == 0 and op.operand[1].val2 == 0:
                        deref += 1
                        xbase = op.operand[1].XBase()
                        lastSz = op.operand[1].Size()
                    else:
                        return REGTRACE()
                else:
                    break
            i -= 1

        res = REGTRACE()
        res.Key = keyval
        if useImgBase:
            res.VmImg = 1
        res.Off = off
        res.KeySz = lastSz
        if isreg:
            if deref == 2:
                res.DataTp = TH_OPR_REG # CALL REG
            elif deref == 3:
                res.DataTp = TH_OPR_MEM_REG
        else:
            if deref == 1:
                res.DataTp = TH_OPR_IMM
            elif deref == 2:
                res.DataTp = TH_OPR_MEM_IMM
        return res



    def CheckHndlTCall(self, h):
        heap = CMDSimpler.heap
        if heap[ CMDSimpler.count - 1 ].instr.ID == OP_RETN:
            lst = list()

            espReg = -1
            espOff = -1
            espOffSz = 0
            addr1 = None
            addr2 = None
            addrOff2 = -1
            for i in range(CMDSimpler.count):
                op = heap[i].instr
                if op.ID == OP_ADD and \
                        op.operand[0].ID == ID_REG and \
                        op.operand[1].IsReg(R_ESP):
                    espReg = op.operand[0].Base()
                    espOff, espOffSz = self.FindSourceReadOff(i - 1, op.operand[0].XBase())
                elif espOff != -1:
                    if op.ID == OP_MOV and \
                       op.operand[0].ID == ID_MEM32 and op.operand[0].Base() == espReg and \
                       op.operand[1].ID == ID_REG:
                        if addr1 == None:
                            addr1 = self.TraceAddr(i, 1)
                        else:
                            addr2 = self.TraceAddr(i, 1)
                            break
                    elif op.ID in (OP_MOV, OP_MOVZX, OP_MOVSX) and \
                        op.operand[0].ID == ID_REG and op.operand[0].XBase() == (espReg >> 4):
                        break
                    elif op.ID == OP_ADD and \
                        op.operand[0].ID == ID_REG and op.operand[0].XBase() == (espReg >> 4) and \
                        op.operand[1].TID() == TID_VAL:
                        addrOff2 = op.operand[1].value

            # h.operands[0].tp = TH_OPR_UNK
            #
            # if CMDSimpler.Bounds(3) and \
            #     heap[2].instr.operand[1].Size() == 3 and \
            #     heap[3].instr.operand[1].IsMem32Base(R_EBP)and \
            #     heap[3].instr.operand[1].val2 == self.vmImgBaseOffset:
            #     #xlog("OFF", hex(self.vmImgBaseOffset))
            #     h.operands[0].tp = TH_OPR_IMM
            # elif CMDSimpler.Bounds(4) and \
            #     heap[4].instr.ID == OP_MOV and heap[4].instr.operand[1].ID == ID_MEM32:
            #         #xlog("OKLOL")
            #         if CMDSimpler.Bounds(5) and \
            #             heap[5].instr.ID == OP_MOV and \
            #             heap[5].instr.operand[1].IsMem32Base( heap[4].instr.operand[0].Base() ):
            #             h.operands[0].tp = TH_OPR_MEM
            #         else:
            #             h.operands[0].tp = TH_OPR_REG

            if addr1 != None and addr1.DataTp != 0:
                h.operands[0].tp = addr1.DataTp
                h.operands[0].sz = addr1.KeySz
                h.operands[0].flags = addr1.VmImg
                h.opcodeOffsets[0] = addr1.Off

            if addr2 != None and addr2.DataTp != 0:
                h.operands[1].tp = addr2.DataTp
                h.operands[1].sz = addr2.KeySz
                h.operands[1].flags = addr2.VmImg
                h.opcodeOffsets[1] = addr2.Off

            h.tp = WH_CALL
            #xlog("CALLLLLLLLLL")
            #exit(0)
            return True
        return False

    def CheckHndlTNop(self, h):
        if h.flowReadIndex == 0:
            h.tp = TH_NOP
            return True
        return False


    def CheckHndlTPush(self, h):
        idx = self.MapUnaryOperation(h, OP_PUSH)
        if idx == -1:
            return False

        if CMDSimpler.Bounds(idx, 1) and\
            CMDSimpler.heap[idx + 1].instr.ID not in (OP_POPF, ):
            h.tp = TH_PUSH
            h.opidx = idx
            #xlog("PUSH")
            return True
        return False

    def CheckHndlTPop(self, h):
        idx = self.MapUnaryOperation(h, OP_POP)
        if idx == -1:
            return False

        h.tp = TH_POP
        h.opidx = idx
        # xlog("POP")
        return True

    def CheckHndlTInc(self, h):
        idx = self.MapUnaryOperation(h,  OP_INC)
        if idx == -1:
            return False

        h.tp = TH_INC
        h.opidx = idx
        #xlog("INC")
        return True

    def CheckHndlTDec(self, h):
        idx = self.MapUnaryOperation(h,  OP_DEC)
        if idx == -1:
            return False

        h.tp = TH_DEC
        h.opidx = idx
        #xlog("DEC")
        return True

    def CheckHndlTNot(self, h):
        idx = self.MapUnaryOperation(h,  OP_NOT)
        if idx == -1:
            return False

        h.tp = TH_NOT
        h.opidx = idx
        #xlog("NOT")
        return True

    def CheckHndlTNeg(self, h):
        idx = self.MapUnaryOperation(h, OP_NEG)
        if idx == -1:
            return False

        h.tp = TH_NEG
        h.opidx = idx
        #xlog("NEG")
        return True

    def CheckHndlTMov(self, h):
        idx = self.MapBinOperation(h, 0, OP_MOV)
        if idx == -1:
            return False

        h.tp = TH_MOV
        h.opidx = idx
        #xlog("MOV")
        return True

    def CheckHndlTMovsx(self, h):
        idx = self.MapBinOperation(h, 0, OP_MOVSX)
        if idx == -1:
            return False

        h.tp = TH_MOVSX
        h.opidx = idx
        #xlog("MOVSX")
        return True

    def CheckHndlTMovzx(self, h):
        idx = self.MapBinOperation(h, 0, OP_MOVZX)
        if idx == -1:
            return False

        h.tp = TH_MOVZX
        h.opidx = idx
        #xlog("MOVZX")
        return True

    def CheckHndlTAdd(self, h):
        idx = self.MapBinOperation(h, 0, OP_ADD)
        if idx == -1:
            return False

        h.tp = TH_ADD
        h.opidx = idx
        #xlog("ADD")
        return True

    def CheckHndlTSub(self, h):
        idx = self.MapBinOperation(h, 0, OP_SUB)
        if idx == -1:
            return False

        h.tp = TH_SUB
        h.opidx = idx
        #xlog("MOV")
        return True

    def CheckHndlTAnd(self, h):
        idx = self.MapBinOperation(h, 0, OP_AND)
        if idx == -1:
            return False

        h.tp = TH_AND
        h.opidx = idx
        #xlog("AND")
        return True

    def CheckHndlTXor(self, h):
        idx = self.MapBinOperation(h, 0, OP_XOR)
        if idx == -1:
            return False

        h.tp = TH_XOR
        h.opidx = idx
        #xlog("XOR")
        return True

    def CheckHndlTOr(self, h):
        idx = self.MapBinOperation(h, 0, OP_OR)
        if idx == -1:
            return False

        h.tp = TH_OR
        h.opidx = idx
        #xlog("OR")
        return True

    def CheckHndlTShl(self, h):
        idx = self.MapBinOperation(h, 0, OP_SHL)
        if idx == -1:
            return False

        h.tp = TH_SHL
        h.opidx = idx
        #xlog("SHL")
        return True

    def CheckHndlTShr(self, h):
        idx = self.MapBinOperation(h, 0, OP_SHR)
        if idx == -1:
            return False

        h.tp = TH_SHR
        h.opidx = idx
        #xlog("SHR")
        return True

    def CheckHndlTRcl(self, h):
        idx = self.MapBinOperation(h, 0, OP_RCL)
        if idx == -1:
            return False

        h.tp = TH_RCL
        h.opidx = idx
        #xlog("RCL")
        return True

    def CheckHndlTRcr(self, h):
        idx = self.MapBinOperation(h, 0, OP_RCR)
        if idx == -1:
            return False

        h.tp = TH_RCR
        h.opidx = idx
        #xlog("RCR")
        return True

    def CheckHndlTRol(self, h):
        idx = self.MapBinOperation(h, 0, OP_ROL)
        if idx == -1:
            return False

        h.tp = TH_ROL
        h.opidx = idx
        #xlog("ROL")
        return True

    def CheckHndlTRor(self, h):
        idx = self.MapBinOperation(h, 0, OP_ROR)
        if idx == -1:
            return False

        h.tp = TH_ROR
        h.opidx = idx
        #xlog("ROR")
        return True

    def CheckHndlTCmp(self, h):
        idx = self.MapBinOperation(h, 0, OP_CMP)
        if idx == -1:
            return False

        h.tp = TH_CMP
        h.opidx = idx
        #xlog("CMP")
        return True

    def CheckHndlTTest(self, h):
        idx = self.MapBinOperation(h, 0, OP_TEST)
        if idx == -1:
            return False

        h.tp = TH_TEST
        h.opidx = idx
        #xlog("TEST")
        return True

    def CheckHndlTImul(self, h):
        idx = self.MapBinOperation(h, 0, OP_IMUL)
        if idx == -1:
            return False

        h.tp = TH_IMUL
        h.opidx = idx
        #xlog("IMUL")
        return True

    def CheckHndlUnshuffle(self, h):
        heap = CMDSimpler.heap
        j = 0
        for i in range(6):
            op0 = heap[j + 0].instr
            op1 = heap[j + 1].instr
            op2 = heap[j + 2].instr
            op3 = heap[j + 3].instr
            op4 = heap[j + 4].instr
            if not (op0.ID == OP_MOV and \
                op1.ID == OP_ADD and \
                op2.ID == OP_MOV and \
                op3.ID == OP_ADD and \
                op4.ID == OP_PUSH):
                return False
            j += 5
        for i in range(6):
            op0 = heap[j + 0].instr
            op1 = heap[j + 1].instr
            op2 = heap[j + 2].instr
            op3 = heap[j + 3].instr
            op4 = heap[j + 4].instr
            if not (op0.ID == OP_MOV and \
                op1.ID == OP_ADD and \
                op2.ID == OP_MOV and \
                op3.ID == OP_ADD and \
                op4.ID == OP_POP):
                return False
            j += 5
        for i in range(12):
            h.opcodeOffsets[i] = heap[1 + i * 5].instr.operand[1].value
        h.tp = TH_UNSHUFLE
        h.opidx = 59
        return True

    def CheckHndlAddImgBase(self, h):
        opKeyIns = None
        i = 0
        while i < CMDSimpler.count:
            (ti, top) = self.FindOperandKeyReadIns(TKEY_OPERAND0, i)
            if ti == -1:
                i += 1
                continue

            i = ti
            stg = 0
            for j in range(i + 1, CMDSimpler.count):
                jop = CMDSimpler.heap[j].instr
                if stg == 0 and \
                        jop.ID == OP_ADD and \
                        jop.operand[0].IsReg(top.operand[0].Base()) and \
                        jop.operand[1].IsReg(R_EBP):
                    stg += 1
                elif stg == 1:
                    if jop.ID == OP_MOV and jop.operand[0].IsReg(top.operand[0].Base()) and \
                        not jop.operand[1].IsMem32Base(top.operand[0].Base()):
                        break
                    elif jop.ID == OP_ADD and \
                            jop.operand[0].TID() == TID_MEM and \
                            jop.operand[0].Base() == top.operand[0].Base():

                        lst = self.TraceListAddr(j, 1)
                        if len(lst) == 1 and lst[0][1].operand[1].TID() == TID_MEM and lst[0][1].operand[1].val2 == self.vmImgBaseOffset:
                            h.addr = CMDSimpler.heap[j].addr
                            h.tp = TH_IMGBASE
                            h.operands[0].tp = TH_OPR_REG
                            h.operands[0].sz = 3
                            h.operands[0].idx = ti
                            h.operands[0].tkey = TKEY_OPR0
                            h.opidx = j
                            return True
                        else:
                            break
            i += 1
        return False

    def DecryptTigerOperandData(self, h, opr):
        ops = TKEY_OPERAND0
        if opr == 1:
            ops = TKEY_OPERAND1

        (idx, top) = self.FindOperandKeyReadIns(ops, 0)
        if idx != -1:
            xlog(idx, OpTxt(top))
            idx += 1
            while CMDSimpler.Bounds(idx):
                op = CMDSimpler.heap[idx].instr
                if IsOpClass(op.ID, 0, 0, 1) and\
                    op.operand[0].ID == ID_REG and \
                    op.operand[0].XBase() == top.operand[0].XBase() and\
                    op.operand[1].TID() == TID_VAL:
                    xlog("Decoder {:d} {} {:d} {:x}".format(opr, OpTxt(op), op.operand[1].Size(), op.operand[1].value))
                    h.operands[opr].decoders.append( TG_OP_DEC(op.ID, op.operand[1].Size(), op.operand[1].value) )
                else:
                    xlog("break {:d} {} {:d} {:x}".format(opr, OpTxt(op), op.operand[1].Size(), op.operand[1].value))
                    break
                idx += 1
        return True

    def BacktraceReg(self, i, xbase):
        lst = list()
        while i >= 0:
            op = CMDSimpler.heap[i].instr
            if IsOpClass(op.ID, 0, 1, 1) and\
                op.operand[0].ID == ID_REG and op.operand[0].XBase() == xbase:
                lst.append(i)
            elif op.ID in (OP_MOV, OP_MOVZX) and \
                op.operand[0].ID == ID_REG and op.operand[0].XBase() == xbase and \
                op.operand[1].TID() == TID_MEM:
                lst.append(i)
                break
            elif op.ID in (OP_MOV, OP_MOVZX) and \
                op.operand[0].ID == ID_REG and op.operand[0].XBase() == xbase and \
                op.operand[1].ID == ID_REG:
                xbase = op.operand[1].XBase()
            i -= 1
        return lst

    def DecryptTigerOperandDataMy(self, h, opr):
        if h.opidx == -1:
            return True

        op = CMDSimpler.heap[h.opidx].instr
        if h.operands[opr].idx != 0:
            lst = self.BacktraceReg(h.opidx - 1, op.operand[opr].XBase())

            while True:
                if len(lst) == 1:
                    lop = CMDSimpler.heap[lst[0]].instr
                    if lop.ID == OP_MOV and lop.operand[1].TID() == TID_MEM and lop.operand[1].Base() != R_EBP:
                        lst = self.BacktraceReg(lst[0] - 1, lop.operand[1].XBase())
                    else:
                        break
                else:
                    break

            for d in reversed(lst):
                dop = CMDSimpler.heap[d].instr
                if IsOpClass(dop.ID, 0, 0, 1) and \
                    dop.operand[1].TID() == TID_VAL:
                    h.operands[opr].decoders.append( TG_OP_DEC(dop.ID, dop.operand[1].Size(), dop.operand[1].value) )
        return True

    def DecryptTigerOperandDataMy2(self, h, opr):
        if h.opidx == -1:
            return True

        opidx = h.opidx
        opn = opr
        if h.operands[opr].usei != -1:
            opidx = h.operands[opr].usei
            opn = h.operands[opr].useopr
        op = CMDSimpler.heap[opidx].instr
        if h.operands[opr].idx != 0:
            lst = self.TraceListAddr(opidx, opn)

            if len(lst) == 0:
                return True

            lop = lst.pop()[1]
            if lop.ID not in (OP_MOV, OP_MOVZX, OP_MOVSX) or \
               lop.operand[1].TID() != TID_MEM or lop.operand[1].val2 != self.GetKeyOffset(h.operands[opr].tkey):
                return True

            h.operands[opr].tp = TH_OPR_IMM

            movcnt = 0
            if op.operand[opr].TID() == TID_MEM:
                movcnt = 1

            while len(lst) > 0:
                lop = lst.pop()[1]
                if IsOpClass(lop.ID, 0, 0, 1) and lop.operand[1].TID() == TID_VAL:
                    h.operands[opr].decoders.append( TG_OP_DEC(lop.ID, lop.operand[1].Size(), lop.operand[1].value) )
                elif lop.ID == OP_ADD and lop.operand[1].IsReg(R_EBP):
                    h.operands[opr].tp = TH_OPR_REG
                elif lop.ID in (OP_MOV, OP_MOVZX, OP_MOVSX) and lop.operand[1].TID() == TID_MEM:
                    movcnt += 1

            if movcnt > 2:
                xlog("!", "if movcnt > 2:", hex(h.hndlID), movcnt)

            if movcnt == 2 and h.operands[opr].tp == TH_OPR_REG:
                h.operands[opr].tp = TH_OPR_MEM_REG
            elif movcnt == 1 and h.operands[opr].tp == TH_OPR_IMM:
                h.operands[opr].tp = TH_OPR_MEM_IMM
            elif movcnt == 1 and h.operands[opr].tp == TH_OPR_REG:
                pass
            elif movcnt == 0 and h.operands[opr].tp == TH_OPR_IMM:
                pass
            else:
                xlog("!", "movcnt", movcnt, "tp", h.operands[opr].tp, hex(h.hndlID))

        return True

    def DecryptTigerData(self, h):
        return self.DecryptTigerOperandDataMy2(h, 0) and self.DecryptTigerOperandDataMy2(h, 1)

    def RecoveryAdvancedHandler(self, h):
        if (self.CheckHndlTCall(h) or \
           self.CheckHndlTNop(h) or \
           self.CheckHndlTPush(h) or \
           self.CheckHndlTPop(h) or \
           self.CheckHndlTInc(h) or \
           self.CheckHndlTInc(h) or \
           self.CheckHndlTDec(h) or \
           self.CheckHndlTNot(h) or \
           self.CheckHndlTNeg(h) or \
           self.CheckHndlTAdd(h) or \
           self.CheckHndlTSub(h) or \
           self.CheckHndlTAnd(h) or \
           self.CheckHndlTXor(h) or \
           self.CheckHndlTOr(h) or \
           self.CheckHndlTShl(h) or \
           self.CheckHndlTShr(h) or \
           self.CheckHndlTRcl(h) or \
           self.CheckHndlTRcr(h) or \
           self.CheckHndlTRol(h) or \
           self.CheckHndlTRor(h) or \
           self.CheckHndlTCmp(h) or
           self.CheckHndlTTest(h) or \
           self.CheckHndlTImul(h) or \
           self.CheckHndlTMovsx(h) or \
           self.CheckHndlTMovzx(h) or \
           self.CheckHndlTMov(h) or \
           self.CheckHndlUnshuffle(h) or \
           self.CheckHndlAddImgBase(h)):
            return self.DecryptTigerData(h)
        return True

    def StepNop(self, h, reader):
        #self.stepParams[0] = OP_NOP

        rk = rkInstruction()
        rk.ID = OP_NOP
        self.traced.Add(rk, reader.addr)

        if h.idxList:
            return self.StepFlow(h, reader.Read2(h.flowReadOffset), False)
        return self.StepFlow(h, reader.Read2(h.flowReadOffset), True)

    def StepPop(self, h, reader):
        self.StepOpcodeRegions(h, reader)

        self.step_params[0] = "POP"

        rk = rkInstruction()
        rk.ID = OP_POP

        val = self.StepOperand(h, 0, rk.operand[0])

        self.step_params[1] = val

        if self.trStkReg >= 0:
            irlreg = self.trStkReg
            self.trStkReg -= 1

            if True:
                #irlreg != 4:
                self.vmReg[val] = irlreg
                self.realRegs.add(val)

            self.StepOperand(h, 0, rk.operand[0])

        if self.traceLog:
            xlog(self.TxtWop(rk))

        self.traced.Add(rk, reader.addr)

        return self.StepFlow(h, reader.Read2(h.flowReadOffset), False)

    def StepUniBin(self, h, reader, TXTMNEM, MNEM, dbg = False):
        self.StepOpcodeRegions(h, reader, dbg)

        rk = rkInstruction()
        rk.ID = MNEM

        val1 = self.StepOperand(h, 0, rk.operand[0])
        val2 = self.StepOperand(h, 1, rk.operand[1])

        self.step_params[0] = TXTMNEM
        self.step_params[1] = val1
        self.step_params[2] = val2

        if self.traceLog:
            xlog(self.TxtWop(rk))

        self.traced.Add(rk, reader.addr)

        return self.StepFlow(h, reader.Read2(h.flowReadOffset), False, dbg)

    def StepUnary(self, h, reader, TXTMNEM, MNEM, dbg = False):
        self.StepOpcodeRegions(h, reader, dbg)

        rk = rkInstruction()
        rk.ID = MNEM

        val = self.StepOperand(h, 0, rk.operand[0])

        self.step_params[0] = TXTMNEM
        self.step_params[1] = val

        if self.traceLog:
            xlog(self.TxtWop(rk))

        self.traced.Add(rk, reader.addr)

        return self.StepFlow(h, reader.Read2(h.flowReadOffset), False, dbg)

    def StepUnshuffle(self, h, reader):
        r1 = reader.Read2(h.opcodeOffsets[0])
        r2 = reader.Read2(h.opcodeOffsets[1])
        r3 = reader.Read2(h.opcodeOffsets[2])
        r4 = reader.Read2(h.opcodeOffsets[3])
        r5 = reader.Read2(h.opcodeOffsets[4])
        r6 = reader.Read2(h.opcodeOffsets[5])
        rv1 = self.GetVMReg(r1)
        rv2 = self.GetVMReg(r2)
        rv3 = self.GetVMReg(r3)
        rv4 = self.GetVMReg(r4)
        rv5 = self.GetVMReg(r5)
        rv6 = self.GetVMReg(r6)
        p1 = reader.Read2(h.opcodeOffsets[6])
        p2 = reader.Read2(h.opcodeOffsets[7])
        p3 = reader.Read2(h.opcodeOffsets[8])
        p4 = reader.Read2(h.opcodeOffsets[9])
        p5 = reader.Read2(h.opcodeOffsets[10])
        p6 = reader.Read2(h.opcodeOffsets[11])
        self.vmReg[p1] = rv6
        self.vmReg[p2] = rv5
        self.vmReg[p3] = rv4
        self.vmReg[p4] = rv3
        self.vmReg[p5] = rv2
        self.vmReg[p6] = rv1

        # seems
        # 7 6 2 1 3 0
        #xlog(rv6, rv5, rv4, rv3, rv2, rv1)

        #self.realRegs.clear()
        self.realRegs.add(p1)
        self.realRegs.add(p2)
        self.realRegs.add(p3)
        self.realRegs.add(p4)
        self.realRegs.add(p5)
        self.realRegs.add(p6)

        self.step_params[0] = "UNSHUFFLE"
        #xlog("--------------------------------------------------------")

        rk = rkInstruction()
        rk.ID = THOP_UNSHUFFLE
        self.traced.Add(rk, reader.addr)
        return self.StepFlow(h, reader.Read2(h.flowReadOffset), False)

    def StepCall(self, h, reader):
        synt = "ERR "
        self.step_params[0] = "ERR"

        rk = rkInstruction()
        rk.addr = h.hndlID

        if h.operands[1].tp != 0: # CALL
            self.step_params[0] = "CALL"
            rk.ID = OP_CALL
        elif h.operands[0].tp != 0:
            self.step_params[0] = "JMP"
            rk.ID = OP_JMP
        else:
            xlog("CALL ERR")
            return False

        val = 0
        if h.operands[0].sz == 1:
            val = reader.Read1(h.opcodeOffsets[0])
        elif h.operands[0].sz == 2:
            val = reader.Read2(h.opcodeOffsets[0])
        elif h.operands[0].sz == 3:
            val = reader.Read4(h.opcodeOffsets[0])

        rk.operand[0].sz = h.operands[0].sz
        if h.operands[0].tp == TH_OPR_REG:
            rk.operand[0].ID = ID_REG
            rk.operand[0].value = (self.ConvReg(val) << 4) | 3
        elif h.operands[0].tp == TH_OPR_IMM:
            rk.operand[0].ID = ID_VAL32
            if h.operands[0].flags != 0:
                val = UINT(val + self.imageBase)
            rk.operand[0].value = val
        elif h.operands[0].tp == TH_OPR_MEM_IMM:
            rk.operand[0].ID = ID_MEM32
            if h.operands[0].flags != 0:
                val = UINT(val + self.imageBase)
            rk.operand[0].val2 = val
        elif h.operands[0].tp == TH_OPR_MEM_REG:
            rk.operand[0].ID = ID_MEM32
            rk.operand[0].xbase = (self.ConvReg(val) << 4) | 3

        if h.operands[1].tp != 0:
            val = 0
            if h.operands[1].sz == 1:
                val = reader.Read1(h.opcodeOffsets[1])
            elif h.operands[1].sz == 2:
                val = reader.Read2(h.opcodeOffsets[1])
            elif h.operands[1].sz == 3:
                val = reader.Read4(h.opcodeOffsets[1])

            retaddr = 0
            if h.operands[1].tp == TH_OPR_REG:
                synt = "\t\tRET-> {}".format(RegName(self.GetVMReg(val), 3))
            elif h.operands[1].tp == TH_OPR_IMM:
                if h.operands[1].flags != 0:
                    val = UINT(val + self.imageBase)
                synt = "\t\tRET-> {:x}".format(val)
                retaddr = val
            elif h.operands[1].tp == TH_OPR_MEM_IMM:
                if h.operands[1].flags != 0:
                    val = UINT(val + self.imageBase)
                synt = "\t\tRET-> [{:x}]".format(val)
                m = self.GetMM(val)
                if m != None:
                    retaddr = GetDWORD(val)
            elif h.operands[1].tp == TH_OPR_MEM_REG:
                synt = "\t\tRET-> [{}]".format(RegName(self.GetVMReg(val), 3))

            if retaddr != 0:
                rk.operand[1].ID = ID_VAL32
                rk.operand[1].value = retaddr
                isvm, of, hid =  self.CheckEnterVM(retaddr)
                if isvm:
                    l = LABELS.GetLabel(UINT(of + self.imageBase), hid)
                    l.specialData = (self.vmReg.copy(), self.realRegs.copy(), self.vmEspReg)
                    rk.operand[1].value = UINT(of + self.imageBase)
                    #xlog("Add RET {:x} {:x}".format(UINT(of + self.imageBase), hid))

        if self.traceLog:
            xlog(self.TxtWop(rk) + synt)

        self.traced.Add(rk, self.trAddr)
        return True

    def StepImgBase(self, h, reader):
        self.StepOpcodeRegions(h, reader)

        rk = rkInstruction()
        rk.ID = OP_ADD

        val1 = self.StepOperand(h, 0, rk.operand[0])
        rk.operand[1].ID = ID_VAL32
        rk.operand[1].value = self.imageBase

        self.step_params[0] = "ADD"
        self.step_params[1] = val1
        self.step_params[2] = self.imageBase

        if self.traceLog:
            xlog(self.TxtWop(rk))

        self.traced.Add(rk, reader.addr)

        return self.StepFlow(h, reader.Read2(h.flowReadOffset), False)

    def StepAdvanced(self, h, reader):

        if h.tp == TH_NOP:
            return self.StepNop(h, reader)
        elif h.tp == TH_POP:
            # HACK
            if self.traced.count >= 2 and \
              ((self.traced.heap[self.traced.count - 1].instr.ID == WOP_RESET and \
               self.traced.heap[self.traced.count - 2].instr.ID == WOP_SSTACK) or \
               (self.traced.heap[self.traced.count - 2].instr.ID == WOP_RESET and \
                self.traced.heap[self.traced.count - 1].instr.ID == WOP_SSTACK)) and \
               self.trStkReg < 0:
                self.trStkReg = 7
                xlog("HACK! Restore POP REGS")
            return self.StepPop(h, reader)
        elif h.tp == TH_PUSH:
            return self.StepUnary(h, reader, "PUSH", OP_PUSH)
        elif h.tp == TH_TEST:
            return self.StepUniBin(h, reader, "TEST", OP_TEST)
        elif h.tp == TH_CMP:
            return self.StepUniBin(h, reader, "CMP", OP_CMP)
        elif h.tp == TH_SUB:
            return self.StepUniBin(h, reader, "SUB", OP_SUB)
        elif h.tp == TH_ADD:
            return self.StepUniBin(h, reader, "ADD", OP_ADD)
        elif h.tp == TH_AND:
            return self.StepUniBin(h, reader, "AND", OP_AND)
        elif h.tp == TH_OR:
            return self.StepUniBin(h, reader, "OR", OP_OR)
        elif h.tp == TH_XOR:
            return self.StepUniBin(h, reader, "XOR", OP_XOR)
        elif h.tp == TH_SHL:
            return self.StepUniBin(h, reader, "SHL", OP_SHL)
        elif h.tp == TH_SHR:
            return self.StepUniBin(h, reader, "SHR", OP_SHR)
        elif h.tp == TH_MOV:
            return self.StepUniBin(h, reader, "MOV", OP_MOV)
        elif h.tp == TH_MOVSX:
            return self.StepUniBin(h, reader, "MOVSX", OP_MOVSX)
        elif h.tp == TH_MOVZX:
            return self.StepUniBin(h, reader, "MOVZX", OP_MOVZX)
        elif h.tp == TH_INC:
            return self.StepUnary(h, reader, "INC", OP_INC)
        elif h.tp == TH_DEC:
            return self.StepUnary(h, reader, "DEC", OP_DEC)
        elif h.tp == TH_NOT:
            return self.StepUnary(h, reader, "NOT", OP_NOT)
        elif h.tp == TH_NEG:
            return self.StepUnary(h, reader, "NEG", OP_NEG)
        elif h.tp == TH_SHL:
            return self.StepUniBin(h, reader, "SHL", OP_SHL)
        elif h.tp == TH_SHR:
            return self.StepUniBin(h, reader, "SHR", OP_SHR)
        elif h.tp == TH_RCL:
            return self.StepUniBin(h, reader, "RCL", OP_RCL)
        elif h.tp == TH_RCR:
            return self.StepUniBin(h, reader, "RCR", OP_RCR)
        elif h.tp == TH_ROL:
            return self.StepUniBin(h, reader, "ROL", OP_ROL)
        elif h.tp == TH_ROR:
            return self.StepUniBin(h, reader, "ROR", OP_ROR)
        elif h.tp == TH_UNSHUFLE:
            return self.StepUnshuffle(h, reader)
        elif h.tp == WH_CALL:
            return self.StepCall(h, reader)
        elif h.tp == TH_IMGBASE:
            return self.StepImgBase(h, reader)
        elif h.tp == -1:
            self.StepOpcodeRegions(h, reader)
            return self.StepFlow(h, reader.Read2(h.flowReadOffset), False)
        return False

    def StepOperand(self, h, opid, outop):
        opi = h.operands[opid]
        val = self.GetKeyData(opi.tkey)

        for d in opi.decoders:
            _, val = ComputeVal(d.mnem, d.sz, val, d.data)

        if opi.tp == TH_OPR_IMM:
            if opi.sz == 1:
                val &= 0xFF
            elif opi.sz == 2:
                val &= 0xFFFF

        if self.trAddr == 0x1141030c:
            xlog(opid, hex(val), opi.tp)

        outop.sz = opi.sz
        if opi.tp == TH_OPR_REG:
            outop.ID = ID_REG
            outop.value = (self.ConvReg(val) << 4) | opi.sz
        elif opi.tp == TH_OPR_IMM:
            outop.ID = ID_VALx | opi.sz
            outop.value = val
        elif opi.tp == TH_OPR_MEM_REG:
            outop.ID = ID_MEMx | opi.sz
            outop.xbase = (self.ConvReg(val) << 4) | 3
        elif opi.tp == TH_OPR_MEM_IMM:
            outop.ID = ID_MEMx | opi.sz
            outop.val2 = val

        return val

    def TxtWildOperator(self, op):
        if op.ID in TIGER_OPTXT:
            return TIGER_OPTXT[op.ID]
        return WILD.TxtWildOperator(self, op)


    def SimplifyDoubleUnshuffle(self, trace):
        i = 0
        while trace.Bounds(i, 1):
            if trace.heap[i].instr.ID == THOP_UNSHUFFLE and \
               trace.heap[i + 1].instr.ID == THOP_UNSHUFFLE:
                trace.heap[i + 1].instr.ID = 0
            i += 1
        trace.Cleaner()

    def SimplifyPushCallJmp(self, trace):
        i = 0
        while i < trace.count:
            if trace.Bounds(i, 11) and \
               trace.heap[i].instr.ID == OP_PUSH and \
               trace.heap[i + 1].instr.ID == OP_PUSH and \
               trace.heap[i + 2].instr.ID == OP_PUSHF and \
               trace.heap[i + 3].instr.ID == OP_PUSH and \
               trace.heap[i + 4].instr.ID == OP_PUSH and \
               trace.heap[i + 5].instr.ID == OP_PUSH and \
               trace.heap[i + 6].instr.ID == OP_PUSH and \
               trace.heap[i + 7].instr.ID == OP_PUSH and \
               trace.heap[i + 8].instr.ID == OP_PUSH and \
               trace.heap[i + 9].instr.ID == OP_PUSH and \
               trace.heap[i + 10].instr.ID == THOP_UNSHUFFLE:
                if trace.heap[i + 11].instr.ID == OP_CALL:
                    for j in range(11):
                        trace.heap[i + j].instr.ID = 0
                elif trace.Bounds(i, 12) and \
                     trace.heap[i + 11].instr.ID == OP_NOP and \
                     trace.heap[i + 12].instr.ID == OP_CALL:
                    for j in range(12):
                        trace.heap[i + j].instr.ID = 0
            if trace.Bounds(i, 10) and \
                trace.heap[i].instr.ID == OP_PUSH and \
                trace.heap[i + 1].instr.ID == OP_PUSHF and \
                trace.heap[i + 2].instr.ID == OP_PUSH and \
                trace.heap[i + 3].instr.ID == OP_PUSH and \
                trace.heap[i + 4].instr.ID == OP_PUSH and \
                trace.heap[i + 5].instr.ID == OP_PUSH and \
                trace.heap[i + 6].instr.ID == OP_PUSH and \
                trace.heap[i + 7].instr.ID == OP_PUSH and \
                trace.heap[i + 8].instr.ID == OP_PUSH and \
                trace.heap[i + 9].instr.ID == THOP_UNSHUFFLE:
                if trace.heap[i + 10].instr.ID in (OP_JMP, WOP_UNDEF) or \
                   trace.heap[i + 10].instr.ID in range(OP_JA, OP_JCXZ):
                    for j in range(10):
                        trace.heap[i + j].instr.ID = 0
                elif trace.Bounds(i, 11) and \
                     trace.heap[i + 10].instr.ID == OP_NOP and \
                    (trace.heap[i + 11].instr.ID in (OP_JMP, WOP_UNDEF) or \
                     trace.heap[i + 11].instr.ID in range(OP_JA, OP_JCXZ)):
                    for j in range(11):
                        trace.heap[i + j].instr.ID = 0
            i += 1
        trace.Cleaner()

    def SimplifyResetPop(self, trace):
        i = 0
        while i < trace.count:
            if trace.Bounds(i, 11) and \
                trace.heap[i].instr.ID == WOP_SSTACK and \
                trace.heap[i + 1].instr.ID == WOP_RESET and \
                trace.heap[i + 2].instr.ID == OP_POP and \
                trace.heap[i + 3].instr.ID == OP_POP and \
                trace.heap[i + 4].instr.ID == OP_POP and \
                trace.heap[i + 5].instr.ID == OP_POP and \
                trace.heap[i + 6].instr.ID == OP_POP and \
                trace.heap[i + 7].instr.ID == OP_POP and \
                trace.heap[i + 8].instr.ID == OP_POP and \
                trace.heap[i + 9].instr.ID == OP_POP and \
                trace.heap[i + 10].instr.ID == OP_POPF and \
                trace.heap[i + 11].instr.ID == WOP_RSTACK:
                for j in range(12):
                    trace.heap[i + j].instr.ID = 0
            elif trace.Bounds(i, 11) and \
                trace.heap[i].instr.ID == WOP_RESET and \
                trace.heap[i + 1].instr.ID == WOP_SSTACK and \
                trace.heap[i + 2].instr.ID == OP_POP and \
                trace.heap[i + 3].instr.ID == OP_POP and \
                trace.heap[i + 4].instr.ID == OP_POP and \
                trace.heap[i + 5].instr.ID == OP_POP and \
                trace.heap[i + 6].instr.ID == OP_POP and \
                trace.heap[i + 7].instr.ID == OP_POP and \
                trace.heap[i + 8].instr.ID == OP_POP and \
                trace.heap[i + 9].instr.ID == OP_POP and \
                trace.heap[i + 10].instr.ID == OP_POPF and \
                trace.heap[i + 11].instr.ID == WOP_RSTACK:
                for j in range(12):
                    trace.heap[i + j].instr.ID = 0
            i += 1
        trace.Cleaner()

    def SimplifyModifyStack(self, trace):
        i = 0
        while i < trace.count:
            if trace.Bounds(i, 1) and \
                trace.heap[i].instr.ID in (OP_ADD, OP_SUB) and \
                trace.heap[i + 1].instr.ID == WOP_LSTACK and \
                trace.heap[i].instr.operand[0].ID == ID_REG and \
                trace.heap[i].instr.operand[0].value == 0x1043:

                trace.heap[i + 1].instr.ID = 0
                trace.heap[i].instr.operand[0].value = R_ESP

            i += 1
        trace.Cleaner()


    def SimplifyComplexUniversal(self, trace):
        i = 0
        while i < trace.count:
            if trace.Bounds(i, 4):
                op0 = trace.heap[i].instr
                op1 = trace.heap[i + 1].instr
                op2 = trace.heap[i + 2].instr
                op3 = trace.heap[i + 3].instr
                op4 = trace.heap[i + 4].instr

                if op0.ID == OP_MOV and \
                   op1.ID == OP_SHL and \
                   op2.ID == OP_ADD and \
                   op3.ID == OP_ADD and \
                   op0.operand[0].ID == ID_REG and \
                   op1.operand[0].ID == ID_REG and \
                   op2.operand[0].ID == ID_REG and \
                   op3.operand[0].ID == ID_REG and \
                   op0.operand[0].value & 0x2000 and \
                   op1.operand[0].value == op0.operand[0].value and \
                   op2.operand[0].value == op0.operand[0].value and \
                   op3.operand[0].value == op0.operand[0].value and \
                   op0.operand[1].ID == ID_REG and \
                   op1.operand[1].TID() == TID_VAL and \
                   op2.operand[1].ID == ID_REG and \
                   op3.operand[1].TID() == TID_VAL:
                    if op4.operand[0].TID() == TID_MEM and op4.operand[0].xbase == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.ID = 0
                        op3.ID = 0
                        op4.operand[0].xbase = 0
                        op4.operand[0].val2 = op3.operand[1].value
                        op4.operand[0].value = 0
                        op4.operand[0].SetB(1, op2.operand[1].Base())
                        op4.operand[0].SetB(2, op0.operand[1].Base())
                        op4.operand[0].SetB(3, op1.operand[1].value & 0xF)
                    elif op4.operand[1].TID() == TID_MEM and op4.operand[1].xbase == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.ID = 0
                        op3.ID = 0
                        op4.operand[1].xbase = 0
                        op4.operand[1].val2 = op3.operand[1].value
                        op4.operand[1].value = 0
                        op4.operand[1].SetB(1, op2.operand[1].Base())
                        op4.operand[1].SetB(2, op0.operand[1].Base())
                        op4.operand[1].SetB(3, op1.operand[1].value & 0xF)
                    elif op4.ID == OP_MOV and \
                         op4.operand[0].ID == ID_REG and \
                         op4.operand[1].ID == ID_REG and \
                         op4.operand[1].value == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.ID = 0
                        op3.ID = 0
                        op4.ID = OP_LEA
                        op4.operand[1].ID = ID_MEM32
                        op4.operand[1].xbase = 0
                        op4.operand[1].val2 = op3.operand[1].value
                        op4.operand[1].value = 0
                        op4.operand[1].SetB(1, op2.operand[1].Base())
                        op4.operand[1].SetB(2, op0.operand[1].Base())
                        op4.operand[1].SetB(3, op1.operand[1].value & 0xF)

            if trace.Bounds(i, 3):
                op0 = trace.heap[i].instr
                op1 = trace.heap[i + 1].instr
                op2 = trace.heap[i + 2].instr
                op3 = trace.heap[i + 3].instr

                if op0.ID == OP_MOV and \
                   op1.ID == OP_SHL and \
                   op2.ID == OP_ADD and \
                   op0.operand[0].ID == ID_REG and \
                   op1.operand[0].ID == ID_REG and \
                   op2.operand[0].ID == ID_REG and \
                   op0.operand[0].value & 0x2000 and \
                   op1.operand[0].value == op0.operand[0].value and \
                   op2.operand[0].value == op0.operand[0].value and \
                   op0.operand[1].ID == ID_REG and \
                   op1.operand[1].TID() == TID_VAL and \
                   op2.operand[1].ID == ID_REG:
                    if op3.operand[0].TID() == TID_MEM and op3.operand[0].xbase == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.ID = 0
                        op3.operand[0].xbase = 0
                        op3.operand[0].val2 = 0
                        op3.operand[0].value = 0
                        op3.operand[0].SetB(1, op2.operand[1].Base())
                        op3.operand[0].SetB(2, op0.operand[1].Base())
                        op3.operand[0].SetB(3, op1.operand[1].value & 0xF)
                    elif op3.operand[1].TID() == TID_MEM and op3.operand[1].xbase == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.ID = 0
                        op3.operand[1].xbase = 0
                        op3.operand[1].val2 = 0
                        op3.operand[1].value = 0
                        op3.operand[1].SetB(1, op2.operand[1].Base())
                        op3.operand[1].SetB(2, op0.operand[1].Base())
                        op3.operand[1].SetB(3, op1.operand[1].value & 0xF)
                    elif op3.ID == OP_MOV and \
                         op3.operand[0].ID == ID_REG and \
                         op3.operand[1].ID == ID_REG and \
                         op3.operand[1].value == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.ID = 0
                        op3.ID = OP_LEA
                        op3.operand[1].ID = ID_MEM32
                        op3.operand[1].xbase = 0
                        op3.operand[1].val2 = 0
                        op3.operand[1].value = 0
                        op3.operand[1].SetB(1, op2.operand[1].Base())
                        op3.operand[1].SetB(2, op0.operand[1].Base())
                        op3.operand[1].SetB(3, op1.operand[1].value & 0xF)

                if op0.ID == OP_MOV and \
                   op1.ID == OP_SHL and \
                   op2.ID == OP_ADD and \
                   op0.operand[0].ID == ID_REG and \
                   op1.operand[0].ID == ID_REG and \
                   op2.operand[0].ID == ID_REG and \
                   op0.operand[0].value & 0x2000 and \
                   op1.operand[0].value == op0.operand[0].value and \
                   op2.operand[0].value == op0.operand[0].value and \
                   op0.operand[1].ID == ID_REG and \
                   op1.operand[1].TID() == TID_VAL and \
                   op2.operand[1].TID() == TID_VAL:
                    if op3.operand[0].TID() == TID_MEM and op3.operand[0].xbase == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.ID = 0
                        op3.operand[0].xbase = 0
                        op3.operand[0].val2 = op2.operand[1].value
                        op3.operand[0].value = 0
                        op3.operand[0].SetB(2, op0.operand[1].Base())
                        op3.operand[0].SetB(3, op1.operand[1].value & 0xF)
                    elif op3.operand[1].TID() == TID_MEM and op3.operand[1].xbase == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.ID = 0
                        op3.operand[1].xbase = 0
                        op3.operand[1].val2 = op2.operand[1].value
                        op3.operand[1].value = 0
                        op3.operand[1].SetB(2, op0.operand[1].Base())
                        op3.operand[1].SetB(3, op1.operand[1].value & 0xF)
                    elif op3.ID == OP_MOV and \
                         op3.operand[0].ID == ID_REG and \
                         op3.operand[1].ID == ID_REG and \
                         op3.operand[1].value == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.ID = 0
                        op3.ID = OP_LEA
                        op3.operand[1].ID = ID_MEM32
                        op3.operand[1].xbase = 0
                        op3.operand[1].val2 = op2.operand[1].value
                        op3.operand[1].value = 0
                        op3.operand[1].SetB(2, op0.operand[1].Base())
                        op3.operand[1].SetB(3, op1.operand[1].value & 0xF)

                if op0.ID == OP_MOV and \
                   op1.ID == OP_ADD and \
                   op2.ID == OP_ADD and \
                   op0.operand[0].ID == ID_REG and \
                   op1.operand[0].ID == ID_REG and \
                   op2.operand[0].ID == ID_REG and \
                   op0.operand[0].value & 0x2000 and \
                   op1.operand[0].value == op0.operand[0].value and \
                   op2.operand[0].value == op0.operand[0].value and \
                   op0.operand[1].ID == ID_REG and \
                   op1.operand[1].ID == ID_REG and \
                   op2.operand[1].TID() == TID_VAL:
                    if op3.operand[0].TID() == TID_MEM and op3.operand[0].xbase == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.ID = 0
                        op3.operand[0].xbase = 0
                        op3.operand[0].val2 = op2.operand[1].value
                        op3.operand[0].value = 0
                        op3.operand[0].SetB(1, op0.operand[1].Base())
                        op3.operand[0].SetB(2, op1.operand[1].Base())
                        op3.operand[0].SetB(3, 0)
                    elif op3.operand[1].TID() == TID_MEM and op3.operand[1].xbase == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.ID = 0
                        op3.operand[1].xbase = 0
                        op3.operand[1].val2 = op2.operand[1].value
                        op3.operand[1].value = 0
                        op3.operand[1].SetB(1, op0.operand[1].Base())
                        op3.operand[1].SetB(2, op1.operand[1].Base())
                        op3.operand[1].SetB(3, 0)
                    elif op3.ID == OP_MOV and \
                         op3.operand[0].ID == ID_REG and \
                         op3.operand[1].ID == ID_REG and \
                         op3.operand[1].value == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.ID = 0
                        op3.ID = OP_LEA
                        op3.operand[1].ID = ID_MEM32
                        op3.operand[1].xbase = 0
                        op3.operand[1].val2 = op2.operand[1].value
                        op3.operand[1].value = 0
                        op3.operand[1].SetB(1, op0.operand[1].Base())
                        op3.operand[1].SetB(2, op1.operand[1].Base())
                        op3.operand[1].SetB(3, 0)

            if trace.Bounds(i, 2):
                op0 = trace.heap[i].instr
                op1 = trace.heap[i + 1].instr
                op2 = trace.heap[i + 2].instr

                if op0.ID == OP_MOV and \
                   op1.ID == OP_ADD and \
                   op0.operand[0].ID == ID_REG and \
                   op1.operand[0].ID == ID_REG and \
                   op0.operand[0].value & 0x2000 and \
                   op1.operand[0].value == op0.operand[0].value and \
                   op0.operand[1].ID == ID_REG and \
                   op1.operand[1].TID() == TID_VAL:
                    if op2.operand[0].TID() == TID_MEM and op2.operand[0].xbase == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.operand[0].xbase = 0
                        op2.operand[0].value = 0
                        op2.operand[0].SetB(1, op0.operand[1].Base())
                        op2.operand[0].val2 = op1.operand[1].value
                    elif op2.operand[1].TID() == TID_MEM and op2.operand[1].xbase == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.operand[1].xbase = 0
                        op2.operand[1].value = 0
                        op2.operand[1].val2 = op1.operand[1].value
                        op2.operand[1].SetB(1, op0.operand[1].Base())
                    elif op2.ID == OP_MOV and \
                         op2.operand[0].ID == ID_REG and \
                         op2.operand[1].ID == ID_REG and \
                         op2.operand[1].value == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.ID = OP_LEA
                        op2.operand[1].ID = ID_MEM32
                        op2.operand[1].xbase = 0
                        op2.operand[1].val2 = op1.operand[1].value
                        op2.operand[1].value = 0
                        op2.operand[1].SetB(1, op0.operand[1].Base())

                if op0.ID == OP_MOV and \
                   op1.ID == OP_ADD and \
                   op0.operand[0].ID == ID_REG and \
                   op1.operand[0].ID == ID_REG and \
                   op0.operand[0].value & 0x2000 and \
                   op1.operand[0].value == op0.operand[0].value and \
                   op0.operand[1].ID == ID_REG and \
                   op1.operand[1].ID == ID_REG:
                    if op2.operand[0].TID() == TID_MEM and op2.operand[0].xbase == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.operand[0].xbase = 0
                        op2.operand[0].value = 0
                        op2.operand[0].SetB(1, op0.operand[1].Base())
                        op2.operand[0].SetB(2, op1.operand[1].Base())
                        op2.operand[0].val2 = 0
                    elif op2.operand[1].TID() == TID_MEM and op2.operand[1].xbase == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.operand[1].xbase = 0
                        op2.operand[1].value = 0
                        op2.operand[1].val2 = 0
                        op2.operand[1].SetB(1, op0.operand[1].Base())
                        op2.operand[1].SetB(2, op1.operand[1].Base())
                    elif op2.ID == OP_MOV and \
                         op2.operand[0].ID == ID_REG and \
                         op2.operand[1].ID == ID_REG and \
                         op2.operand[1].value == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = 0
                        op2.ID = OP_LEA
                        op2.operand[1].ID = ID_MEM32
                        op2.operand[1].xbase = 0
                        op2.operand[1].val2 = 0
                        op2.operand[1].value = 0
                        op2.operand[1].SetB(1, op0.operand[1].Base())
                        op2.operand[1].SetB(2, op1.operand[1].Base())

            if trace.Bounds(i, 1):
                op0 = trace.heap[i].instr
                op1 = trace.heap[i + 1].instr

                if op0.ID == OP_MOV and \
                   op0.operand[0].ID == ID_REG and \
                   op0.operand[0].value & 0x2000 and \
                   op0.operand[1].TID() in (TID_REG, TID_VAL):
                    if op1.operand[0].TID() == TID_MEM and op1.operand[0].xbase == op0.operand[0].value:
                        op0.ID = 0
                        op1.operand[0].xbase = 0
                        op1.operand[0].val2 = 0
                        op1.operand[0].value = 0
                        if op0.operand[1].ID == ID_REG:
                            op1.operand[0].SetB(1, op0.operand[1].Base())
                        else:
                            op1.operand[0].val2 = op0.operand[1].value
                    elif op1.operand[1].TID() == TID_MEM and op1.operand[1].xbase == op0.operand[0].value:
                        op0.ID = 0
                        op1.operand[1].xbase = 0
                        op1.operand[1].val2 = 0
                        op1.operand[1].value = 0
                        if op0.operand[1].ID == ID_REG:
                            op1.operand[1].SetB(1, op0.operand[1].Base())
                        else:
                            op1.operand[1].val2 = op0.operand[1].value

                    elif op1.ID in (OP_CALL, OP_JMP, OP_PUSH) and \
                        op1.operand[0].ID == ID_REG and \
                        op1.operand[0].value == op0.operand[0].value:

                        op0.ID = 0
                        op1.operand[0].xbase = 0
                        op1.operand[0].ID = op0.operand[1].ID
                        op1.operand[0].value = op0.operand[1].value

                    elif op1.ID == OP_MOV and \
                         op1.operand[0].ID == ID_REG and \
                         op1.operand[1].ID == ID_REG and \
                         op1.operand[1].value == op0.operand[0].value:
                        op0.ID = 0
                        op1.ID = OP_LEA
                        op1.operand[1].xbase = 0
                        op1.operand[1].ID = ID_MEM32
                        op1.operand[1].val2 = 0
                        op1.operand[1].value = 0
                        if op0.operand[1].ID == ID_REG:
                            op1.operand[1].SetB(1, op0.operand[1].Base())
                        else:
                            op1.operand[1].val2 = op0.operand[1].value

            i += 1
        trace.Cleaner()

    def SimplifyComplexAddress(self, trace):
        i = 0
        while i < trace.count:
            if not trace.Bounds(i, 1):
                break

            op0 = trace.heap[i].instr
            op1 = trace.heap[i + 1].instr

            if op0.ID in (OP_MOV, OP_ADD) and \
               op1.ID == OP_ADD and \
               op0.operand[0].ID == ID_REG and \
               op0.operand[0].value & 0x2000 and \
               op0.operand[1].TID() == TID_VAL and \
               op1.operand[0].ID == ID_REG and \
               op1.operand[1].TID() == TID_VAL and \
               op1.operand[0].value == op0.operand[0].value:

                op1.ID = 0
                op0.operand[1].value = UINT(op0.operand[1].value + op1.operand[1].value)

            i += 1
        trace.Cleaner()

    def DeleteSpecial(self, trace):
        i = 0
        while i < trace.count:
            op = trace.heap[i].instr
            if op.ID in (WOP_RESET, THOP_UNSHUFFLE, WOP_LSTACK):
                op.ID = 0
            elif op.ID == OP_MOV and \
                op.operand[0].ID == ID_REG and \
                op.operand[1].ID == ID_REG and \
                op.operand[0].value == op.operand[1].value:
                op.ID = 0
            i += 1
        trace.Cleaner()

    def Simplify(self, trace):
        counter = 0
        while True:
            cnt = trace.count
            self.SimplifyDoubleUnshuffle(trace)
            self.SimplifyPushCallJmp(trace)
            self.SimplifyResetPop(trace)
            self.SimplifyModifyStack(trace)
            self.SimplifyComplexAddress(trace)
            self.SimplifyComplexUniversal(trace)

            self.DeleteSpecial(trace)

            if cnt == trace.count:
                counter += 1
                if counter >= 2:
                    break
            else:
                counter = 0