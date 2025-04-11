from xrkutil import *
from xrkdsm import *

class OperandInfo:
	ID = 0
	value = 0
	val2 = 0

	sz = 0
	xbase = 0

	def Base(self):
		if self.TID() == TID_REG:
			return self.GetB(0)
		elif self.TID() == TID_MEM:
			return self.GetB(1)
		return -1



	def XBase(self):
		if self.TID() == TID_REG:
			return self.GetB(0) >> 4
		elif self.TID() == TID_MEM:
			return self.GetB(1) >> 4
		return -1
	
	def SetB(self, b, val):
		val = UB(val)
		self.value = (self.value & (~(0xFF << (b * 8)))) | (val << (b * 8))
	
	def SetBA(self, b, ba):
		l = len(ba)
		M = 0
		val = 0
		for i in range(l):
			M = (M << 8) | 0xFF
			val = (val << 8) | ba[-(i + 1)]
		
		val = val << (b * 8)
		M = M << (b * 8)
		self.value = (self.value & M) | val
		
	def Size(self):
		if self.ID == ID_REG:
			return self.value & 0xF
		else:
			return self.ID & 0xF

	
	def GetB(self, b):
		return 0xFF & ((self.value & 0xFFFFFFFF) >> (b * 8))
	
	def TID(self):
		return self.ID >> 4

	def Copy(self):
		t = OperandInfo()
		t.ID = self.ID
		t.value = self.value
		t.val2 = self.val2
		return t

	def IsReg8(self):
		return self.ID == ID_REG and (self.GetB(0) & 0xF) == 1

	def IsReg16(self):
		return self.ID == ID_REG and (self.GetB(0) & 0xF) == 2

	def IsReg32(self):
		return self.ID == ID_REG and (self.GetB(0) & 0xF) == 3

	def IsReg(self, reg):
		return self.ID == ID_REG and self.GetB(0) == reg

	def IsRegNot(self, reg):
		return self.ID == ID_REG and self.GetB(0) != reg

	def IsRegIn(self, regz):
		return self.ID == ID_REG and self.GetB(0) in regz

	def IsMem32Base(self, base):
		return self.ID == ID_MEM32 and self.GetB(1) == base

	def IsMem32R(self, r1, r2, mult):
		return self.ID == ID_MEM32 and self.GetB(1) == r1 and self.GetB(2) == r2 and self.GetB(3) == mult

	def IsMem32Roff(self, r1, r2, mult, off):
		return self.ID == ID_MEM32 and self.GetB(1) == r1 and self.GetB(2) == r2 and self.GetB(3) == mult and self.val2 == off

	def IsMem16Base(self, base):
		return self.ID == ID_MEM16 and self.GetB(1) == base

	def IsMem16R(self, r1, r2, mult):
		return self.ID == ID_MEM16 and self.GetB(1) == r1 and self.GetB(2) == r2 and self.GetB(3) == mult

	def IsMem16Roff(self, r1, r2, mult, off):
		return self.ID == ID_MEM16 and self.GetB(1) == r1 and self.GetB(2) == r2 and self.GetB(3) == mult and self.val2 == off

	def IsMem8Base(self, base):
		return self.ID == ID_MEM8 and self.GetB(1) == base

	def IsMem8Roff(self, r1, r2, mult):
		return self.ID == ID_MEM8 and self.GetB(1) == r1 and self.GetB(2) == r2 and self.GetB(3) == mult

	def IsMem8Roff(self, r1, r2, mult, off):
		return self.ID == ID_MEM8 and self.GetB(1) == r1 and self.GetB(2) == r2 and self.GetB(3) == mult and self.val2 == off

	def IsMemBase0(self, r1):
		return (self.TID() == TID_MEM and self.GetB(1) == r1 and self.GetB(2) == 0 and self.GetB(3) == 0 and self.val2 == 0) or \
		       (self.TID() == TID_MEM and self.GetB(1) == 0 and self.GetB(2) == r1 and self.GetB(3) == 0 and self.val2 == 0)

