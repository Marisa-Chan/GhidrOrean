from xrkutil import *

class OperandInfo:
	ID = 0
	value = 0
	val2 = 0
	
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

def FUN_1008d4e0(p1, p2):
	p1 &= 7
	vals = ((0x32, 0x62), 
			(0x32, 0x72), 
			(0x52, 0x62), 
			(0x52, 0x72), 
			(0x62, 0), 
			(0x72, 0), 
			(0x52, 0), 
			(0x32, 0))
	return vals[p1][p2 != 0]

def FUN_1008d600(bts, opr, op66, oprnd):
	sz = GetOperandSize(op66, oprnd, 0)
	b = UB(bts[0])
	if b & 0xC0 == 0xC0:
		opr.ID = 0x10
		opr.SetB(0, ((b & 7) << 4) | sz)
		return 1
	elif b & 0x80 == 0x80:
		opr.ID = sz | 0x30
		t = FUN_1008d4e0(b & 7, 0)
		opr.SetB(1, t)
		t = FUN_1008d4e0(b & 7, 1)
		opr.SetB(2, t)
		opr.val2 = GetWORD(bts[1:3])
		return 3
	elif b & 0x40 == 0x40:
		opr.ID = sz | 0x30
		t = FUN_1008d4e0(b & 7, 0)
		opr.SetB(1, t)
		t = FUN_1008d4e0(b & 7, 1)
		opr.SetB(2, t)
		opr.val2 = UB(bts[1])
		return 2
	else:
		opr.ID = sz | 0x30
		if (b & 7) == 6:
			opr.val2 = GetWORD(bts[1:3])
			return 3
		else:
			t = FUN_1008d4e0(b & 7, 0)
			opr.SetB(1, t)
			t = FUN_1008d4e0(b & 7, 1)
			opr.SetB(2, t)
			return 1


def FUN_1008d150(bts, opr):
	v1 = ((bts[1] & 7) << 4) | 3
	v2 = (((UB(bts[1]) >> 3) & 7) << 4) | 3
	v3 = UB(bts[1]) >> 6
	opr.SetB(1, v1)
	opr.SetB(2, v2)
	opr.SetB(3, v3)

	if v2 == 0x43:
		opr.SetB(2, 0)
	
	b = UB(bts[0])
	if b & 0xc0 == 0:
		if v1 == 0x53:
			opr.SetB(1, 0)
			opr.val2 = GetDWORD(bts[2:6])
			return 6
		else:
			return 2
	elif b & 0xc0 == 0x40:
		opr.val2 = UB(bts[2])
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
		opr.ID = 0x10
		opr.SetB(0, ((b & 7) << 4) | sz)
		return 1
	elif (b & 0x80) == 0x80:
		opr.ID = 0x30 | sz
		if (b & 7) == 4:
			return FUN_1008d150(bts, opr)
		else:
			opr.SetB(1, ((bts[0] & 7) << 4) | 3)
			opr.val2 = GetDWORD(bts[1:5])
			return 5
	elif (b & 0x40) == 0x40:
		opr.ID = 0x30 | sz
		if (b & 7) == 4:
			return FUN_1008d150(bts, opr)
		else:
			opr.SetB(1, ((bts[0] & 7) << 4) | 3)
			opr.val2 = UB(bts[1])
			return 2
	else:
		opr.ID = 0x30 | sz
		if (b & 7) == 4:
			return FUN_1008d150(bts, opr)
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
		rki.operand[i].ID = 0x10
		rki.operand[i].SetB(0, (((UB(bts[0]) >> 3) & 7) << 4) | sz)
		#if (UB(bts[0]) == 0xe1):
		#	print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!@@@@@@@@@@@@  {:x}".format(rki.operand[i].value))
		return 0
	elif opr == 8:
		rki.operand[i].ID = 0x20 | sz
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
		rki.operand[i].ID = 0x20 | sz
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
			rki.operand[i].ID = 0x30 | sz
			rki.operand[i].val2 = GetDWORD(bts[offset:offset + 4])
			return 4
		elif rki.op67 == 0x67:
			rki.operand[i].ID = 0x30 | sz
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
			if rki.operand[i].ID == 0x10:
				rki.operand[i].ID = 0x90
			return ln
		return -1
	elif opr == 0x16:
		rki.operand[i].ID = 0x30 | sz
		rki.operand[i].SetB(1, 0x63)
		rki.operand[i].SetB(2, 0)
		rki.operand[i].SetB(3, 0)
		rki.operand[i].val2 = 0
		return 0
	elif opr == 0x17:
		rki.operand[i].ID = 0x30 | sz
		rki.operand[i].SetB(1, 0x73)
		rki.operand[i].SetB(2, 0)
		rki.operand[i].SetB(3, 0)
		rki.operand[i].val2 = 0
		return 0
	elif opr in (0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f):
		rki.operand[i].ID = 0x10
		rki.operand[i].SetB(0, ((((oprnd & 0x3f) - 0x18) & 7) << 4) | sz)
		return 0
	elif opr in (0x20, 0x21, 0x22, 0x23, 0x24, 0x25):
		rki.operand[i].ID = 0x60
		rki.operand[i].SetB(0, ((((oprnd & 0x3f) - 0x20) & 7) << 4) | sz)
		return 0
	elif opr == 0x26:
		rki.operand[i].ID = 0x20 | sz
		rki.operand[i].value = 1
		return 0
	elif opr in (0x27, 0x28, 0x29, 0x2a, 0x2b, 0x2c, 0x2d, 0x2e):
		rki.operand[i].ID = 0x70
		rki.operand[i].SetB(0, ((((oprnd & 0x3f) - 0x27) & 7) << 4) | sz)
		return 0
	else:
		print("Err incorr method")
		return -1