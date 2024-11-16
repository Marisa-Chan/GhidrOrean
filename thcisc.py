from xrkutil import *
from xrkdsm import *
from thobfus import *
from xrkasm import *
from thvm import *
from __main__ import *
import ConfigParser


class CHNDL:
    ID = 0
    hid = -2
    sz = 0
    ids = None
    vals = None
    a = 0
    HasData = 0

    def __init__(self):
        self.ids = [0] * 4
        self.vals = [0] * 2


class VOPT:
    ID = 0
    addr = 0
    pushval = 0
    valign = 0
    fld2 = 0

class CJUNK:
    good = None
    handler = None
    def __init__(self):
        self.good = []
        self.handler = []

class CASMARG:
    src = 0
    notHave = 0
    reg = 0
    v0 = 0
    v1 = 0
    v2 = 0
    v3 = 0
    cons = 0

class CASM:
    handlers = None
    args = None
    mr1 = 0
    mr2 = 0
    scale = 0
    mo = 0
    mnem = ""
    def __init__(self):
        self.handlers = []
        self.args = []

class CSYNTX:
    insx = 0
    sufx = 0
    handler = None
    def __init__(self):
        self.handler = []



class CISC(VM):

    C2D0 = (0x57, 0x58, 0x59, 0x5b, 0x5c, 0x5d, 0x5f,\
            0x60, 0x61, 0x63, 0x64, 0x65, 0x67, 0x68, 0x69, 0x6b, 0x6c, 0x6d, 0x6f,\
            0x70, 0x71, 0x73, 0x74, 0x75)

    ARYTHM = (OP_ADD, OP_SUB, OP_SBB, OP_CMP, OP_ADC, OP_AND, OP_OR, OP_XOR)

    heap = None
    heapSize = 0
    beginAddr = 0
    pushValue = 0
    MainHandlerAddr = 0
    fld50 = 0
    fld54 = 0
    Step1Addr = 0
    ImageBase = 0
    Align = 0
    IatAddr = 0
    IatDis = 0
    IatCount = 0
    vmEntry = None
    CiscHndl = None
    CiscHndlMap = None
    CiscHndlRevMap = None
    fld6x = [0] * 11
    fld70 = 0
    fld74 = 0
    fld78 = 0
    fld7c = 0
    WrkDir = ""

    maxVops = 0
    countVops = 0
    Vops = None

    vpaddr = -1

    dbg = True

    JUNK = None
    ASM = None
    SYNT = None
    INS = None
    SUF = None

    TRNM = None
    TRID = None

    def __init__(self, d):
        VM.__init__(self, 1, d)
        self.vmEntry = dict()
        self.CiscHndl = list()
        self.CiscHndlMap = dict()
        self.CiscHndlRevMap = dict()

        self.LoadJunk()
        self.LoadSyntax()
        self.LoadAsm()
        self.LoadInstructions()

    def LoadInstructions(self):
        self.INS = dict()
        self.SUF = dict()

        f = None
        try:
            f = open("{}/CISC/CiscInstruction.cfg".format(self.WrkDir), "r")
        except:
            print("Can't load CISC/CiscInstruction.cfg")
            return

        cfg = ConfigParser.ConfigParser(allow_no_value=True)
        cfg.readfp(f)

        for i in range(0x1000):
            try:
                v = cfg.get("CODE_INSTRUCTION", "INS_{:02X}".format(i))
                self.INS[i] = v
            except:
                pass

            try:
                v = cfg.get("CODE_SUFFIX", "SUF_{:02X}".format(i))
                self.SUF[i] = v
            except:
                pass

        f.close()
        print("Loaded {:d} ins and {:d} suf".format(len(self.INS), len(self.SUF)))

    def LoadAsm(self):
        self.ASM = []

        f = None
        try:
            f = open("{}/CISC/OreansAssembler.cfg".format(self.WrkDir), "r")
        except:
            print("Can't load CISC/OreansAssembler.cfg")
            return

        while True:
            l = f.readline()
            if l == "":
                break

            l = l.strip()
            if l[:2] == "//" or len(l) < 3:
                continue

            a = SPLIT(l, "\t \n/")
            num = int(a[0], 16)

            asm = CASM()
            asm.handlers = [0] * num

            for i in range(num):
                asm.handlers[i] = int(a[1 + i], 16)

            l = f.readline().strip()
            a = SPLIT(l, "\t \n/")

            num = int(a[0], 16)
            asm.args = [None] * num

            for i in range(num):
                arg = CASMARG()
                asm.args[i] = arg

                l = f.readline().strip()
                a = SPLIT(l, "\t \n/")

                arg.src = int(a[0], 16)
                if arg.src & 0x80:
                    arg.src &= 0x7F
                    arg.notHave = 1
                elif (arg.src & 0xF0) == 0x10:
                    arg.reg = int(a[1], 16)
                elif (arg.src & 0xF0) == 0x20:
                    arg.cons = int(a[1], 16)
                elif (arg.src & 0xF0) == 0x30:
                    arg.v0 = int(a[1], 16)
                    arg.v1 = int(a[2], 16)
                    arg.v2 = int(a[3], 16)
                    arg.v3 = int(a[4], 16)

            l = f.readline().strip()

            if l[0] == "1":
                asm.mr1 = 1
            if l[1] == "1":
                asm.mr2 = 1
            if l[2] == "1":
                asm.scale = 1
            if l[3] == "1":
                asm.mo = 1

            if len(l) > 4:
                asm.mnem = l[4:]

            self.ASM.append(asm)

        f.close()
        print("Loaded {:d} assembly".format(len(self.ASM)))

    def LoadSyntax(self):
        self.SYNT = []

        f = None
        try:
            f = open("{}/CISC/OreansSyntax.cfg".format(self.WrkDir), "r")
        except:
            print("Can't load CISC/OreansSyntax.cfg")
            return

        while True:
            l = f.readline()
            if l == "":
                break

            l = l.strip()
            if l[:2] == "//" or len(l) < 3:
                continue

            a = SPLIT(l, "\t \n/")
            sx = CSYNTX()
            sx.insx = int(a[0], 16)
            sx.sufx = int(a[1], 16)

            l = f.readline().strip()
            a = SPLIT(l, "\t \n/")

            num = int(a[0], 16)
            sx.handler = [0] * num
            for i in range(num):
                sx.handler[i] = int(a[1 + i], 16)

            self.SYNT.append(sx)

        f.close()
        print("Loaded {:d} syntax".format(len(self.SYNT)))

    def LoadJunk(self):
        self.JUNK = []

        f = None
        try:
            f = open("{}/CISC/OreansJunk.cfg".format(self.WrkDir), "r")
        except:
            print("Can't load CISC/OreansJunk.cfg")
            return

        while True:
            l = f.readline()
            if l == "":
                break

            l = l.strip()
            if l[:2] == "//" or len(l) < 3:
                continue

            a = SPLIT(l, "\t \n/")
            num = int(a[0], 16) & 0xFF

            jk = CJUNK()
            self.JUNK.append(jk)
            jk.handler = [0] * num
            for i in range(num):
                jk.handler[i] = int(a[1 + i], 16)


            l = f.readline().strip()
            a = SPLIT(l, "\t \n/")
            num = int(a[0], 16) & 0xFF

            if num == 0xFF:
                continue

            jk.good = [0] * num
            for i in range(num):
                jk.good[i] = int(a[1 + i], 16)



        print("Loaded {:d} junks".format(len(self.JUNK)))

    def LoadIat(self, addr):
        f = None
        try:
            f = open("{}/TXT/Cisc_Iat_{:08x}.txt".format(self.WrkDir, addr),"r")
        except:
            return False

        readiat = True
        for l in f:
            if l[:2] == "//":
                continue
            elif len(l) > 9:
                a = SPLIT(l.strip(), "\t \n/")

                if readiat:
                    print("Load IAT", a)
                    self.CiscHndl = list()
                    self.CiscHndlMap = dict()
                    self.CiscHndlRevMap = dict()
                    self.ImageBase = int(a[0], 16)
                    self.Align = int(a[1], 16)
                    self.IatAddr = int(a[2], 16)
                    self.IatDis = int(a[3], 16)
                    self.IatCount = int(a[4], 16)
                    self.fld50 = int(a[5], 16)
                    readiat = False
                else:
                    h = CHNDL()
                    h.ID = int(a[0], 16)
                    h.hid = int(a[1], 16)
                    h.ids[0] = int(a[2], 10)
                    h.ids[1] = int(a[3], 10)
                    h.ids[2] = int(a[4], 10)
                    h.ids[3] = int(a[5], 10)
                    h.vals[0] = int(a[6], 16)
                    h.vals[1] = int(a[7], 16)
                    h.sz = int(a[8], 10)
                    h.HasData = int(a[9], 10)
                    h.a = 1
                    self.CiscHndl.append(h)
                    self.CiscHndlMap[h.hid] = h
                    self.CiscHndlRevMap[h.ID] = h
        f.close()
        return True

    def Step0(self, addr):
        mblock = GetMemBlockInfo(addr)
        if not mblock:
            print("Can't get mem block at {:08X}".format(addr))
            return False

        print("Getting section {:08X} - {:08X}".format(mblock.addr, mblock.addr + mblock.size))

        self.mblk.data = GetBytes(mblock.addr, mblock.size)
        self.mblk.addr = mblock.addr
        self.mblk.size = mblock.size
        return True

    def Step1(self, addr):

        self.pushValue = 0

        i = 0

        ftime = False
        getPush = False
        while True:
            if not self.InBlock(addr + i):
                if ftime:
                    print("FTIME")
                    return False

                bs = GetBytes(addr, 5)
                if UB(bs[0]) != 0xe9:
                    print("Not contain 0xe9: ", bs)
                    return False

                vl = GetSInt(bs[1:6])

                if not self.InBlock(UINT(addr + i + 5 + vl)):
                    print("Not in block: {:08X}".format(UINT(addr + i + 5 + vl)))
                    return False

                ftime = True
                i = UINT(i + 5 + vl)

            m = self.GetMM(addr + i)
            j, rk = XrkDecode(m)
            i += j

            if rk.ID == OP_PUSH and rk.operand[0].ID == 0x23:
                getPush = True
                self.pushValue = rk.operand[0].value
                print("Get PUSH {:X}".format(self.pushValue))
            elif getPush and rk.ID == OP_JMP:
                vmaddr = self.GetHdr(UINT(addr + i + rk.operand[0].value))
                self.Step1Addr = addr
                return vmaddr
            else:
                print("OP {}".format(rk.opInfo.MNEM))
                return False

    def GetHdr(self, addr):
        self.MainHandlerAddr = 0
        self.fld50 = 0
        self.fld54 = 0

        CMDSimpler.Clear()

        i = 0
        while True:
            if i + addr - self.mblk.addr >= self.mblk.size:
                return 0

            m = self.GetMM(i + addr)
            j, rki = XrkDecode(m)

            iAddr = UINT(i + addr)

            if not CMDSimpler.Add(rki, i + addr):
                break

            i += j

            if rki.opfx != 0:
                k = 0
                while k <= 3:
                    m = self.GetMM(i + addr)
                    j, rki = XrkDecode(m)
                    iAddr = UINT(i + addr)
                    i += j
                    if rki.ID == OP_LODS and rki.operand[0].ID == 0x31:
                        break
                    k += 1

                if k > 3:
                    return 0

                CMDSimpler.Simple(self, 0xfffd, 'A')
                CMDSimpler.RebuildInfo()
                txt = CMDSimpler.GetListing(True, True)

                print("\nCISC HEADER:")
                for t in txt:
                    print(t)

                print("\n")

                self.MainHandlerAddr = iAddr
                return iAddr
        return 0

    def Step2(self, addr):
        self.pushValue = 0

        scndTime = False
        fnd = False
        i = 0
        while True:
            if not self.InBlock(addr + i):
                if scndTime:
                    return 0

                bt = GetBytes(addr, 5)
                if bt[0] != 0xe9:
                    return 0

                if not self.InBlock(UINT(addr + 5 + i + GetSInt(bt[1:]))):
                    return 0

                scndTime = True
                i = i + 5 + GetSInt(bt[1:])

            mm = self.GetMM(addr + i)
            sz, rk = XrkDecode(mm)
            i += sz

            if rk.ID == OP_PUSH and rk.operand[0].ID == 0x23:
                fnd = True
                self.pushValue = rk.operand[0].value
            else:
                if fnd and rk.ID == OP_JMP:
                    return addr + i + rk.operand[0].value
                else:
                    return 0

    def Step3(self, imgBase, align, iA, iD, iC):
        self.ImageBase = imgBase
        self.Align = align
        self.IatAddr = iA
        self.IatDis = iD
        self.IatCount = iC

        if imgBase == 0:
            adr = 0
            fnd = False
            for i in range(CMDSimpler.count):
                op = CMDSimpler.heap[i].instr
                if op.ID == OP_CALL and op.operand[0].value == 0:
                    adr = CMDSimpler.heap[i].addr
                    fnd = True
                else:
                    if fnd and IsOpClass(op.ID, 0, 0, 1) and \
                            op.operand[0].ID == 0x10 and op.operand[1].ID == 0x23 and \
                            op.operand[0].GetB(0) == 0x73:
                        _, adr = ComputeVal(op.ID, op.operand[0].GetB(0) & 0xF, adr, op.operand[1].value)
                    if op.ID == OP_CMP:
                        break
            self.ImageBase = adr

        if align == 0:
            fnd = False
            val = 0
            for i in range(CMDSimpler.count):
                op = CMDSimpler.heap[i].instr
                if op.ID == OP_CALL and op.operand[0].value == 0:
                    val = CMDSimpler.heap[i].addr
                    fnd = True
                else:
                    if fnd and IsOpClass(op.ID, 0, 0, 1) and \
                            op.operand[0].ID == 0x10 and op.operand[1].ID == 0x23 and \
                            op.operand[0].GetB(0) == 0x73:
                        _, val = ComputeVal(op.ID, op.operand[0].GetB(0) & 0xF, val, op.operand[1].value)
                    if (op.ID == OP_MOV and op.operand[0].ID == 0x10 and \
                        op.operand[1].ID == 0x10 and op.operand[0].GetB(0) == 3 and \
                        op.operand[1].GetB(0) == 0x73) or op.ID == OP_CMP:
                        break
            self.Align = val

        if iD == 0:
            i = 0
            steps = 0
            while True:
                if i >= CMDSimpler.count or steps > 0xfff:
                    break

                op = CMDSimpler.heap[i].instr
                opa = CMDSimpler.heap[i].addr

                #print("{:08x}   {}    {:x} {:x}     {:x} {:x}".format(opa, XrkText(op),  op.operand[0].ID, op.operand[0].value, op.operand[1].ID, op.operand[1].value))
                if op.ID == OP_JMP and op.operand[0].TID() == 2:
                    t = 5
                    if op.operand[0].ID & 0xF != 3:
                        t = 2
                    cmd = CMDSimpler.GetFirstAfterAddr(UINT(opa + t + op.operand[0].value))
                    if cmd:
                        i = CMDSimpler.AddrToIndex(cmd.addr)
                elif op.ID == OP_JNZ and op.operand[0].TID() == 2:
                    t = 6
                    if op.operand[0].ID & 0xF != 3:
                        t = 2
                    cmd = CMDSimpler.GetFirstAfterAddr(UINT(opa + t + op.operand[0].value))
                    if cmd:
                        i = CMDSimpler.AddrToIndex(cmd.addr)
                elif op.ID == OP_ADD and op.operand[0].ID == 0x33 and \
                        op.operand[1].ID == 0x10 and \
                        op.operand[0].GetB(1) == 0x73 and \
                        op.operand[0].GetB(2) == 0x13 and \
                        op.operand[0].GetB(3) == 2 and \
                        op.operand[0].val2 != 0 and op.operand[1].GetB(0) == 3:
                    self.IatDis = UINT(op.operand[0].val2 + 4)
                    break
                else:
                    i += 1
                steps += 1

        if iA == 0:
            self.IatAddr = self.ImageBase + self.IatDis

        if iC == 0:
            for i in range(CMDSimpler.count):
                op = CMDSimpler.heap[i].instr
                if op.ID == OP_MOV and \
                        op.operand[0].ID == 0x10 and op.operand[1].ID == 0x23 and \
                        op.operand[0].GetB(0) == 0x13:
                    self.IatCount = op.operand[1].value
                    break

        for i in range(CMDSimpler.count):
            op = CMDSimpler.heap[i].instr
            if op.ID == OP_CMP:
                if op.operand[0].ID == 0x10 and op.operand[1].ID == 0x33:
                    self.fld54 = op.operand[1].val2
                break
            if op.opfx != 0:
                break

        print("")
        print(
            "CISC IMGBase {:08x} Align {:x} IatAddr {:08x} IatDis {:x} IatCount {:x}".format(self.ImageBase, self.Align,
                                                                                             self.IatAddr, self.IatDis,
                                                                                             self.IatCount))
        print("")

    def FUN_1005da10(self, opid, inz, mode):
        CMDSimpler.unk = 1
        opz = CMDSimpler.heap[CMDSimpler.count - 1].instr
        uvr4 = 0
        if opz.ID == OP_MOV:
            return (0, inz)
        elif opz.ID == OP_CMP:
            return (1, inz)
        elif opz.ID == OP_TEST:
            return (0x101, inz)
        elif opz.ID == OP_OR and opz.operand[0].TID() == 1 and opz.operand[1].TID() == 1 and \
                opz.operand[0].GetB(0) == opz.operand[1].GetB(0):
            return (1, inz)
        else:
            (a, b, val) = CMDSimpler.FUN_1005d720()
            if a == 0:
                CMDSimpler.Simple(self, 0xfffe, mode)
                (a, b, val) = CMDSimpler.FUN_1005d720()
                if a == 0:
                    return (0, inz)
            l = b
            FLG = EFlags()
            while l < CMDSimpler.count - 1:
                op = CMDSimpler.heap[l].instr
                if opz.operand[0].TID() == 1:
                    CalcEFlags(op.ID, op.operand[0].GetB(0) & 0xF, val, op.operand[1].value, FLG)
                    _, val = ComputeVal(op.ID, op.operand[0].GetB(0) & 0xF, val, op.operand[1].value)
                else:
                    CalcEFlags(op.ID, op.operand[0].ID & 0xF, val, op.operand[1].value, FLG)
                    _, val = ComputeVal(op.ID, op.operand[0].ID & 0xF, val, op.operand[1].value)

                inz = FUN_1005ddf0(opid, FLG)
                l += 1
        CMDSimpler.unk = 0
        return (1, inz)

    def StoreVmHandle(self, p):
        lst = [CmdEntry()] * 10
        self.vmEntry[p] = lst
        for i in range(10):
            if CMDSimpler.heap[i].instr.ID == 0:
                break
            lst[i] = CMDSimpler.heap[i].Copy()

    def CISCER1(self, hid):
        vme = self.vmEntry[hid]
        op0 = vme[0].instr
        op1 = vme[1].instr
        op2 = vme[2].instr
        op3 = vme[3].instr
        op4 = vme[4].instr
        op5 = vme[5].instr
        op6 = vme[6].instr
        op7 = vme[7].instr
        op8 = vme[8].instr
        op9 = vme[9].instr

        hndl = CHNDL()

        if op0.ID == OP_LODS:
            hndl.hid = hid
            hndl.sz = op0.operand[0].ID & 0xf
            hndl.HasData = 1

            if op1.operand[0].ID == 0x10 and op1.operand[1].ID == 0x10 and \
                    op2.operand[0].ID == 0x10 and op2.operand[1].TID() == 2 and \
                    op3.operand[0].ID == 0x10 and op3.operand[1].TID() == 2 and \
                    op4.operand[0].ID == 0x10 and op4.operand[1].ID == 0x10 and \
                    op1.ID in (OP_ADD, OP_SUB, OP_XOR) and \
                    op2.ID in (OP_ADD, OP_SUB, OP_XOR) and \
                    op3.ID in (OP_ADD, OP_SUB, OP_XOR) and \
                    op4.ID in (OP_ADD, OP_SUB, OP_XOR) and \
                    op1.operand[0].GetB(0) == op2.operand[0].GetB(0) and \
                    op2.operand[0].GetB(0) == op3.operand[0].GetB(0) and \
                    op3.operand[0].GetB(0) == op4.operand[1].GetB(0) and \
                    op1.operand[1].GetB(0) == op4.operand[0].GetB(0) and \
                    (op1.operand[0].GetB(0) >> 4) == 0 and \
                    (op1.operand[1].GetB(0) >> 4) == 3:
                hndl.a = 1
                hndl.ids[0] = op1.ID
                hndl.ids[1] = op2.ID
                hndl.ids[2] = op3.ID
                hndl.ids[3] = op4.ID
                hndl.vals[0] = op2.operand[1].value
                hndl.vals[1] = op3.operand[1].value

            if hid == 0xffff:
                hndl.ID = 0xffff

            elif op6.ID == OP_LEA:
                hndl.ID = 0

            elif op5.ID == OP_MOVZX and op5.operand[0].ID == 0x10 and \
                    op5.operand[1].ID == 0x10 and op5.operand[0].GetB(0) == 3 and op5.operand[1].GetB(0) == 1 and \
                    op6.ID == OP_PUSH and op6.operand[0].ID == 0x10 and op6.operand[0].GetB(0) == 2 and \
                    op7.ID == 0:
                hndl.ID = 2

            elif op5.ID == OP_MOVZX and op5.operand[0].ID == 0x10 and\
                 op5.operand[1].ID == 0x10 and\
                 op5.operand[0].GetB(0) == 3 and op5.operand[1].GetB(0) == 2 and\
                 op6.ID == OP_PUSH and\
                 op6.operand[0].ID == 0x10 and op6.operand[0].GetB(0) == 2 and\
                 op7.ID == 0:
                hndl.ID = 3

            elif op5.ID == OP_PUSH and op5.operand[0].ID == 0x10 and\
                 op5.operand[0].GetB(0) == 3 and op6.ID == 0:
                hndl.ID = 4

            elif op5.ID == OP_MOVZX and op5.operand[0].ID == 0x10 and op5.operand[1].ID == 0x10 and\
                 op5.operand[0].GetB(0) == 3 and op5.operand[1].GetB(0) == 1 and\
                 op6.ID == OP_PUSH and op6.operand[0].ID == 0x33 and op6.operand[0].GetB(1) == 0x73 and\
                 op6.operand[0].GetB(2) == 3 and op6.operand[0].GetB(3) == 2 and op6.operand[0].val2 == 0 and\
                 op7.ID == 0:
                hndl.ID = 7

            elif op5.ID == OP_MOVZX and op5.operand[0].ID == 0x10 and op5.operand[1].ID == 0x10 and\
                 op5.operand[0].GetB(0) == 3 and op5.operand[1].GetB(0) == 1 and\
                 op6.ID == OP_MOV and op6.operand[0].ID == 0x10 and op6.operand[0].GetB(0) == 3 and\
                 op6.operand[1].ID == 0x33 and op6.operand[1].GetB(1) == 0x73 and\
                 op6.operand[1].GetB(2) == 3 and op6.operand[1].GetB(3) == 2 and\
                 op6.operand[1].val2 == 0 and op7.ID == OP_MOVZX and\
                 op7.operand[0].ID == 0x10 and op7.operand[0].GetB(0) == 2 and op7.operand[1].ID == 0x31 and\
                 op7.operand[1].GetB(1) == 3 and op7.operand[1].GetB(2) == 0 and op7.operand[1].GetB(3) == 0 and\
                 op7.operand[1].val2 == 0 and op8.ID == OP_PUSH and op8.operand[0].ID == 0x10 and\
                 op8.operand[0].GetB(0) == 2 and op9.ID == 0:
                hndl.ID = 0xe

            elif op5.ID == OP_MOVZX and op5.operand[0].ID == 0x10 and op5.operand[1].ID == 0x10 and\
                 op5.operand[0].GetB(0) == 3 and op5.operand[1].GetB(0) == 1 and\
                 op6.ID == OP_MOV and op6.operand[0].ID == 0x10 and op6.operand[0].GetB(0) == 3 and\
                 op6.operand[1].ID == 0x33 and op6.operand[1].GetB(1) == 0x73 and\
                 op6.operand[1].GetB(2) == 3 and op6.operand[1].GetB(3) == 2 and\
                 op6.operand[1].val2 == 0 and op7.ID == OP_PUSH and op7.operand[0].ID == 0x32 and\
                 op7.operand[0].GetB(1) == 3 and op7.operand[0].GetB(2) == 0 and\
                 op7.operand[0].GetB(3) == 0 and op7.operand[0].val2 == 0 and op8.ID == 0:
                hndl.ID = 0xf

            elif op5.ID == OP_MOVZX and op5.operand[0].ID == 0x10 and op5.operand[0].GetB(0) == 2 and\
            op5.operand[1].ID == 0x31 and op5.operand[1].GetB(1) == 3 and op5.operand[1].GetB(2) == 0 and\
            op5.operand[1].GetB(3) == 0 and op5.operand[1].val2 == 0 and op6.ID == OP_PUSH and\
            op6.operand[0].ID == 0x10 and op6.operand[0].GetB(0) == 2 and op7.ID == 0:
                hndl.ID = 0x11

            elif op5.ID == OP_PUSH and op5.operand[0].ID == 0x32 and op5.operand[0].GetB(1) == 3 and\
                 op5.operand[0].GetB(2) == 0 and op5.operand[0].GetB(3) == 0 and op5.operand[0].val2 == 0 and\
                 op6.ID == 0:
                hndl.ID = 0x12

            elif op5.ID == OP_PUSH and op5.operand[0].ID == 0x33 and op5.operand[0].GetB(1) == 3 and\
                 op5.operand[0].GetB(2) == 0 and op5.operand[0].GetB(2) == 0 and op5.operand[0].val2 == 0 and\
                 op6.ID == 0:
                hndl.ID = 0x13

            elif op5.ID == OP_MOVZX and op5.operand[0].ID == 0x10 and op5.operand[1].ID == 0x10 and\
                 op5.operand[0].GetB(0) == 3 and op5.operand[1].GetB(0) == 1 and op6.ID == OP_POP and\
                 op6.operand[0].ID == 0x10 and op6.operand[0].GetB(0) == 0x22 and\
                 op7.ID == OP_MOV and op7.operand[0].ID == 0x31 and op7.operand[0].GetB(1) == 0x73 and\
                 op7.operand[0].GetB(2) == 3 and op7.operand[0].GetB(3) == 2 and op7.operand[0].val2 == 0 and\
                 op7.operand[1].ID == 0x10 and op7.operand[1].GetB(0) == 0x21 and op8.ID == 0:
                hndl.ID = 0x1a

            elif op5.ID == OP_MOVZX and op5.operand[0].ID == 0x10 and op5.operand[1].ID == 0x10 and\
                 op5.operand[0].GetB(0) == 3 and op5.operand[1].GetB(0) == 1 and op6.ID == OP_POP and\
                 op6.operand[0].ID == 0x32 and op6.operand[0].GetB(1) == 0x73 and op6.operand[0].GetB(2) == 3 and\
                 op6.operand[0].GetB(3) == 2 and op6.operand[0].val2 == 0 and op7.ID == 0:
                hndl.ID = 0x1b

            elif op5.ID == OP_MOVZX and op5.operand[0].ID == 0x10 and op5.operand[1].ID == 0x10 and\
                 op5.operand[0].GetB(0) == 3 and op5.operand[1].GetB(0) == 1 and op6.ID == OP_POP and\
                 op6.operand[0].ID == 0x33 and op6.operand[0].GetB(1) == 0x73 and\
                 op6.operand[0].GetB(2) == 3 and op6.operand[0].GetB(3) == 2 and\
                 op6.operand[0].val2 == 0 and op7.ID == 0:
                hndl.ID = 0x1c

            elif op5.ID == OP_POP and op5.operand[0].ID == 0x10 and op5.operand[0].GetB(0) == 0x22 and\
                 op6.ID == OP_MOV and op6.operand[0].ID == 0x31 and op6.operand[0].GetB(1) == 3 and\
                 op6.operand[0].GetB(2) == 0 and op6.operand[0].GetB(3) == 0 and op6.operand[0].val2 == 0 and\
                 op6.operand[1].ID == 0x10 and op6.operand[1].GetB(0) == 0x21 and op7.ID == 0:
                hndl.ID = 0x1e

            elif op5.ID == OP_POP and op5.operand[0].ID == 0x32 and op5.operand[0].GetB(1) == 3 and\
                 op5.operand[0].GetB(2) == 0 and op5.operand[0].GetB(3) == 0 and op5.operand[0].val2 == 0 and\
                 op6.ID == 0:
                hndl.ID = 0x1f

            elif op5.ID == OP_POP and op5.operand[0].ID == 0x33 and op5.operand[0].GetB(1) == 3 and\
                 op5.operand[0].GetB(2) == 0 and op5.operand[0].GetB(3) == 0 and op5.operand[0].val2 == 0 and\
                 op6.ID == 0:
                hndl.ID = 0x20

            elif op5.ID == OP_ADD and op5.operand[0].ID == 0x10 and\
                 op5.operand[0].GetB(0) == 0x73 and op5.operand[1].TID() == 2 and op5.operand[1].value == 0x3fc:
                hndl.ID = 0x14b

            elif op5.ID == OP_ADD and op5.operand[0].ID == 0x10 and op5.operand[0].GetB(0) == 0x73 and\
                 op5.operand[1].TID() == 2 and op5.operand[1].value == 0x400:
                hndl.ID = 0x14b

            elif op6.ID == OP_CMP and op6.operand[0].ID == 0x10 and op6.operand[0].GetB(0) == 3 and\
                 op6.operand[1].TID() == 2 and op6.operand[1].value == 7:
                hndl.ID = 0x153

            elif op1.ID == OP_ADD and op1.operand[0].ID == 0x10 and op1.operand[1].ID == 0x10 and\
                 op1.operand[0].GetB(0) == 0x63 and op1.operand[1].GetB(0) == 3:
                hndl.ID = 0x154
                hndl.a = 1
                hndl.ids[0] = OP_ADD
                hndl.ids[1] = OP_ADD
                hndl.ids[2] = OP_ADD
                hndl.ids[3] = OP_ADD
                hndl.vals[0] = 0
                hndl.vals[1] = 0

            elif op5.ID == OP_AND and op5.operand[0].ID == 0x10 and\
                 op5.operand[1].TID() == 2 and op5.operand[0].GetB(0) == 1 and op5.operand[1].value == 0x7f:
                hndl.ID = 0x155

            elif op1.ID == OP_CMP:
                hndl.ID = 0x156
                hndl.a = 1
                hndl.ids[0] = OP_ADD
                hndl.ids[1] = OP_ADD
                hndl.ids[2] = OP_ADD
                hndl.ids[3] = OP_ADD
                hndl.vals[0] = 0
                hndl.vals[1] = 0

            elif op5.ID == OP_MOV and op5.operand[0].ID == 0x31 and\
                 op5.operand[0].GetB(1) == 0x73 and op5.operand[0].GetB(2) == 0 and op5.operand[0].GetB(3) == 0 and\
                 self.fld70 != -1 and self.fld70 != op5.operand[0].val2 and op5.operand[1].ID == 0x10 and\
                 op5.operand[1].GetB(0) == 1 and op6.ID == 0:
                hndl.ID = 0x157

            elif op5.ID == OP_MOVZX and op5.operand[0].ID == 0x10 and\
                 op5.operand[1].ID == 0x10 and\
                 op5.operand[0].GetB(0) == 3 and op5.operand[1].GetB(0) == 1 and\
                 op6.ID == OP_POP and op6.operand[0].ID == 0x10 and op6.operand[0].GetB(0) == 0x22 and\
                 op7.ID == OP_MOV and op7.operand[0].ID == 0x31 and op7.operand[0].GetB(1) == 0x73 and\
                 op7.operand[0].GetB(2) == 3 and op7.operand[0].GetB(3) == 2 and op7.operand[0].val2 == 1 and\
                 op7.operand[1].ID == 0x10 and op7.operand[1].GetB(0) == 0x21 and op8.ID == 0:
                hndl.ID = 0x158

            elif op5.ID == OP_ADD and op5.operand[0].ID == 0x10 and op5.operand[0].GetB(0) == 3 and\
                 op5.operand[1].ID == 0x33 and op5.operand[1].GetB(1) == 0x73 and op5.operand[1].GetB(2) == 0 and\
                 op5.operand[1].GetB(3) == 0 and op6.ID == OP_PUSH and op6.operand[0].ID == 0x10 and\
                 op6.operand[0].GetB(0) == 3 and op7.ID == 0:
                self.fld74 = op5.operand[1].val2
                hndl.ID = 0x15a

            elif op5.ID == OP_MOV and op5.operand[0].ID == 0x31 and op5.operand[0].GetB(1) == 0x73 and\
                 op5.operand[0].GetB(2) == 0 and op5.operand[0].GetB(3) == 0 and\
                 op5.operand[0].val2 == self.fld70 and op5.operand[1].ID == 0x10 and op5.operand[1].GetB(0) == 1 and\
                 op6.ID == 0:
                hndl.ID = 0x168

            elif op5.ID == OP_SUB and op5.operand[0].ID == 0x10 and op5.operand[0].GetB(0) == 0x23 and\
                 op5.operand[1].ID == 0x10 and op5.operand[1].GetB(0) == 3 and op6.ID == 0:
                hndl.ID = 0x169

            elif op5.ID == OP_ADD and op5.operand[0].ID == 0x10 and\
                 op5.operand[0].GetB(0) == 0x23 and op5.operand[1].ID == 0x10 and op5.operand[1].GetB(0) == 3 and\
                 op6.ID == 0:
                hndl.ID = 0x16a

            elif op5.ID == OP_XOR and op5.operand[0].ID == 0x10 and\
                 op5.operand[0].GetB(0) == 0x23 and op5.operand[1].ID == 0x10 and op5.operand[1].GetB(0) == 3 and\
                 op6.ID == 0:
                hndl.ID = 0x16b

            elif op5.ID == OP_MOV and op5.operand[0].ID == 0x10 and\
                 op5.operand[0].GetB(0) == 0x23 and op5.operand[1].ID == 0x10 and op5.operand[1].GetB(0) == 3 and\
                 op6.ID == 0:
                hndl.ID = 0x16f

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and\
             op0.operand[0].GetB(0) == 0x23 and op1.ID == 0 and self.fld6x[0] == 0:
            self.fld6x[0] = 1
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 1

        elif op0.ID == OP_POP and\
             op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_ADD and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 3 and op1.op2x3x6x == 0 and op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 6

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x23 and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 9

        elif op0.ID == OP_MOVZX and op0.operand[0].ID == 0x10 and\
             op0.operand[0].GetB(0) == 2 and op0.operand[1].ID == 0x31 and op0.operand[1].GetB(1) == 0x23 and\
             op0.operand[1].GetB(2) == 0 and op0.operand[1].GetB(3) == 0 and op0.operand[1].val2 == 0 and\
             op0.op2x3x6x == 0 and op1.ID == OP_PUSH and op1.operand[0].ID == 0x10 and\
             op1.operand[0].GetB(0) == 2 and op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 10

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x32 and op0.operand[0].GetB(1) == 0x23 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0 and\
             op0.op2x3x6x == 0 and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0xb

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x23 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0 and\
             op0.op2x3x6x == 0 and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xc

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and\
             op0.operand[0].GetB(0) == 0x23 and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x15

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and\
             op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_MOV and op1.operand[0].ID == 0x31 and\
             op1.operand[0].GetB(1) == 0x23 and\
             op1.operand[0].GetB(2) == 0 and\
             op1.operand[0].GetB(3) == 0 and\
             op1.operand[0].val2 == 0 and op1.op2x3x6x == 0 and op1.operand[1].ID == 0x10 and\
             op1.operand[1].GetB(0) == 1 and op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x16

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x32 and\
             op0.operand[0].GetB(1) == 0x23 and op0.operand[0].GetB(2) == 0 and\
             op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0 and\
             op0.op2x3x6x == 0 and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x17

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x23 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0 and\
             op0.op2x3x6x == 0 and op1.ID == 0 and self.fld6x[1] == 0:
            self.fld6x[1] = 1
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x18

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x33 and\
             op0.operand[0].GetB(1) == 0x23 and op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and\
             op0.operand[0].val2 == 0 and op0.op2x3x6x == 0 and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x19

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
        op1.ID == OP_ADD and op1.operand[0].ID == 0x31 and op1.operand[0].GetB(1) == 0x43 and\
        op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
        op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 1 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x22

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_ADD and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 2 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x23

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_ADD and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 3 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x24

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_SUB and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 3 and op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x26

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_SUB and op1.operand[0].ID == 0x31 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 1 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x27

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_SUB and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 2 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x28

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_SUB and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and\
             op1.operand[0].val2 == 0 and op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 3 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x29

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 0x12 and\
             op2.ID == OP_IMUL and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x12 and\
             op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 2 and op3.ID == OP_PUSH and\
             op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x12 and op4.ID == OP_PUSHF and op5.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x2c

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 0x13 and\
             op2.ID == OP_IMUL and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x13 and\
             op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 3 and\
             op3.ID == OP_PUSH and op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x13 and\
             op4.ID == OP_PUSHF and op5.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x2d

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x33 and\
             op0.operand[0].GetB(1) == 0x73 and op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and\
             op0.operand[0].val2 == 0x1c and\
             op1.ID == OP_POPF and op2.ID == OP_POP and op2.operand[0].ID == 0x10 and\
             op2.operand[0].GetB(0) == 2 and op3.ID == OP_ADC and op3.operand[0].ID == 0x31 and\
             op3.operand[0].GetB(1) == 0x43 and op3.operand[0].GetB(2) == 0 and op3.operand[0].GetB(3) == 0 and\
             op3.operand[0].val2 == 0 and op3.operand[1].ID == 0x10 and op3.operand[1].GetB(0) == 1 and\
             op4.ID == OP_PUSHF and op5.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x2f

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x73 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0x1c and\
             op1.ID == OP_POPF and op2.ID == OP_POP and op2.operand[0].ID == 0x10 and\
             op2.operand[0].GetB(0) == 2 and op3.ID == OP_ADC and op3.operand[0].ID == 0x32 and\
             op3.operand[0].GetB(1) == 0x43 and op3.operand[0].GetB(2) == 0 and op3.operand[0].GetB(3) == 0 and\
             op3.operand[0].val2 == 0 and op3.operand[1].ID == 0x10 and op3.operand[1].GetB(0) == 2 and\
             op4.ID == OP_PUSHF and op5.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x30

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x33 and\
             op0.operand[0].GetB(1) == 0x73 and op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and\
             op0.operand[0].val2 == 0x1c and op1.ID == OP_POPF and op2.ID == OP_POP and op2.operand[0].ID == 0x10 and\
             op2.operand[0].GetB(0) == 3 and op3.ID == OP_ADC and op3.operand[0].ID == 0x33 and\
             op3.operand[0].GetB(1) == 0x43 and op3.operand[0].GetB(2) == 0 and op3.operand[0].GetB(3) == 0 and\
             op3.operand[0].val2 == 0 and op3.operand[1].ID == 0x10 and op3.operand[1].GetB(0) == 3 and op4.ID == OP_PUSHF and op5.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x31

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_AND and op1.operand[0].ID == 0x31 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 1 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x33

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_AND and op1.operand[0].ID == 0x32 and\
             op1.operand[0].GetB(1) == 0x43 and op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and\
             op1.operand[0].val2 == 0 and op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 2 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x34

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_AND and op1.operand[0].ID == 0x33 and\
             op1.operand[0].GetB(1) == 0x43 and op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and\
             op1.operand[0].val2 == 0 and op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 3 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x35

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and\
             op1.operand[0].GetB(0) == 0x12 and op2.ID == OP_CMP and op2.operand[0].ID == 0x10 and\
             op2.operand[0].GetB(0) == 0x11 and op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 1 and\
             op3.ID == OP_PUSHF and op4.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x37

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 0x12 and\
             op2.ID == OP_CMP and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x12 and\
             op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 2 and op3.ID == OP_PUSHF and op4.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x38

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 0x13 and\
             op2.ID == OP_CMP and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x13 and\
             op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 3 and op3.ID == OP_PUSHF and op4.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x39

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_XOR and op1.operand[0].ID == 0x31 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 1 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x3b

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_XOR and op1.operand[0].ID == 0x32 and\
             op1.operand[0].GetB(1) == 0x43 and op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and\
             op1.operand[0].val2 == 0 and op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 2 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x3c

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and\
             op0.operand[0].GetB(0) == 3 and op1.ID == OP_XOR and op1.operand[0].ID == 0x33 and\
             op1.operand[0].GetB(1) == 0x43 and op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and\
             op1.operand[0].val2 == 0 and op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 3 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x3d

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_OR and op1.operand[0].ID == 0x31 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 1 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x3f

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_OR and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 2 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x40

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_OR and op1.operand[0].ID == 0x33 and\
             op1.operand[0].GetB(1) == 0x43 and op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and\
             op1.operand[0].val2 == 0 and op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 3 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x41

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 0x12 and\
             op2.ID == OP_TEST and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 1 and\
             op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 0x11 and\
             op3.ID == OP_PUSHF and op4.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x43

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 0x12 and\
             op2.ID == OP_TEST and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 2 and\
             op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 0x12 and\
             op3.ID == OP_PUSHF and op4.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x44

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 0x13 and\
             op2.ID == OP_TEST and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 3 and\
             op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 0x13 and\
             op3.ID == OP_PUSHF and op4.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x45

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 2 and\
             op2.ID == OP_MOVZX and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x12 and\
             op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 1 and op3.ID == OP_PUSH and\
             op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x12 and op4.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x48

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x13 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 3 and\
             op2.ID == OP_MOVZX and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x13 and\
             op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 1 and op3.ID == OP_PUSH and\
             op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x13 and op4.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x49

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x13 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 3 and\
             op2.ID == OP_MOVZX and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x13 and\
             op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 2 and op3.ID == OP_PUSH and\
             op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x13 and op4.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x4d

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_INC and op1.operand[0].ID == 0x31 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x53

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_INC and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x54

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_INC and op1.operand[0].ID == 0x33 and\
             op1.operand[0].GetB(1) == 0x43 and op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and\
             op1.operand[0].val2 == 0 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x55

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x73 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0x1c and\
             op1.ID == OP_POPF and op2.ID == OP_POP and op2.operand[0].ID == 0x10 and\
             op2.operand[0].GetB(0) == 0x12 and op3.ID == OP_RCL and op3.operand[0].ID == 0x31 and\
             op3.operand[0].GetB(1) == 0x43 and op3.operand[0].GetB(2) == 0 and op3.operand[0].GetB(3) == 0 and\
             op3.operand[0].val2 == 0 and op3.operand[1].ID == 0x10 and op3.operand[1].GetB(0) == 0x11 and\
             op4.ID == OP_PUSHF and op5.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x57

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x33 and\
             op0.operand[0].GetB(1) == 0x73 and op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0x1c and\
             op1.ID == OP_POPF and op2.ID == OP_POP and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x12 and\
             op3.ID == OP_RCL and op3.operand[0].ID == 0x32 and\
             op3.operand[0].GetB(1) == 0x43 and op3.operand[0].GetB(2) == 0 and op3.operand[0].GetB(3) == 0 and\
             op3.operand[0].val2 == 0 and op3.operand[1].ID == 0x10 and op3.operand[1].GetB(0) == 0x11 and\
             op4.ID == OP_PUSHF and op5.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x58

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x33 and\
             op0.operand[0].GetB(1) == 0x73 and op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and\
             op0.operand[0].val2 == 0x1c and\
             op1.ID == OP_POPF and op2.ID == OP_POP and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x12 and\
             op3.ID == OP_RCL and op3.operand[0].ID == 0x33 and\
             op3.operand[0].GetB(1) == 0x43 and op3.operand[0].GetB(2) == 0 and op3.operand[0].GetB(3) == 0 and\
             op3.operand[0].val2 == 0 and op3.operand[1].ID == 0x10 and op3.operand[1].GetB(0) == 0x11 and\
             op4.ID == OP_PUSHF and op5.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x59

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x33 and\
             op0.operand[0].GetB(1) == 0x73 and op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and\
             op0.operand[0].val2 == 0x1c and op1.ID == OP_POPF and op2.ID == OP_POP and\
             op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x12 and op3.ID == OP_RCR and\
             op3.operand[0].ID == 0x31 and\
             op3.operand[0].GetB(1) == 0x43 and op3.operand[0].GetB(2) == 0 and op3.operand[0].GetB(3) == 0 and\
             op3.operand[0].val2 == 0 and op3.operand[1].ID == 0x10 and op3.operand[1].GetB(0) == 0x11 and\
             op4.ID == OP_PUSHF and op5.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x5b

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x33 and\
             op0.operand[0].GetB(1) == 0x73 and op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and\
             op0.operand[0].val2 == 0x1c and op1.ID == OP_POPF and\
             op2.ID == OP_POP and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x12 and\
             op3.ID == OP_RCR and op3.operand[0].ID == 0x32 and\
             op3.operand[0].GetB(1) == 0x43 and op3.operand[0].GetB(2) == 0 and op3.operand[0].GetB(3) == 0 and\
             op3.operand[0].val2 == 0 and op3.operand[1].ID == 0x10 and op3.operand[1].GetB(0) == 0x11 and\
             op4.ID == OP_PUSHF and op5.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x5c

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x33 and\
             op0.operand[0].GetB(1) == 0x73 and op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and\
             op0.operand[0].val2 == 0x1c and\
             op1.ID == OP_POPF and op2.ID == OP_POP and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x12 and\
             op3.ID == OP_RCR and op3.operand[0].ID == 0x33 and\
             op3.operand[0].GetB(1) == 0x43 and op3.operand[0].GetB(2) == 0 and op3.operand[0].GetB(3) == 0 and\
             op3.operand[0].val2 == 0 and op3.operand[1].ID == 0x10 and\
             op3.operand[1].GetB(0) == 0x11 and op4.ID == OP_PUSHF and op5.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x5d

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_ROL and op1.operand[0].ID == 0x31 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x5f

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_ROL and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x60

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_ROL and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x61

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_ROR and op1.operand[0].ID == 0x31 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 99

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_ROR and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 100

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_ROR and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x65

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_SHL and op1.operand[0].ID == 0x31 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and\
             op2.ID == OP_PUSHF and op3.ID == 0 and self.fld6x[2] == 0:
            self.fld6x[2] = 1
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x67

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_SHL and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and op2.ID == OP_PUSHF and\
             op3.ID == 0 and self.fld6x[3] == 0:
            self.fld6x[3] = 1
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x68

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_SHL and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and\
             op2.ID == OP_PUSHF and op3.ID == 0 and self.fld6x[4] == 0:
            self.fld6x[4] = 1
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x69

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_SAR and op1.operand[0].ID == 0x31 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x6b

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_SAR and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x6c

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and\
             op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_SAR and op1.operand[0].ID == 0x33 and\
             op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and\
             op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x6d

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
              op1.ID == OP_SHL and op1.operand[0].ID == 0x31 and op1.operand[0].GetB(1) == 0x43 and\
              op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
              op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and\
              op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x6f

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_SHL and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x70

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_SHL and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x71

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_SHR and op1.operand[0].ID == 0x31 and\
             op1.operand[0].GetB(1) == 0x43 and op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and\
             op1.operand[0].val2 == 0 and op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x73

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_SHR and op1.operand[0].ID == 0x32 and\
             op1.operand[0].GetB(1) == 0x43 and op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and\
             op1.operand[0].val2 == 0 and op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x74

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_SHR and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x75

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_DEC and op1.operand[0].ID == 0x31 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x77

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_DEC and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x78

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_DEC and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x79

        elif op0.ID == OP_MOV and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op0.operand[1].ID == 0x10 and op0.operand[1].GetB(0) == 3 and op1.ID == 0 and self.fld6x[10] == 0:
            self.fld6x[10] = 1
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x7b

        elif op0.ID == OP_ADD and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op0.operand[1].ID == 0x23 and op1.ID == OP_SUB and op1.operand[0].ID == 0x10 and\
             op1.operand[0].GetB(0) == 3 and op1.operand[1].ID == 0x23 and\
             op0.operand[1].value == op1.operand[1].value and\
             op2.ID == 0 and self.fld6x[10] == 0:
            self.fld6x[10] = 1
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x7b

        elif op0.ID == OP_SUB and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op0.operand[1].ID == 0x23 and op1.ID == OP_ADD and op1.operand[0].ID == 0x10 and\
             op1.operand[0].GetB(0) == 3 and op1.operand[1].ID == 0x23 and op0.operand[1].value == op1.operand[1].value and\
             op2.ID == 0 and self.fld6x[10] == 0:
            self.fld6x[10] = 1
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x7b

        elif op0.ID == OP_XOR and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op0.operand[1].ID == 0x23 and op1.ID == OP_XOR and op1.operand[0].ID == 0x10 and\
             op1.operand[0].GetB(0) == 3 and op1.operand[1].ID == 0x23 and op0.operand[1].value == op1.operand[1].value and\
             op2.ID == 0 and self.fld6x[10] == 0:
            self.fld6x[10] = 1
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x7b

        elif op0.ID == OP_MOV and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op0.operand[1].ID == 0x10 and op0.operand[1].GetB(0) == 3 and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xa3

        elif op0.ID == OP_XOR and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op0.operand[1].ID == 0x23 and op1.ID == OP_XOR and op1.operand[0].ID == 0x10 and\
             op1.operand[0].GetB(0) == 3 and op1.operand[1].ID == 0x23 and op0.operand[1].value == op1.operand[1].value and\
             op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xa3

        elif op0.ID == OP_SUB and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op0.operand[1].ID == 0x23 and op1.ID == OP_ADD and op1.operand[0].ID == 0x10 and\
             op1.operand[0].GetB(0) == 3 and op1.operand[1].ID == 0x23 and\
             op0.operand[1].value == op1.operand[1].value and op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xa3

        elif op0.ID == OP_ADD and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op0.operand[1].ID == 0x23 and op1.ID == OP_SUB and op1.operand[0].ID == 0x10 and\
             op1.operand[0].GetB(0) == 3 and op1.operand[1].ID == 0x23 and\
             op0.operand[1].value == op1.operand[1].value and op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xa3

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 2 and\
             op2.ID == OP_MOVSX and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x12 and\
             op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 1 and op3.ID == OP_PUSH and\
             op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x12 and op4.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x80

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x13 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 3 and\
             op2.ID == OP_MOVSX and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x13 and\
             op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 1 and op3.ID == OP_PUSH and\
             op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x13 and op4.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x81

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x13 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 3 and\
             op2.ID == OP_MOVSX and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x13 and\
             op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 2 and op3.ID == OP_PUSH and\
             op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x13 and op4.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x85

        elif op0.ID == OP_AND and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x73 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0x1c and\
             op0.operand[1].TID() == 2 and op0.operand[1].value == 0xfe or op0.operand[1].value == 0xfffffffe and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x87

        elif op0.ID == OP_AND and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x73 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0x1c and\
             op0.operand[1].ID == 0x23 and op0.operand[1].value == 0xfffffbff and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x8b

        elif op1.ID == OP_AND and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x73 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0x1c and\
             op1.operand[1].ID == 0x23 and op1.operand[1].value == 0xfffffbff and op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x8b

        elif op0.ID == OP_MOV and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op0.operand[1].ID == 0x23 and op0.operand[1].value == 0x53947 and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x8f

        elif op0.ID == OP_AND and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x73 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0x1c and\
             op0.operand[1].ID == 0x23 and op0.operand[1].value == 0xfffffdff and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x8f

        elif op0.ID == OP_MOV and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op0.operand[1].ID == 0x33 and op0.operand[1].GetB(1) == 0x73 and\
             op0.operand[1].GetB(2) == 0 and op0.operand[1].GetB(3) == 0 and op0.operand[1].val2 == 0x1c and\
             op1.ID == OP_AND and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 3 and\
             op1.operand[1].TID() == 2 and op1.operand[1].value == 1:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x93

        elif op0.ID == OP_OR and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x73 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0x1c and\
             op0.operand[1].TID() == 2 and op0.operand[1].value == 1 and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x97

        elif op0.ID == OP_OR and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x73 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0x1c and\
             op0.operand[1].TID() == 2 and op0.operand[1].value == 0x400 and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x9b

        elif op1.ID == OP_OR and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x73 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0x1c and\
             op1.operand[1].TID() == 2 and op1.operand[1].value == 0x400 and op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x9b

        elif op0.ID == OP_OR and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x73 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0x1c and\
             op0.operand[1].TID() == 2 and op0.operand[1].value == 0x200 and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x9f

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x73 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == self.fld74 and\
             op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xa3

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_BT and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 2 and\
             op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0xa8

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_BT and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 3 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xa9

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_BTC and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 2 and op2.ID == OP_PUSHF and\
             op3.ID == 0 and self.fld6x[7] == 0:
            self.fld6x[7] = 1
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0xab

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_BTC and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 2 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xac

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_BTR and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and\
             op1.operand[0].val2 == 0 and op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 2 and\
             op2.ID == OP_PUSHF and op3.ID == 0 and self.fld6x[8] == 0:
            self.fld6x[8] = 1
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0xaf

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_BTR and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 2 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            if self.IatCount < 0xa9:
                hndl.ID = 0xb0
            else:
                hndl.sz = 2
                hndl.ID = 0xaf

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_BTR and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 3 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xb0

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_BTS and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 2 and op2.ID == OP_PUSHF and op3.ID == 0 and self.fld6x[9] == 0:
            self.fld6x[9] = 1
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0xb3

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_BTS and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 2 and op2.ID == OP_PUSHF and op3.ID == 0:

            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            if self.IatCount < 0xa9:
                hndl.ID = 0xb4
            else:
                hndl.ID = 0xb3
                hndl.sz = 2

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_BTS and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 3 and op2.ID == OP_PUSHF and op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xb4

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x73 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0x1c and\
             op1.ID == OP_POPF and op2.ID == OP_POP and op2.operand[0].ID == 0x10 and\
             op2.operand[0].GetB(0) == 2 and op3.ID == OP_SBB and op3.operand[0].ID == 0x31 and\
             op3.operand[0].GetB(1) == 0x43 and op3.operand[0].GetB(2) == 0 and op3.operand[0].GetB(3) == 0 and\
             op3.operand[0].val2 == 0 and op3.operand[1].ID == 0x10 and op3.operand[1].GetB(0) == 1 and\
             op4.ID == OP_PUSHF and op5.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0xb7

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x73 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0x1c and\
             op1.ID == OP_POPF and op2.ID == OP_POP and op2.operand[0].ID == 0x10 and\
             op2.operand[0].GetB(0) == 2 and op3.ID == OP_SBB and op3.operand[0].ID == 0x32 and\
             op3.operand[0].GetB(1) == 0x43 and op3.operand[0].GetB(2) == 0 and op3.operand[0].GetB(3) == 0 and\
             op3.operand[0].val2 == 0 and op3.operand[1].ID == 0x10 and op3.operand[1].GetB(0) == 2 and\
             op4.ID == OP_PUSHF and op5.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0xb8

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x73 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0x1c and\
             op1.ID == OP_POPF and op2.ID == OP_POP and op2.operand[0].ID == 0x10 and\
             op2.operand[0].GetB(0) == 3 and op3.ID == OP_SBB and op3.operand[0].ID == 0x33 and\
             op3.operand[0].GetB(1) == 0x43 and op3.operand[0].GetB(2) == 0 and\
             op3.operand[0].GetB(3) == 0 and op3.operand[0].val2 == 0 and op3.operand[1].ID == 0x10 and\
             op3.operand[1].GetB(0) == 3 and op4.ID == OP_PUSHF and op5.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xb9

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 2 and\
             op2.ID == OP_MUL and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x11 and\
             op3.ID == OP_MOVZX and op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x12 and\
             op3.operand[1].ID == 0x10 and op3.operand[1].GetB(0) == 0x41 and op4.ID == OP_PUSH and\
             op4.operand[0].ID == 0x10 and op4.operand[0].GetB(0) == 0x12 and op5.ID == OP_MOVZX and\
             op5.operand[0].ID == 0x10 and op5.operand[0].GetB(0) == 0x12 and op5.operand[1].ID == 0x10 and\
             op5.operand[1].GetB(0) == 1 and op6.ID == OP_PUSH and op6.operand[0].ID == 0x10 and\
             op6.operand[0].GetB(0) == 0x12 and op7.ID == OP_PUSHF and op8.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0xbb

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 2 and\
             op2.ID == OP_MUL and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x12 and\
             op3.ID == OP_PUSH and op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x22 and\
             op4.ID == OP_PUSH and op4.operand[0].ID == 0x10 and op4.operand[0].GetB(0) == 2 and\
             op5.ID == OP_PUSHF and op6.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0xbc

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x13 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 3 and\
             op2.ID == OP_MUL and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x13 and\
             op3.ID == OP_PUSH and op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x23 and\
             op4.ID == OP_PUSH and op4.operand[0].ID == 0x10 and op4.operand[0].GetB(0) == 3 and\
             op5.ID == OP_PUSHF and op6.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xbd

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 2 and\
             op2.ID == OP_IMUL and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x11 and\
             op3.ID == OP_MOVZX and op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x12 and\
             op3.operand[1].ID == 0x10 and op3.operand[1].GetB(0) == 0x41 and\
             op4.ID == OP_PUSH and op4.operand[0].ID == 0x10 and op4.operand[0].GetB(0) == 0x12 and\
             op5.ID == OP_MOVZX and op5.operand[0].ID == 0x10 and op5.operand[0].GetB(0) == 0x12 and\
             op5.operand[1].ID == 0x10 and op5.operand[1].GetB(0) == 1 and\
             op6.ID == OP_PUSH and op6.operand[0].ID == 0x10 and op6.operand[0].GetB(0) == 0x12 and\
             op7.ID == OP_PUSHF and op8.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0xbf

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 2 and\
             op2.ID == OP_IMUL and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x12 and\
             op3.ID == OP_PUSH and op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x22 and\
             op4.ID == OP_PUSH and op4.operand[0].ID == 0x10 and op4.operand[0].GetB(0) == 2 and\
             op5.ID == OP_PUSHF and op6.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0xc0

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x13 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 3 and\
             op2.ID == OP_IMUL and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x13 and\
             op3.ID == OP_PUSH and op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x23 and\
             op4.ID == OP_PUSH and op4.operand[0].ID == 0x10 and op4.operand[0].GetB(0) == 3 and\
             op5.ID == OP_PUSHF and op6.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xc1

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 2 and\
             op2.ID == OP_DIV and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x11 and\
             op3.ID == OP_MOVZX and op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x12 and\
             op3.operand[1].ID == 0x10 and op3.operand[1].GetB(0) == 0x41 and op4.ID == OP_PUSH and\
             op4.operand[0].ID == 0x10 and op4.operand[0].GetB(0) == 0x12 and op5.ID == OP_MOVZX and\
             op5.operand[0].ID == 0x10 and op5.operand[0].GetB(0) == 0x12 and op5.operand[1].ID == 0x10 and\
             op5.operand[1].GetB(0) == 1 and op6.ID == OP_PUSH and op6.operand[0].ID == 0x10 and\
             op6.operand[0].GetB(0) == 0x12 and op7.ID == OP_PUSHF and op8.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0xc3

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 2 and\
             op2.ID == OP_POP and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 2 and\
             op3.ID == OP_DIV and op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x12 and\
             op4.ID == OP_PUSH and op4.operand[0].ID == 0x10 and op4.operand[0].GetB(0) == 0x22 and\
             op5.ID == OP_PUSH and op5.operand[0].ID == 0x10 and op5.operand[0].GetB(0) == 2 and\
             op6.ID == OP_PUSHF and op7.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0xc4

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x13 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 3 and\
             op2.ID == OP_POP and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x23 and\
             op3.ID == OP_DIV and op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x13 and\
             op4.ID == OP_PUSH and op4.operand[0].ID == 0x10 and op4.operand[0].GetB(0) == 0x23 and\
             op5.ID == OP_PUSH and op5.operand[0].ID == 0x10 and op5.operand[0].GetB(0) == 3 and\
             op6.ID == OP_PUSHF and op7.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xc5

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 2 and\
             op2.ID == OP_IDIV and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x11 and\
             op3.ID == OP_MOVZX and op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x12 and\
             op3.operand[1].ID == 0x10 and op3.operand[1].GetB(0) == 0x41 and op4.ID == OP_PUSH and\
             op4.operand[0].ID == 0x10 and op4.operand[0].GetB(0) == 0x12 and op5.ID == OP_MOVZX and\
             op5.operand[0].ID == 0x10 and op5.operand[0].GetB(0) == 0x12 and op5.operand[1].ID == 0x10 and\
             op5.operand[1].GetB(0) == 1 and op6.ID == OP_PUSH and op6.operand[0].ID == 0x10 and\
             op6.operand[0].GetB(0) == 0x12 and op7.ID == OP_PUSHF and op8.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 199

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x12 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 2 and\
             op2.ID == OP_POP and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x22 and\
             op3.ID == OP_IDIV and op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x12 and\
             op4.ID == OP_PUSH and op4.operand[0].ID == 0x10 and op4.operand[0].GetB(0) == 0x22 and\
             op5.ID == OP_PUSH and op5.operand[0].ID == 0x10 and op5.operand[0].GetB(0) == 2 and\
             op6.ID == OP_PUSHF and op7.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 200

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x13 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 3 and\
             op2.ID == OP_POP and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x23 and\
             op3.ID == OP_IDIV and op3.operand[0].ID == 0x10 and op3.operand[0].GetB(0) == 0x13 and\
             op4.ID == OP_PUSH and op4.operand[0].ID == 0x10 and op4.operand[0].GetB(0) == 0x23 and\
             op5.ID == OP_PUSH and op5.operand[0].ID == 0x10 and op5.operand[0].GetB(0) == 3 and\
             op6.ID == OP_PUSHF and op7.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xc9

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_BSWAP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 3 and\
             op2.ID == OP_PUSH and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 3 and\
             op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xcd

        elif op0.ID == OP_NEG and op0.operand[0].ID == 0x31 and op0.operand[0].GetB(1) == 0x43 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0 and\
             op1.ID == OP_PUSHF and op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0xcf

        elif op0.ID == OP_NEG and op0.operand[0].ID == 0x32 and op0.operand[0].GetB(1) == 0x43 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0 and\
             op1.ID == OP_PUSHF and op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0xd0

        elif op0.ID == OP_NEG and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x43 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0 and\
             op1.ID == OP_PUSHF and op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xd1

        elif op0.ID == OP_NOT and op0.operand[0].ID == 0x31 and op0.operand[0].GetB(1) == 0x43 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0 and\
             op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0xd3

        elif op0.ID == OP_NOT and op0.operand[0].ID == 0x32 and op0.operand[0].GetB(1) == 0x43 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0 and\
             op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0xd4

        elif op0.ID == OP_NOT and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x43 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0 and\
             op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0xd5

        ###FIX IT?
        elif op1.ID == OP_MOV and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 0x23 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x73 and\
             op2.ID == OP_OR and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x13 and\
             op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 0x13:
            self.fld70 = op0.operand[1].val2
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x14a

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x43 and\
             op1.ID == 0 and self.fld6x[5] == 0:
            self.fld6x[5] = 1
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x14c

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x43 and\
             op1.ID == 0 and self.fld6x[6] == 0:
            self.fld6x[6] = 1
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x14d

        elif op0.ID == OP_MOV and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x23 and\
             op0.operand[1].ID == 0x10 and op0.operand[1].GetB(0) == 0x43 and\
             op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x14e
        
        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x42 and\
             op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x14f

        elif op0.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x14f

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x43 and\
             op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x150

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x42 and\
             op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x151

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x43 and\
             op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x152

        elif op0.ID == OP_MOV and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op0.operand[1].ID == 0x33 and op0.operand[1].GetB(1) == 0x73 and\
             op0.operand[1].GetB(2) == 0 and op0.operand[1].GetB(3) == 0 and\
             op1.ID == OP_ADD and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 3 and\
             op2.ID == 0:
            self.fld78 = op0.operand[1].val2
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x15d

        elif op0.ID == OP_MOV and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op0.operand[1].ID == 0x33 and op0.operand[1].GetB(1) == 0x73 and\
             op0.operand[1].GetB(2) == 0 and op0.operand[1].GetB(3) == 0 and\
             op0.operand[1].val2 == self.fld78 and\
             op1.ID == OP_ADD and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 0x23 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 3 and op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x15e

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 0x13 and\
             op1.ID == OP_SHL and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 0x11 and op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x15f

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_XOR and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x43 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 3 and op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x160

        elif op0.ID == OP_MOV and op0.operand[0].ID == 0x10 and op0.operand[1].TID() == 2 and\
             op0.operand[0].GetB(0) == 0x33 and op0.operand[1].value == 0 and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x161

        elif op0.ID == OP_MOVZX and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op0.operand[1].ID == 0x31 and op0.operand[1].GetB(1) == 0x23 and op0.operand[1].GetB(2) == 0 and\
             op0.operand[1].GetB(3) == 0 and op0.operand[1].val2 == 0 and op0.op2x3x6x == 100 and\
             op1.ID == OP_PUSH and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 2 and\
             op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x162

        elif op0.ID == OP_MOV and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op0.operand[1].ID == 0x32 and op0.operand[1].GetB(1) == 0x23 and op0.operand[1].GetB(2) == 0 and\
             op0.operand[1].GetB(3) == 0 and op0.operand[1].val2 == 0 and op0.op2x3x6x == 100 and\
             op1.ID == OP_PUSH and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 2 and op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x163

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x23 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and\
             op0.operand[0].val2 == 0 and op0.op2x3x6x == 100 and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x164

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_MOV and op1.operand[0].ID == 0x31 and op1.operand[0].GetB(1) == 0x23 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.op2x3x6x == 0x64 and op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 1 and\
             op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 1
            hndl.ID = 0x165

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 2 and\
             op1.ID == OP_MOV and op1.operand[0].ID == 0x32 and op1.operand[0].GetB(1) == 0x23 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op1.op2x3x6x == 0x64 and op1.operand[1].ID == 0x10 and op1.operand[1].GetB(0) == 2 and op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 2
            hndl.ID = 0x166

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x23 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0 and\
             op0.op2x3x6x == 0x64 and op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x167

        elif op0.ID == OP_PUSH and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x73 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == self.fld7c and\
             op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x16c

        # FIX IT ? NEEDS op2.ID == 0?
        elif op0.ID == OP_MOV and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op0.operand[1].ID == 0x33 and op0.operand[1].GetB(1) == 0x43 and\
             op0.operand[1].GetB(2) == 0 and op0.operand[1].GetB(3) == 0 and op0.operand[1].val2 == 4 and\
             op1.ID == OP_MOV and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 0x73 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[1].ID == 0x10 and\
             op1.operand[1].GetB(0) == 3:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x16d
            self.fld7c = op1.operand[0].val2

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x73 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == self.fld7c and\
             op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x16e

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_PUSH and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 0x23 and\
             op2.ID == OP_MOV and op2.operand[0].ID == 0x10 and op2.operand[0].GetB(0) == 0x23 and\
             op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 3 and\
             op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x170

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_POP and op1.operand[0].ID == 0x10 and op1.operand[0].GetB(0) == 0x13 and\
             op2.ID == OP_MOV and op2.operand[0].ID == 0x33 and op2.operand[0].GetB(1) == 3 and\
             op2.operand[0].GetB(2) == 0 and op2.operand[0].GetB(3) == 0 and op2.operand[0].val2 == 0 and\
             op2.operand[1].ID == 0x10 and op2.operand[1].GetB(0) == 0x13 and\
             op3.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x171

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x10 and op0.operand[0].GetB(0) == 3 and\
             op1.ID == OP_PUSH and op1.operand[0].ID == 0x33 and op1.operand[0].GetB(1) == 3 and\
             op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and op1.operand[0].val2 == 0 and\
             op2.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x172

        elif op0.ID == OP_POP and op0.operand[0].ID == 0x33 and op0.operand[0].GetB(1) == 0x73 and\
             op0.operand[0].GetB(2) == 0 and op0.operand[0].GetB(3) == 0 and op0.operand[0].val2 == 0x1c and\
             op1.ID == 0:
            hndl.a = 1
            hndl.hid = hid
            hndl.sz = 3
            hndl.ID = 0x173

        self.CiscHndl.append(hndl)
        self.CiscHndlMap[hid] = hndl
        self.CiscHndlRevMap[hndl.ID] = hndl

    def WriteIATFile(self):
        f = open("{}/TXT/Cisc_Iat_{:08x}.txt".format(self.WrkDir, self.MainHandlerAddr),"w")
        f.write("// Cisc Machine Header\n// ImageBase\tAlign\t\tIatAddr\t\tIatDis\t\tIatCount\tDLLCheck\n")
        f.write("{:08X}\t{:08X}\t{:08X}\t{:08X}\t{:08X}\t{:08X}\n\n".format(self.ImageBase, self.Align, self.IatAddr, self.IatDis, self.IatCount, self.fld50))
        f.write("")

        for h in self.CiscHndl:
            txt = "\t{:04X}\t{:02X}\t{:d}\t{:d}\t{:d}\t{:d}\t{:08X}\t{:08X}\t{:d}\t{:d}".format(h.ID, h.hid, h.ids[0], h.ids[1], h.ids[2], h.ids[3], h.vals[0], h.vals[1], h.sz, h.HasData)
            if h.a == 0:
                txt += " // Corrupted handler"
            txt += "\n"
            f.write(txt)

        f.close()

    def Analyze(self):
        CMDSimpler.Clear()

        vmf = open("{}/TXT/Cisc_Vm_{:08x}.txt".format(self.WrkDir, self.MainHandlerAddr),"w")
        i = 0
        adr = self.MainHandlerAddr
        while self.InBlock(UINT(adr + i)):
            mm = self.GetMM(UINT(adr + i))

            opAdr = UINT(adr + i)

            sz, rk = XrkDecode(mm)
            i += sz

            i = UINT(i)

            if rk.ID == OP_JMP:
                if rk.operand[0].TID() == 2:
                    i += rk.operand[0].value
                else:
                    CMDSimpler.Add(rk, opAdr)
                    break
            elif rk.ID >= OP_JA and rk.ID <= OP_JS:
                (a, b) = self.FUN_1005da10(rk.ID, False, 'A')
                if (a & 0xFF) == 0:
                    print("Follow Jump?")
                    b = False

                if b:
                    i += rk.operand[0].value
            else:
                CMDSimpler.Add(rk, opAdr)

            i = UINT(i)

        CMDSimpler.Simple(self, 0xffff, 'A')
        CMDSimpler.RebuildInfo()

        self.StoreVmHandle(0xffff)

        print("/////////////////    Main Handler")
        vmf.write("//////////////////////////////////////\n")
        vmf.write("/////////////////    Main Handler\n")

        for t in CMDSimpler.GetListing(True, True):
            print(t)
            vmf.write("{}\n".format(t))

        bt = GetBytes(UINT(self.ImageBase + self.fld54), 4)
        align = GetDWORD(bt)
        if align == self.Align:
            align = 0
        else:
            align = self.Align

        for z in range(self.IatCount):
            mm = self.GetMM(self.IatAddr + z * 4)
            CMDSimpler.Clear()
            adr = UINT(GetDWORD(mm) + align)

            k = 0
            while self.InBlock(UINT(adr + k)) and self.MainHandlerAddr != UINT(adr + k):
                mn = self.GetMM(UINT(adr + k))
                opAdr = UINT(adr + k)

                sz, rk = XrkDecode(mn)
                k += sz

                k = UINT(k)

                if rk.ID == OP_JMP:
                    if rk.operand[0].TID() == 2:
                        k += rk.operand[0].value
                    else:
                        CMDSimpler.Add(rk, opAdr)
                        break
                elif rk.ID >= OP_JA and rk.ID <= OP_JS:
                    (a, b) = self.FUN_1005da10(rk.ID, False, 'A')
                    if (a & 0xFF) == 0:
                        print("Follow Jump?")
                        b = False

                    if b:
                        k += rk.operand[0].value
                else:
                    CMDSimpler.Add(rk, opAdr)

                k = UINT(k)

            CMDSimpler.Simple(self, z, 'A')
            CMDSimpler.RebuildInfo()

            print("\n/////////////////    Handler {:04x}".format(z))

            vmf.write("//////////////////////////////////////\n")
            vmf.write("/////////////////    Handler {:04x}\n".format(z))


            for t in CMDSimpler.GetListing(True, True):
                print(t)
                vmf.write("{}\n".format(t))

            self.StoreVmHandle(z)

        vmf.close()

        for j in range(2):
            self.CiscHndl = list()
            self.CiscHndlMap = dict()
            self.CiscHndlRevMap = dict()
            self.fld6x = [0] * 11

            self.CISCER1(0xffff)
            for q in range(self.IatCount):
                self.CISCER1(q)

        print(hex(len(self.CiscHndl)), hex(self.fld78), hex(self.fld54))
        self.fld50 = self.fld78
        if self.fld54 == self.fld50:
            self.fld50 |= 0x80000000

        self.WriteIATFile()

    def MakeSpecialHandlers(self):
        hndl1 = None
        hndl18 = None
        hndl150 = None
        hndl152 = None

        for h in self.CiscHndl:
            if h.ID == 0x15:
                hndl1 = h
            elif h.ID == 0x19:
                hndl18 = h
            elif h.ID == 0x14c:
                hndl150 = h
            elif h.ID == 0x14d:
                hndl152 = h

        if hndl1:
            hndl1.ID = 1
        if hndl18:
            hndl18.ID = 0x18
        if hndl150:
            hndl150.ID = 0x150
        if hndl152:
            hndl152.ID = 0x152


    def AllocVops(self, cnt):
        self.maxVops = cnt
        self.countVops = 0
        self.Vops = list()
        for i in range(cnt):
            self.Vops.append(VOPT())

    def GetCiscHandler(self, hid):
        if hid in self.CiscHndlMap:
            return self.CiscHndlMap[hid]
        return None

    def IsHndlIDHasData(self, id):
        if id in self.CiscHndlRevMap:
            return self.CiscHndlRevMap[id].HasData
        return 0


    def SortVops(self):
        self.Vops[:self.countVops] = sorted(self.Vops[:self.countVops], key=lambda x:x.addr, reverse=False)

    def AddVop(self, id, addr):
        if self.countVops >= self.maxVops:
            self.maxVops += 1
            self.Vops.append(VOPT())

        vo = self.Vops[self.countVops]
        self.countVops += 1
        vo.ID = id
        vo.addr = addr
        return vo

    def Isolated(self, vop, addr):
        mm = self.GetMM(addr)
        sz, rk = XrkDecode(mm)
        if rk.ID != OP_PUSH or rk.operand[0].ID != 0x23:
            vop.valign = addr
            mm = self.GetMM( UINT(addr + sz) )
            sz, rk = XrkDecode(mm)
            if rk.ID != OP_PUSH or rk.operand[0].ID != 0x23:
                print("Extrange isolated opcode")
                return False
        LABELS.GetLabel(UINT(rk.operand[0].value + self.Align), rk.operand[0].value)
        return True


    def DumpVops(self, addr, pushvl):
        l = LABELS.FindLabel(addr)
        mh = self.GetCiscHandler(0xffff)

        if not mh:
            print("Add main handler into iat file!")
            return False

        h = None # type: CHNDL
        i = 0
        k = 0
        opidx = 0

        while True:
            #if opidx > 100:
            #    exit(1)
            k = i
            mm = self.GetMM(UINT(addr + i))
            s = UB(mm[0])
            _, s = ComputeVal(mh.ids[0], mh.sz, s, pushvl)
            _, s = ComputeVal(mh.ids[1], mh.sz, s, mh.vals[0])
            _, s = ComputeVal(mh.ids[2], mh.sz, s, mh.vals[1])
            _, pushvl = ComputeVal(mh.ids[3], mh.sz, pushvl, s)
            s &= 0xFF

            h = self.GetCiscHandler(UWORD(s - (self.IatDis >> 2) ))

            if not h:
                #print("{:08x}\t{:02x} -> {:02x} ({:04x})".format(UINT(addr + i),UB(mm[0]), s, UWORD(s - (self.IatDis >> 2))))
                print("NULL handler for {:02x}".format(UWORD(s - (self.IatDis >> 2) )))
                l.size = i + 1
                l.idx = opidx
                return True

            if LABELS.IsUsed(UINT(addr + i)):
                l.size = i + 1
                l.idx = opidx
                #print("USED")
                return True

            if h.ID == 0x161:
                pushvl = 0
                i += 1
                continue

            vop = self.AddVop(h.ID, UINT(addr + i))

            if not vop:
                l.size = i + 1
                l.idx = opidx
                #print("vop")
                return True

            opidx += 1

            if h.ID == 0x14a:
                l.size = i + 1
                l.idx = opidx
                return True

            if h.HasData != 1:
                i += 1
                #print("{:08x}\t{:02x} -> {:02x} ({:04x}) h.ID {:04x}(sz {:d})     ({:08x})".format(vop.addr, UB(mm[0]), s,
                #                                                                                   UWORD(s - (self.IatDis >> 2)),
                #                                                                                   h.ID, h.sz, pushvl))
                continue

            if h.sz == 1:
                v = UB(self.GetMM(UINT(addr + i + 1))[0])
                _, v = ComputeVal(h.ids[0], h.sz, v, pushvl)
                _, v = ComputeVal(h.ids[1], h.sz, v, h.vals[0])
                _, v = ComputeVal(h.ids[2], h.sz, v, h.vals[1])
                _, pushvl = ComputeVal(h.ids[3], h.sz, pushvl, v)
                vop.pushval = v
                i += 2

                if h.ID == 0x14b:
                    l.size = i + 1
                    l.idx = opidx
                    return True

            elif h.sz == 2:
                v = GetWORD( self.GetMM(UINT(addr + i + 1)) )
                _, v = ComputeVal(h.ids[0], h.sz, v, pushvl)
                _, v = ComputeVal(h.ids[1], h.sz, v, h.vals[0])
                _, v = ComputeVal(h.ids[2], h.sz, v, h.vals[1])
                _, pushvl = ComputeVal(h.ids[3], h.sz, pushvl, v)
                vop.pushval = v
                i += 3

            elif h.sz == 3:
                v = GetDWORD( self.GetMM(UINT(addr + i + 1)) )
                if h.ID not in (0x154, 0x156):
                    _, v = ComputeVal(h.ids[0], h.sz, v, pushvl)
                    _, v = ComputeVal(h.ids[1], h.sz, v, h.vals[0])
                    _, v = ComputeVal(h.ids[2], h.sz, v, h.vals[1])
                    _, pushvl = ComputeVal(h.ids[3], h.sz, pushvl, v)
                vop.pushval = v
                i += 5

                if h.ID == 0x154:
                    LABELS.GetLabel(UINT(addr + i + v), 0)
                    l.size = i
                    l.idx = opidx
                    return True
                elif h.ID == 0x156:
                    LABELS.GetLabel(UINT(addr + i + v), 0)
                elif h.ID == 0x15a:
                    self.Isolated(vop, UINT(v + self.Align))

            #print("{:08x}\t{:02x} -> {:02x} ({:04x}) h.ID {:04x}(sz {:d})  (push {:08x})      ({:08x})".format(vop.addr, UB(mm[0]), s,
            #                                                                      UWORD(s - (self.IatDis >> 2)),
            #                                                                      h.ID, h.sz, vop.pushval, pushvl))

    def EraseVops(self, i, num):
        self.Vops[i: self.maxVops - num] = self.Vops[i + num: self.maxVops]
        #for j in range(i, self.maxVops - num):
        #    self.Vops[j] = self.Vops[j + num]
        for j in range(self.maxVops - num, self.maxVops):
            self.Vops[j] = VOPT()

    def VopSimple(self, i):
        if i + 6 >= self.maxVops:
            self.maxVops += 6
            for z in range(6):
                self.Vops.append(VOPT())

        vop0 = self.Vops[i]
        vop1 = self.Vops[i+1]
        vop2 = self.Vops[i+2]
        vop3 = self.Vops[i+3]
        vop4 = self.Vops[i+4]

        if vop0.ID == 4 and vop1.ID == 1 and vop2.ID == 9 and vop3.ID == 4 and\
           vop4.ID in (6, 0x26, 0x160):
            if vop4.ID == 6:
                vop0.pushval = UINT(vop0.pushval + vop3.pushval)
            elif vop4.ID == 0x26:
                vop0.pushval = UINT(vop0.pushval - vop3.pushval)
            elif vop4.ID == 0x160:
                vop0.pushval = UINT(vop0.pushval ^ vop3.pushval)

            self.EraseVops(i + 3, 2)
            self.countVops -= 2
        elif vop0.ID == 0x16c and vop1.ID == 0x16d and vop2.ID == 0x16c and vop3.ID == 1 and vop4.ID == 0x16e:
            vop0.ID = 1
            self.EraseVops(i + 1, 4)
            self.countVops -= 4
        elif vop0.ID == 4 and vop1.ID in (9, 0x16c) and\
            ((vop2.ID == 6 and vop4.ID == 0x26) or\
             (vop2.ID == 0x26 and vop4.ID == 6) or\
             (vop2.ID == 0x160 and vop4.ID == 0x160)) and\
            vop3.ID == 4 and vop0.pushval == vop3.pushval:
            vop0.ID = vop1.ID
            self.EraseVops(i + 1, 4)
            self.countVops -= 4
        elif ((vop0.ID == 0x169 and vop3.ID == 6) or\
              (vop0.ID == 0x16a and vop3.ID == 0x26) or\
              (vop0.ID == 0x16b and vop3.ID == 0x160)) and\
               vop1.ID == 9 and vop2.ID == 4 and vop0.pushval == vop2.pushval:
            vop0.ID = 9
            self.EraseVops(i + 1, 3)
            self.countVops -= 3
        elif vop0.ID == 4 and\
             ((vop1.ID == 6 and vop3.ID == 0x169) or\
             (vop1.ID == 0x26 and vop3.ID == 0x16a) or\
             (vop1.ID == 0x160 and vop3.ID == 0x16b)) and\
             vop2.ID == 1 and vop0.pushval == vop3.pushval:
            vop0.ID = 1
            self.EraseVops(i + 1, 3)
            self.countVops -= 3
        elif vop0.ID == 9 and vop1.ID == 0x16f and vop2.ID in (0x169, 0x16a, 0x16b) and vop3.ID == 0x170:
            vop0.ID = 4
            if vop2.ID == 0x169:
                vop0.pushval = UINT(vop1.pushval - vop2.pushval)
            elif vop2.ID == 0x16a:
                vop0.pushval = UINT(vop1.pushval + vop2.pushval)
            elif vop2.ID == 0x16b:
                vop0.pushval = UINT(vop1.pushval ^ vop2.pushval)

            self.EraseVops(i + 1, 3)
            self.countVops -= 3
        elif vop0.ID == 4 and vop1.ID == 1 and vop2.ID in (0x169, 0x16a, 0x16b):
            if vop2.ID == 0x169:
                vop0.pushval = UINT(vop0.pushval - vop2.pushval)
            elif vop2.ID == 0x16a:
                vop0.pushval = UINT(vop0.pushval + vop2.pushval)
            elif vop2.ID == 0x16b:
                vop0.pushval = UINT(vop0.pushval ^ vop2.pushval)

            self.EraseVops(i + 2, 1)
            self.countVops -= 1
        elif vop0.ID == 9 and vop1.ID == 0x171:
            vop0.ID = 0x18
            self.EraseVops(i + 1, 1)
            self.countVops -= 1
        elif vop0.ID == 4 and vop1.ID == 4 and vop2.ID in (6, 0x26, 0x160) :
            if vop2.ID == 0x26:
                vop0.pushval = UINT(vop0.pushval - vop1.pushval)
            elif vop2.ID == 6:
                vop0.pushval = UINT(vop0.pushval + vop1.pushval)
            elif vop2.ID == 0x160:
                vop0.pushval = UINT(vop0.pushval ^ vop1.pushval)

            self.EraseVops(i + 1, 2)
            self.countVops -= 2
        elif vop0.ID == 4 and vop1.ID == 6 and vop2.ID == 1 and vop3.ID == 0x15e:
            vop0.fld2 = 1
            vop0.pushval = UINT(vop0.pushval + self.fld50)
            self.EraseVops(i + 3, 1)
            self.countVops -= 1
        elif vop0.ID == 4 and vop1.ID == 1 and vop2.ID == 0x15a and vop3.ID == 0x15e:
            vop0.fld2 = 1
            vop0.pushval = UINT(vop0.pushval + self.fld50)
            self.EraseVops(i + 3, 1)
            self.countVops -= 1
        elif vop0.ID == 4 and vop1.ID == 1 and vop2.ID == 0x15e:
            vop0.fld2 = 1
            vop0.pushval = UINT(vop0.pushval + self.fld50)
            self.EraseVops(i + 2, 1)
            self.countVops -= 1
        elif vop0.ID == 4 and vop1.ID == 0x15d:
            vop0.fld2 = 1
            vop0.pushval = UINT(vop0.pushval + self.fld50)
            self.EraseVops(i + 1, 1)
            self.countVops -= 1

    def DeOfus(self):
        print("DeOfus CISC-2 Vops...")
        while True:
            cnt = self.countVops
            i = 0
            while i < self.countVops:
                self.VopSimple(i)
                i += 1

            if cnt == self.countVops:
                break

        self.VopDump("{}/TXT/Cisc_Jk_Dump_{:08x}.txt".format(self.WrkDir, self.pushValue))

        self.RemoveJunk()

        self.VopDump("{}/TXT/Cisc_Vo_Syntax_{:08x}.txt".format(self.WrkDir, self.pushValue))

    def TRinit(self):
        if self.countVops <= 26:
            return

        self.TRNM = dict()
        self.TRID = dict()
        for i in range(8):
            self.TRID[i] = 0
            self.TRNM[i] = ""

        if self.Vops[0].pushval == 7:
            self.TRNM[self.Vops[0].pushval] = "VM_FLAGS"
            self.TRNM[self.Vops[3].pushval] = "VM_EDI"
            self.TRNM[self.Vops[6].pushval] = "VM_ESI"
            self.TRNM[self.Vops[9].pushval] = "VM_EBP"
            self.TRNM[self.Vops[12].pushval] = "VM_ESP"
            self.TRNM[self.Vops[16].pushval] = "VM_EBX"
            self.TRNM[self.Vops[19].pushval] = "VM_EDX"
            self.TRNM[self.Vops[22].pushval] = "VM_ECX"
            self.TRNM[self.Vops[25].pushval] = "VM_EAX"
            self.TRID[self.Vops[0].pushval] = 4
            self.TRID[self.Vops[3].pushval] = 7
            self.TRID[self.Vops[6].pushval] = 6
            self.TRID[self.Vops[9].pushval] = 5
            self.TRID[self.Vops[12].pushval] = 4
            self.TRID[self.Vops[16].pushval] = 3
            self.TRID[self.Vops[19].pushval] = 2
            self.TRID[self.Vops[22].pushval] = 1
            self.TRID[self.Vops[25].pushval] = 0
        else:
            self.TRNM[self.Vops[0].pushval] = "VM_EDI"
            self.TRNM[self.Vops[3].pushval] = "VM_ESI"
            self.TRNM[self.Vops[6].pushval] = "VM_EBP"
            self.TRNM[self.Vops[9].pushval] = "VM_ESP"
            self.TRNM[self.Vops[13].pushval] = "VM_EBX"
            self.TRNM[self.Vops[16].pushval] = "VM_EDX"
            self.TRNM[self.Vops[19].pushval] = "VM_ECX"
            self.TRNM[self.Vops[22].pushval] = "VM_EAX"
            self.TRNM[self.Vops[26].pushval] = "VM_FLAGS"
            self.TRID[self.Vops[0].pushval] = 7
            self.TRID[self.Vops[3].pushval] = 6
            self.TRID[self.Vops[6].pushval] = 5
            self.TRID[self.Vops[9].pushval] = 4
            self.TRID[self.Vops[13].pushval] = 3
            self.TRID[self.Vops[16].pushval] = 2
            self.TRID[self.Vops[19].pushval] = 1
            self.TRID[self.Vops[22].pushval] = 0
            self.TRID[self.Vops[26].pushval] = 4

    def RemoveJunk(self):
        while True:
            cnt = self.countVops
            i = 0
            while i < self.countVops:
                self.VopSimple(i)

                for jk in self.JUNK:
                    vop = self.Vops[i]
                    if len(jk.handler) > 0 and jk.handler[0] == vop.ID:
                        bv = False
                        for z, vid in enumerate(jk.handler):
                            if i + z >= self.countVops:
                                bv = True
                                break

                            zvop = self.Vops[i + z]
                            if vid == 0xFFFF or\
                              (vid == 0xFFFE and vid_22_d7(zvop.ID)) or\
                              (vid == 0xFFFD and vid_2c_2d_bb_ca(zvop.ID)) or\
                              zvop.ID == vid:
                                pass
                            else:
                                bv = True
                                break

                        if not bv:
                            if not jk.good:
                                self.EraseVops(i, len(jk.handler))
                                self.countVops -= len(jk.handler)
                                i -= 1
                            else:
                                adr = vop.addr
                                for z, idx in enumerate(jk.good):
                                    self.Vops[i + z] = self.Vops[i + idx]

                                self.Vops[i].addr = adr
                                self.EraseVops(i + len(jk.good), len(jk.handler) - len(jk.good))
                                self.countVops -= len(jk.handler) - len(jk.good)
                                i -= 1
                i += 1

            if cnt == self.countVops:
                break

    def VopDump(self, fname):
        self.TRinit()
        f = open(fname, "w")

        i = 0
        while i < self.countVops:
            spclSeq = 0
            vop = self.Vops[i]

            sfnd = None
            datavop = None

            for snt in self.SYNT:
                if len(snt.handler) > 0 and snt.handler[0] == vop.ID:
                    if len(snt.handler) == 4 and snt.handler[0] == 0 and snt.handler[1] == 4 and \
                       snt.handler[2] == 6 and snt.handler[3] in (1, 0x15):
                        spclSeq = 1
                    else:
                        spclSeq = 0

                    sfnd = snt
                    datavop = None
                    if not snt.handler:
                        break
                    else:
                        for z, vid in enumerate(snt.handler):
                            if i + z >= self.countVops:
                                sfnd = None
                                break

                            zvop = self.Vops[i + z]

                            if vid != zvop.ID:
                                sfnd = None
                                break

                            if self.IsHndlIDHasData(zvop.ID) == 1:
                                datavop = zvop

                        if sfnd:
                            break

            if sfnd:
                buf = "\t{:08X}\t".format(vop.addr)
                if snt.insx in self.INS:
                    buf += self.INS[snt.insx]
                buf += " "
                if snt.sufx in self.SUF:
                    buf += self.SUF[snt.sufx]

                if spclSeq:
                    datavop = vop

                if not datavop:
                    buf += "\n"
                    f.write(buf)
                else:
                    if datavop.ID in (0, 7, 0xe, 0xf, 0x1a, 0x158, 0x1b, 0x1c):
                        if datavop.pushval < 7:
                            if spclSeq:
                                buf += " ({}) [SPECIAL REGISTER]\n"
                            else:
                                buf += " ({})\n"
                            f.write(buf.format(datavop.pushval, self.TRNM[datavop.pushval]))
                        elif datavop.pushval == 7:
                            buf += " ({})\n"
                            f.write(buf.format(datavop.pushval,"FLAGS"))
                        else:
                            buf += "(Vm_Unk)\n"
                            f.write(buf.format(datavop.pushval,))
                    else:
                        buf += "\n"
                        f.write(buf.format(datavop.pushval,))


                i += len(snt.handler)
            else:
                if self.IsHndlIDHasData(vop.ID) == 1:
                    f.write("\t{:08X}\t{:04X}({:08X})\n".format(vop.addr, vop.ID, vop.pushval))
                else:
                    f.write("\t{:08X}\t{:04X}\n".format(vop.addr, vop.ID))

                i += 1

        f.close()

    def DeVirt(self, maxVopt):
        if self.fld50 & 0x80000000:
            self.fld50 = self.Align
        else:
            bt = GetBytes(UINT(self.ImageBase + self.fld50), 4)
            self.fld50 = GetDWORD(bt)

        self.AllocVops(maxVopt)
        LABELS.Init()
        LABELS.GetLabel(UINT(self.Align + self.pushValue), self.pushValue)

        print("")
        while True:
            l = LABELS.GetNextToProceed()
            if not l:
                break

            l.proceed = 1
            print("Reading label at {:08x}".format(l.addr))
            if not self.DumpVops(l.addr, l.pushVal):
                break

        print("")
        LABELS.Sort()
        self.SortVops()

        if self.dbg:
            f = open("{}/TXT/Cisc_Vo_Dump_{:08x}.txt".format(self.WrkDir, self.pushValue),"w")
            for i in range(self.countVops):
                v = self.Vops[i]
                if i % 8 == 0:
                    f.write("\n{:08X}\t".format(v.addr))
                if v.pushval == 0:
                    f.write("{:04X} ".format(v.ID))
                else:
                    f.write("{:04X}({:08X}) ".format(v.ID, v.pushval))
            f.close()

        self.DeOfus()
        self.UvDump()

    def CheckVopSeq(self, i, seq):
        if i + len(seq) > self.countVops:
            return False
        for j, v in enumerate(seq):
            if isinstance(v, (int, long)):
                if v != -1 and self.Vops[i + j].ID != v:
                    return False
            elif self.Vops[i + j].ID not in v:
                return False
        return True

    def PreUv(self):
        i = 0
        while i < self.countVops:
            vp = self.Vops
            if i + 33 <= self.countVops:
                if self.CheckVopSeq(i, (0,1,0x18, 0,1,0x18, 0,1,0x18, 0,1,0x18, # 0 3 6 9
                                               0x157, # 12
                                               0,1,0x18, 0,1,0x18, 0,1,0x18, 0,1,0x18, 0,1,0x18, # 13 16 19 22 25
                                               #28   29 30 31  32
                                               0x14e, 9, 4, 6, 0x152)) and\
                      vp[i + 30].pushval == 4:
                    self.EraseVops(i, 33)
                    self.countVops -= 33
                    i -= 1
                elif self.CheckVopSeq(i, (0,1,0x18, 0,1,0x18, 0,1,0x18, 0,1,0x18, 0,1,0x18, # 0 3 6 9 12
                                               0x157, #15
                                               0,1,0x18, 0,1,0x18, 0,1,0x18, 0,1,0x18, # 16 19 22 25
                                               #28   29 30 31  32
                                               0x14e, 9, 4, 6, 0x152)) and\
                      vp[i + 30].pushval == 4:
                    self.EraseVops(i, 33)
                    self.countVops -= 33
                    i -= 1
            elif i + 28 <= self.countVops:
                if self.CheckVopSeq(i, (0,1,0xc, 0,1,0xc, 0,1,0xc, 0,1,0xc, 0,1,0xc, # 0 3 6 9 12
                                        0,1,0xc, 0,1,0xc, 0,1,0xc, 0,1,0xc, # 15 18 21 24
                                        0x14a)): #27
                    self.vpaddr = vp[i].addr
                    self.EraseVops(i, 28)
                    self.countVops -= 28
                    i -= 1
            i += 1

    def VopAsm(self, i, rk):
        if rk:
            rk.Clear()

        vp = self.Vops

        if i + 67 <= self.countVops and self.CheckVopSeq(i, \
             (0x155, 0x156, 7, 1, 9, 4, 0x26, 1, 9, 0x1c, #0
                  7, 1, 0xc, 7, 1, 0xc, 0x39, 0x155, 0x156, 7, #10
                  1, 9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, #20
                  7, 1, 9, 4, 0x26, 1, 9, 0, 1, 0x18, #30
                  0x155, 0x156, 7, 1, 9, 4, 6, 1, 9, 0, #40
                  1, 0x18, 0x154, 7, 1, 9, 4, 0x26, 1, 9, #50
                  0, 1, 0x18, 0x173, 0x155, 0x156, 0x154 )):
            if rk:
                rk.opfx = 0xf3 - ((vp[i + 64].pushval & 0xFFFFFF00) != 0x800)
                rk.op66 = 0
                rk.ID = OP_CMPS
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, 0x63)
                rk.operand[1].ID = 0x33
                rk.operand[1].SetB(1, 0x73)
            return 67
        elif i + 67 <= self.countVops and self.CheckVopSeq(i, \
          (0x155, 0x156, 7, 1, 9, 4, 0x26, 1, 9, 0x1c,  #0
               7, 1, 0xb, 7, 1, 0xb, 0x38, 0x155, 0x156, 7,  #10
               1, 9, 4, 6, 1, 9, 0, 1, 0x18, 0x154,  # 20
               7, 1, 9, 4, 0x26, 1, 9, 0, 1, 0x18,  # 30
               0x155, 0x156, 7, 1, 9, 4, 6, 1, 9, 0,  # 40
               1, 0x18, 0x154, 7, 1, 9, 4, 0x26, 1, 9,  # 50
               0, 1, 0x18, 0x173, 0x155, 0x156, 0x154)):
            if rk:
                rk.opfx = 0xf3 - ((vp[i + 64].pushval & 0xFFFFFF00) != 0x800)
                rk.op66 = 0x66
                rk.ID = OP_CMPS
                rk.operand[0].ID = 0x32
                rk.operand[0].SetB(1, 0x63)
                rk.operand[1].ID = 0x32
                rk.operand[1].SetB(1, 0x73)
            return 67
        elif i + 67 <= self.countVops and self.CheckVopSeq(i, \
          (0x155, 0x156, 7, 1, 9, 4, 0x26, 1, 9, 0x1c,  #0
               7, 1, 0xa, 7, 1, 0xa, 0x37, 0x155, 0x156, 7,  #10
               1, 9, 4, 6, 1, 9, 0, 1, 0x18, 0x154,  # 20
               7, 1, 9, 4, 0x26, 1, 9, 0, 1, 0x18,  # 30
               0x155, 0x156, 7, 1, 9, 4, 6, 1, 9, 0,  # 40
               1, 0x18, 0x154, 7, 1, 9, 4, 0x26, 1, 9,  # 50
               0, 1, 0x18, 0x173, 0x155, 0x156, 0x154)):
            if rk:
                rk.opfx = 0xf3 - ((vp[i + 64].pushval & 0xFFFFFF00) != 0x800)
                rk.op66 = 0
                rk.ID = OP_CMPS
                rk.operand[0].ID = 0x31
                rk.operand[0].SetB(1, 0x63)
                rk.operand[1].ID = 0x31
                rk.operand[1].SetB(1, 0x73)
            return 67
        elif i + 63 <= self.countVops and self.CheckVopSeq(i, \
        (0x155, 0x156, 7, 1, 9, 4, 0x26, 1, 9, 0x1c,  # 0
             7, 1, 0xc, 7, 1, 0x18, 0x155, 0x156, 7, 1,  # 10
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7, # 20
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18, 0x155,  # 30
             0x156, 7, 1, 9, 4, 6, 1, 9, 0, 1,  # 40
             0x18, 0x154, 7, 1, 9, 4, 0x26, 1, 9, 0, # 50
             1, 0x18, 0x154)):
            if rk:
                rk.opfx = 0xf3
                rk.op66 = 0
                rk.ID = OP_MOVS
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, 0x73)
                rk.operand[1].ID = 0x33
                rk.operand[1].SetB(1, 0x63)
            return 63
        elif i + 63 <= self.countVops and self.CheckVopSeq(i, \
        (0x155, 0x156, 7, 1, 9, 4, 0x26, 1, 9, 0x1c,  # 0
             7, 1, 0xb, 7, 1, 0x17, 0x155, 0x156, 7, 1,  # 10
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7, # 20
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18, 0x155,  # 30
             0x156, 7, 1, 9, 4, 6, 1, 9, 0, 1,  # 40
             0x18, 0x154, 7, 1, 9, 4, 0x26, 1, 9, 0, # 50
             1, 0x18, 0x154)):
            if rk:
                rk.opfx = 0xf3
                rk.op66 = 0x66
                rk.ID = OP_MOVS
                rk.operand[0].ID = 0x32
                rk.operand[0].SetB(1, 0x73)
                rk.operand[1].ID = 0x32
                rk.operand[1].SetB(1, 0x63)
            return 63
        elif i + 63 <= self.countVops and self.CheckVopSeq(i, \
        (0x155, 0x156, 7, 1, 9, 4, 0x26, 1, 9, 0x1c,  # 0
             7, 1, 0xa, 7, 1, 0x16, 0x155, 0x156, 7, 1,  # 10
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7, # 20
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18, 0x155,  # 30
             0x156, 7, 1, 9, 4, 6, 1, 9, 0, 1,  # 40
             0x18, 0x154, 7, 1, 9, 4, 0x26, 1, 9, 0, # 50
             1, 0x18, 0x154)):
            if rk:
                rk.opfx = 0xf3
                rk.op66 = 0
                rk.ID = OP_MOVS
                rk.operand[0].ID = 0x31
                rk.operand[0].SetB(1, 0x73)
                rk.operand[1].ID = 0x31
                rk.operand[1].SetB(1, 0x63)
            return 63
        elif i + 44 <= self.countVops and self.CheckVopSeq(i, \
          (0x155, 0x156, 7, 1, 9, 4, 0x26, 1, 9, 0x1c,  # 0
               0, 1, 0xc, 7, 1, 0xc, 0x39, 0x155, 0x156, 7,  # 10
               1, 9, 4, 6, 1, 9, 0, 1, 0x18, 0x154,  # 20
               7, 1, 9, 4, 0x26, 1, 9, 0, 1, 0x18,  # 30
               0x173, 0x155, 0x156, 0x154)):
            if rk:
                rk.opfx = 0xf3 - ((vp[i + 41].pushval & 0xFFFFFF00) != 0x800)
                rk.op66 = 0
                rk.ID = OP_SCAS
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, 0x73)
            return 44
        elif i + 44 <= self.countVops and self.CheckVopSeq(i, \
          (0x155, 0x156, 7, 1, 9, 4, 0x26, 1, 9, 0x1c,  # 0
               0, 1, 0xb, 7, 1, 0xb, 0x38, 0x155, 0x156, 7,  # 10
               1, 9, 4, 6, 1, 9, 0, 1, 0x18, 0x154,  # 20
               7, 1, 9, 4, 0x26, 1, 9, 0, 1, 0x18,  # 30
               0x173, 0x155, 0x156, 0x154)):
            if rk:
                rk.opfx = 0xf3 - ((vp[i + 41].pushval & 0xFFFFFF00) != 0x800)
                rk.op66 = 0x66
                rk.ID = OP_SCAS
                rk.operand[0].ID = 0x32
                rk.operand[0].SetB(1, 0x73)
            return 44
        elif i + 44 <= self.countVops and self.CheckVopSeq(i, \
          (0x155, 0x156, 7, 1, 9, 4, 0x26, 1, 9, 0x1c,  # 0
               0, 1, 0xa, 7, 1, 0xa, 0x37, 0x155, 0x156, 7,  # 10
               1, 9, 4, 6, 1, 9, 0, 1, 0x18, 0x154,  # 20
               7, 1, 9, 4, 0x26, 1, 9, 0, 1, 0x18,  # 30
               0x173, 0x155, 0x156, 0x154)):
            if rk:
                rk.opfx = 0xf3 - ((vp[i + 41].pushval & 0xFFFFFF00) != 0x800)
                rk.op66 = 0
                rk.ID = OP_SCAS
                rk.operand[0].ID = 0x31
                rk.operand[0].SetB(1, 0x73)
            return 44
        elif i + 40 <= self.countVops and self.CheckVopSeq(i, \
        (0x155, 0x156, 7, 1, 9, 4, 0x26, 1, 9, 0x1c,  # 0
             7, 1, 0xc, 0, 1, 0x18, 0x155, 0x156, 7, 1,  # 10
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7, # 20
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18, 0x154)):
            if rk:
                rk.opfx = 0xf3
                rk.op66 = 0
                rk.ID = OP_LODS
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, 0x63)
            return 40
        elif i + 40 <= self.countVops and self.CheckVopSeq(i, \
        (0x155, 0x156, 7, 1, 9, 4, 0x26, 1, 9, 0x1c,  # 0
             7, 1, 0xb, 0, 1, 0x17, 0x155, 0x156, 7, 1,  # 10
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7, # 20
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18, 0x154)):
            if rk:
                rk.opfx = 0xf3
                rk.op66 = 0x66
                rk.ID = OP_LODS
                rk.operand[0].ID = 0x32
                rk.operand[0].SetB(1, 0x63)
            return 40
        elif i + 40 <= self.countVops and self.CheckVopSeq(i, \
        (0x155, 0x156, 7, 1, 9, 4, 0x26, 1, 9, 0x1c,  # 0
             7, 1, 0xa, 0, 1, 0x16, 0x155, 0x156, 7, 1,  # 10
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7, # 20
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18, 0x154)):
            if rk:
                rk.opfx = 0xf3
                rk.op66 = 0
                rk.ID = OP_LODS
                rk.operand[0].ID = 0x31
                rk.operand[0].SetB(1, 0x63)
            return 40
        elif i + 40 <= self.countVops and self.CheckVopSeq(i, \
        (0x155, 0x156, 7, 1, 9, 4, 0x26, 1, 9, 0x1c,  # 0
             0, 1, 0xc, 7, 1, 0x18, 0x155, 0x156, 7, 1,  # 10
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7, # 20
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18, 0x154)):
            if rk:
                rk.opfx = 0xf3
                rk.op66 = 0
                rk.ID = OP_STOS
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, 0x73)
            return 40
        elif i + 40 <= self.countVops and self.CheckVopSeq(i, \
        (0x155, 0x156, 7, 1, 9, 4, 0x26, 1, 9, 0x1c,  # 0
             0, 1, 0xb, 7, 1, 0x17, 0x155, 0x156, 7, 1,  # 10
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7, # 20
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18, 0x154)):
            if rk:
                rk.opfx = 0xf3
                rk.op66 = 0x66
                rk.ID = OP_STOS
                rk.operand[0].ID = 0x32
                rk.operand[0].SetB(1, 0x73)
            return 40
        elif i + 40 <= self.countVops and self.CheckVopSeq(i, \
        (0x155, 0x156, 7, 1, 9, 4, 0x26, 1, 9, 0x1c,  # 0
             0, 1, 0xa, 7, 1, 0x16, 0x155, 0x156, 7, 1,  # 10
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7, # 20
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18, 0x154)):
            if rk:
                rk.opfx = 0xf3
                rk.op66 = 0
                rk.ID = OP_STOS
                rk.operand[0].ID = 0x31
                rk.operand[0].SetB(1, 0x73)
            return 40
        elif i + 53 <= self.countVops and self.CheckVopSeq(i, \
        (7, 1, 0xc, 7, 1, 0xc, 0x39, 0x155, 0x156, 7, #0
             1, 9, 4, 6, 1, 9, 0, 1, 0x18, 0x154,  #10
             7, 1, 9, 4, 0x26, 1, 9, 0, 1, 0x18,  # 20
             0x155, 0x156, 7, 1, 9, 4, 6, 1, 9, 0, # 30
             1, 0x18, 0x154, 7, 1, 9, 4, 0x26, 1, 9, #40
             0, 1, 0x18)):
            if rk:
                rk.opfx = 0
                rk.op66 = 0
                rk.ID = OP_CMPS
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, 0x63)
                rk.operand[1].ID = 0x33
                rk.operand[1].SetB(1, 0x73)
            return 53
        elif i + 53 <= self.countVops and self.CheckVopSeq(i, \
        (7, 1, 0xb, 7, 1, 0xb, 0x38, 0x155, 0x156, 7, #0
             1, 9, 4, 6, 1, 9, 0, 1, 0x18, 0x154,  #10
             7, 1, 9, 4, 0x26, 1, 9, 0, 1, 0x18,  # 20
             0x155, 0x156, 7, 1, 9, 4, 6, 1, 9, 0, # 30
             1, 0x18, 0x154, 7, 1, 9, 4, 0x26, 1, 9, #40
             0, 1, 0x18)):
            if rk:
                rk.opfx = 0
                rk.op66 = 0x66
                rk.ID = OP_CMPS
                rk.operand[0].ID = 0x32
                rk.operand[0].SetB(1, 0x63)
                rk.operand[1].ID = 0x32
                rk.operand[1].SetB(1, 0x73)
            return 53
        elif i + 53 <= self.countVops and self.CheckVopSeq(i, \
        (7, 1, 0xa, 7, 1, 0xa, 0x37, 0x155, 0x156, 7, #0
             1, 9, 4, 6, 1, 9, 0, 1, 0x18, 0x154,  #10
             7, 1, 9, 4, 0x26, 1, 9, 0, 1, 0x18,  # 20
             0x155, 0x156, 7, 1, 9, 4, 6, 1, 9, 0, # 30
             1, 0x18, 0x154, 7, 1, 9, 4, 0x26, 1, 9, #40
             0, 1, 0x18)):
            if rk:
                rk.opfx = 0
                rk.op66 = 0
                rk.ID = OP_CMPS
                rk.operand[0].ID = 0x31
                rk.operand[0].SetB(1, 0x63)
                rk.operand[1].ID = 0x31
                rk.operand[1].SetB(1, 0x73)
            return 53
        elif i + 52 <= self.countVops and self.CheckVopSeq(i, \
        (7, 1, 0xc, 7, 1, 0x18, 0x155, 0x156, 7, 1, #0
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7,  #10
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18, 0x155,  # 20
             0x156, 7, 1, 9, 4, 6, 1, 9, 0, 1, # 30
             0x18, 0x154, 7, 1, 9, 4, 0x26, 1, 9, 0, #40
             1, 0x18)):
            if rk:
                rk.opfx = 0
                rk.op66 = 0
                rk.ID = OP_MOVS
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, 0x73)
                rk.operand[1].ID = 0x33
                rk.operand[1].SetB(1, 0x63)
            return 52
        elif i + 52 <= self.countVops and self.CheckVopSeq(i, \
        (7, 1, 0xb, 7, 1, 0x17, 0x155, 0x156, 7, 1, #0
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7,  #10
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18, 0x155,  # 20
             0x156, 7, 1, 9, 4, 6, 1, 9, 0, 1, # 30
             0x18, 0x154, 7, 1, 9, 4, 0x26, 1, 9, 0, #40
             1, 0x18)):
            if rk:
                rk.opfx = 0
                rk.op66 = 0x66
                rk.ID = OP_MOVS
                rk.operand[0].ID = 0x32
                rk.operand[0].SetB(1, 0x73)
                rk.operand[1].ID = 0x32
                rk.operand[1].SetB(1, 0x63)
            return 52
        elif i + 52 <= self.countVops and self.CheckVopSeq(i, \
        (7, 1, 0xa, 7, 1, 0x16, 0x155, 0x156, 7, 1, #0
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7,  #10
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18, 0x155,  # 20
             0x156, 7, 1, 9, 4, 6, 1, 9, 0, 1, # 30
             0x18, 0x154, 7, 1, 9, 4, 0x26, 1, 9, 0, #40
             1, 0x18)):
            if rk:
                rk.opfx = 0
                rk.op66 = 0
                rk.ID = OP_MOVS
                rk.operand[0].ID = 0x31
                rk.operand[0].SetB(1, 0x73)
                rk.operand[1].ID = 0x31
                rk.operand[1].SetB(1, 0x63)
            return 52
        elif i + 30 <= self.countVops and self.CheckVopSeq(i, \
        (0, 1, 0xc, 7, 1, 0xc, 0x39, 0x155, 0x156, 7, #0
             1, 9, 4, 6, 1, 9, 0, 1, 0x18, 0x154,  #10
             7, 1, 9, 4, 0x26, 1, 9, 0, 1, 0x18)):
            if rk:
                rk.opfx = 0
                rk.op66 = 0
                rk.ID = OP_SCAS
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, 0x73)
            return 30
        elif i + 30 <= self.countVops and self.CheckVopSeq(i, \
        (0, 1, 0xb, 7, 1, 0xb, 0x38, 0x155, 0x156, 7, #0
             1, 9, 4, 6, 1, 9, 0, 1, 0x18, 0x154,  #10
             7, 1, 9, 4, 0x26, 1, 9, 0, 1, 0x18)):
            if rk:
                rk.opfx = 0
                rk.op66 = 0x66
                rk.ID = OP_SCAS
                rk.operand[0].ID = 0x32
                rk.operand[0].SetB(1, 0x73)
            return 30
        elif i + 30 <= self.countVops and self.CheckVopSeq(i, \
        (0, 1, 0xa, 7, 1, 0xa, 0x37, 0x155, 0x156, 7, #0
             1, 9, 4, 6, 1, 9, 0, 1, 0x18, 0x154,  #10
             7, 1, 9, 4, 0x26, 1, 9, 0, 1, 0x18)):
            if rk:
                rk.opfx = 0
                rk.op66 = 0
                rk.ID = OP_SCAS
                rk.operand[0].ID = 0x31
                rk.operand[0].SetB(1, 0x73)
            return 30
        elif i + 29 <= self.countVops and self.CheckVopSeq(i, \
        (7, 1, 0xc, 0, 1, 0x18, 0x155, 0x156, 7, 1, #0
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7,  #10
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18)):
            if rk:
                rk.opfx = 0
                rk.op66 = 0
                rk.ID = OP_LODS
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, 0x63)
            return 29
        elif i + 29 <= self.countVops and self.CheckVopSeq(i, \
        (7, 1, 0xb, 0, 1, 0x17, 0x155, 0x156, 7, 1, #0
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7,  #10
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18)):
            if rk:
                rk.opfx = 0
                rk.op66 = 0x66
                rk.ID = OP_LODS
                rk.operand[0].ID = 0x32
                rk.operand[0].SetB(1, 0x63)
            return 29
        elif i + 29 <= self.countVops and self.CheckVopSeq(i, \
        (7, 1, 0xa, 0, 1, 0x16, 0x155, 0x156, 7, 1, #0
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7,  #10
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18)):
            if rk:
                rk.opfx = 0
                rk.op66 = 0
                rk.ID = OP_LODS
                rk.operand[0].ID = 0x31
                rk.operand[0].SetB(1, 0x63)
            return 29
        elif i + 29 <= self.countVops and self.CheckVopSeq(i, \
        (0, 1, 0xc, 7, 1, 0x18, 0x155, 0x156, 7, 1, #0
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7,  #10
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18)):
            if rk:
                rk.opfx = 0
                rk.op66 = 0
                rk.ID = OP_STOS
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, 0x73)
            return 29
        elif i + 29 <= self.countVops and self.CheckVopSeq(i, \
        (0, 1, 0xb, 7, 1, 0x17, 0x155, 0x156, 7, 1, #0
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7,  #10
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18)):
            if rk:
                rk.opfx = 0
                rk.op66 = 0x66
                rk.ID = OP_STOS
                rk.operand[0].ID = 0x32
                rk.operand[0].SetB(1, 0x73)
            return 29
        elif i + 29 <= self.countVops and self.CheckVopSeq(i, \
        (0, 1, 0xa, 7, 1, 0x16, 0x155, 0x156, 7, 1, #0
             9, 4, 6, 1, 9, 0, 1, 0x18, 0x154, 7,  #10
             1, 9, 4, 0x26, 1, 9, 0, 1, 0x18)):
            if rk:
                rk.opfx = 0
                rk.op66 = 0
                rk.ID = OP_STOS
                rk.operand[0].ID = 0x31
                rk.operand[0].SetB(1, 0x73)
            return 29
        elif i + 7 <= self.countVops and self.CheckVopSeq(i, \
             (7, 1, 0x153, 0x15a, 0x7b, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, (self.TRID[ vp[i].pushval ] << 4) | 3) #7
                rk.operand[0].SetB(2, (self.TRID[ vp[i + 2].pushval ] << 4) | 3) #0x153
            return 7
        elif i + 7 <= self.countVops and self.CheckVopSeq(i, \
             (7, 1, 0x153, 0x15a, 0xa3, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, (self.TRID[ vp[i].pushval ] << 4) | 3) #7
                rk.operand[0].SetB(2, (self.TRID[ vp[i + 2].pushval ] << 4) | 3) #0x153
            return 7
        elif i + 11 <= self.countVops and self.CheckVopSeq(i, \
             (7, 1, 0x153, 9, 4, 6, 1, 0x15a, 0x7b, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, (self.TRID[ vp[i].pushval ] << 4) | 3) #7
                rk.operand[0].SetB(2, (self.TRID[ vp[i + 2].pushval ] << 4) | 3) #0x153
                rk.operand[0].val2 = vp[i + 4].pushval
            return 11
        elif i + 11 <= self.countVops and self.CheckVopSeq(i, \
             (7, 1, 0x153, 9, 4, 6, 1, 0x15a, 0xa3, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, (self.TRID[ vp[i].pushval ] << 4) | 3) #7
                rk.operand[0].SetB(2, (self.TRID[ vp[i + 2].pushval ] << 4) | 3) #0x153
                rk.operand[0].val2 = vp[i + 4].pushval
            return 11
        elif i + 9 <= self.countVops and self.CheckVopSeq(i, \
             (0x14e, 9, 4, 6, 1, 0x15a, 0x7b, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, 0x43)
                rk.operand[0].val2 = vp[i + 2].pushval
            return 9
        elif i + 9 <= self.countVops and self.CheckVopSeq(i, \
             (0x14e, 9, 4, 6, 1, 0x15a, 0xa3, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, 0x43)
                rk.operand[0].val2 = vp[i + 2].pushval
            return 9
        elif i + 14 <= self.countVops and self.CheckVopSeq(i, \
             (7, 1, 9, 4, 0x15f, 1, 0, 4, 6, 1,     0x15a, 0x7b, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(2, (self.TRID[ vp[i].pushval ] << 4) | 3) #7
                rk.operand[0].SetB(3, vp[i + 3].pushval & 0xFF ) #4
                rk.operand[0].val2 = vp[i + 7].pushval
            return 14
        elif i + 14 <= self.countVops and self.CheckVopSeq(i, \
             (7, 1, 9, 4, 0x15f, 1, 0, 4, 6, 1,     0x15a, 0xa3, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(2, (self.TRID[ vp[i].pushval ] << 4) | 3) #7
                rk.operand[0].SetB(3, vp[i + 3].pushval & 0xFF ) #4
                rk.operand[0].val2 = vp[i + 7].pushval
            return 14
        elif i + 10 <= self.countVops and self.CheckVopSeq(i, \
             (7, 1, 9, 4, 6, 1, 0x15a, 0x7b, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, (self.TRID[ vp[i].pushval ] << 4) | 3) #7
                rk.operand[0].val2 = vp[i + 3].pushval
            return 10
        elif i + 10 <= self.countVops and self.CheckVopSeq(i, \
             (7, 1, 9, 4, 6, 1, 0x15a, 0xa3, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, (self.TRID[ vp[i].pushval ] << 4) | 3) #7
                rk.operand[0].val2 = vp[i + 3].pushval
            return 10
        elif i + 10 <= self.countVops and self.CheckVopSeq(i, \
             (7, 1, 9, 4, 0x15f, 1, 0x15a, 0x7b, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(2, (self.TRID[vp[i].pushval] << 4) | 3)  # 7
                rk.operand[0].SetB(3, vp[i + 3].pushval & 0xFF)  # 4
            return 10
        elif i + 10 <= self.countVops and self.CheckVopSeq(i, \
             (7, 1, 9, 4, 0x15f, 1, 0x15a, 0xa3, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(2, (self.TRID[vp[i].pushval] << 4) | 3)  # 7
                rk.operand[0].SetB(3, vp[i + 3].pushval & 0xFF)  # 4
            return 10
        elif i + 6 <= self.countVops and self.CheckVopSeq(i, \
             (7, 1, 0x15a, 0x7b, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, (self.TRID[vp[i].pushval] << 4) | 3)  # 7
            return 6
        elif i + 6 <= self.countVops and self.CheckVopSeq(i, \
             (7, 1, 0x15a, 0xa3, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x33
                rk.operand[0].SetB(1, (self.TRID[vp[i].pushval] << 4) | 3)  # 7
            return 6
        elif i + 6 <= self.countVops and self.CheckVopSeq(i, \
             (4, 1, 0x15a, 0x7b, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x33
                rk.operand[0].val2 = vp[i].pushval
            return 6
        elif i + 6 <= self.countVops and self.CheckVopSeq(i, \
             (4, 1, 0x15a, 0xa3, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x33
                rk.operand[0].val2 = vp[i].pushval
            return 6
        elif i + 6 <= self.countVops and self.CheckVopSeq(i, \
             (0, 1, 0x15a, 0x7b, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x10
                rk.operand[0].SetB(0, (self.TRID[vp[i].pushval] << 4) | 3)
            return 6
        elif i + 6 <= self.countVops and self.CheckVopSeq(i, \
             (0, 1, 0x15a, 0xa3, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x10
                rk.operand[0].SetB(0, (self.TRID[vp[i].pushval] << 4) | 3)
            return 6
        elif i + 5 <= self.countVops and self.CheckVopSeq(i, \
             (0x14e, 0x15a, 0x7b, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x10
                rk.operand[0].SetB(0, 0x43)
            return 5
        elif i + 5 <= self.countVops and self.CheckVopSeq(i, \
             (0x14e, 0x15a, 0xa3, 0xc, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x10
                rk.operand[0].SetB(0, 0x43)
            return 5
        elif i + 6 <= self.countVops and self.CheckVopSeq(i, \
             (4, 1, 0x15a, 0x7b, 9, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x23
                rk.operand[0].val2 = vp[i].pushval
                rk.operand[0].value = vp[i].pushval
            return 6
        #### INVALID?
        elif i + 6 <= self.countVops and self.CheckVopSeq(i, \
             (4, 1, 0x15a, 0xa3, 9, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x23
                rk.operand[0].val2 = vp[i].pushval
                rk.operand[0].value = vp[i].pushval
            return 6
        #### INVALID?
        elif i + 5 <= self.countVops and self.CheckVopSeq(i, \
             (4, 1, 0x15a, 9, 0x154)):
            if rk:
                rk.ID = OP_CALL
                rk.operand[0].ID = 0x23
                rk.operand[0].val2 = vp[i].pushval
                rk.operand[0].value = vp[i].pushval
            return 5
        elif i + 6 <= self.countVops and self.CheckVopSeq(i, \
             (4, 1, 9, 0x155, 0x156, 1)):
            if rk:
                rk.ID = XrkAsm.MnemToOP(  self.GetJxx(vp[i + 3].pushval)  )
                rk.operand[0].ID = 0x23
                rk.operand[0].val2 = vp[i].pushval
                rk.operand[0].value = vp[i].pushval
            return 6
        elif i + 4 <= self.countVops and self.CheckVopSeq(i, \
             (4, 1, 9, 0x154)):
            if rk:
                rk.ID = OP_JMP
                rk.operand[0].ID = 0x23
                rk.operand[0].val2 = vp[i].pushval
                rk.operand[0].value = vp[i].pushval
            return 4
        elif i + 4 <= self.countVops and self.CheckVopSeq(i, \
             (4, 1, 0x155, 0x156)):
            if rk:
                rk.ID = XrkAsm.MnemToOP(  self.GetJxx(vp[i + 2].pushval)  )
                rk.operand[0].ID = 0x23
                rk.operand[0].val2 = 0
                rk.operand[0].value = vp[i + 3].pushval
                vp[i].addr = vp[i + 3].addr
            return 4
        elif i + 3 <= self.countVops and self.CheckVopSeq(i, \
             (4, 1, 0x154)):
            if rk:
                rk.ID = OP_JMP
                rk.operand[0].ID = 0x23
                rk.operand[0].val2 = 0
                rk.operand[0].value = vp[i + 2].pushval
                vp[i].addr = vp[i + 2].addr
            return 3
        elif i + 2 <= self.countVops and self.CheckVopSeq(i, \
             (0x155, 0x156)):
            if rk:
                rk.ID = XrkAsm.MnemToOP(  self.GetJxx(vp[i].pushval)  )
                rk.operand[0].ID = 0x23
                rk.operand[0].val2 = 0
                rk.operand[0].value = vp[i + 1].pushval
                vp[i].addr = vp[i + 1].addr
            return 2
        elif i + 2 <= self.countVops and self.CheckVopSeq(i, \
             (0x15a, 0x154)):
            if rk:
                mm = self.GetMM(vp[i].valign)
                _,t = XrkDecode(mm)
                rk.CopyFrom(t)
            return 2
        elif i + 2 <= self.countVops and self.CheckVopSeq(i, \
             (4, 0x154)) and\
              vp[i+1].addr + 5 + vp[i+1].pushval == self.vpaddr:
            if rk:
                rk.ID = OP_JMP
                rk.operand[0].ID = 0x23
                rk.operand[0].val2 = vp[i].pushval
                rk.operand[0].value = vp[i].pushval
                vp[i].addr = vp[i + 1].addr
            return 2
        elif i + 2 <= self.countVops and self.CheckVopSeq(i, \
             (0x168, 0x154)) and\
              vp[i+1].addr + 5 + vp[i+1].pushval == self.vpaddr:
            if rk:
                rk.ID = OP_RETN
                rk.operand[0].ID = 0x22
                rk.operand[0].value = vp[i].pushval
                vp[i].addr = vp[i + 1].addr
            return 2
        elif i + 1 <= self.countVops and vp[i].ID == 0x154 and\
              vp[i].addr + 5 + vp[i].pushval == self.vpaddr:
            if rk:
                rk.ID = OP_RETN
            return 1
        elif i + 1 <= self.countVops and vp[i].ID == 0x154:
            if rk:
                rk.ID = OP_JMP
                rk.operand[0].ID = 0x23
                rk.operand[0].value = vp[i].pushval
                rk.operand[0].val2 = 0
            return 1
        return 0


    def GetJxx(self, val):
        jcc = {0x200:"JNB", 0x300:"JB", 0x800:"JNZ", 0xa00:"JA", 0xc00:"JE", 0xf00:"JBE",\
               0x2000:"JNS", 0x3000:"JS", 0x8000:"JNO", 0xc000:"JO",\
               0x20000:"JNP", 0x30000:"JP", 0x80000:"JGE", 0x80800:"JG", 0xc0000:"JL", 0xc0c00:"JLE",\
               0x200000:"JCXZ", 0x800000:"JECXZ"}
        v = val & 0xFFFFFF00
        if v not in jcc:
            return "JCC"
        return jcc[v]

    def UvDump(self):
        CMDSimpler.Clear()
        self.PreUv()
        f = open("{}/TXT/Cisc_Uv_Dump_{:08x}.txt".format(self.WrkDir, self.pushValue),"w")

        i = 0
        while i < self.countVops:
            vp = self.Vops

            lbl = LABELS.GetLabelNotPrinted(vp[i].addr)
            if lbl:
                f.write("\n\n@Label_{:08x}\n".format(lbl.addr))
                lbl.printed = True

            ln = self.VopAsm(i, None)

            casm = None
            stdmnem = False
            bv4 = False
            bv3 = False
            bv2 = False
            cv5 = 0
            sz = -1
            notThis = True
            stdID = -1
            loc30 = 0

            if ln == 0:
                for csm in self.ASM:
                    if not csm.handlers or csm.handlers[0] != vp[i].ID:
                        continue


                    casm = csm
                    stdmnem = False
                    bv4 = False
                    bv3 = False
                    bv2 = False
                    cv5 = 0
                    sz = -1
                    notThis = False
                    stdID = -1

                    for z, vid in enumerate(csm.handlers):
                        if i + z >= self.countVops:
                            notThis = True
                            casm = None
                            break

                        zvop = vp[i + z]
                        if vid in (0xFFFE, 0xFFFD):
                            if vid == 0xFFFD and not vid_2c_2d_bb_ca(zvop.ID):
                                notThis = True
                                casm = None
                                break

                            if not vid_22_d7(zvop.ID) or self.StdMnem(zvop.ID) == "":
                                notThis = True
                                casm = None
                                break

                            stdmnem = True
                            stdID = zvop.ID
                            if zvop.ID in (0x37, 0x38, 0x39, 0x3a,  0x43, 0x44, 0x45, 0x46):
                                bv2 = True
                            if zvop.ID in (0x80, 0x81, 0x85, 0x48, 0x49, 0x4d):
                                bv4 = True
                        else:
                            if (zvop.ID == 0x162 and vid == 0xa) or \
                               (zvop.ID == 0x163 and vid == 0xb) or \
                               (zvop.ID == 0x164 and vid == 0xc) or \
                               (zvop.ID == 0x165 and vid == 0x16) or \
                               (zvop.ID == 0x166 and vid == 0x17) or \
                               (zvop.ID == 0x167 and vid == 0x18):
                                cv5 = True
                                break

                            if vid != zvop.ID:
                                if zvop.ID == 2 and   vp[i + 1 + z].ID in self.C2D0 and   vid in (3, 4):
                                    bv3 = True
                                elif zvop.ID == 10 and   vp[i + 1 + z].ID in self.C2D0 and  vid in (0xb, 0xc):
                                    bv3 = True
                                else:
                                    notThis = True
                                    casm = None
                                    break
                            if bv2 and zvop.ID == 0x1C:
                                sz = z + 1
                                break

                    if not notThis:
                        break

            loc48 = 0
            if stdmnem:
                loc48 = XrkAsm.MnemToOP( self.StdMnem(stdID) )
            elif casm:
                loc48 = XrkAsm.MnemToOP( casm.mnem )

            #if notThis or (loc48 == 0 and ln == 0):
            if notThis and ln == 0 and loc48 == 0:
                if self.IsHndlIDHasData(vp[i].ID):
                    f.write("\t{:08X}\t{:04X}({:08X})\n".format(vp[i].addr, vp[i].ID, vp[i].pushval))
                else:
                    f.write("\t{:08X}\t{:04X}\n".format(vp[i].addr, vp[i].ID))
                i += 1
            else:
                rk = rkInstruction()
                if ln == 0:
                    rk.ID = loc48
                    if cv5:
                        rk.op2x3x6x = 0x64
                    if casm and casm.args and casm.args[0].src & 0xF == 2:
                        rk.op66 = 0x66

                    if casm and casm.args:
                        for aa, arg in enumerate(casm.args):
                            t = (arg.src >> 4) & 0xF
                            if t == 1:
                                rk.operand[aa].ID = 0x10
                                if vp[i + arg.reg].ID in range(0x14e, 0x153):
                                    rk.operand[aa].SetB(0, 0x40 | (arg.src & 0xF))
                                elif arg.notHave == 0:
                                    rk.operand[aa].SetB(0, (self.TRID[vp[i + arg.reg].pushval] << 4) | (arg.src & 0xF))
                                else:
                                    rk.operand[aa].SetB(0, ((self.TRID[vp[i + arg.reg].pushval] + 4) << 4) | (arg.src & 0xF))
                            elif t == 2:
                                rk.operand[aa].ID = (arg.src & 0xF) | 0x20
                                rk.operand[aa].value = vp[i + arg.cons].pushval
                                if rk.ID in self.ARYTHM and not IsSignedOverflow(rk.operand[aa].value, 8):
                                    rk.operand[aa].ID = 0x21
                                if rk.ID == OP_PUSH and not IsSignedOverflow(rk.operand[aa].value, 8):
                                    rk.operand[aa].ID = 0x21
                                if rk.ID == OP_IMUL and not IsSignedOverflow(rk.operand[aa].value, 8):
                                    rk.operand[aa].ID = 0x21
                                if rk.ID == OP_RETN and rk.operand[aa].value == 0:
                                    rk.operand[aa].ID = 0
                                if rk.ID == OP_TEST:
                                    if rk.operand[aa].ID & 0xf == 1:
                                        rk.operand[aa].value = rk.operand[aa].value & 0xFF
                                    elif rk.operand[aa].ID & 0xf == 2:
                                        rk.operand[aa].value = rk.operand[aa].value & 0xFFFF
                            elif t == 3:
                                rk.operand[aa].ID = (arg.src & 0xf) | 0x30
                                if casm.mr1:
                                    if vp[i + arg.v0].ID in range(0x14e, 0x153):
                                        rk.operand[aa].SetB(1, 0x43)
                                    else:
                                        rk.operand[aa].SetB(1, (self.TRID[vp[i + arg.v0].pushval] << 4) | 3)
                                if casm.mr2:
                                    rk.operand[aa].SetB(2, (self.TRID[vp[i + arg.v1].pushval] << 4) | 3)
                                if casm.scale:
                                    rk.operand[aa].SetB(3, vp[i + arg.v2].pushval & 0xFF )
                                if casm.mo:
                                    rk.operand[aa].val2 = vp[i + arg.v3].pushval

                    if bv3:
                        if rk.operand[1].TID() == 1:
                            rk.operand[1].value = (rk.operand[1].value & ~0xF) | 1
                        elif rk.operand[1].TID() == 2:
                            rk.operand[1].ID = (rk.operand[1].ID & ~0xF) | 1

                    if bv4:
                        if stdID in (128, 72):
                            rk.op66 = 0x66
                            if rk.operand[0].TID() == 1:
                                rk.operand[0].value = (rk.operand[0].value & ~0xF) | 2
                            else:
                                rk.operand[0].ID = (rk.operand[0].ID & ~0xF) | 2

                            if rk.operand[1].TID() == 1:
                                rk.operand[1].value = (rk.operand[1].value & ~0xF) | 1
                            else:
                                rk.operand[1].ID = (rk.operand[1].ID & ~0xF) | 1
                        elif stdID in (129, 73):
                            rk.op66 = 0
                            if rk.operand[0].TID() == 1:
                                rk.operand[0].value = (rk.operand[0].value & ~0xF) | 3
                            else:
                                rk.operand[0].ID = (rk.operand[0].ID & ~0xF) | 3

                            if rk.operand[1].TID() == 1:
                                rk.operand[1].value = (rk.operand[1].value & ~0xF) | 1
                            else:
                                rk.operand[1].ID = (rk.operand[1].ID & ~0xF) | 1
                        elif stdID in (133, 77):
                            rk.op66 = 0
                            if rk.operand[0].TID() == 1:
                                rk.operand[0].value = (rk.operand[0].value & ~0xF) | 3
                            else:
                                rk.operand[0].ID = (rk.operand[0].ID & ~0xF) | 3

                            if rk.operand[1].TID() == 1:
                                rk.operand[1].value = (rk.operand[1].value & ~0xF) | 2
                            else:
                                rk.operand[1].ID = (rk.operand[1].ID & ~0xF) | 2
                    loc30 = 0
                else:
                    sz = self.VopAsm(i, rk)
                    loc30 = sz

                if rk.ID in (OP_DEC, OP_INC):
                    rk.operand[1].ID = 0
                    rk.operand[1].val2 = 0
                    rk.operand[1].value = 0

                bts = XrkAsm.AsmRk(rk)

                if bts:
                    _, rk = XrkDecode(bts)

                    f.write("\t{:08X}\t{}\n".format(vp[i].addr, XrkText(rk)))

                else:
                    f.write("Assemble failed at {:08X}, no opcode found!\r\n".format(vp[i].addr))

                if not bv2 and loc30 == 0 and casm:
                    sz = len(casm.handlers)

                i += sz

        f.close()
        print("UV Dump complete into : {}/TXT/Cisc_Uv_Dump_{:08x}.txt".format(self.WrkDir, self.pushValue))



    def StdMnem(self, vop):
        mnems = {34: "ADD", 35: "ADD", 36: "ADD", 39: "SUB", 40: "SUB", 41: "SUB", \
                 44: "IMUL", 45: "IMUL", 47: "ADC", 48: "ADC", 49: "ADC", \
                 51: "AND", 52: "AND", 53: "AND", 55: "CMP", 56: "CMP", 57: "CMP", \
                 59: "XOR", 60: "XOR", 61: "XOR", 63: "OR", 64: "OR", 65: "OR", \
                 67: "TEST", 68: "TEST", 69: "TEST", 72: "MOVZX", 73: "MOVZX", 77: "MOVZX", \
                 83: "INC", 84: "INC", 85: "INC", 87: "RCL", 88: "RCL", 89: "RCL", \
                 91: "RCR", 92: "RCR", 93: "RCR", 95: "ROL", 96: "ROL", 97: "ROL", \
                 99: "ROR", 100: "ROR", 101: "ROR", 103: "SAL", 104: "SAL", 105: "SAL", \
                 107: "SAR", 108: "SAR", 109: "SAR", 111: "SHL", 112: "SHL", 113: "SHL", \
                 115: "SHR", 116: "SHR", 117: "SHR", 119: "DEC", 120: "DEC", 121: "DEC", \
                 123: "NOP", 128: "MOVSX", 129: "MOVSX", 133: "MOVSX", 135: "CLC", 139: "CLD", \
                 143: "CLI", 147: "CMC", 151: "STC", 155: "STD", 159: "STI", 168: "BT", 169: "BT", \
                 171: "BTC", 172: "BTC", 175: "BTR", 176: "BTR", 183: "SBB", 184: "SBB", 185: "SBB", \
                 187: "MUL", 188: "MUL", 189: "MUL", 191: "IMUL", 192: "IMUL", 193: "IMUL", \
                 195: "DIV", 196: "DIV", 197: "DIV", 199: "IDIV", 200: "IDIV", 201: "IDIV", \
                 204: "BSWAP", 207: "NEG", 208: "NEG", 209: "NEG", 211: "NOT", 212: "NOT", 213: "NOT"}
        if vop not in mnems:
            return ""
        return mnems[vop]