def GetOperandSize(op66, oprnd, unk):
	tp = (UWORD(oprnd) >> 6) & 0x3F
	if tp == 1:
		if op66 != 0:
			return 3
		else:
			return 5
	elif tp == 2:
		return 1
	elif tp in (3,4, 0x15, 0x16, 0x19):
		if tp == 3:
			print("{:X} tp {:x} Error operand_size not yet developed".format(oprnd, tp))
		return 3
	elif tp in (5, 0x1b, 0x1c, 0x1f):
		return 5
	elif tp == 6:
		if op66 == 0 and unk == 0:
			return 4
		elif op66 == 0x66 and unk == 0:
			return 3
		else:
			print("{:X} tp {:x} Error operand_size not yet developed".format(oprnd, tp))
			return 0
	elif tp == 0xd:
		if op66 == 0 and unk == 0:
			return 5
		else:
			print("{:X} tp {:x} Error operand_size not yet developed".format(oprnd, tp))
			return 0
	elif tp == 0xe:
		if op66 == 0 and unk == 0:
			return 3
		else:
			print("{:X} tp {:x} Error operand_size not yet developed".format(oprnd, tp))
			return 0
	elif tp == 0xf:
		print("{:X} tp {:x} Error operand_size not yet developed".format(oprnd, tp))
		return 0
	elif tp == 0x10:
		if op66 == 0 and unk == 0:
			return 3
		elif op66 == 0x66 and unk == 0:
			return 2
		else:
			print("{:X} tp {:x} Error operand_size not yet developed".format(oprnd, tp))
			return 0
	elif tp in (0x11, 0x18, 0x1e):
		return 2
	elif tp == 0x14:
		if op66 == 0x66:
			return 2
		else:
			return 3
	elif tp == 0x17:
		if op66 == 0x66:
			return 7
		else:
			return 9
	elif tp in (0x1a, 0x20):
		return 6
	elif tp == 0x1d:
		if op66 == 0x66:
			return 10
		else:
			return 11
	else:
		print("{:X} tp {:x} Error operand_size not yet developed".format(oprnd, tp))
	return 0

def DecodeMemReg16(p1, p2):
	p1 &= 7
	vals = ((R_BX, R_SI),
			(R_BX, R_DI),
			(R_BP, R_SI),
			(R_BP, R_DI),
			(R_SI, 0),
			(R_DI, 0),
			(R_BP, 0),
			(R_BX, 0))
	return vals[p1][p2 != 0]

def FUN_1008d600(bts, opr, op66, oprnd):
	sz = GetOperandSize(op66, oprnd, 0)
	b = UB(bts[0])
	if b & 0xC0 == 0xC0:
		opr.ID = ID_REG
		opr.SetB(0, ((b & 7) << 4) | sz)
		return 1
	elif b & 0x80 == 0x80:
		opr.ID = sz | ID_MEMx
		t = DecodeMemReg16(b & 7, 0)
		opr.SetB(1, t)
		t = DecodeMemReg16(b & 7, 1)
		opr.SetB(2, t)
		opr.val2 = Ext16to32( GetWORD(bts[1:3]) )
		return 3
	elif b & 0x40 == 0x40:
		opr.ID = sz | ID_MEMx
		t = DecodeMemReg16(b & 7, 0)
		opr.SetB(1, t)
		t = DecodeMemReg16(b & 7, 1)
		opr.SetB(2, t)
		opr.val2 = Ext8to32( bts[1] )
		return 2
	else:
		opr.ID = sz | ID_MEMx
		if (b & 7) == 6:
			opr.val2 = GetWORD(bts[1:3])
			return 3
		else:
			t = DecodeMemReg16(b & 7, 0)
			opr.SetB(1, t)
			t = DecodeMemReg16(b & 7, 1)
			opr.SetB(2, t)
			return 1


