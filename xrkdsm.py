EFLG_CF = (1<<0)
EFLG_PF = (1<<2)
EFLG_AF = (1<<4)
EFLG_ZF = (1<<6)
EFLG_SF = (1<<7)
EFLG_TF = (1<<8)
EFLG_IF = (1<<9)
EFLG_DF = (1<<10)
EFLG_OF = (1<<11)
EFLG_IOPL = (3<<12)
EFLG_NT = (1<<14)
EFLG_RF = (1<<16)
EFLG_VM = (1<<17)
EFLG_AC = (1<<18)
EFLG_VIF = (1<<19)
EFLG_VIP = (1<<20)
EFLG_ID = (1<<21)

TID_REG = 1
TID_VAL = 2
TID_MEM = 3

ID_REG = 0x10
ID_VALx = 0x20
ID_VAL8 = 0x21
ID_VAL16 = 0x22
ID_VAL32 = 0x23
ID_MEMx = 0x30
ID_MEM8 = 0x31
ID_MEM16 = 0x32
ID_MEM32 = 0x33

R_EAX = 0x03
R_ECX = 0x13
R_EDX = 0x23
R_EBX = 0x33
R_ESP = 0x43
R_EBP = 0x53
R_ESI = 0x63
R_EDI = 0x73

R_AX = 0x02
R_CX = 0x12
R_DX = 0x22
R_BX = 0x32
R_SP = 0x42
R_BP = 0x52
R_SI = 0x62
R_DI = 0x72

R_AL = 0x01
R_CL = 0x11
R_DL = 0x21
R_BL = 0x31
R_AH = 0x41
R_CH = 0x51
R_DH = 0x61
R_BH = 0x71


from xrktbl import *
from xrkutil import *
from xrkopr import *

class EFlags:
	CF = False #0
	PF = False #2
	AF = False #4
	ZF = False #6
	SF = False #7
	TF = False #8
	IF = False #9
	DF = False #10
	OF = False #11
	IOPL = 0 #12-13
	NT = False #14
	RF = False #16
	VM = False #17
	AC = False #18
	VIF = False #19
	VIP = False #20
	ID = False #21


class rkInstruction:
	ID = 0 #word	
	op2x3x6x = 0 #byte
	op66 = 0 #byte
	op67 = 0 #byte
	opfx = 0 #byte
	operand = None
	opInfo = None
	bts = None
	
	def __init__(self):
		self.operand = [OperandInfo(), OperandInfo(), OperandInfo(), OperandInfo()]
	
	def Clear(self):
		self.ID = 0
		self.op2x3x6x = 0
		self.op66 = 0
		self.op67 = 0
		self.opfx = 0
		self.operand = [OperandInfo(), OperandInfo(), OperandInfo(), OperandInfo()]
		self.opInfo = None
	
	def CopyOpFields(self, b):
		self.op67 = b.op67
		self.op66 = b.op66
		self.opfx = b.opfx
		self.op2x3x6x = b.op2x3x6x
	
	def Compare(self, b):
		if self.ID != b.ID:
			return False
		for i in range(4):
			io = self.operand[i]
			bo = b.operand[i]
			if io.ID != bo.ID or\
			   io.value != bo.value or\
			   io.val2 != bo.val2:
			   return False
		return True

	def Copy(self):
		t = rkInstruction()
		t.ID = self.ID
		t.CopyOpFields(self)
		t.operand[0] = self.operand[0].Copy()
		t.operand[1] = self.operand[1].Copy()
		t.operand[2] = self.operand[2].Copy()
		t.operand[3] = self.operand[3].Copy()
		t.opInfo = self.opInfo
		t.bts = self.bts[:]
		return t

	def CopyFrom(self, b):
		self.ID = b.ID
		self.CopyOpFields(b)
		self.operand[0] = b.operand[0].Copy()
		self.operand[1] = b.operand[1].Copy()
		self.operand[2] = b.operand[2].Copy()
		self.operand[3] = b.operand[3].Copy()
		self.opInfo = b.opInfo
		self.bts = b.bts[:]
	
