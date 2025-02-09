import opcode
import time
import sys

from xrkutil import *
from xrkdsm import *
from thobfus import *
from xrkasm import *
from thvm import *
from __main__ import *

WILD_NONE = 0
WILD_FISH = 1
WILD_TIGER = 2

class VMXCHG:
    index = -1
    reg1 = -1
    reg2 = -1
    off1 = -1
    off2 = -1

class WKEY:
    Offset = 0
    Data = 0

class FKEY:
    keyId = 0
    idx = 0
    operand = 0
    mnemonic = 0
    parameter = 0
    tid = 0
    sz = 0
    dkeyparam = False
    condition = None



WH_JMP_INS = 1 #
WH_JMP_OUT_REG = 2
WH_JMP_OUT_MEM = 3
WH_JMP_OUT_IMM = 4
WH_JCC_INS = 5 #
WH_JCC_OUT = 6 #
WH_RET = 7
WH_CALL = 8
WH_UNDEF = 9 #
WH_LODSB = 10
WH_LODSW = 11
WH_LODSD = 12
WH_STOSB = 13 #?
WH_STOSW = 14 #?
WH_STOSD = 15 #?
WH_SCASB = 16
WH_SCASW = 17
WH_SCASD = 18
WH_CMPSB = 19
WH_CMPSW = 20
WH_CMPSD = 21
WH_MOVSB = 22
WH_MOVSW = 23
WH_MOVSD = 24
WH_PUSHFD = 25 #
WH_POPFD = 26 #
WH_EFLAGS = 27
WH_RESTORE_STK = 28 #
WH_LOAD_STK = 29 #
WH_STORE_STK = 30 #
WH_RESET_EFLAGS = 31
WH_RESET = 32 #
WH_CRYPT = 33 #
WH_CNT = 34
WH_INVALID = 0xFFFF

WOP_UNDEF = 0x1000
WOP_RSTACK = 0x1001
WOP_LSTACK = 0x1002
WOP_SSTACK = 0x1003
WOP_REFLAGS = 0x1004
WOP_RESET = 0x1005
WOP_CRYPT = 0x1006

OPSZ_SUB = 0x4000
OPSZ_RETN = 0x8000
OPSZ_INVALID = 0xFFFF

TH_OPR_UNK = 0
TH_OPR_REG = 1
TH_OPR_IMM = 2
TH_OPR_MEM_IMM = 3
TH_OPR_MEM_REG = 4

WILD_OPTXT = {WOP_UNDEF: "UNDEF",
              WOP_RSTACK: "RESTORE STACK",
              WOP_LSTACK: "LOAD STACK",
              WOP_SSTACK: "STORE STACK",
              WOP_REFLAGS: "RESET EFLAGS",
              WOP_RESET: "RESET",
              WOP_CRYPT: "CRYPT"}


class OPREGION:
    tp = 0
    opcodeOffset = 0
    opcodeSize = 0
    indexStart = 0
    indexEnd = 0

    def __init__(self, tp = 0, a = 0, b = 0, c = 0, d = 0):
        self.tp = tp
        self.opcodeOffset = a
        self.opcodeSize = b
        self.indexStart = c
        self.indexEnd = d

class WHNDL:
    flowReadIndex = -1
    flowReadOffset = -1
    flowDataIndex = -1
    flowMutateIndex = -1
    flowMutateMnemonic = 0
    flowMutateConst = 0
    opcodeOffsets = None
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
    code = None
    regions = None
    opcodeSize = OPSZ_INVALID
    dumpAddr = 0

    def __init__(self, id = -1):
        self.idxList = []
        self.hndlID = id
        self.keys = []
        self.f_530 = []
        self.opcodeOffsets = [-1] * 16
        self.regions = list()


def KeyProtTempl(vm, key):
    keyData = vm.GetKey(key.keyId)
    if keyData == None:
        return False
    #xlog("----------------- KEYDATA {:x}".format(keyData))
    return (keyData & 1) != 0