def DecodeMem32(bts, opr):
	reg1 = ((bts[1] & 7) << 4) | 3
	reg2 = (((UB(bts[1]) >> 3) & 7) << 4) | 3
	mult = UB(bts[1]) >> 6
	opr.SetB(1, reg1)
	opr.SetB(2, reg2)
	opr.SetB(3, mult)

	if reg2 == R_ESP:
		opr.SetB(2, 0)
	
	b = UB(bts[0])
	if b & 0xc0 == 0:
		if reg1 == R_EBP:
			opr.SetB(1, 0)
			opr.val2 = GetDWORD(bts[2:6])
			return 6
		else:
			return 2
	elif b & 0xc0 == 0x40:
		opr.val2 = Ext8to32(bts[2])
		return 3
	elif b & 0xc0 == 0x80:
		opr.val2 = GetDWORD(bts[2:6])
		return 6
		
	print("mod_bit == 11")
	return 2


def FUN_1008d2b0(bts, opr, op66, oprnd):
	sz  = GetOperandSize(op66, oprnd, 0)
	b = UB(bts[0])
	if (b & 0xC0) == 0xc0:
		opr.ID = ID_REG
		opr.SetB(0, ((b & 7) << 4) | sz)
		return 1
	elif (b & 0x80) == 0x80:
		opr.ID = ID_MEMx | sz
		if (b & 7) == 4:
			return DecodeMem32(bts, opr)
		else:
			opr.SetB(1, ((bts[0] & 7) << 4) | 3)
			opr.val2 = GetDWORD(bts[1:5])
			return 5
	elif (b & 0x40) == 0x40:
		opr.ID = ID_MEMx | sz
		if (b & 7) == 4:
			return DecodeMem32(bts, opr)
		else:
			opr.SetB(1, ((bts[0] & 7) << 4) | 3)
			opr.val2 = Ext8to32(bts[1])
			return 2
	else:
		opr.ID = ID_MEMx | sz
		if (b & 7) == 4:
			return DecodeMem32(bts, opr)
		elif (b & 7) == 5:
			opr.val2 = GetDWORD(bts[1:5])
			return 5
		else:
			opr.SetB(1, ((bts[0] & 7) << 4) | 3)
			return 1