def GetLeading(bts, rki):
	fnd = [False, ] * 4
	i = 0
	while(True):
		ub = UB(bts[i])
		if ub in (0x26, 0x2e, 0x36, 0x3e, 0x64, 0x65):
			if fnd[1]: return i
			rki.op2x3x6x = ub
			fnd[1] = True
		elif ub == 0x66:
			if fnd[2]: return i
			rki.op66 = ub
			fnd[2] = True
		elif ub == 0x67:
			if fnd[3]: return i
			rki.op67 = ub
			fnd[3] = True
		elif ub in (0xf0, 0xf2, 0xf3):
			if fnd[0]: return i
			rki.opfx = ub
			fnd[0] = True
		else:
			return i
		i += 1	


def XrkDecode(bts):
	rki = rkInstruction()
	i = GetLeading(bts, rki)
	
	opInfo = None
	
	b1 = UB(bts[i])
	
	if b1 == 0xF:
		b2 = UB(bts[i+1])
		b2f0 = b2 & 0xF0
		
		if b2 == 0xBA:
			opInfo = OP_0FBAx[ (UB(bts[i+2]) >> 3) & 7 ]
		elif b2f0 in (0, 0x30, 0x40, 0x80, 0x90, 0xa0):
			opInfo = OP_2B[b2]
		elif b2f0 == 0x10:
			if (b2 & 0xF) < 8:
				if rki.opfx == 0xf2:
					opInfo = OP_F20F1x[b2 & 0xF]
				elif rki.opfx == 0xf3:
					opInfo = OP_F30F1x[b2 & 0xF]
				elif rki.opfx == 0x66:
					opInfo = OP_660F1x[b2 & 0xF]
				else:
					opInfo = OP_2B[b2]
			else:
				opInfo = OP_2B[b2]
		elif b2f0 == 0x20:
			if (b2 & 0xF) < 8:
				opInfo = OP_2B[b2]
			elif rki.opfx == 0xf2:
				opInfo = OP_F20F2x[b2 & 0xF]
			elif rki.opfx == 0xf3:
				opInfo = OP_F30F2x[b2 & 0xF]
			elif rki.opfx == 0x66:
				opInfo = OP_660F2x[b2 & 0xF]
			else:
				opInfo = OP_2B[b2]
		elif b2f0 == 0x50:
			if rki.opfx == 0xf2:
				opInfo = OP_F20F5x[b2 & 0xF]
			elif rki.opfx == 0xf3:
				opInfo = OP_F30F5x[b2 & 0xF]
			elif rki.opfx == 0x66:
				opInfo = OP_660F5x[b2 & 0xF]
			else:
				opInfo = OP_2B[b2]
		elif b2f0 == 0x60:
			if rki.opfx == 0xf3:
				opInfo = OP_F30F6x[b2 & 0xF]
			elif rki.opfx == 0x66:
				opInfo = OP_660F6x[b2 & 0xF]
			else:
				opInfo = OP_2B[b2]
		elif b2f0 == 0x70:
			if rki.opfx == 0xf2:
				opInfo = OP_F20F7x[b2 & 0xF]
			elif rki.opfx == 0xf3:
				opInfo = OP_F30F7x[b2 & 0xF]
			elif rki.opfx == 0x66:
				opInfo = OP_660F7x[b2 & 0xF]
			else:
				opInfo = OP_2B[b2]
		elif b2f0 == 0xB0:
			if (b2 & 0xF) < 8:
				opInfo = OP_2B[b2]
			elif rki.opfx == 0xf3 and (b2 & 0xF) < 0xE:
				opInfo = OP_F30FBx[b2 & 0xF]
			else:
				opInfo = OP_2B[b2]
		elif b2f0 == 0xC0:
			if (b2 & 0xF) < 8:
				if rki.opfx == 0xf2:
					opInfo = OP_F20FCx[b2 & 0xF]
				elif rki.opfx == 0xf3:
					opInfo = OP_F30FCx[b2 & 0xF]
				elif rki.opfx == 0x66:
					opInfo = OP_660FCx[b2 & 0xF]
				else:
					opInfo = OP_2B[b2]
			else:
				opInfo = OP_2B[b2]
		elif b2f0 == 0xD0:
			if rki.opfx == 0xf2:
				opInfo = OP_F20FDx[b2 & 0xF]
			elif rki.opfx == 0xf3:
				opInfo = OP_F30FDx[b2 & 0xF]
			elif rki.opfx == 0x66:
				opInfo = OP_660FDx[b2 & 0xF]
			else:
				opInfo = OP_2B[b2]
		elif b2f0 == 0xE0:
			if rki.opfx == 0xf2:
				opInfo = OP_F20FEx[b2 & 0xF]
			elif rki.opfx == 0xf3:
				opInfo = OP_F30FEx[b2 & 0xF]
			elif rki.opfx == 0x66:
				opInfo = OP_660FEx[b2 & 0xF]
			else:
				opInfo = OP_2B[b2]
		elif b2f0 == 0xF0:
			if rki.opfx == 0xf2:
				opInfo = OP_F20FFx[b2 & 0xF]
			elif rki.opfx == 0x66:
				opInfo = OP_660FFx[b2 & 0xF]
			else:
				opInfo = OP_2B[b2]
		i += 2
	elif b1 == 0x80:
		opInfo = OP_80x[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	elif b1 == 0x81:
		opInfo = OP_81x[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	elif b1 == 0x82:
		opInfo = OP_82x[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	elif b1 == 0x83:
		opInfo = OP_83x[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	elif b1 == 0x8F:
		opInfo = OP_8Fx[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	elif b1 == 0xC0:
		opInfo = OP_C0x[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	elif b1 == 0xC1:
		opInfo = OP_C1x[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	elif b1 == 0xC6:
		opInfo = OP_C6x[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	elif b1 == 0xC7:
		opInfo = OP_C7x[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	elif b1 == 0xD0:
		opInfo = OP_D0x[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	elif b1 == 0xD1:
		opInfo = OP_D1x[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	elif b1 == 0xD2:
		opInfo = OP_D2x[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	elif b1 == 0xD3:
		opInfo = OP_D3x[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	elif b1 == 0xD8:
		if (bts[i+1] & 0xC0) == 0xC0:
			opInfo = OP_D8Cx[ bts[i+1] & 0x3F ]
			i += 2
		else:
			opInfo = OP_D8x[ (UB(bts[i+1]) >> 3) & 7 ]
			i += 1
	elif b1 == 0xD9:
		if (bts[i+1] & 0xC0) == 0xC0:
			opInfo = OP_D9Cx[ bts[i+1] & 0x3F ]
			i += 2
		else:
			opInfo = OP_D9x[ (UB(bts[i+1]) >> 3) & 7 ]
			i += 1
	elif b1 == 0xDA:
		if (bts[i+1] & 0xC0) == 0xC0:
			opInfo = OP_DACx[ bts[i+1] & 0x3F ]
			i += 2
		else:
			opInfo = OP_DAx[ (UB(bts[i+1]) >> 3) & 7 ]
			i += 1
	elif b1 == 0xDB:
		if (bts[i+1] & 0xC0) == 0xC0:
			opInfo = OP_DBCx[ bts[i+1] & 0x3F ]
			i += 2
		else:
			opInfo = OP_DBx[ (UB(bts[i+1]) >> 3) & 7 ]
			i += 1
	elif b1 == 0xDC:
		if (bts[i+1] & 0xC0) == 0xC0:
			opInfo = OP_DCCx[ bts[i+1] & 0x3F ]
			i += 2
		else:
			opInfo = OP_DCx[ (UB(bts[i+1]) >> 3) & 7 ]
			i += 1
	elif b1 == 0xDD:
		if (bts[i+1] & 0xC0) == 0xC0:
			opInfo = OP_DDCx[ bts[i+1] & 0x3F ]
			i += 2
		else:
			opInfo = OP_DDx[ (UB(bts[i+1]) >> 3) & 7 ]
			i += 1
	elif b1 == 0xDE:
		if (bts[i+1] & 0xC0) == 0xC0:
			opInfo = OP_DECx[ bts[i+1] & 0x3F ]
			i += 2
		else:
			opInfo = OP_DEx[ (UB(bts[i+1]) >> 3) & 7 ]
			i += 1
	elif b1 == 0xDF:
		if (bts[i+1] & 0xC0) == 0xC0:
			opInfo = OP_DFCx[ bts[i+1] & 0x3F ]
			i += 2
		else:
			opInfo = OP_DFx[ (UB(bts[i+1]) >> 3) & 7 ]
			i += 1
	elif b1 == 0xF6:
		opInfo = OP_F6x[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	elif b1 == 0xF7:
		opInfo = OP_F7x[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	elif b1 == 0xFE:
		opInfo = OP_FEx[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	elif b1 == 0xFF:
		opInfo = OP_FFx[ (UB(bts[i+1]) >> 3) & 7 ]
		i += 1
	else:
		opInfo = OP_1B[ b1 ]
		i += 1
	
	if opInfo != None and opInfo.ID != OP_UNDEFINED:
		if opInfo.a3 == 0x66:
			rki.op66 = 0
		elif opInfo.a3 in (0xF2, 0xF3):
			rki.opfx = 0
		
		
		rki.ID = opInfo.ID
		rki.opInfo = opInfo
		
		oproff = 0
		for j in range(4):
			if opInfo.operand[j] != 0:
				oproff += DecodeOperand(bts[i:], rki, j, opInfo.operand[j], oproff)
		
		if opInfo.b1 == 0 and opInfo.b2 == 0x83:
			sz = rki.operand[1].ID & 0xf
			if sz == 1:
				rki.operand[1].value &= 0xFF
				if rki.operand[1].value & 0x80:
					rki.operand[1].value |= 0xFFFFFF00
			elif sz == 2:
				rki.operand[1].value &= 0xFFFF
				if rki.operand[1].value & 0x8000:
					rki.operand[1].value |= 0xFFFF0000
			#elif sz == 3:
			#	rki.operand[1].value &= 0xFFFFFFFF
		
		if opInfo.b1 == 0 and opInfo.b2 == 0x6a:
			sz = rki.operand[0].ID & 0xf
			if sz == 1:
				rki.operand[0].value &= 0xFF
				if rki.operand[0].value & 0x80:
					rki.operand[0].value |= 0xFFFFFF00
			elif sz == 2:
				rki.operand[0].value &= 0xFFFF
				if rki.operand[0].value & 0x8000:
					rki.operand[0].value |= 0xFFFF0000
			elif sz == 3:
				rki.operand[0].value &= 0xFFFFFFFF
		
		if opInfo.b1 == 0 and opInfo.b2 == 0x6b:
			sz = rki.operand[2].ID & 0xf
			if sz == 1:
				rki.operand[2].value &= 0xFF
				if rki.operand[2].value & 0x80:
					rki.operand[2].value |= 0xFFFFFF00
			elif sz == 2:
				rki.operand[2].value &= 0xFFFF
				if rki.operand[2].value & 0x8000:
					rki.operand[2].value |= 0xFFFF0000
			elif sz == 3:
				rki.operand[2].value &= 0xFFFFFFFF
		
		i += oproff
		
		rki.bts = ByteSlice(bts, 0, i)
	
	return i,rki



REG8NAME = ("AL", "CL", "DL", "BL", "AH", "CH", "DH", "BH")
REG16NAME = ("AX", "CX", "DX", "BX", "SP", "BP", "SI", "DI")
REG32NAME = ("EAX", "ECX", "EDX", "EBX", "ESP", "EBP", "ESI", "EDI")
PTRNAME = ("UNK PTR", "BYTE PTR ", "WORD PTR ", "DWORD PTR ",\
		   "FWORD PTR ", "QWORD PTR ", "TBYTE PTR ", "(14-BYTE) PTR ",\
		   "UNK PTR", "(28-BYTE) PTR ", "(98-BYTE) PTR ", "(108-BYTE) PTR ",\
		   "UNK PTR", "UNK PTR", "UNK PTR", "UNK PTR")
MULNAME = ("*1", "*2", "*4", "*8")
SEGNAME = ("ES", "CS", "SS", "DS", "FS", "GS", "SEG?", "SEG?",\
		   "SEG?", "SEG?", "SEG?", "SEG?", "SEG?", "SEG?", "SEG?", "SEG?")

def XrkTextOp(rk, i = 0):
	o = ""
	if i == 0:
		o = " "
	else:
		o = ","
	op = rk.operand[i]
	tid = op.TID()
	if tid == 1:
		sz = op.GetB(0) & 0xf
		regid = op.GetB(0) >> 4
		if sz == 1:
			o += REG8NAME[regid]
		elif sz == 2:
			o += REG16NAME[regid]
		elif sz == 3:
			o += REG32NAME[regid]
		else:
			o += "REG UNK"
	elif tid == 2:
		sz = op.ID & 0xF
		if sz == 1:
			o += "0x{:x}".format(UB(op.value))
		elif sz == 2:
			o += "0x{:x}".format(UWORD(op.value))
		elif sz == 3:
			o += "0x{:x}".format(UINT(op.value))
		else:
			o += "IMMC UNK"
	elif tid == 3:
		sz = op.ID & 0xF
		o += PTRNAME[sz]
		if rk.op2x3x6x == 0x2e:
			o += "CS: "
		elif rk.op2x3x6x == 0x36:
			o += "SS: "
		elif rk.op2x3x6x == 0x3e:
			o += "DS: "
		elif rk.op2x3x6x == 0x26:
			o += "ES: "
		elif rk.op2x3x6x == 0x64:
			o += "FS: "
		elif rk.op2x3x6x == 0x65:
			o += "GS: "
		elif rk.op2x3x6x != 0:
			o += "UNK: "
		o += "["

		if op.GetB(1) != 0:
			sz = op.GetB(1) & 0xf
			rid = op.GetB(1) >> 4
			if sz == 2:
				o += REG16NAME[rid]
			elif sz == 3:
				o += REG32NAME[rid]
			else:
				o += "REG?"

		if op.GetB(2) != 0:
			if op.GetB(1) != 0:
				o += "+"
			sz = op.GetB(2) & 0xf
			rid = op.GetB(2) >> 4
			if sz == 2:
				o += REG16NAME[rid]
			elif sz == 3:
				o += REG32NAME[rid]
			else:
				o += "REG?"
		if op.GetB(3) != 0:
			if op.GetB(2) == 0:
				o += "ERROR"
			else:
				o += MULNAME[op.GetB(3)]

		if op.val2 != 0 or (op.GetB(1) == 0 and op.GetB(2) == 0):
			if op.GetB(1) != 0 or op.GetB(2) != 0:
				o += "+"
			o += "0x{:x}".format(op.val2)
		o += "]"
	elif tid == 6:
		o += SEGNAME[ op.GetB(0) >> 4 ]
	elif tid == 7:
		rid = op.GetB(0) >> 4
		if rid < 8:
			o += "ST({:d})".format(rid)
		else:
			o += "ST(?)"
	elif tid == 9:
		o += "XMM{:d}".format(op.GetB(0) >> 4)
	elif tid == 10:
		o += "YMM{:d}".format(op.GetB(0) >> 4)
	elif tid == 12:
		pass
	else:
		o += "UNK"
	return o

def XrkText(rk):
	o = ""
	inf = rk.opInfo

	if rk.opfx == 0xf0:
		o = "LOCK "
	elif rk.opfx == 0xf2:
		o = "REPNE "
	elif rk.opfx == 0xf3:
		o = "REP "
	elif rk.opfx != 0:
		o = "PFX GRP1 UNK "

	if rk.ID == OP_CBW:
		if rk.op66 == 0:
			o += "CWDE"
		else:
			o += inf.MNEM
	elif rk.ID == OP_CWD:
		if rk.op66 == 0:
			o += "CDQ"
		else:
			o += inf.MNEM
	elif rk.ID in (OP_POPA, OP_POPF, OP_PUSHA, OP_PUSHF):
		o += inf.MNEM
		if rk.op66 == 0:
			o += "D"
	else:
		o += inf.MNEM

	for i in range(4):
		if rk.operand[i].ID == 0:
			break
		o += XrkTextOp(rk, i)
	return o

def CalcEFlags(opid, sz, val1, val2, flags):
	if sz == 1:
		v1 = UB(val1)
		v2 = UB(val2)
		r = 0
		flg = 0
		if opid == OP_NOT:
			pass
		elif opid == OP_ADD:
			flg = EFLG_OF | EFLG_SF | EFLG_ZF | EFLG_AF | EFLG_CF | EFLG_PF
			r = v1 + v2
		elif opid == OP_AND:
			flg = EFLG_SF | EFLG_ZF | EFLG_PF
			flags.OF = 0
			flags.CF = 0
			r = v1 & v2
		elif opid == OP_DEC:
			r = v1 - 1
			flg = EFLG_OF | EFLG_SF | EFLG_ZF | EFLG_AF | EFLG_PF
		elif opid == OP_INC:
			r = v1 + 1
			flg = EFLG_OF | EFLG_SF | EFLG_ZF | EFLG_AF | EFLG_PF
		elif opid == OP_NEG:
			r = v1 + 1
			if v1 == 0:
				flags.CF = 0
			else:
				flags.CF = 1
			flg = EFLG_OF | EFLG_SF | EFLG_ZF | EFLG_AF | EFLG_PF
		elif opid == OP_OR:
			r = v1 | v2
			flg = EFLG_SF | EFLG_ZF | EFLG_PF
			flags.OF = 0
			flags.CF = 0
		elif opid == OP_SHL:
			cnt = v2 & 0x1F
			r = v1 << cnt
			if cnt:
				flg = EFLG_SF | EFLG_ZF | EFLG_PF
				if cnt == 1:
					flg |= EFLG_OF
				flags.CF = (r & 0x100) != 0
		elif opid == OP_SHR:
			cnt = v2 & 0x1F
			r = v1 >> cnt
			if cnt:
				flg = EFLG_SF | EFLG_ZF | EFLG_PF
				if cnt == 1:
					flg |= EFLG_OF
				flags.CF = (v1 & ( 1 << (cnt - 1))) != 0
		elif opid == OP_SUB:
			flg = EFLG_OF | EFLG_SF | EFLG_ZF | EFLG_AF | EFLG_CF | EFLG_PF
			r = v1 - v2
		elif opid == OP_XOR:
			r = v1 | v2
			flg = EFLG_SF | EFLG_ZF | EFLG_PF
			flags.OF = 0
			flags.CF = 0

		if flg & EFLG_OF:
			flags.OF = (r & 0x80) != (v1 & 0x80)
		if flg & EFLG_CF:
			flags.CF = (r & 0xFF00) != 0
		if flg & EFLG_ZF:
			flags.ZF = (r & 0xFF) == 0
		if flg & EFLG_SF:
			flags.SF = (r & 0x80) != 0
		if flg & EFLG_PF:
			t = r & 0xFF
			t = ((r & 0xAA) >> 1) ^ (r & 0x55)
			t = ((t & 0x50) >> 4) ^ (t & 5)
			flags.PF = ((t >> 2) ^ (t & 1)) == 0
	elif sz == 2:
		v1 = UWORD(val1)
		v2 = UWORD(val2)
		r = 0
		flg = 0
		if opid == OP_NOT:
			pass
		elif opid == OP_ADD:
			flg = EFLG_OF | EFLG_SF | EFLG_ZF | EFLG_AF | EFLG_CF | EFLG_PF
			r = v1 + v2
		elif opid == OP_AND:
			flg = EFLG_SF | EFLG_ZF | EFLG_PF
			flags.OF = 0
			flags.CF = 0
			r = v1 & v2
		elif opid == OP_DEC:
			r = v1 - 1
			flg = EFLG_OF | EFLG_SF | EFLG_ZF | EFLG_AF | EFLG_PF
		elif opid == OP_INC:
			r = v1 + 1
			flg = EFLG_OF | EFLG_SF | EFLG_ZF | EFLG_AF | EFLG_PF
		elif opid == OP_NEG:
			r = v1 + 1
			if v1 == 0:
				flags.CF = 0
			else:
				flags.CF = 1
			flg = EFLG_OF | EFLG_SF | EFLG_ZF | EFLG_AF | EFLG_PF
		elif opid == OP_OR:
			r = v1 | v2
			flg = EFLG_SF | EFLG_ZF | EFLG_PF
			flags.OF = 0
			flags.CF = 0
		elif opid == OP_SHL:
			cnt = v2 & 0x1F
			r = v1 << cnt
			if cnt:
				flg = EFLG_SF | EFLG_ZF | EFLG_PF
				if cnt == 1:
					flg |= EFLG_OF
				flags.CF = (r & 0x10000) != 0
		elif opid == OP_SHR:
			cnt = v2 & 0x1F
			r = v1 >> cnt
			if cnt:
				flg = EFLG_SF | EFLG_ZF | EFLG_PF
				if cnt == 1:
					flg |= EFLG_OF
				flags.CF = (v1 & (1 << (cnt - 1))) != 0
		elif opid == OP_SUB:
			flg = EFLG_OF | EFLG_SF | EFLG_ZF | EFLG_AF | EFLG_CF | EFLG_PF
			r = v1 - v2
		elif opid == OP_XOR:
			r = v1 | v2
			flg = EFLG_SF | EFLG_ZF | EFLG_PF
			flags.OF = 0
			flags.CF = 0

		if flg & EFLG_OF:
			flags.OF = (r & 0x8000) != (v1 & 0x8000)
		if flg & EFLG_CF:
			flags.CF = (r & 0xFFFF0000) != 0
		if flg & EFLG_ZF:
			flags.ZF = (r & 0xFFFF) == 0
		if flg & EFLG_SF:
			flags.SF = (r & 0x8000) != 0
		if flg & EFLG_PF:
			t = r & 0xFFFF
			t = ((r & 0xAAAA) >> 1) ^ (r & 0x5555)
			t = ((r & 0x5500) >> 8) ^ (r & 0x55)
			t = ((t & 0x50) >> 4) ^ (t & 5)
			flags.PF = ((t >> 2) ^ (t & 1)) == 0
	elif sz == 3:
		v1 = UINT(val1)
		v2 = UINT(val2)
		r = 0
		flg = 0
		if opid == OP_NOT:
			pass
		elif opid == OP_ADD:
			flg = EFLG_OF | EFLG_SF | EFLG_ZF | EFLG_AF | EFLG_CF | EFLG_PF
			r = v1 + v2
		elif opid == OP_AND:
			flg = EFLG_SF | EFLG_ZF | EFLG_PF
			flags.OF = 0
			flags.CF = 0
			r = v1 & v2
		elif opid == OP_DEC:
			r = v1 - 1
			flg = EFLG_OF | EFLG_SF | EFLG_ZF | EFLG_AF | EFLG_PF
		elif opid == OP_INC:
			r = v1 + 1
			flg = EFLG_OF | EFLG_SF | EFLG_ZF | EFLG_AF | EFLG_PF
		elif opid == OP_NEG:
			r = v1 + 1
			if v1 == 0:
				flags.CF = 0
			else:
				flags.CF = 1
			flg = EFLG_OF | EFLG_SF | EFLG_ZF | EFLG_AF | EFLG_PF
		elif opid == OP_OR:
			r = v1 | v2
			flg = EFLG_SF | EFLG_ZF | EFLG_PF
			flags.OF = 0
			flags.CF = 0
		elif opid == OP_SHL:
			cnt = v2 & 0x1F
			r = v1 << cnt
			if cnt:
				flg = EFLG_SF | EFLG_ZF | EFLG_PF
				if cnt == 1:
					flg |= EFLG_OF
				flags.CF = (r & 0x100000000) != 0
		elif opid == OP_SHR:
			cnt = v2 & 0x1F
			r = v1 >> cnt
			if cnt:
				flg = EFLG_SF | EFLG_ZF | EFLG_PF
				if cnt == 1:
					flg |= EFLG_OF
				flags.CF = (v1 & (1 << (cnt - 1))) != 0
		elif opid == OP_SUB:
			flg = EFLG_OF | EFLG_SF | EFLG_ZF | EFLG_AF | EFLG_CF | EFLG_PF
			r = v1 - v2
		elif opid == OP_XOR:
			r = v1 | v2
			flg = EFLG_SF | EFLG_ZF | EFLG_PF
			flags.OF = 0
			flags.CF = 0

		if flg & EFLG_OF:
			flags.OF = (r & 0x80000000) != (v1 & 0x80000000)
		if flg & EFLG_CF:
			flags.CF = (r & 0xFFFFFFFF00000000) != 0
		if flg & EFLG_ZF:
			flags.ZF = (r & 0xFFFFFFFF) == 0
		if flg & EFLG_SF:
			flags.SF = (r & 0x80000000) != 0
		if flg & EFLG_PF:
			t = r & 0xFFFFFFFF
			t = ((r & 0xAAAAAAAA) >> 1) ^ (r & 0x55555555)
			t = ((r & 0x55550000) >> 16) ^ (r & 0x5555)
			t = ((r & 0x5500) >> 8) ^ (r & 0x55)
			t = ((t & 0x50) >> 4) ^ (t & 5)
			flags.PF = ((t >> 2) ^ (t & 1)) == 0


def FUN_1005ddf0(opid, flg):
	if opid == OP_JA:
		return (not flg.CF) and (not flg.ZF)
	elif opid == OP_JB:
		return flg.CF != False
	elif opid == OP_JBE:
		return flg.CF or flg.ZF
	elif opid == OP_JE:
		return flg.ZF
	elif opid == OP_JG:
		return flg.SF == flg.OF and not flg.ZF
	elif opid == OP_JGE:
		return flg.SF == flg.OF
	elif opid == OP_JL:
		return flg.SF != flg.OF
	elif opid == OP_JLE:
		return flg.SF == flg.OF and not flg.ZF
	elif opid == OP_JNB:
		return not flg.CF
	elif opid == OP_JNO:
		return not flg.OF
	elif opid == OP_JNP:
		return not flg.PF
	elif opid == OP_JNS:
		return not flg.SF
	elif opid == OP_JNZ:
		return not flg.ZF
	elif opid == OP_JO:
		return flg.OF
	elif opid == OP_JP:
		return flg.PF
	elif opid == OP_JS:
		return flg.SF
	else:
		print("Error-DoMultiBranchJump got an unknown nID as parameter")
		return False