class WILD(VM):
    HANDLER = WHNDL
    wildType = WILD_NONE
    jmpaddr = -1
    push1 = 0
    push1_2 = 0
    push2 = 0
    push2_2 = 0
    VMAddr = -1
    imageBase = 0
    VmContext = 0
    vmImgBaseOffset = 0 # Add it to address
    vmOldBase = 0 # Sub it from address
    val4 = 0
    vmEIP = 0
    iatAddr = 0
    HTableOff = 0
    iatCount = 0
    f_c01a = 0
    f_c01c = 0
    f_c01e = 0
    f_c020 = 0
    compares = 0

    hndl_tp0_fnd = 0

    CryptoOffset = 0
    CryptoOffsetInited = 0

    initedEflagsTypes = False
    mnemonicTypes = None

    initedJccTypes = False
    jccMnemonicTypes = None

    fres = None
    frescnt = 0

    Keys = None

    hndl = None
    hndlCount = 0

    traced = None
    trAddr = 0
    trHid = 0
    trStkReg = -1

    dmAddr = 0
    dmRk = None
    dmPos = 0
    dmSz = 0
    dmRkAddr = 0

    vmReg = None

    JmpLabel = None

    TraceBranchObfus = False
    BranchContinue = -1
    BranchRemain = 0

    JccBranches = None

    realRegs = None
    vmEspReg = -1

    traceLog = True



    def __init__(self, t, d):
        VM.__init__(self, 5, d)
        self.wildType = t

        self.Keys = []

        self.hndl = dict()
        self.jccMnemonicTypes = dict()
        self.mnemonicTypes = dict()
        self.HANDLER = WHNDL
        self.vmReg = dict()
        self.JmpLabel = dict()
        self.JccBranches = list()
        self.realRegs = set()
        self.vmEspReg = -1

    def GetMnemonic(self, k):
        if k in self.mnemonicTypes:
            return self.mnemonicTypes[k]
        return OP_NONE

    def SetMnemonic(self, k, v):
        if k in self.mnemonicTypes:
            return False
        self.mnemonicTypes[k] = v
        return True

    def ResetKeys(self):
        self.Keys = []

    def ResetKeyData(self):
        for k in self.Keys:
            k.Data = 0

    def AddKey(self, offset):
        k = WKEY()
        k.Offset = offset
        self.Keys.append(k)

    def SetKey(self, offset, data):
        for k in self.Keys:
            if k.Offset == offset:
                k.Data = data
                return True
        #xlog("Can't set key {:x} {:x}".format(offset, data))
        return False

    def IsHasKey(self, offset):
        for k in self.Keys:
            if k.Offset == offset:
                return True
        return False

    def GetKey(self, offset, none = None):
        for k in self.Keys:
            if k.Offset == offset:
                return k.Data
        xlog("NONE")
        return none

    def GetKeyOffset(self, idx):
        if idx < len(self.Keys):
            return self.Keys[idx].Offset
        return 0

    def GetKeyData(self, idx):
        if idx < len(self.Keys):
            return self.Keys[idx].Data
        return 0

    def Step0(self, addr):

        bs = GetBytes(addr, 5)
        if UB(bs[0]) not in (0xe8, 0xe9):
            xlog("Not JMP or CALL at: {:08x}".format(addr))
            return False

        self.jmpaddr = addr
        vl = GetSInt(bs[1:6])

        vma = UINT(addr + 5 + vl)

        mblock = GetMemBlockInfo(vma)
        if not mblock:
            xlog("Can't get mem block at {:08X}".format(vma))
            return False

        xlog("Getting section {:08X} - {:08X}".format(mblock.addr, mblock.addr + mblock.size))

        self.mblk.data = GetBytes(mblock.addr, mblock.size)
        self.mblk.addr = mblock.addr
        self.mblk.size = mblock.size

        pushA = vma
        for i in range(2):
            m = self.GetMM(pushA)
            sz, rk = XrkDecode(m)

            if rk.ID != OP_PUSH:
                xlog("Instruction at {:08X} not a PUSH".format(pushA))
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
            xlog("Instruction at {:08X} not a JMP".format(pushA))
            return False

        maddr = UINT(pushA + sz + rk.operand[0].value)

        mblock = GetMemBlockInfo(maddr)
        if not mblock:
            xlog("Can't get mem block at {:08X}".format(maddr))
            return False

        xlog("Getting section {:08X} - {:08X}".format(mblock.addr, mblock.addr + mblock.size))
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

            if rk.ID == OP_JMP and rk.operand[0].TID() == TID_MEM:
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
                    xlog("FindImageBase OP_CALL {:08x}".format(val))

            elif flg[0] and IsOpClass(op.ID, 0, 0, 1) and \
                op.operand[0].IsReg(R_ECX) and\
                op.operand[1].TID() == TID_VAL:
                _,val = ComputeVal(op.ID, op.operand[0].Size(), val, op.operand[1].value)
                flg[0] = False
                flg[1] = True

                if dbg:
                    xlog("FindImageBase asx0 {:08x} = {:08x}".format(op.operand[1].value, val))

            elif flg[1] and IsOpClass(op.ID, 0, 0, 1) and \
                 op.operand[0].IsReg(R_ECX) and \
                 op.operand[1].ID == ID_VAL32:
                _,val = ComputeVal(op.ID, op.operand[0].Size(), val, op.operand[1].value)
                flg[2] = True
                flg[1] = False

                if dbg:
                    xlog("FindImageBase asx1 {:08x} = {:08x}".format(op.operand[1].value, val))

            elif flg[2] and op.ID == OP_MOV and \
                 op.operand[0].IsReg(R_EBP) and\
                 op.operand[1].ID == ID_VAL32:
                if dbg:
                    xlog("FindImageBase OP_MOV {:d} {:08x}".format(i, val))
                return (i, val)

            elif op.ID == OP_PUSH:
                if dbg:
                    xlog("FindImageBase OP_PUSH")
                break

            i += 1
        return (0, 0)

    def FindVMContext(self, startn = 0, dbg = False):
        reg = 0
        addr = 0
        flg = False

        i = startn
        while i < CMDSimpler.count:
            op = CMDSimpler.heap[i].instr

            if op.ID == OP_MOV and op.operand[0].IsReg(R_EBP) and op.operand[1].ID == ID_VAL32:
                addr = op.operand[1].value
                reg = op.operand[0].Base()
                flg = True
                if dbg:
                    xlog("FindImageBase OP_MOV ")

            elif flg and IsOpClass(op.ID, 0, 0, 1) and \
                 op.operand[0].IsReg(reg) and \
                 op.operand[1].IsReg(R_ECX):

                if dbg:
                    xlog("FindImageBase asx001 {:08x} = ".format(op.operand[1].value))

                return (i + 1, UINT(self.imageBase + addr))

            elif op.ID == OP_PUSH:
                if dbg:
                    xlog("FindImageBase OP_PUSH")
                break
            i += 1
        return (0, 0)

    def GetVmImgBaseOffset(self, startn):
        i = startn
        while i < CMDSimpler.count:
            op = CMDSimpler.heap[i].instr
            op1 = CMDSimpler.heap[i + 1].instr

            if op.ID == OP_MOV and op1.ID == OP_MOV and\
                op.operand[0].ID == ID_REG and op.operand[1].ID == ID_VAL32 and\
                op1.operand[0].ID == ID_MEM32 and op1.operand[1].ID == ID_REG and \
                (op.operand[0].Base() == op1.operand[0].Base() or op.operand[0].Base() == op1.operand[0].GetB(2)):
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
                op.operand[0].ID == ID_REG and op.operand[1].ID == ID_VAL32 and\
                op1.operand[0].ID == ID_MEM32 and op1.operand[1].ID == ID_VAL32 and \
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
                op.operand[0].ID == ID_MEM32 and\
                op.operand[0].GetB(1) != 0 and op.operand[0].GetB(2) != 0 and op.operand[0].GetB(3) == 0 and \
                op.operand[0].val2 == 0 and op.operand[1].ID == ID_VAL32:
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

            if op.ID == OP_MOV and op.operand[0].ID == ID_REG and op.operand[0].GetB(0) != R_ESP and\
               op.operand[1].IsMem32Roff(R_ESP, 0, 0, 0x28):
                flg = True

            elif flg and op.ID == OP_MOV and op.operand[0].ID == ID_REG and op.operand[0].GetB(0) != R_ESP and\
                op.operand[1].ID == ID_VAL32 and op.operand[1].value != 0:
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
                op.operand[0].ID == ID_REG and op.operand[1].ID == ID_VAL32 and\
                op1.operand[0].ID == ID_REG and op1.operand[1].ID == ID_MEM32 and \
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
                op.operand[0].ID == ID_REG and op1.operand[0].ID == ID_REG and\
                op1.operand[1].ID == ID_VAL32 and \
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

        i, self.VmContext = self.FindVMContext(i)
        if self.VmContext == 0:
            return False

        popPos = CMDSimpler.NextOpPos(OP_POP, i)
        if popPos == -1:
            return False

        i, self.vmImgBaseOffset = self.GetVmImgBaseOffset(popPos)
        if self.vmImgBaseOffset == 0:
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

        i, self.HTableOff = self.fn7(i)
        if self.HTableOff == 0:
            return False

        self.iatCount = self.GetIatCount(i)
        if self.iatCount == 0:
            return False

        self.push1_2 = UINT(self.push1_2 + self.imageBase)
        self.push1 = UINT(self.push1 + self.imageBase)

        xlog("v1 {:08x} pop {:d} vmImgBaseOffset {:08x} v3 {:08x} v4 {:08x} vmEIP {:08x} iatAddr {:08x} v7 {:08x} iatCount {:08x}".format(self.VmContext, popPos, self.vmImgBaseOffset, self.vmOldBase, self.val4, self.vmEIP, self.iatAddr, self.HTableOff, self.iatCount))
        return True

    def EvalSimpleBranch(self):
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


    def IsBranchObfuscation(self):
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

    def TraceJccBack(self):
        if len(self.JccBranches) == 0:
            return False

        while len(self.JccBranches) != 0:
            jccDst = self.JccBranches.pop()

            if CMDSimpler.GetAddr(jccDst) == None:
                self.dmPos = 0
                self.dmAddr = jccDst
                return True
        return False

    def TraceObfuscationContinue(self):
        if self.TraceBranchObfus and self.BranchContinue != -1:
            self.dmAddr = self.BranchContinue
            self.dmPos = 0

            self.TraceBranchObfus = False
            self.BranchContinue = -1
            return True
        return False


    def TraceJmp(self):
        if self.dmRk.operand[0].TID() == TID_VAL:
            jmpaddr = UINT(self.dmAddr + self.dmPos + self.dmRk.operand[0].value)

            if CMDSimpler.GetAddr(jmpaddr) == None:
                self.dmPos = UINT(self.dmPos + self.dmRk.operand[0].value)
                return True #just skip this jmp because this addr not in list

            CMDSimpler.Add(self.dmRk, self.dmRkAddr)
            return self.TraceJccBack()
        else:
            CMDSimpler.Add(self.dmRk, self.dmRkAddr)
            return self.TraceObfuscationContinue()
        return True

    def TraceBranchCompares(self):
        if self.IsBranchObfuscation():
            self.TraceBranchObfus = True
            self.BranchRemain = 15
        else:
            self.TraceBranchObfus = False

    def TraceBranchObfuscation(self):
        if self.BranchRemain > 0:
            self.dmPos = UINT(self.dmPos + self.dmRk.operand[0].value)
        elif self.BranchRemain == 0:
            self.BranchContinue = UINT(self.dmAddr + self.dmPos + self.dmRk.operand[0].value)

        self.BranchRemain -=1

    def TraceJcc(self, J):
        if self.EvalSimpleBranch():
            CMDSimpler.Add(self.dmRk, self.dmRkAddr)

            if self.compares == 3:
                self.TraceBranchCompares()

            if self.TraceBranchObfus:
                self.TraceBranchObfuscation()
            else:
                self.JccBranches.append(UINT(self.dmAddr + self.dmPos + self.dmRk.operand[0].value))
        else:
            b = 0
            if J == 1:
                a, b = CMDSimpler.EvaluateBranch(self, self.dmRk.ID, False, 'C')
                if (a & 0xFF) == 0:
                    xlog("Follow Jump?")
                    b = 0
            else:
                b = 1

            if b == 1:
                self.dmPos = UINT(self.dmPos + self.dmRk.operand[0].value)
            else:
                CMDSimpler.Add(self.dmRk, self.dmRkAddr)

    def DumpHandler(self, addr, J):
        CMDSimpler.Clear()
        self.compares = 0

        self.dmAddr = addr
        self.dmSz = 0
        self.dmPos = 0
        self.dmRk = None
        self.JccBranches = []

        self.TraceBranchObfus = False
        self.BranchContinue = -1
        self.BranchRemain = 0

        while UINT(self.dmPos + self.dmAddr) < self.mblk.addr + self.mblk.size:

            m = self.GetMM(UINT(self.dmPos + self.dmAddr))
            self.dmSz, self.dmRk = XrkDecode(m)

            self.dmRkAddr = UINT(self.dmPos + self.dmAddr)
            self.dmPos = UINT(self.dmPos + self.dmSz)

            if self.dmRk.ID == OP_CMP:
                CMDSimpler.Add(self.dmRk, self.dmRkAddr)
                self.compares += 1
            elif self.dmRk.ID == OP_JMP:
                if not self.TraceJmp():
                    break
            elif self.dmRk.ID == OP_RETN:
                CMDSimpler.Add(self.dmRk, self.dmRkAddr)
                if not self.TraceObfuscationContinue():
                    break
            elif self.dmRk.ID >= OP_JA and self.dmRk.ID <= OP_JS:
                self.TraceJcc(J)
            else:
                CMDSimpler.Add(self.dmRk, self.dmRkAddr)

            if CMDSimpler.GetAddr(UINT(self.dmPos + self.trAddr)) != None:
                break

        CMDSimpler.Simple(self, 0xFFFF,'C')
        self.DeofuscateVmContextAccess()
        self.DeofuscateUnusedInstructions()



    def DeofuscateVmContextAccess(self):
        cmds = CMDSimpler.heap
        i = 0
        while i < CMDSimpler.count:
            op = cmds[i].instr
            #  MOV  reg(not ESP/EBP), EBP
            if op.ID == OP_MOV and op.operand[0].ID == ID_REG and op.operand[1].ID == ID_REG and\
               op.operand[0].GetB(0) not in (R_ESP, R_EBP) and op.operand[1].GetB(0) == R_EBP:
                operations = 1
                reg = op.operand[0].GetB(0)

                k = i + 1
                while k < CMDSimpler.count:
                    opk = cmds[k].instr

                    if opk.ID != 0:
                        # ADD   reg, const
                        if opk.ID == OP_ADD and\
                           opk.operand[0].ID == ID_REG and opk.operand[1].ID == ID_VAL32 and\
                           opk.operand[0].GetB(0) == reg:
                            operations += 1
                            for z in range(k + 1, CMDSimpler.count):
                                opz = cmds[z].instr
                                if opz.ID != 0:
                                    if opz.ID != OP_MOVS:
                                        if opz.operand[0].TID() == TID_MEM and\
                                           opz.operand[0].GetB(1) == reg and opz.operand[0].GetB(2) == 0 and opz.operand[0].GetB(3) == 0 and\
                                           opz.operand[0].val2 == 0 and operations == 2:
                                            opz.operand[0].SetB(1, R_EBP)
                                            opz.operand[0].val2 = opk.operand[1].value
                                            opk.ID = 0
                                            op.ID = 0
                                            operations = 3
                                        elif opz.operand[1].TID() == TID_MEM and\
                                             opz.operand[1].GetB(1) == reg and opz.operand[1].GetB(2) == 0 and opz.operand[1].GetB(3) == 0 and\
                                             opz.operand[1].val2 == 0 and operations == 2:
                                            opz.operand[1].SetB(1, R_EBP)
                                            opz.operand[1].val2 = opk.operand[1].value
                                            opk.ID = 0
                                            op.ID = 0
                                            operations = 3
                                        elif opz.operand[0].ID == ID_REG and opz.operand[0].GetB(0) == reg:
                                            operations += 1
                                    if operations > 2:
                                        break
                        elif opk.operand[0].ID == ID_REG and opk.operand[0].GetB(0) == reg:
                            operations += 1

                        if operations >= 2:
                            break

                    k += 1

            i += 1
        CMDSimpler.Cleaner()

        i = 0
        while i < CMDSimpler.count:
            op = cmds[i].instr
            # MOV reg, imm
            if op.ID == OP_MOV and op.operand[0].TID() == TID_REG and op.operand[1].TID() == TID_VAL:
                operations = 0
                reg = op.operand[0].Base()
                j = i + 1
                while j < CMDSimpler.count:
                    opj = cmds[j].instr

                    ## break if change 'reg' to another value or place value into [reg]
                    ##  ...   reg, ...
                    ##  ...   [reg ], ...
                    if (opj.operand[0].TID() == TID_REG and (opj.operand[0].Base() & 0xF0) == (reg & 0xF0)) or\
                       (opj.operand[0].TID() == TID_MEM and (opj.operand[0].Base() == reg or opj.operand[0].GetB(2) == reg)):
                        break

                    ## ...   [ebp + ?], reg
                    ## change to
                    ## ...   [ebp + ?], imm
                    if opj.operand[1].TID() == TID_REG and opj.operand[1].Base() == reg and \
                       opj.operand[0].TID() == TID_MEM and \
                       opj.operand[0].GetB(1) == R_EBP and opj.operand[0].GetB(2) == 0 and opj.operand[0].GetB(3) == 0:
                        opj.operand[1].ID = (opj.operand[1].GetB(0) & 0xf) | ID_VALx
                        opj.operand[1].value = op.operand[1].value
                        operations += 1
                    j += 1
                if operations > 0:
                    op.ID = 0
            ###  MOV   reg, [ebp + keyX]
            elif op.ID == OP_MOV and op.operand[0].TID() == TID_REG and op.operand[1].TID() == TID_MEM and\
                 self.IsIdxOpEbpKey(i, 1):
                reg = op.operand[0].Base()
                j = i + 1
                while j < CMDSimpler.count:
                    opj = cmds[j].instr

                    ## break if change 'reg' to another value or place value into [reg]
                    ##  ...   reg, ...
                    ##  ...   [reg ], ...
                    if (opj.operand[0].TID() == TID_REG and (opj.operand[0].Base() & 0xF0) == (reg & 0xF0)) or \
                       (opj.operand[0].TID() == TID_MEM and (opj.operand[0].Base() == reg or opj.operand[0].GetB(2) == reg)):
                        break

                    ## write reg value into [key]
                    ## ...  [ebp + keyX], reg
                    if opj.operand[1].TID() == TID_REG and opj.operand[1].Base() == reg and\
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
                    if self.IsHasKey(op.operand[0].val2):
                        return True
            elif op.operand[1].TID() == TID_MEM:
                if op.operand[1].GetB(1) == R_EBP and op.operand[1].GetB(2) == 0 and op.operand[1].GetB(3) == 0:
                    if self.IsHasKey(op.operand[1].val2):
                        return True
        return False

    def BacktraceOperandRoot(self, i, opt, reindex = 1, dbg = False):
        if reindex == 1 and i >= 0 and i < CMDSimpler.count:
            CMDSimpler.heap[i].index = 1

        op = CMDSimpler.heap[i].instr
        reg = op.operand[opt].XBase()

        # not xSP/xBP
        if reg not in (4,5) and i > 0:
            rootFound = False
            j = i - 1
            while j > -1 and not rootFound:
                opj = CMDSimpler.heap[j].instr

                if opj.ID in (OP_MOV, OP_MOVSX, OP_MOVZX):
                    if opj.operand[0].TID() == TID_REG and opj.operand[0].XBase() == reg:
                        CMDSimpler.heap[j].index = 1
                        rootFound = True
                        if opj.operand[1].TID() == TID_REG and opj.operand[1].GetB(0) not in (R_ESP, R_EBP):
                            if opj.ID == OP_MOV and opj.operand[0].GetB(0) == opj.operand[1].GetB(0):
                                CMDSimpler.heap[j].index = 0
                                rootFound = False
                            else:
                                self.BacktraceOperandRoot(j, 1, reindex)
                elif opj.ID == OP_POP:
                    if opj.operand[0].TID() == TID_REG and (opj.operand[0].GetB(0) >> 4) == reg:
                        CMDSimpler.heap[j].index = 1
                        rootFound = True
                else:
                    if opj.ID in (OP_CMP, OP_TEST):
                        opj1 = CMDSimpler.heap[j + 1].instr
                        if opj1.ID != OP_PUSHF and opj1.ID != 0 and (opj1.ID <= OP_JMP or opj1.ID >= OP_JCXZ):
                            j -= 1
                            continue

                    if opj.operand[0].TID() == TID_REG and (opj.operand[0].GetB(0) >> 4) == reg:
                        CMDSimpler.heap[j].index = 1
                        if opj.operand[1].TID() == TID_REG and opj.operand[1].GetB(0) not in (R_ESP, R_EBP):
                            self.BacktraceOperandRoot(j, 1, reindex)
                j -= 1

    def DeofuscateUnusedInstructions(self):
        foundHandlerTable = 0
        notIndex = -1
        i = 0
        while i < CMDSimpler.count:
            op = CMDSimpler.heap[i].instr

            if op.ID in (OP_CALL, OP_JMP):
                if op.operand[0].TID() != TID_VAL:
                    self.BacktraceOperandRoot(i, 0)
            elif op.ID in (OP_CMP, OP_TEST):
                if notIndex != -1 and notIndex + 1 == i:
                    CMDSimpler.heap[i].index = 1
                else:
                    op1 = CMDSimpler.heap[i + 1].instr
                    if op1.ID == OP_PUSHF or op1.ID == 0 or (op1.ID > OP_JMP and op1.ID < OP_JCXZ):
                        self.BacktraceOperandRoot(i, 0)
                        if op.operand[1].TID() != TID_VAL:
                            self.BacktraceOperandRoot(i, 1)
            elif op.ID in range(OP_JA, OP_JCXZ):
                CMDSimpler.heap[i].index = 1
                if i > 0:
                    self.BacktraceOperandRoot(i - 1, 0, 1)
                    if  CMDSimpler.heap[i - 1].instr.operand[1].TID() == TID_REG:
                        self.BacktraceOperandRoot(i - 1, 1)
            elif op.ID == OP_MOVS:
                CMDSimpler.heap[i].index = 1
                self.BacktraceOperandRoot(i, 0)
                self.BacktraceOperandRoot(i, 1)
            elif op.ID == OP_POP:
                CMDSimpler.heap[i].index = 1
                if op.operand[0].TID() == TID_MEM:
                    self.BacktraceOperandRoot(i, 0)
            elif op.ID == OP_PUSHF:
                CMDSimpler.heap[i].index = 1
                if notIndex + 2 != i:
                    op1 = CMDSimpler.heap[i - 1].instr
                    if op1.operand[0].TID() == TID_REG:
                        self.BacktraceOperandRoot(i - 1, 0)
                    if op1.operand[0].TID() == TID_MEM:
                        self.BacktraceOperandRoot(i - 1, 0)
                    if op1.operand[1].TID() == TID_REG:
                        self.BacktraceOperandRoot(i - 1, 1)
            elif op.ID == OP_RETN:
                CMDSimpler.heap[i].index = 1
            elif op.ID != 0:
                if op.ID == OP_NOT:
                    notIndex = i

                if foundHandlerTable == 1 and self.CryptoOffsetInited == 0 and IsOpClass(op.ID, 0, 0, 1) and\
                       op.operand[0].ID == ID_MEM32 and op.operand[1].ID == ID_REG and\
                       op.operand[0].GetB(1) == R_EBP and op.operand[0].GetB(2) == 0 and op.operand[0].GetB(3) == 0 and\
                       self.IsHasKey(op.operand[0].val2) == False and op.operand[0].val2 != self.vmEIP:
                    self.CryptoOffsetInited = 1
                    self.CryptoOffset = op.operand[0].val2 & 0xFFFF
                    op.ID = 0
                elif foundHandlerTable == 1 and self.CryptoOffsetInited == 1 and IsOpClass(op.ID, 0, 0, 1) and\
                        op.operand[0].ID == ID_MEM32 and op.operand[1].ID == ID_REG and \
                        op.operand[0].GetB(1) == R_EBP and op.operand[0].GetB(2) == 0 and op.operand[0].GetB(3) == 0 and\
                        op.operand[0].val2 == self.CryptoOffset:
                    op.ID = 0
                else:
                    if foundHandlerTable == 0 and op.ID == OP_MOV and op.operand[0].ID == ID_REG and op.operand[1].ID == ID_MEM32 and\
                       op.operand[1].GetB(1) == R_EBP and op.operand[1].GetB(2) == 0 and op.operand[1].GetB(3) == 0 and\
                       op.operand[1].val2 == self.HTableOff:
                        foundHandlerTable = 1
                    if op.operand[0].ID == 0:
                        CMDSimpler.heap[i].index = 1
                    elif op.operand[0].TID() == TID_VAL:
                        CMDSimpler.heap[i].index = 1
                    elif op.operand[0].TID() == TID_MEM:
                        CMDSimpler.heap[i].index = 1
                        self.BacktraceOperandRoot(i, 0)
                        if op.operand[1].TID() == TID_REG:
                            CMDSimpler.heap[i].index = 1
                            self.BacktraceOperandRoot(i, 1)
                    elif op.operand[1].TID() == TID_MEM:
                        CMDSimpler.heap[i].index = 1
                        self.BacktraceOperandRoot(i, 1)
                    else:
                        if op.ID == OP_PUSH and op.operand[0].TID() == TID_REG:
                            CMDSimpler.heap[i].index = 1
                            self.BacktraceOperandRoot(i, 0)
                        if op.operand[0].TID() == TID_REG and (op.operand[0].GetB(0) >> 4) == 4: # xSP
                            CMDSimpler.heap[i].index = 1
            i += 1

        for i in range(CMDSimpler.count):
            if CMDSimpler.heap[i].index == 0:
                CMDSimpler.heap[i].instr.ID = 0

        CMDSimpler.Cleaner()

    def CheckForKeysHandle(self):
        return False

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
                        #xlog("{:08x} ".format(UINT(self.push1 + opj1.operand[1].value)))
                        self.push2_2 = GetWORD(m)
                        self.push1 = UINT(self.push1 + N)
                        return True
                j -= 1

            xlog(j)
        return False

    def KeyWalk(self):
        b = GetBytes(UINT(self.VmContext + self.HTableOff), 4)
        if not b:
            return False

        ibase = GetDWORD(b)
        if self.iatAddr == ibase:
            ibase = 0
        else:
            ibase = self.imageBase

        xlog("[AntiFISH] Searching for keys...")

        self.ResetKeys()

        f = open("{}/TXT/Fish_KeyWalk_{:08x}.txt".format(self.WrkDir, self.VMAddr),"w")

        for i in range(5):
            m = self.GetMM(UINT(self.iatAddr + self.push2_2 * 4))
            haddr = GetDWORD(m)

            self.DumpHandler(UINT(ibase + haddr), 1)

            xlog("Process handle at {:08x}".format( UINT(ibase + haddr) ))

            f.write("//////////////////////////////////////////////\r\n// FISH Virtual Handler {:04x} {:08X}\r\n".format(i, UINT(ibase + haddr) ))
            for l in CMDSimpler.GetListing(True, False):
                f.write("{}\n".format(l))

            if self.CheckForKeysHandle():
                f.close()
                xlog("Key found")
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

    def FindReadIndex(self):
        i = CMDSimpler.count - 1
        while i >= 0:
            op = CMDSimpler.heap[i].instr
            if op.ID == OP_MOV and op.operand[0].ID == ID_REG and self.IsVmEipOp(op):
                return i
            i -= 1
        return -1

    def FindReadOffset(self, i, reg):
        while i < CMDSimpler.count:
            ## ADD  reg, imm
            op = CMDSimpler.heap[i].instr
            if op.ID == OP_ADD and op.operand[0].ID == ID_REG and op.operand[0].GetB(0) == reg and \
                op.operand[1].TID() == TID_VAL:
                return i
            i += 1
        return -1

    def FindAddDataIndex(self, h, i, reg):
        while i < CMDSimpler.count:
            # MOVZX reg, word ptr [reg]
            op = CMDSimpler.heap[i].instr

            if op.ID == OP_MOVZX and op.operand[0].ID == ID_REG and op.operand[1].ID == ID_MEM16 and\
               op.operand[1].GetB(1) == reg and op.operand[1].GetB(2) == 0 and op.operand[1].GetB(3) == 0 and\
               op.operand[1].val2 == 0:
                h.flowDataIndex = CMDSimpler.heap[i].index
                treg = op.operand[0].GetB(0)
                return self.FindAddAnd(h, i + 1, treg)

            elif op.ID == OP_MOV and op.operand[0].ID == ID_REG and op.operand[1].ID == ID_MEM16 and\
                 op.operand[1].GetB(1) == reg and op.operand[1].GetB(2) == 0 and op.operand[1].GetB(3) == 0 and \
                 op.operand[1].val2 == 0:
                h.flowDataIndex = CMDSimpler.heap[i].index
                return True
            i += 1
        return False

    def FindAddAnd(self, h, i, reg):
        while i < CMDSimpler.count:
            op = CMDSimpler.heap[i].instr

            if op.ID == OP_AND and op.operand[0].ID == ID_REG and op.operand[0].GetB(0) == reg and \
               op.operand[1].TID() == TID_VAL and op.operand[1].value == 0xFFFF:
                return True

            if IsOpClass(op, 0, 0, 1):
                if self.IsIdxOpEbpKey(i, 0):
                    if op.operand[0].ID == ID_REG and op.operand[0].GetB(0) == reg:
                        h.idxList.append(CMDSimpler.heap[i].index)
                    elif op.operand[1].ID == ID_REG and op.operand[1].GetB(0) == reg:
                        h.idxList.append(CMDSimpler.heap[i].index)
                if op.operand[0].ID == ID_REG and op.operand[1].TID() == TID_VAL and op.operand[0].GetB(0) == reg:
                    h.flowMutateIndex = CMDSimpler.heap[i].index
                    h.flowMutateMnemonic = op.ID
                    h.flowMutateConst = op.operand[1].value
            i += 1
        return False

    def FindSubDataIndex(self, h, i, reg):
        while i < CMDSimpler.count:
            # MOVZX reg, word ptr [reg]
            op = CMDSimpler.heap[i].instr
            if op.ID == OP_MOV and op.operand[0].ID == ID_REG and op.operand[1].ID == ID_MEM32 and \
               op.operand[1].GetB(1) == reg and op.operand[1].GetB(2) == 0 and op.operand[1].GetB(3) == 0 and \
               op.operand[1].val2 == 0:
                h.flowDataIndex = i
                treg = op.operand[0].GetB(0)
                return self.FindSubNegativeCheck(h, i + 1, treg)
            i += 1
        return False

    def FindSubNegativeCheck(self, h, i, reg):
        while i < CMDSimpler.count:
            op = CMDSimpler.heap[i].instr
            if op.ID == OP_AND and op.operand[0].ID == ID_REG and op.operand[0].Base() == reg and \
               op.operand[1].TID() == TID_VAL and op.operand[1].value == 0x80000000:
                return True
            i += 1
        return False

    def RecoverJumpData(self, h):
        cmds = CMDSimpler.heap
        if cmds[CMDSimpler.count - 1].instr.ID != OP_JMP:
            return True

        i = self.FindReadIndex()
        if i == -1:
            return False

        h.flowReadIndex = CMDSimpler.heap[i].index
        #xlog("flowReadIndex {:x}".format(CMDSimpler.heap[i].addr))
        reg = cmds[i].instr.operand[0].GetB(0)

        i = self.FindReadOffset(i + 1, reg)
        if i == -1:
            return False

        h.flowReadOffset = CMDSimpler.heap[i].instr.operand[1].value

        if cmds[CMDSimpler.count - 2].instr.ID == OP_ADD:
            return self.FindAddDataIndex(h, i + 1, reg)
        elif cmds[CMDSimpler.count - 2].instr.ID == OP_SUB:
            return self.FindSubDataIndex(h, i + 1, reg)
        return True

    def DecryptKeyProtectTemplate(self, h):
        heap = CMDSimpler.heap
        i = 0
        while i < CMDSimpler.count:
            op = heap[i].instr

            if op.ID != OP_MOV or \
               op.operand[0].ID != ID_REG or \
               not self.IsIdxOpEbpKey(i, 1):
                i += 1
                continue

            # mov reg, [ebp + ...]
            reg = op.operand[0].XBase()
            binOff = 0
            for j in range(i + 1, CMDSimpler.count):
                jop = heap[j].instr
                if jop.operand[0].ID != ID_REG or \
                   jop.operand[0].XBase() != reg:
                    continue

                if binOff == 0 and IsOpClass(jop.ID, 0, 0, 1):
                    binOff = j
                elif binOff != 0 and CMDSimpler.Bounds(j, 3):
                    jop1 = heap[j + 1].instr
                    jop2 = heap[j + 2].instr
                    if jop.ID == OP_CMP and jop.operand[1].TID() == TID_VAL and jop.operand[1].value == 0 and \
                       jop1.ID == OP_JE and \
                       IsOpClass(jop2.ID, 0, 0, 1) and jop2.operand[0].TID() == TID_MEM and \
                       self.IsIdxOpEbpKey(j + 2, 1) and jop2.operand[0].val2 == op.operand[1].val2:
                        key = FKEY()
                        key.keyId = jop2.operand[0].val2 & 0xFFFF
                        key.idx = heap[i].index
                        key.mnemonic = jop2.ID
                        key.operand = 0
                        key.tid = jop2.operand[1].TID()
                        key.sz = jop2.operand[0].Size()
                        key.dkeyparam = False
                        key.parameter = jop2.operand[1].value
                        key.condition = KeyProtTempl

                        h.keys.append(key)

                        #xlog(key.idx, hex(key.koff1), key.tid, key.sz, hex(key.mnemonic), hex(key.parameter))
                        #xlog(XrkText(op))
                        #xlog(XrkText(heap[binOff].instr))
                        #xlog(XrkText(jop))
                        #xlog(XrkText(jop1))
                        #xlog(XrkText(jop2))

                        jop.iD = 0
                        jop1.ID = 0
                        jop2.ID = 0
                        heap[binOff].instr.ID = 0
                        op.ID = 0
                        CMDSimpler.Cleaner(i, j + 5 - i)

                        i -= 1
                        break
                    else:
                        break
                else:
                    break
            i += 1



    def RecoverKeyData(self, h):
        self.DecryptKeyProtectTemplate(h)

        for i in range(CMDSimpler.count):
            if not self.IsIdxOpEbpKey(i, 0):
                continue

            ## ADD/SUB/XOR/AND/OR/SHL/SHR     not MOV

            cmd = CMDSimpler.heap[i]
            op = cmd.instr

            key = FKEY()
            prime = False
            if cmd.keyData & 0x80000000 == 0x80000000:
                key.dkeyparam = True
                if op.operand[0].TID() == TID_MEM:
                    key.operand = 0
                    key.keyId = op.operand[0].val2 & 0xFFFF
                    key.mnemonic = op.ID
                    key.idx = cmd.index
                    key.tid = op.operand[1].TID()
                    key.sz = op.operand[0].Size()
                    key.parameter = cmd.keyData & 0x7FFFFFFF
                else:
                    key.operand = 1
                    key.keyId = op.operand[1].val2 & 0xFFFF
                    key.mnemonic = op.ID
                    key.idx = cmd.index
                    key.tid = op.operand[0].TID()
                    key.sz = op.operand[1].Size()
                    key.parameter = cmd.keyData & 0x7FFFFFFF
                cmd.keyData = 0
            else:
                key.dkeyparam = False
                if op.operand[0].TID() == TID_MEM:
                    key.operand = 0
                    key.keyId = op.operand[0].val2 & 0xFFFF
                    key.mnemonic = op.ID
                    key.idx = cmd.index
                    key.tid = op.operand[1].TID()
                    key.sz = op.operand[0].Size()
                    key.parameter = op.operand[1].value
                else:
                    key.operand = 1
                    key.keyId = op.operand[1].val2 & 0xFFFF
                    key.mnemonic = op.ID
                    key.idx = cmd.index
                    key.tid = op.operand[0].TID()
                    key.sz = op.operand[1].Size()
                    key.parameter = op.operand[0].value

            op.ID = 0
            h.keys.append(key)
        CMDSimpler.Cleaner()

        h.keys.sort(key=lambda x: x.idx)
        return True

    def CheckHndlJmp(self, h):
        heap = CMDSimpler.heap
        if CMDSimpler.Bounds(0, 16) and \
            heap[0].instr.ID == OP_MOV and \
            heap[1].instr.ID == OP_ADD and \
            heap[2].instr.ID == OP_MOV and \
            heap[3].instr.ID == OP_SHL and \
            heap[4].instr.ID == OP_MOV and \
            heap[5].instr.ID == OP_ADD and \
            heap[6].instr.ID == OP_MOV and \
            heap[7].instr.ID == OP_MOV and \
            heap[8].instr.ID == OP_ADD and \
            heap[9].instr.ID == OP_MOV and \
            heap[10].instr.ID == OP_MOV and \
            heap[11].instr.ID == OP_AND and \
            heap[12].instr.ID == OP_CMP and \
            heap[13].instr.ID == OP_JE and \
            heap[14].instr.ID == OP_AND and \
            heap[15].instr.ID == OP_SUB and \
            heap[16].instr.ID == OP_JMP:

            h.tp = WH_JMP_INS
            #xlog("JMPINS {:X} {:X}".format(heap[1].instr.operand[1].ID, heap[8].instr.operand[1].ID))
            h.opcodeOffsets[0] = heap[1].instr.operand[1].value
            h.opcodeOffsets[1] = heap[8].instr.operand[1].value
            return True
        elif CMDSimpler.Bounds(0, 10) and \
            heap[0].instr.ID == OP_MOV and \
            heap[1].instr.ID == OP_ADD and \
            heap[2].instr.ID == OP_MOV and \
            heap[3].instr.ID == OP_ADD and \
            heap[4].instr.ID == OP_MOV and \
            heap[4].instr.operand[1].Base() == heap[3].instr.operand[0].Base() and \
            heap[5].instr.ID == OP_MOV and \
            heap[6].instr.ID == OP_ADD and \
            heap[7].instr.ID == OP_MOV and \
            heap[8].instr.ID == OP_ADD and \
            heap[9].instr.ID == OP_MOV and \
            heap[9].instr.operand[1].Base() == heap[4].instr.operand[0].Base() and \
            heap[10].instr.ID == OP_MOV:
            h.tp = WH_JMP_OUT_REG
            #xlog("JMP OUT REG {:X}".format(heap[1].instr.operand[1].ID))
            h.opcodeOffsets[0] = heap[1].instr.operand[1].value # must be IMM
            return True
        elif CMDSimpler.Bounds(0, 11) and \
            heap[0].instr.ID == OP_MOV and \
            heap[1].instr.ID == OP_ADD and \
            heap[2].instr.ID == OP_MOV and \
            heap[3].instr.ID == OP_ADD and \
            heap[4].instr.ID == OP_MOV and \
            heap[4].instr.operand[1].Base() == heap[3].instr.operand[0].Base() and \
            heap[5].instr.ID == OP_MOV and \
            heap[5].instr.operand[1].Base() == heap[4].instr.operand[0].Base() and \
            heap[6].instr.ID == OP_MOV and \
            heap[7].instr.ID == OP_ADD and \
            heap[8].instr.ID == OP_MOV and \
            heap[9].instr.ID == OP_ADD and \
            heap[10].instr.ID == OP_MOV and \
            heap[11].instr.ID == OP_MOV:
            h.tp = WH_JMP_OUT_MEM
            #xlog("JMP OUT MEM {:X}".format(heap[1].instr.operand[1].ID))
            h.opcodeOffsets[0] = heap[1].instr.operand[1].value # must be IMM
            return True
        elif CMDSimpler.Bounds(0, 18) and \
            heap[0].instr.ID == OP_MOV and \
            heap[1].instr.ID == OP_ADD and \
            heap[2].instr.ID == OP_MOV and \
            heap[3].instr.ID == OP_ADD and \
            heap[4].instr.ID == OP_MOV and \
            heap[5].instr.ID == OP_ADD and \
            heap[6].instr.ID == OP_MOV and \
            heap[7].instr.ID == OP_ADD and \
            heap[7].instr.operand[1].IsReg(R_ESP) and \
            heap[8].instr.ID == OP_MOV and \
            heap[9].instr.ID == OP_MOV and \
            heap[10].instr.ID == OP_POP and \
            heap[11].instr.ID == OP_POP and \
            heap[12].instr.ID == OP_POP and \
            heap[13].instr.ID == OP_POP and \
            heap[14].instr.ID == OP_POP and \
            heap[15].instr.ID == OP_POP and \
            heap[16].instr.ID == OP_POP and \
            heap[17].instr.ID in (OP_POP, OP_POPF) and \
            heap[18].instr.ID == OP_RETN:
            h.tp = WH_JMP_OUT_IMM
            #xlog("JMP OUT IMM {:X}".format(heap[1].instr.operand[1].ID))
            h.opcodeOffsets[0] = heap[1].instr.operand[1].value # must be IMM
            return True
        return False

    def ParseJccParameters(self, h):
        if not self.initedJccTypes:
            r = 0
            index = 8
            for i in range(17):
                op = None
                while True:
                    index = CMDSimpler.NextOpPos(OP_CMP, index + 1)
                    if index == -1:
                        return False

                    op = CMDSimpler.heap[index].instr
                    if op.operand[0].IsReg8():
                        if r == 0:
                            r = op.operand[0].Base()
                            break
                        elif op.operand[0].Base() == r:
                            break

                jccTbl = (OP_JE, OP_JLE, OP_JNZ, OP_JA,
                          OP_JNB, OP_JB, OP_JBE, OP_JG,
                          OP_JGE, OP_JL, OP_JCXZ, OP_JNO,
                          OP_JNP, OP_JNS, OP_JO, OP_JP, OP_JS)

                t = op.operand[1].value
                if t not in self.jccMnemonicTypes:
                    self.jccMnemonicTypes[t] = jccTbl[i]
            self.initedJccTypes = True

        occur = 0
        i = 40
        while i < CMDSimpler.count - 1:
            op = CMDSimpler.heap[i].instr
            if op.ID == OP_MOV and self.IsVmEipOp(op):
                op1 = CMDSimpler.heap[i + 1].instr
                if occur == 0:
                    h.opcodeOffsets[1] = op1.operand[1].value
                elif occur == 1:
                    h.opcodeOffsets[2] = op1.operand[1].value
                    return True
                occur += 1
            i += 1
        return False

    def CheckHndlJcc(self, h):
        heap = CMDSimpler.heap
        if CMDSimpler.Bounds(0, 14) and \
            heap[0].instr.ID == OP_MOV and \
            heap[1].instr.ID == OP_MOV and \
            heap[2].instr.ID == OP_ADD and \
            heap[3].instr.ID == OP_MOV and \
            heap[4].instr.ID == OP_ADD and \
            heap[5].instr.ID == OP_MOV and \
            heap[6].instr.ID == OP_MOV and \
            heap[7].instr.ID == OP_ADD and \
            heap[8].instr.ID == OP_MOV and \
            heap[9].instr.ID == OP_CMP and \
            heap[10].instr.ID == OP_JE and \
            heap[11].instr.ID == OP_CMP and \
            heap[12].instr.ID == OP_JE and \
            heap[13].instr.ID == OP_CMP and \
            heap[14].instr.ID == OP_JNZ:
            idx = CMDSimpler.count - 25
            if CMDSimpler.Bounds(0, 25) and CMDSimpler.NextOpPos(OP_RETN, idx) != -1:
                h.tp = WH_JCC_OUT
            else:
                h.tp = WH_JCC_INS
            #xlog("JCC  {:X}".format(heap[7].instr.operand[1].ID))
            h.opcodeOffsets[0] = heap[7].instr.operand[1].value
            return self.ParseJccParameters(h)
        return False

    def CheckHndlRetn(self, h):
        heap = CMDSimpler.heap
        for i in range(2, 15):
            if heap[i].instr.ID == OP_STD:
                h.tp = WH_RET
                h.opcodeOffsets[0] = heap[1].instr.operand[1].value
                return True
        return False

    def CheckHndlUndef(self, h):
        heap = CMDSimpler.heap
        if CMDSimpler.Bounds(0, 10) and \
            heap[0].instr.ID == OP_MOV and \
            heap[1].instr.ID == OP_ADD and \
            heap[2].instr.ID == OP_MOV and \
            heap[3].instr.ID == OP_CMP and \
            heap[4].instr.ID == OP_JE and \
            heap[5].instr.ID == OP_CMP and \
            heap[6].instr.ID == OP_JE and \
            heap[7].instr.ID == OP_MOV and \
            heap[8].instr.ID == OP_ADD and \
            heap[9].instr.ID == OP_MOV and \
            heap[10].instr.ID == OP_ADD:
            idx = CMDSimpler.count - 25
            h.tp = WH_UNDEF
            # xlog("JCC  {:X}".format(heap[7].instr.operand[1].ID))
            h.opcodeOffsets[0] = heap[1].instr.operand[1].value
            h.opcodeOffsets[1] = heap[8].instr.operand[1].value
            return True
        return False

    def CheckHndlLods(self, h):
        heap = CMDSimpler.heap
        # mov
        # and
        # pop

        popIdx = CMDSimpler.NextOpPos(OP_POP, 18)
        if popIdx == -1:
            return False

        if heap[popIdx - 2].instr.ID != OP_MOV or \
            heap[popIdx - 1].instr.ID != OP_AND:
            return False

        # push  reg
        idx = CMDSimpler.NextOpPos(OP_PUSH, 2)
        if idx == -1 or idx >= 15 or heap[idx].instr.operand[0].ID != ID_REG:
            return False

        memIdx = -1
        for i in range(idx, 16):
            if i >= CMDSimpler.count:
                break

            # mov ptr [reg], ...
            if heap[i].instr.ID == OP_MOV and \
               heap[i].instr.operand[0].TID() == TID_MEM:
                memIdx = i
                break

        if memIdx == -1:
            return False
        if not CMDSimpler.Bounds(popIdx, 3):
            return False

        # cmp   ..., 0
        # je    ...
        # sub   ..., ...

        if heap[popIdx + 1].instr.ID == OP_CMP and \
           heap[popIdx + 1].instr.operand[1].TID() == TID_VAL and heap[popIdx + 1].instr.operand[1].value == 0 and \
           heap[popIdx + 2].instr.ID == OP_JE and \
           heap[popIdx + 3].instr.ID == OP_SUB:
            if heap[memIdx].instr.operand[0].Base() != heap[idx].instr.operand[0].Base():
                t = heap[popIdx + 3].instr.operand[1].value
                if t == 1:
                    h.tp = WH_LODSB
                elif t == 2:
                    h.tp = WH_LODSW
                elif t == 4:
                    h.tp = WH_LODSD
                else:
                    return False
                #xlog("LODS ", t)
                return True
        return False

    def CheckHndlStos(self, h):
        heap = CMDSimpler.heap
        # mov
        # and
        # pop

        popIdx = CMDSimpler.NextOpPos(OP_POP, 18)
        if popIdx == -1:
            return False

        if heap[popIdx - 2].instr.ID != OP_MOV or \
            heap[popIdx - 1].instr.ID != OP_AND:
            return False

        # push  reg
        idx = CMDSimpler.NextOpPos(OP_PUSH, 2)
        if idx == -1 or idx >= 15 or heap[idx].instr.operand[0].ID != ID_REG:
            return False

        memIdx = -1
        for i in range(idx, 16):
            if i >= CMDSimpler.count:
                break

            # mov ptr [reg], ...
            if heap[i].instr.ID == OP_MOV and \
               heap[i].instr.operand[0].TID() == TID_MEM:
                memIdx = i
                break

        if memIdx == -1:
            return False
        if not CMDSimpler.Bounds(popIdx, 3):
            return False

        # cmp   ..., 0
        # je    ...
        # sub   ..., ...

        if heap[popIdx + 1].instr.ID == OP_CMP and \
           heap[popIdx + 1].instr.operand[1].TID() == TID_VAL and heap[popIdx + 1].instr.operand[1].value == 0 and \
           heap[popIdx + 2].instr.ID == OP_JE and \
           heap[popIdx + 3].instr.ID == OP_SUB:
            if heap[memIdx].instr.operand[0].Base() == heap[idx].instr.operand[0].Base():
                t = heap[popIdx + 3].instr.operand[1].value
                if t == 1:
                    h.tp = WH_STOSB
                elif t == 2:
                    h.tp = WH_STOSW
                elif t == 4:
                    h.tp = WH_STOSD
                else:
                    return False
                #xlog("STOS ", t)
                return True
        return False

    def CheckHndlScas(self, h):
        heap = CMDSimpler.heap
        # sub
        # pushfd

        Idx = CMDSimpler.NextOpPos(OP_PUSHF, 10)
        if Idx == -1:
            return False

        if heap[Idx - 1].instr.ID != OP_SUB:
            return False


        Idx = CMDSimpler.NextOpPos(OP_CMP, 10)
        if Idx == -1:
            return False
        if not CMDSimpler.Bounds(Idx, 2):
            return False

        # cmp   ..., 0
        # je    ...
        # sub   ..., imm

        if heap[Idx].instr.ID == OP_CMP and \
           heap[Idx].instr.operand[1].TID() == TID_VAL and heap[Idx].instr.operand[1].value == 0 and \
           heap[Idx + 1].instr.ID == OP_JE and \
           heap[Idx + 2].instr.ID == OP_SUB and heap[Idx + 2].instr.operand[1].TID() == TID_VAL:
            t = heap[Idx + 2].instr.operand[1].value
            if t == 1:
                h.tp = WH_SCASB
            elif t == 2:
                h.tp = WH_SCASW
            elif t == 4:
                h.tp = WH_SCASD
            else:
                return False
            #xlog("SCAS ", t)
            return True
        return False

    def CheckHndlCmps(self, h):
        heap = CMDSimpler.heap
        # cmp
        # pushfd

        Idx = CMDSimpler.NextOpPos(OP_PUSHF, 10)
        if Idx == -1:
            return False

        if heap[Idx - 1].instr.ID != OP_CMP:
            return False

        Idx = CMDSimpler.NextOpPos(OP_CMP, Idx)
        if Idx == -1:
            return False

        if not CMDSimpler.Bounds(Idx, 3):
            return False

        # cmp   ..., 0
        # je    ...
        # sub   ..., imm
        # sub   ..., ...

        if heap[Idx].instr.operand[1].TID() == TID_VAL and heap[Idx].instr.operand[1].value == 0 and \
            heap[Idx + 1].instr.ID == OP_JE and \
            heap[Idx + 2].instr.ID == OP_SUB and heap[Idx + 2].instr.operand[1].TID() == TID_VAL and \
            heap[Idx + 3].instr.ID == OP_SUB :
            t = heap[Idx + 2].instr.operand[1].value
            if t == 1:
                h.tp = WH_CMPSB
            elif t == 2:
                h.tp = WH_CMPSW
            elif t == 4:
                h.tp = WH_CMPSD
            else:
                return False
            # xlog("SCAS ", t)
            return True
        return False

    def CheckHndlMovs(self, h):
        heap = CMDSimpler.heap

        memIdx = -1
        for i in range(10, 25):
            op = heap[i].instr
            if op.ID == OP_MOV and op.operand[0].TID() == TID_MEM:
                memIdx = i
                break

        # cmp ..., 0
        # je
        # sub ..., ...
        # sub ..., imm

        if memIdx == -1:
            return False

        idx = CMDSimpler.NextOpPos(OP_CMP, memIdx)
        if idx == -1:
            return False

        if not CMDSimpler.Bounds(idx, 3):
            return False

        if (idx - memIdx) not in range(10, 21):
            return False

        if heap[idx].instr.operand[1].TID() == TID_VAL and heap[idx].instr.operand[1].value == 0 and \
            heap[idx + 1].instr.ID == OP_JE and \
            heap[idx + 2].instr.ID == OP_SUB and \
            heap[idx + 3].instr.ID == OP_SUB and heap[idx + 3].instr.operand[1].TID() == TID_VAL:
            t = heap[idx + 3].instr.operand[1].value
            if t == 1:
                h.tp = WH_MOVSB
            elif t == 2:
                h.tp = WH_MOVSW
            elif t == 4:
                h.tp = WH_MOVSD
            else:
                return False
            # xlog("MOVS ", t)
            return True
        return False

    def ParseEflagsParameters(self):
        if self.initedEflagsTypes:
            return True

        b = 0
        idx = 5
        for i in range(7):
            op = None
            while True:
                idx = CMDSimpler.NextOpPos(OP_CMP, idx + 1)
                if idx == -1:
                    return False

                op = CMDSimpler.heap[idx].instr
                if op.operand[0].IsReg8():
                    if b != 0:
                        b = op.operand[0].Base()
                        break
                    elif op.operand[0].Base() == b:
                        break

            if self.GetMnemonic( op.operand[1].value ) != OP_NONE :
                xlog("EFLAGS mnemonic table corrupt with {:08X}".format(self.GetMnemonic( op.operand[1].value )))
            else:
                mnems = (OP_CLC, OP_CLD, OP_CLI, OP_CMC, OP_STC, OP_STD, OP_STI)
                self.SetMnemonic( op.operand[1].value, mnems[i] )
        self.initedEflagsTypes = True
        return True

    def CheckHndlEflags(self, h):
        heap = CMDSimpler.heap

        if CMDSimpler.Bounds(0, 8) and \
            heap[0].instr.ID == OP_MOV and \
            heap[1].instr.ID == OP_ADD and \
            heap[2].instr.ID == OP_MOV and \
            heap[3].instr.ID == OP_ADD and heap[3].instr.operand[1].ID == ID_REG and \
            heap[4].instr.ID == OP_MOV and \
            heap[5].instr.ID == OP_ADD and \
            heap[6].instr.ID == OP_MOV and \
            heap[7].instr.ID == OP_CMP and \
            heap[8].instr.ID == OP_JNZ :
            h.tp = WH_EFLAGS
            h.opcodeOffsets[0] = heap[1].instr.operand[1].value
            h.opcodeOffsets[1] = heap[5].instr.operand[1].value
            return self.ParseEflagsParameters()

        matches = []

        for i in range(CMDSimpler.count):
            op = heap[i].instr
            if op.ID == OP_MOV and op.operand[0].ID == ID_REG and self.IsVmEipOp(op):
                idx = i
                ins = None

                # add reg, ...
                (idx, cmd) = CMDSimpler.NextOp0Reg(idx + 1, op.operand[0].Base())
                if idx == -1 or cmd.instr.ID != OP_ADD:
                    continue

                (idx, cmd) = CMDSimpler.NextOp1MemReg(idx + 1, op.operand[0].Base())
                if idx == -1 or cmd.instr.ID != OP_MOVZX:
                    continue

                dbs = cmd.instr.operand[0].Base()

                # add  reg, ebp
                (idx, cmd) = CMDSimpler.NextOp0Reg(idx + 1, dbs)
                if idx == -1 or cmd.instr.ID != OP_ADD or not cmd.instr.operand[1].IsReg(R_EBP):
                    continue

                # ...   unk ptr [reg]
                (idx, cmd) = CMDSimpler.NextOp0MemReg(idx + 1, dbs)
                if idx == -1 or idx > 20:
                    continue

                matches.append( (idx, cmd.instr) )

        if not matches:
            return False

        for i in range(2):
            ofsCnt = 0
            oprCnt = 0

            cop1 = OP_UNDEFINED
            cop2 = OP_UNDEFINED
            if i==0:
                cop1 = OP_SUB
                cop2 = OP_PUSH
            else:
                cop1 = OP_ADD
                cop2 = OP_POP

            for j in range(len(matches)):
                # sub/add unk ptr [reg], 0x4
                mt = matches[j]
                if mt[1].ID == cop1 and \
                   mt[1].operand[1].TID() == TID_VAL and \
                   mt[1].operand[1].value == 4:
                    ofsCnt += 1
                elif mt[1].ID == cop2:
                    if mt[1].ID == OP_PUSH and CMDSimpler.Bounds(mt[0], 1) and\
                       heap[ mt[0] + 1 ].instr.ID in (OP_POPF, OP_POP):
                        break
                    oprCnt += 1

            if ofsCnt == 1 and oprCnt == 1:
                if i == 0:
                    h.tp = WH_PUSHFD
                else:
                    h.tp = WH_POPFD
                return True
        return False


    def CheckHndlStack(self, h):
        heap = CMDSimpler.heap
        # mov   ...,...
        # add   ...,...
        # movzx ...,...
        # add   ...,...
        # mov   esp,...
        if  CMDSimpler.Bounds(0, 4) and \
            heap[0].instr.ID == OP_MOV and \
            heap[1].instr.ID == OP_ADD and \
            heap[2].instr.ID == OP_MOVZX and \
            heap[3].instr.ID == OP_ADD and \
            heap[4].instr.ID == OP_MOV and \
            heap[4].instr.operand[0].IsReg(R_ESP):
            h.tp = WH_LOAD_STK
            h.opcodeOffsets[0] = heap[1].instr.operand[1].value
            return True

        # mov   ...,...
        # add   ...,...
        # movzx ...,...
        # add   ...,...
        # mov   ...,esp
        elif CMDSimpler.Bounds(0, 4) and \
            heap[0].instr.ID == OP_MOV and \
            heap[1].instr.ID == OP_ADD and \
            heap[2].instr.ID == OP_MOVZX and \
            heap[3].instr.ID == OP_ADD and \
            heap[4].instr.ID == OP_MOV and \
            heap[4].instr.operand[1].IsReg(R_ESP):
            h.tp = WH_STORE_STK
            h.opcodeOffsets[0] = heap[1].instr.operand[1].value
            return True

        else:
            for i in range(3, 9):
                if i >= CMDSimpler.count:
                    return False

                op = heap[i].instr
                if op.ID == OP_ADD and op.operand[0].IsReg(R_ESP) and op.operand[1].IsRegNot(R_ESP):
                    h.tp = WH_RESTORE_STK
                    h.opcodeOffsets[0] = heap[4].instr.operand[1].value
                    return True
        return False

    def CheckHndlResetEflags(self, h):
        if not CMDSimpler.Bounds(0, 0):
            return False

        op = CMDSimpler.heap[0].instr
        if  op.ID == OP_MOV and\
            op.operand[0].IsMem32Base(R_EBP) and\
            op.operand[1].TID() == TID_VAL and op.operand[1].value == 0 and \
            h.flowReadIndex == 1:
            h.tp = WH_RESET_EFLAGS
            return True
        return False

    def CheckHndlReset(self, h):
        for i in range(5):
            if i >= CMDSimpler.count:
                break

            if CMDSimpler.heap[i].instr.ID != OP_MOV:
                return False
        h.tp = WH_RESET
        return True

    def CheckHndlCrypt(self, h):
        if not CMDSimpler.Bounds(0, 6):
            return False

        base = 0
        opcodes = 0

        for i in range(5):
            if i >= CMDSimpler.count:
                break

            op = CMDSimpler.heap[i].instr
            if op.operand[0].TID() == TID_MEM:
                return False

            if op.ID == OP_MOV and op.operand[1].TID() == TID_MEM:
                if self.IsVmEipOp(op):
                    opcodes += 1
                elif op.operand[0].IsReg32() and \
                    op.operand[1].Base() == R_EBP and \
                    not self.IsHasKey(op.operand[1].val2):
                    base = op.operand[0].Base()

        op5 = CMDSimpler.heap[5].instr
        if  opcodes == 1 and \
            op5.operand[0].ID == ID_MEM32 and \
            op5.operand[1].IsReg(base):
            h.tp = WH_CRYPT

            for i in range(5):
                op = CMDSimpler.heap[i].instr
                if op.ID == OP_MOV and op.operand[1].ID == ID_MEM32 and \
                    not self.IsVmEipOp(op):
                    h.opcodeOffsets[1] = op.operand[1].val2
                elif op.ID == OP_ADD and op.operand[1].TID() == TID_VAL:
                    h.opcodeOffsets[0] = op.operand[1].value
            return True
        return False

    def RecoveryAdvancedHandler(self, h):
        return False

    def RecoveryHandler(self, h):
        return (self.CheckHndlJmp(h) or
                self.CheckHndlJcc(h) or
                self.CheckHndlRetn(h) or
                self.CheckHndlUndef(h) or
                self.CheckHndlLods(h) or
                self.CheckHndlStos(h) or
                self.CheckHndlScas(h) or
                self.CheckHndlCmps(h) or
                self.CheckHndlMovs(h) or
                self.CheckHndlEflags(h) or
                self.CheckHndlStack(h) or
                self.CheckHndlResetEflags(h) or
                self.CheckHndlReset(h) or
                self.CheckHndlCrypt(h))

    def FindXCHGRegs(self):
        lst = list()
        i = 0
        while i < CMDSimpler.count:
            if not CMDSimpler.Bounds(i, 3):
                break
            op0 = CMDSimpler.heap[i].instr
            op1 = CMDSimpler.heap[i + 1].instr
            op2 = CMDSimpler.heap[i + 2].instr
            op3 = CMDSimpler.heap[i + 3].instr

            if op0.ID == OP_PUSH and op1.ID == OP_PUSH and\
               op2.ID == OP_POP and op3.ID == OP_POP and\
               op0.operand[0].ID == ID_MEM32 and \
               op1.operand[0].ID == ID_MEM32 and \
               op2.operand[0].ID == ID_MEM32 and \
               op3.operand[0].ID == ID_MEM32 and \
               op0.operand[0].Base() == op2.operand[0].Base() and \
               op1.operand[0].Base() == op3.operand[0].Base():
                x = VMXCHG()
                x.index = i
                x.reg1 = op0.operand[0].Base()
                x.reg2 = op1.operand[0].Base()
                lst.append( x )
                i += 4
            else:
                i += 1
        return lst




    def DecryptOpcodeRegions(self, h, dbg=False):
        heap = CMDSimpler.heap

        xchg = self.FindXCHGRegs()

        for i in range(CMDSimpler.count):
            op = heap[i].instr
            if op.ID == OP_MOV and \
               op.operand[0].ID == ID_REG and \
               self.IsVmEipOp(op):
                opOffset = -1
                tp = -1
                sz = -1
                offset = 0
                for j in range(i + 1, CMDSimpler.count):
                    jop = heap[j].instr
                    if jop.ID == OP_ADD and \
                        jop.operand[0].ID == ID_REG and \
                        jop.operand[0].XBase() == op.operand[0].XBase() and \
                        jop.operand[1].TID() == TID_VAL:
                        opOffset = jop.operand[1].value
                    elif jop.ID in (OP_MOV, OP_MOVZX) and \
                        jop.operand[1].TID() == TID_MEM and \
                        jop.operand[1].XBase() == op.operand[0].XBase():
                        tp = jop.operand[0].XBase()
                        sz = jop.operand[1].Size()
                        offset = j
                        break
                    elif jop.ID == OP_MOV and \
                        jop.operand[0].ID == ID_REG and \
                        jop.operand[0].XBase() == op.operand[0].XBase():
                        break

                #xlog(hex(offset))
                if opOffset == -1 or tp == -1:
                    continue

                index = heap[offset].index + 1
                indexes = list()
                endindex = heap[CMDSimpler.count - 1].index

                while index <= endindex and index < h.flowReadIndex:
                    opdxi = CMDSimpler.FindIndexByIndex(index)
                    if opdxi != -1:
                        opdx = heap[opdxi].instr
                        if opdx.ID in (OP_MOV, OP_MOVZX) and \
                                opdx.operand[0].ID == ID_REG and \
                                opdx.operand[0].XBase() == tp:
                            break
                        if CMDSimpler.Bounds(opdxi, 3):
                            op1 = CMDSimpler.heap[opdxi + 1].instr
                            op2 = CMDSimpler.heap[opdxi + 2].instr
                            op3 = CMDSimpler.heap[opdxi + 3].instr

                            if opdx.ID == OP_PUSH and op1.ID == OP_PUSH and \
                                    op2.ID == OP_POP and op3.ID == OP_POP and \
                                    opdx.operand[0].ID == ID_MEM32 and \
                                    op1.operand[0].ID == ID_MEM32 and \
                                    op2.operand[0].ID == ID_MEM32 and \
                                    op3.operand[0].ID == ID_MEM32 and \
                                    opdx.operand[0].Base() == op2.operand[0].Base() and \
                                    op1.operand[0].Base() == op3.operand[0].Base() and \
                                    (opdx.operand[0].XBase() == tp or op1.operand[0].XBase() == tp):
                                indexes = list()
                                break

                    for k in h.keys:
                        if k.idx == index:
                            if k.tid == TID_REG and \
                               k.dkeyparam == False and \
                               heap[offset].instr.operand[0].XBase() == (k.parameter >> 4):
                                indexes.append(index)
                            break



                    index += 1

                if len(indexes) > 0:
                    h.regions.append( OPREGION(0, opOffset, sz, indexes[0], indexes[-1]) )
                    continue

                if len(xchg) == 0:
                    continue

                vmreg = False
                for j in range(offset + 1, CMDSimpler.count):
                    jop = heap[j].instr

                    if jop.ID == OP_MOV and \
                        jop.operand[0].ID == ID_REG and \
                        jop.operand[0].XBase() == tp:
                        break
                    elif not vmreg and \
                         jop.ID == OP_ADD and \
                         tp != -1 and sz == 2 and \
                         jop.operand[0].ID == ID_REG and \
                         jop.operand[0].XBase() == tp and \
                         jop.operand[1].IsReg(R_EBP):
                        vmreg = True
                    elif vmreg and jop.ID == OP_PUSH and \
                         jop.operand[0].ID == ID_MEM32 and \
                         jop.operand[0].XBase() == tp:
                        reg = jop.operand[0].Base()
                        for x in xchg:
                            if j >= x.index and j < x.index + 4:
                                if x.off1 == -1 and x.reg1 == reg:
                                    x.off1 = opOffset
                                    if x.off2 != -1:
                                        h.regions.append(OPREGION(1, x.off1, 2, CMDSimpler.heap[j].index, x.off2))
                                        #xlog("PushPop Added")
                                elif x.off2 == -1 and x.reg2 == reg:
                                    x.off2 = opOffset
                                    if x.off1 != -1:
                                        h.regions.append(OPREGION(1, x.off1, 2, CMDSimpler.heap[j].index, x.off2))
                                        #xlog("PushPop Added")
                                else:
                                    xlog("PushPop collision")
                        break

    def DecryptOpcodeSize(self, h):
        lastop = CMDSimpler.Last().instr
        if lastop.ID == OP_RETN:
            h.opcodeSize = OPSZ_RETN
        elif lastop.ID == OP_JMP:
            op = CMDSimpler.heap[ CMDSimpler.count - 2 ].instr
            if self.IsVmEipOp(op):
                if op.ID == OP_SUB:
                    h.opcodeSize = OPSZ_SUB
                elif op.ID == OP_ADD:
                    h.opcodeSize = op.operand[1].value

    def RecoverHandle(self, h, fdbg = None):
        if not self.RecoverJumpData(h):
            xlog("Error while recover jump data")
            return False

        if not self.RecoverKeyData(h):
            xlog("Error while recover key data")
            return False

        if fdbg != None:
            if CMDSimpler.count > 0:
                fdbg.write("//////////////////////////////////////////////\r\n// FISH Virtual Handler {:04x} {:08x}\r\n".format(h.hndlID, CMDSimpler.heap[0].addr))
                for l in CMDSimpler.GetListing(1, 1):
                    fdbg.write("{}\n".format(l))

        if not self.RecoveryHandler(h):
            if not self.RecoveryAdvancedHandler(h):
                return False

        self.DecryptOpcodeRegions(h)
        self.DecryptOpcodeSize(h)

        #self.RecoveryHandleType(h)

        #if h.tp == -1:
        #    xlog("Error while recover handler type")
        #    return False
        #else:
        #    xlog("Handler {:x}".format(h.tp))

        return True

    def EnumOps(self):
        for i in range(CMDSimpler.count):
            CMDSimpler.heap[i].index = i

    def DeofusHndl(self, i):
        if i not in range(self.iatCount):
            return False

        if i in self.hndl:
            return True

        m = self.GetMM(UINT(self.iatAddr + i * 4))
        haddr = GetDWORD(m)

        hndlAddr = UINT(self.ivmbase + haddr)
        self.DumpHandler(hndlAddr, 1)

        ####
        self.fmach.write("//////////////////////////////////////////////\r\n// FISH Virtual Handler {:04x} {:08x}\r\n".format(i, hndlAddr))
        for l in CMDSimpler.GetListing(1, 1, True):
            self.fmach.write("{}\n".format(l))

        self.EnumOps()

        h = self.HANDLER(i)
        h.c024 = self.compares
        h.code = CMDSimpler.Clone()
        h.dumpAddr = hndlAddr

        if not self.RecoverHandle(h, self.fdmach):
            # time.sleep(1.5)
            pass

        if h.tp != -1:
            xlog(
                "\t{:04x} Handler {:04x} {:08x} {:d}({:d}) {:d}".format(h.tp, i, hndlAddr, h.operands[0].tp,
                                                                        h.operands[0].sz, h.operands[1].tp))
            self.fdmach.write("Handler {:04x}\n".format(h.tp))
        else:
            xlog("\t{:04x} Handler {:04x} {:08x} keys {:d} regions {:d} size {:d}".format(h.tp, i, hndlAddr,
                                                                                           len(h.keys), len(h.regions),
                                                                                           h.opcodeSize))
        # xlog(" " + hex(h.tp))

        self.hndl[i] = h
        self.hndlCount += 1
        return True


    def DeofusVM(self):
        b = GetBytes(UINT(self.VmContext + self.HTableOff), 4)
        if not b:
            return False

        self.ivmbase = GetDWORD(b)
        if self.iatAddr == self.ivmbase:
            self.ivmbase = 0
        else:
            self.ivmbase = self.imageBase

        self.f_6f038 = 0

        xlog("Open out file ", "{}/TXT/Fish_Machine_{:08x}.txt".format(self.WrkDir, self.VMAddr),)

        self.fmach = open("{}/TXT/Fish_Machine_{:08x}.txt".format(self.WrkDir, self.VMAddr), "w")
        self.fdmach = open("{}/TXT/Fish_Machine_dbg_{:08x}.txt".format(self.WrkDir, self.VMAddr), "w")

        return True

        f = open("{}/TXT/Fish_FULL_{:08x}.txt".format(self.WrkDir, self.VMAddr), "w")
        f2 = open("{}/TXT/Fish_FULL_dbg_{:08x}.txt".format(self.WrkDir, self.VMAddr), "w")
        for i in range(self.iatCount):
            m = self.GetMM( UINT(self.iatAddr + i * 4) )
            haddr = GetDWORD(m)

            self.DumpHandler( UINT(self.ivmbase + haddr), 1 )

            ####
            #sys.stdout.write("\tHandler {:04x} {:08x}".format(i, UINT(self.ivmbase + haddr)))
            f.write("//////////////////////////////////////////////\r\n// FISH Virtual Handler {:04x} {:08x}\r\n".format(i, UINT(self.ivmbase + haddr)))
            for l in CMDSimpler.GetListing(1, 1, True):
                f.write("{}\n".format(l))

            self.EnumOps()

            h = self.HANDLER(i)
            h.c024 = self.compares
            h.code = CMDSimpler.Clone()

            if not self.RecoverHandle(h, f2):
                #time.sleep(1.5)
                pass

            if h.tp != -1 :
                xlog("\t{:04x} Handler {:04x} {:08x} {:d}({:d}) {:d}".format(h.tp, i, UINT(self.ivmbase + haddr), h.operands[0].tp, h.operands[0].sz, h.operands[1].tp))
            else:
                xlog("\t{:04x} Handler {:04x} {:08x} keys {:d} regions {:d} size {:d}".format(h.tp, i, UINT(self.ivmbase + haddr), len(h.keys), len(h.regions), h.opcodeSize))
            #xlog(" " + hex(h.tp))

            self.hndl[i] = h
            self.hndlCount += 1
        #exit()
        return True

    def IsFlowHandler(self, h):
        return h.tp in (WH_JMP_INS, WH_JMP_OUT_REG, WH_JMP_OUT_MEM, WH_JMP_OUT_IMM, WH_RET, WH_CALL, WH_UNDEF)

    def StepAdvanced(self, h, reader):
        return False

    def FindFirstKeyAfter(self, h, idx):
        for i in range(len(h.keys)):
            if h.keys[i].idx >= idx:
                return i
        return -1

    def FindLastKeyBefore(self, h, idx):
        i = len(h.keys) - 1
        while i >= 0:
            if h.keys[i].idx <= idx:
                return i
            i -= 1
        return -1

    def StepFlow(self, h, rawOff, skipMutate, dbg = False):
        if skipMutate:
            self.trHid = rawOff & 0xFFFF
            self.trAddr += h.opcodeSize
        else:
            hoff = rawOff

            if h.opcodeSize in (OPSZ_SUB, OPSZ_RETN, OPSZ_INVALID):
                xlog("h.opcodeSize in (OPSZ_SUB, OPSZ_RETN, OPSZ_INVALID) {:x}".format(h.opcodeSize))
                return False

            if len(h.idxList) == 0:
                if h.flowMutateIndex != -1:
                    if dbg:
                        xlog("Flow mutate {:d} {} {:x}, {:x}".format(h.flowMutateIndex, OpTxt(h.flowMutateMnemonic), hoff, h.flowMutateConst))
                    _, hoff = ComputeVal(h.flowMutateMnemonic, 3, hoff, h.flowMutateConst)
            else:
                c = self.FindFirstKeyAfter(h, h.idxList[0])
                e = self.FindLastKeyBefore(h, h.idxList[-1])

                if c == -1 or e == -1:
                    xlog("c == -1 or e == -1")
                    return False

                fmutate = False
                while c <= e:
                    if h.flowMutateIndex != -1 and not fmutate and h.keys[c].idx > h.flowMutateIndex:
                        if dbg:
                            xlog("Flow mutate {:d} {} {:x}, {:x}".format(h.flowMutateIndex, OpTxt(h.flowMutateMnemonic), hoff, h.flowMutateConst))
                        _, hoff = ComputeVal(h.flowMutateMnemonic, 3, hoff, h.flowMutateConst)
                        fmutate = True

                    res, hoff = self.PerformHndlKey(h, c, hoff, dbg)
                    if not res:
                        xlog("if not res")
                        return False
                    c += 1

                if h.flowMutateIndex != -1 and not fmutate:
                    if dbg:
                        xlog("Flow mutate {:d} {} {:x}, {:x}".format(h.flowMutateIndex, OpTxt(h.flowMutateMnemonic), hoff, h.flowMutateConst))
                    _, hoff = ComputeVal(h.flowMutateMnemonic, 3, hoff, h.flowMutateConst)

            self.trHid = hoff & 0xFFFF
            self.trAddr += h.opcodeSize

        xlog("Flow {:x} {:x}\n".format(self.trAddr, self.trHid))
        return True

    def PerformHndlKey(self, h, i, data, dbg = False):
        #dbg = True
        k = h.keys[i]
        # skip perform if condition exist and not satisfed
        if k.condition != None and not k.condition(self, k):
            if dbg:
                xlog("False condition")
            return (True, data)

        if k.dkeyparam:
            if k.tid != TID_REG:
                xlog("[CodeDevirtualizer] Direct key param type != REG.")
                return (False, data)
            srcKeyData = self.GetKey(k.parameter)
            if srcKeyData == None:
                xlog("[CodeDevirtualizer] Could not get key data from source key.")
                return (False, data)
            dstKeyData = self.GetKey(k.keyId)
            if srcKeyData == None:
                xlog("[CodeDevirtualizer] Could not get key data from destination key.")
                return (False, data)

            if dbg:
                xlog("VM[ {:x} ] ({:x})  {}:{:d}  VM[ {:x} ] ({:x})".format(k.keyId, dstKeyData,  OpTxt(k.mnemonic), k.sz,   k.parameter, srcKeyData ))
            _,dstKeyData = ComputeVal(k.mnemonic, k.sz, dstKeyData, srcKeyData)

            if not self.SetKey(k.keyId, dstKeyData):
                xlog("[CodeDevirtualizer] Could not set key data for destination key.")
                return (False, data)
        elif k.operand > 0:
            if k.tid != TID_REG:
                xlog("[CodeDevirtualizer] Indirect key type != REG.")
                return (False, data)
            keyData = self.GetKey(k.keyId)
            if keyData == None:
                xlog("[CodeDevirtualizer] k.operand Could not get data from key.  (keyId {:d})".format(k.keyId))
                return (False, data)

            if dbg:
                xlog(".. {}:{:d}   {:x}   {:x} ({:x})".format(OpTxt(k.mnemonic), k.sz, data, k.keyId, keyData))
            _, data = ComputeVal(k.mnemonic, k.sz, data, keyData)
        elif k.tid == TID_VAL:
            keyData = self.GetKey(k.keyId)
            if keyData == None:
                xlog("[CodeDevirtualizer] TID_VAL Could not get data from key.")
                return (False, data)

            if dbg:
                xlog("VM[ {:x} ({:x}) ]  {}:{:d}  {:x}".format(k.keyId, keyData,  OpTxt(k.mnemonic), k.sz,   k.parameter))
            _, keyData = ComputeVal(k.mnemonic, k.sz, keyData, k.parameter)

            if not self.SetKey(k.keyId, keyData):
                xlog("[CodeDevirtualizer] Could not set data for key.")
                return (False, data)
        else:
            if k.tid != TID_REG:
                xlog("[CodeDevirtualizer] Accessor key type != REG.")
                return (False, data)
            keyData = self.GetKey(k.keyId)
            if keyData == None:
                xlog("[CodeDevirtualizer] else TID_REG Could not get data from key.")
                return (False, data)

            if dbg:
                xlog("VM[ {:x} ({:x}) ]  {}:{:d}  {:x}".format(k.keyId, keyData, OpTxt(k.mnemonic), k.sz, data))
            _, keyData = ComputeVal(k.mnemonic, k.sz, keyData, data)
            if not self.SetKey(k.keyId, keyData):
                xlog("[CodeDevirtualizer] Could not set data for key.")
                return (False, data)
        return (True, data)


    def PerformKeySeq(self, h, bix, eix, data, dbg = False):
        c = self.FindFirstKeyAfter(h, bix)
        e = self.FindLastKeyBefore(h, eix)
        if c == -1 or e == -1:
            return (False, data)

        while c <= e:
            if dbg:
                xlog("Perform {:d}".format(h.keys[c].idx))
            (res, data) = self.PerformHndlKey(h, c, data, dbg)
            if res == False:
                return (False, data)
            c += 1
        return (True, data)

    def StepOpcodeRegions(self, h, reader, dbg = False):
        keyData = 0
        if len(h.regions) == 0:
            _, keyData = self.PerformKeySeq(h, 0, h.flowDataIndex, keyData)
        else:
            if len(h.keys) > 0 and h.keys[0].idx < h.regions[0].indexStart:
                if dbg:
                    xlog("PRESTEP Region:  {:d}-{:d}".format( 0, h.regions[0].indexStart - 1))
                _, keyData = self.PerformKeySeq(h, 0, h.regions[0].indexStart - 1, keyData, dbg)

            for i in range(len(h.regions)):
                r = h.regions[i]
                if r.tp == 0:
                    keyData = 0

                    if r.opcodeSize == 1:
                        keyData = reader.Read1(r.opcodeOffset)
                    elif r.opcodeSize == 2:
                        keyData = reader.Read2(r.opcodeOffset)
                    elif r.opcodeSize == 3:
                        keyData = reader.Read4(r.opcodeOffset)
                elif r.tp == 1:
                    reg1 = reader.Read2(r.opcodeOffset)
                    reg2 = reader.Read2(r.indexEnd)
                    rv1 = self.GetVMReg(reg1)
                    rv2 = self.GetVMReg(reg2)
                    if self.traceLog:
                        xlog("VMXCHG: VM[{:x}] ({:x}) <=> VM[{:x}] ({:x})".format(reg1, rv1, reg2, rv2))
                    self.vmReg[reg1] = rv2
                    self.vmReg[reg2] = rv1

                indexEnd = 0
                if (i + 1) < len(h.regions):
                    indexEnd = h.regions[i + 1].indexStart
                else:
                    indexEnd = h.flowReadIndex

                if dbg:
                    xlog("Step Region: {:x}  {:x}    {:d}({:d})-{:d}".format(r.opcodeOffset, keyData, r.indexStart, r.indexEnd, indexEnd - 1))

                _, keyData = self.PerformKeySeq(h, r.indexStart, indexEnd - 1, keyData, dbg)
        return True


    def StepStoreStack(self, h, reader):
        regid = reader.Read2(h.opcodeOffsets[0])
        self.vmReg[regid] = 4 #ESP

        self.step_params[0] = "STORE STACK"
        self.step_params[1] = regid

        rk = rkInstruction()
        rk.addr = h.hndlID
        rk.ID = WOP_SSTACK

        rk.operand[0].ID = ID_REG
        rk.operand[0].value = (self.ConvReg(regid) << 4) | 3

        #if self.vmEspReg == -1:
        self.vmEspReg = regid
        self.realRegs.add(regid)

        self.traced.Add(rk, self.trAddr)
        return  self.StepFlow(h, reader.Read2(h.flowReadOffset), True)

    def StepLoadStack(self, h, reader):
        regid = reader.Read2(h.opcodeOffsets[0])

        self.step_params[0] = "LOAD STACK"
        self.step_params[1] = regid

        rk = rkInstruction()
        rk.addr = h.hndlID
        rk.ID = WOP_LSTACK

        self.traced.Add(rk, self.trAddr)
        return  self.StepFlow(h, reader.Read2(h.flowReadOffset), False)

    def StepReset(self, h, reader):
        self.ResetKeyData()

        self.step_params[0] = "RESET"

        #self.trStkReg = 7
        #self.realRegs.clear()
        #self.vmEspReg = -1

        rk = rkInstruction()
        rk.addr = h.hndlID
        rk.ID = WOP_RESET

        self.traced.Add(rk, self.trAddr)
        return self.StepFlow(h, reader.Read2(h.flowReadOffset), True)

    def StepPushF(self, h, reader):
        self.StepOpcodeRegions(h, reader)

        self.step_params[0] = "PUSHFD"

        rk = rkInstruction()
        rk.addr = h.hndlID
        rk.ID = OP_PUSHF

        self.traced.Add(rk, self.trAddr)
        return self.StepFlow(h, reader.Read2(h.flowReadOffset), False)

    def StepPopF(self, h, reader):
        self.StepOpcodeRegions(h, reader)

        self.step_params[0] = "POPFD"

        rk = rkInstruction()
        rk.addr = h.hndlID
        rk.ID = OP_POPF

        self.traced.Add(rk, self.trAddr)
        return self.StepFlow(h, reader.Read2(h.flowReadOffset), False)

    def StepRestoreStack(self, h, reader):
        val = reader.Read1(h.opcodeOffsets[0])

        self.step_params[0] = "RESTORE STACK"
        self.step_params[1] = val

        rk = rkInstruction()
        rk.addr = h.hndlID
        rk.ID = WOP_RSTACK
        rk.operand[0].ID = ID_VAL32
        rk.operand[0].value = val

        self.traced.Add(rk, self.trAddr)
        return self.StepFlow(h, reader.Read2(h.flowReadOffset), False)

    def StepStos(self, h, reader):
        self.StepOpcodeRegions(h, reader)

        self.step_params[0] = "STOS"

        rk = rkInstruction()
        rk.addr = h.hndlID
        rk.ID = OP_STOS
        #rk.operand[0].ID =

        xlog("STOS")
        exit(1)
        self.traced.Add(rk, self.trAddr)
        return self.StepFlow(h, reader.Read2(h.flowReadOffset), False)

    def StepCrypt(self, h, reader):
        regid = reader.Read2(h.opcodeOffsets[0])
        val = h.opcodeOffsets[1]

        self.step_params[0] = "CRYPT"
        self.step_params[1] = regid
        self.step_params[2] = val

        bts = GetBytes(self.VmContext + val, 4)
        val = GetDWORD(bts)

        self.step_params[3] = val

        rk = rkInstruction()
        rk.addr = h.hndlID
        rk.ID = WOP_CRYPT
        rk.operand[0].ID = ID_REG
        rk.operand[0].SetB(0, (self.GetVMReg(regid) << 4) | 3)
        rk.operand[1].ID = ID_VAL32
        rk.operand[1].value = val

        self.traced.Add(rk, self.trAddr)
        return self.StepFlow(h, reader.Read2(h.flowReadOffset), False)

    def StepJccIns(self, h, reader):
        jccid = reader.Read1(h.opcodeOffsets[0])
        hid = reader.Read2(h.opcodeOffsets[1])
        distance = reader.Read4(h.opcodeOffsets[2])

        if distance & 0x80000000:
            distance = -(distance & 0x7FFFFFFF)

        self.step_params[0] = "JCC_INS"
        self.step_params[1] = jccid
        self.step_params[2] = hid
        self.step_params[3] = distance

        rk = rkInstruction()
        rk.addr = h.hndlID
        rk.ID = self.GetJccMnem(jccid)
        rk.operand[0].ID = ID_VAL32
        rk.operand[0].value = distance

        l = LABELS.GetLabel( UINT(self.trAddr + distance), hid )
        l.specialData = (self.vmReg.copy(), self.realRegs.copy(), self.vmEspReg)

        self.traced.Add(rk, self.trAddr)
        return self.StepFlow(h, reader.Read2(h.flowReadOffset), False)

    def StepJccOut(self, h, reader):
        jccid = reader.Read1(h.opcodeOffsets[0])
        offset = reader.Read4(h.opcodeOffsets[1])

        self.step_params[0] = "JCC_OUT"
        self.step_params[1] = jccid
        self.step_params[2] = offset

        rk = rkInstruction()
        rk.addr = h.hndlID
        rk.ID = self.GetJccMnem(jccid)
        rk.operand[0].ID = ID_VAL32
        rk.operand[0].value = UINT(offset + self.imageBase)

        #LABELS.GetLabel( UINT(self.trAddr + distance), hid )

        self.traced.Add(rk, self.trAddr)
        return self.StepFlow(h, reader.Read2(h.flowReadOffset), False)

    def StepJmpIns(self, h, reader):
        hid = reader.Read2(h.opcodeOffsets[0])
        distance = reader.Read4(h.opcodeOffsets[1])

        if distance & 0x80000000:
            distance = -(distance & 0x7FFFFFFF)

        self.step_params[0] = "JMP_INS"
        self.step_params[1] = hid
        self.step_params[2] = distance

        rk = rkInstruction()
        rk.addr = h.hndlID
        rk.ID = OP_JMP
        rk.operand[0].ID = ID_VAL32
        rk.operand[0].value = distance

        l = LABELS.GetLabel( UINT(self.trAddr + distance), hid )
        l.specialData = (self.vmReg.copy(), self.realRegs.copy(), self.vmEspReg)

        self.traced.Add(rk, self.trAddr)
        return True

    def StepUndef(self, h, reader):
        tp = reader.Read1(h.opcodeOffsets[0])
        retaddr = reader.Read4(h.opcodeOffsets[1])

        self.step_params[0] = "UNDEF"
        self.step_params[1] = tp
        self.step_params[2] = retaddr

        retaddr = UINT(self.imageBase + retaddr)

        rk = rkInstruction()
        rk.addr = h.hndlID
        rk.ID = WOP_UNDEF
        rk.operand[0].ID = ID_VAL32
        rk.operand[0].value = retaddr

        mm = self.GetMM(retaddr)
        _,urk = XrkDecode(mm)

        cont, p1, p2 = self.CheckEnterVM(retaddr + urk.size)
        if cont:
            l = LABELS.GetLabel(UINT(self.imageBase + p1), p2)
            rk.operand[1].ID = ID_VAL32
            rk.operand[1].value = l.addr

        self.traced.Add(rk, self.trAddr)
        return True

    def StepHandler(self, h, reader):
        if h.tp == WH_STORE_STK:
            return self.StepStoreStack(h, reader)
        elif h.tp == WH_RESTORE_STK:
            return self.StepRestoreStack(h, reader)
        elif h.tp == WH_LOAD_STK:
            return self.StepLoadStack(h, reader)
        elif h.tp == WH_RESET:
            return self.StepReset(h, reader)
        elif h.tp == WH_PUSHFD:
            return self.StepPushF(h, reader)
        elif h.tp == WH_POPFD:
            return self.StepPopF(h, reader)
        elif h.tp == WH_CRYPT:
            return self.StepCrypt(h, reader)
        elif h.tp in (WH_STOSB, WH_STOSW, WH_STOSD):
            return self.StepStos(h, reader)
        elif h.tp == WH_JCC_INS:
            return self.StepJccIns(h, reader)
        elif h.tp == WH_JMP_INS:
            return self.StepJmpIns(h, reader)
        elif h.tp == WH_JCC_OUT:
            return self.StepJccOut(h, reader)
        elif h.tp == WH_UNDEF:
            return self.StepUndef(h, reader)

        return self.StepAdvanced(h, reader)

    def ProcessVirtualPointer(self, l):
        self.trHid = l.pushVal
        self.trAddr = l.addr
        if l.specialData != None:
            self.vmEspReg = l.specialData[2]
            self.vmReg = l.specialData[0].copy()
            self.realRegs = l.specialData[1].copy()
        else:
            self.trStkReg = 7
        while True:
            if self.trAddr in LABELS.proceed:
                xlog("{:08x} hndl {:04x} already proceeded. break.".format(self.trAddr, self.trHid))
                break

            LABELS.proceed[self.trAddr] = self.trHid

            #xlog("{:08x} hndl {:04x}".format(self.trAddr, self.trHid))

            if self.trHid not in self.hndl and not self.DeofusHndl(self.trHid):
                xlog("Error deoufus hndl {:04x}".format(self.trHid))
                return False

            rdr = READER(self, self.trAddr)

            self.step_params[0] = None

            h = self.hndl[self.trHid]
            xlog("{:08x} hndl {:04x} ( {:x}  {:x}  size {:x})".format(self.trAddr, self.trHid, h.tp, h.dumpAddr, h.opcodeSize))

            kks = ""
            for kk in self.Keys:
                kks += "{:x}:{:x}  ".format(kk.Offset, kk.Data)
            xlog(kks)

            kks = ""
            for rrg in self.realRegs:
                kks += "{:x}:{:x} ".format(rrg, self.GetVMReg(rrg))
            xlog(kks)

            if not self.StepHandler(h, rdr):
                xlog("Not stepped")
                return False

            if self.step_params[0] != None:
                xlog(self.step_params[0])
                xlog("")

            if self.IsFlowHandler(h):
                break

        return True

    def Trace(self):
        LABELS.Init()
        LABELS.GetLabel(self.push1_2, self.push2)

        self.traced = Defus()
        self.traced.Clear()
        self.step_params = dict()
        self.trStkReg = 7
        succ = True

        while True:
            l = LABELS.GetNextToProceed()
            if not l:
                break

            l.proceed = 1

            xlog("\nLABEL at {:08x} {:04x}\n".format(l.addr, l.pushVal))

            if not self.ProcessVirtualPointer(l):
                succ = False
                break

        self.traced.SortByAddr()
        self.Simplify(self.traced)

        for l in self.GetWildListing(self.traced, True, True, True):
            xlog(l)

        return succ
        #for l in self.traced.GetListing(1, 1, True, True):
        #    xlog("{}".format(l))

    def GetWildListing(self, oplist, index = False, addr = False, labels = False):
        lableList = list()
        for l in LABELS.arr:
            if l.used:
                lableList.append(l.addr)
        lableList.sort(reverse=True)

        lst = list()
        for i in range(oplist.count):
            if len(lableList) and labels:
                while len(lableList) and lableList[-1] <= oplist.heap[i].addr:
                    lb = lableList.pop()
                    lst.append("LABEL_{:x}:".format(lb))
            op = oplist.heap[i].instr
            t = ""
            if index:
                t += "{:d}\t ".format(i)
            if addr:
                t += "{:08x}\t ".format(oplist.heap[i].addr)
            t += self.TxtWop(op)

            if (op.ID >= OP_JA and op.ID <= OP_JS) or op.ID == OP_JMP and \
                op.operand[0].TID() == TID_VAL:
                aaadr = op.operand[0].value
                if op.operand[0].value <= 0xFFFFFF:
                    aaadr = UINT(oplist.heap[i].addr + op.operand[0].value)
                if self.InBlock(aaadr):
                    t += " \t ( {:08x} )".format(aaadr)

            lst.append(t)
        return lst

    def GetVMReg(self, rid):
        if rid in self.vmReg:
            return self.vmReg[rid]
        return 0xFFFFFFFF

    def GetJccMnem(self, id):
        if id in self.jccMnemonicTypes:
            return self.jccMnemonicTypes[id]
        return OP_NONE

    def CheckEnterVM(self, addr):
        m = self.GetMM(addr)
        if m == None:
            return (False, 0, 0)

        i, rk1 = XrkDecode(m)
        if rk1.ID != OP_PUSH:
            return (False, 0, 0)
        m = m[i:]
        i, rk2 = XrkDecode(m)
        if rk2.ID != OP_PUSH:
            return (False, 0, 0)
        m = m[i:]
        i, rk3 = XrkDecode(m)
        if rk3.ID != OP_JMP:
            return (False, 0, 0)
        return (True, rk1.operand[0].value, rk2.operand[0].value)

    def TxtOp(self, op):
        txt = OpTxt(op)
        if op.operand[0].ID != 0:
            txt += " " + XrkTextOp(op, 0)

        if op.operand[1].ID != 0:
            txt += " " + XrkTextOp(op, 1)
        return txt

    def GetRegName(self, offset, sz):
        if offset in self.realRegs:
            return RegName(self.GetVMReg(offset), sz)
        if self.vmEspReg != -1 and offset == self.vmEspReg:
            return "VM_ESP"
        return "R{:x}".format(offset)

    def VMRegOper(self, op):
        if op.TID() == TID_REG:
            return (op.value >> 4) & 0xFF
        elif op.TID() == TID_MEM:
            return (op.xbase >> 4) & 0xFF

    def TxtWopOperand(self, opr):
        if opr.TID() == TID_REG:
            if opr.value & 0xFFF0 == 0x1040:
                return "VM_ESP"
            elif opr.value & 0x2000:
                if opr.Size() == 1:
                    return "B,R{:x}".format(self.VMRegOper(opr))
                elif opr.Size() == 2:
                    return "W,R{:x}".format(self.VMRegOper(opr))
                return "R{:x}".format(self.VMRegOper(opr))
            else:
                return RegName(opr.XBase(), opr.Size())
        elif opr.TID() == TID_VAL:
            return "0x{:x}".format(opr.value)
        elif opr.TID() == TID_MEM:
            if opr.val2 == 0 and opr.xbase != 0:
                t = ""
                if opr.Size() == 1:
                    t = "BYTE PTR["
                elif opr.Size() == 2:
                    t = "WORD PTR["
                elif opr.Size() == 3:
                    t = "DWORD PTR["

                if opr.xbase & 0xFFF0 == 0x1040:
                    return t + "VM_ESP]"
                elif opr.xbase & 0x2000:
                    return t + "R{:x}]".format(self.VMRegOper(opr))
                else:
                    return t + RegName(self.VMRegOper(opr), opr.xbase & 0xF) + "]"
            else:

                sz = opr.ID & 0xF
                t = PTRNAME[sz]
                t += "["

                if opr.GetB(1) != 0:
                    sz = opr.GetB(1) & 0xf
                    rid = opr.GetB(1) >> 4
                    if sz == 2:
                        t += REG16NAME[rid]
                    elif sz == 3:
                        t += REG32NAME[rid]
                    else:
                        t += "REG?"

                if opr.GetB(2) != 0:
                    if opr.GetB(1) != 0:
                        t += "+"
                    sz = opr.GetB(2) & 0xf
                    rid = opr.GetB(2) >> 4
                    if sz == 2:
                        t += REG16NAME[rid]
                    elif sz == 3:
                        t += REG32NAME[rid]
                    else:
                        t += "REG?"
                if opr.GetB(3) != 0:
                    if opr.GetB(2) == 0:
                        t += "ERROR"
                    else:
                        t += MULNAME[opr.GetB(3)]

                if opr.val2 != 0 or (opr.GetB(1) == 0 and opr.GetB(2) == 0):
                    if opr.GetB(1) != 0 or opr.GetB(2) != 0:
                        t += "+"
                    t += "0x{:x}".format(opr.val2)
                t += "]"
                return t
        return "UNK"

    def TxtWildOperator(self, op):
        if op.ID in WILD_OPTXT:
            return WILD_OPTXT[op.ID]
        return ""

    def TxtWop(self, op):
        t = ""
        if op.ID >= 0x1000:
            t = self.TxtWildOperator(op)
        else:
            t = OpTxt(op)
        if op.operand[0].ID != 0:
            t += " " + self.TxtWopOperand(op.operand[0])

        if op.operand[1].ID != 0:
            t += ", " + self.TxtWopOperand(op.operand[1])
        return t

    def ConvReg(self, offset):
        if offset in self.realRegs:
            return self.GetVMReg(offset)
        if self.vmEspReg != -1 and offset == self.vmEspReg:
            return 0x104
        return 0x200 | offset

    def Simplify(self, trace):
        pass