def DecodeOperand(bts, rki, i, oprnd, offset):
	#print("DecodeOperand {} i {:d} , opr {:X}, off {:d}".format(rki.opInfo.MNEM, i, oprnd, offset))
	sz = GetOperandSize(rki.op66, oprnd, 0)
	opr = oprnd & 0x3f

	if opr == 1:
		if sz == 4:
			rki.operand[i].ID = 0xb4
			rki.operand[i].value = GetDWORD(bts)
			rki.operand[i].val2 = GetWORD(bts[4:])
			return 6
		elif sz == 3:
			rki.operand[i].ID = 0xb3
			rki.operand[i].value = GetWORD(bts)
			rki.operand[i].val2 = GetWORD(bts[2:])
			return 4
		else:
			print("Incorrect opr {:x} {:x}".format(opr, oprnd)) 
			return 0
	elif opr == 2:
		rki.operand[i].ID = 0x40
		rki.operand[i].SetB(0, (((UB(bts[0]) >> 3) & 7) << 4) | sz)
		return 0
	elif opr == 3:
		rki.operand[i].ID = 0x50
		rki.operand[i].SetB(0, (((UB(bts[0]) >> 3) & 7) << 4) | sz)
		return 0
	elif opr == 4:
		if rki.op67 == 0:
			return FUN_1008d2b0(bts, rki.operand[i], rki.op66, oprnd)
		else:
			return FUN_1008d600(bts, rki.operand[i], rki.op66, oprnd)
	elif opr == 5:
		rki.operand[i].ID = 0xc0 | sz
		return 0
	elif opr == 6:
		rki.operand[i].ID = ID_REG
		rki.operand[i].SetB(0, (((UB(bts[0]) >> 3) & 7) << 4) | sz)
		#if (UB(bts[0]) == 0xe1):
		#	print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!@@@@@@@@@@@@  {:x}".format(rki.operand[i].value))
		return 0
	elif opr == 8:
		rki.operand[i].ID = ID_VALx | sz
		if sz == 1:
			rki.operand[i].value = UB(bts[offset])
			return 1
		elif sz == 2:
			rki.operand[i].value = GetWORD(bts[offset:offset+2])
			return 2
		elif sz == 3:
			rki.operand[i].value = GetDWORD(bts[offset:offset+4])
			return 4
	elif opr == 9:
		rki.operand[i].ID = ID_VALx | sz
		if sz == 1:
			rki.operand[i].value = UB(bts[offset])
			return 1
		elif sz == 2:
			rki.operand[i].value = GetWORD(bts[offset:offset+2])
			return 2
		elif sz == 3:
			rki.operand[i].value = GetDWORD(bts[offset:offset+4])
			return 4
	elif opr == 0xc:
		if rki.op67 == 0:
			return FUN_1008d2b0(bts, rki.operand[i], rki.op66, oprnd)
		else:
			return FUN_1008d600(bts, rki.operand[i], rki.op66, oprnd)
	elif opr == 0xe:
		if rki.op67 == 0:
			rki.operand[i].ID = ID_MEMx | sz
			rki.operand[i].val2 = GetDWORD(bts[offset:offset + 4])
			return 4
		elif rki.op67 == 0x67:
			rki.operand[i].ID = ID_MEMx | sz
			rki.operand[i].val2 = GetWORD(bts[offset:offset + 2])
			return 2
		else:
			print("Incorrect opr {:x} {:x}".format(opr, oprnd)) 
			return 0
	elif opr == 0x12:
		rki.operand[i].ID = 0x60
		rki.operand[i].SetB(0, (((UB(bts[0]) >> 3) & 7) << 4) | sz)
		return 0
	elif opr == 0x14:
		if rki.op66 == 0:
			rki.operand[i].ID = 0x90
			rki.operand[i].SetB(0, (((UB(bts[0]) >> 3) & 7) << 4) | sz)
			return 0
		return -1
	elif opr == 0x15:
		if rki.op66 == 0:
			ln = FUN_1008d2b0(bts, rki.operand[i], rki.op66, oprnd)
			if rki.operand[i].ID == ID_REG:
				rki.operand[i].ID = 0x90
			return ln
		return -1
	elif opr == 0x16:
		rki.operand[i].ID = ID_MEMx | sz
		rki.operand[i].SetB(1, R_ESI)
		rki.operand[i].SetB(2, 0)
		rki.operand[i].SetB(3, 0)
		rki.operand[i].val2 = 0
		return 0
	elif opr == 0x17:
		rki.operand[i].ID = ID_MEMx | sz
		rki.operand[i].SetB(1, R_EDI)
		rki.operand[i].SetB(2, 0)
		rki.operand[i].SetB(3, 0)
		rki.operand[i].val2 = 0
		return 0
	elif opr in (0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f):
		rki.operand[i].ID = ID_REG
		rki.operand[i].SetB(0, ((((oprnd & 0x3f) - 0x18) & 7) << 4) | sz)
		return 0
	elif opr in (0x20, 0x21, 0x22, 0x23, 0x24, 0x25):
		rki.operand[i].ID = 0x60
		rki.operand[i].SetB(0, ((((oprnd & 0x3f) - 0x20) & 7) << 4) | sz)
		return 0
	elif opr == 0x26:
		rki.operand[i].ID = ID_VALx | sz
		rki.operand[i].value = 1
		return 0
	elif opr in (0x27, 0x28, 0x29, 0x2a, 0x2b, 0x2c, 0x2d, 0x2e):
		rki.operand[i].ID = 0x70
		rki.operand[i].SetB(0, ((((oprnd & 0x3f) - 0x27) & 7) << 4) | sz)
		return 0
	else:
		print("Err incorr method")
		return -1