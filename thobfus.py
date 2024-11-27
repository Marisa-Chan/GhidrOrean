from xrkutil import *
from xrkdsm import *
from xrkasm import *
import inspect
import binascii

class CmdEntry:
	instr = rkInstruction()
	addr = 0
	unk1 = 0
	unk2 = 0
	unk3 = 0
	
	def __init__(self, ins = rkInstruction() , ad = 0, un1 = 0, un2 = 0, un3 = 0):
		self.instr = ins
		self.addr = ad
		self.unk1 = un1
		self.unk2 = un2
		self.unk3 = un3

	def Copy(self):
		t = CmdEntry()
		t.addr = self.addr
		t.unk1 = self.unk1
		t.unk2 = self.unk2
		t.unk3 = self.unk3
		t.instr = self.instr.Copy()
		return t


def FUN_10065850(op1, op2):
	t = UB(op2) >> 4
	if (op1 & 0xF) < (op2 & 0xF):
		return False
	else:
		if (op2 & 0xF) == 1 and t > 3:
			t = t - 4
		if (UB(op1) >> 4) == t:
			return True
	return False

def IsOpClass(opid, mv, idnn, asx):
	if mv and opid == OP_MOV:
		return True
	elif idnn and opid in (OP_INC, OP_DEC, OP_NEG, OP_NOT):
		return True
	elif asx and opid in (OP_ADD, OP_SUB, OP_XOR, OP_OR, OP_AND, OP_SHL, OP_SHR):
		return True
	return False

def FUN_10060650(rk):
	if (rk.ID == OP_ADD or rk.ID == OP_SUB) and rk.operand[1].TID() == 2 and\
	   (UINT(rk.operand[1].value) == 0xffffffff or rk.operand[1].value == 1):
		return True
	return False

ComputeValDbg = False

def ComputeVal(op, sz, val1, val2):
	if sz == 1:
		v1 = UB(val1)
		v2 = UB(val2)
	elif sz == 2:
		v1 = UWORD(val1)
		v2 = UWORD(val2)
	elif sz == 3:
		v1 = UINT(val1)
		v2 = UINT(val2)
	else:
		print("FUN_10070640 incorrect size {:d}".format(sz))
		return False, val1

	if ComputeValDbg:
		print("op {:x}   {:x} {:x}".format(op, v1, v2))
		
	if op == OP_ADD:
		v1 = v1 + v2
	elif op == OP_AND:
		v1 = v1 & v2
	elif op == OP_DEC:
		v1 = v1 - 1
	elif op == OP_INC:
		v1 = v1 + 1
	elif op == OP_NEG:
		v1 = -v1
	elif op == OP_NOT:
		v1 = ~v1
	elif op == OP_OR:
		v1 = v1 | v2
	elif op == OP_SHL:
		v1 = v1 << (v2 & 0x1f)
	elif op == OP_SHR:
		v1 = v1 >> (v2 & 0x1f)
	elif op == OP_SUB:
		v1 = v1 - v2
	elif op == OP_XOR:
		v1 = v1 ^ v2
	else:
		return False, val1
	
	if sz == 1:
		return True, (val1 & 0xFFFFFF00) | UB(v1)
	elif sz == 2:
		return True, (val1 & 0xFFFF0000) | UWORD(v1)
	elif sz == 3:
		return True, UINT(v1)


class Defus:
	unk = 0
	maxlen = 0x10000
	heap = None
	count = 0
	errAddr = -1
	errAddr2 = -1
	log = None

	def __init__(self):
		self.log = list()
		self.heap = list()
	
	def GetOP(self, a):
		for i in range(self.count):
			if self.heap[i].addr == a:
				ins = self.heap[i].instr
				t = rkInstruction()
				t.ID = ins.ID
				for z in range(4):
					t.operand[z].ID = ins.operand[z].ID
					t.operand[z].value = ins.operand[z].value
					t.operand[z].val2 = ins.operand[z].val2
				return t
		return None

	def GetOpPos(self, a):
		for i in range(self.count):
			if self.heap[i].addr == a:
				return i
		return -1
	
	def Clear(self):
		self.heap = [None] * self.maxlen
		for i in range(self.maxlen):
			self.heap[i] = CmdEntry()
		self.unk = 0
		self.count = 0
	
	def Add(self, instr, addr):
		if self.count >= self.maxlen:
			return False
		self.heap[self.count] = CmdEntry(instr, addr)
		self.count += 1
		return True
	
	def Cleaner(self, i = 0, cnt = -1):
		while cnt != 0:
			if i >= self.count:
				break
			if self.heap[i].instr.ID == 0:
				self.heap[i:self.maxlen-1] = self.heap[i+1:self.maxlen]
				#for j in range(i, self.maxlen - 1):
				#	self.heap[j] = self.heap[j + 1]
				self.heap[self.maxlen - 1] = CmdEntry()
				i -= 1
				self.count -= 1
			cnt -= 1
			i += 1

	def GetFirstAfterAddr(self, addr):
		for i in range(self.count):
			if self.heap[i].addr >= addr:
				return self.heap[i]
		return None

	def AddrToIndex(self, addr):
		for i in range(self.count):
			if self.heap[i].addr == addr:
				return i
		return -1


	def CheckCommonArithmetic(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i + 1].instr

		if op0.ID == OP_MOV and op1.ID != OP_MOV and\
		   op0.operand[0].TID() in (1, 3) and\
		   op0.operand[1].TID() == 2 and\
		   op1.operand[0].value == op0.operand[0].value and\
		   op1.operand[0].val2 == op0.operand[0].val2:

			j = 0
			while j < self.count - i:
				ojp = self.heap[i + 1 + j].instr
				if IsOpClass(ojp.ID, 0, 1, 1) and\
				   ojp.operand[0].ID == op0.operand[0].ID and\
				   ojp.operand[1].TID() in (0, 2) and\
				   ojp.operand[0].value == op0.operand[0].value and\
				   ojp.operand[0].val2 == op0.operand[0].val2 :
					j += 1
				else:
					break

			if j > 0:
				if self.unk == 1 and self.count <= i + 1 + j:
					return True #brake

				self.DebugErrModify(i, j + 1, 0)

				val = op0.operand[1].value
				for k in range(j):
					okp = self.heap[i + 1 + k].instr
					if op0.operand[0].TID() == 1:
						_,val = ComputeVal(okp.ID, op0.operand[0].GetB(0) & 0xf, val, okp.operand[1].value)
					else:
						_,val = ComputeVal(okp.ID, op0.operand[0].ID & 0xf, val, okp.operand[1].value)
					okp.ID = 0

				op0.operand[1].value = val

				self.Cleaner(i, 10 + k)
				return True #brake
		return False

	def CheckRiscArithmetic(self, i):
		return False

	def CollapseArithmetic(self, vmtp):
		i = self.count - 1
		while i >= 0:
			if vmtp in (3, 4):
				if self.CheckRiscArithmetic(i):
					break
			else:
				if self.CheckCommonArithmetic(i):
					break
			i -= 1

	def DebugErrModify(self, i, num, part):
		fun = inspect.stack()[1][3]
		j = 0

		self.log.append("{:08x} - {:08x}  {}".format(self.heap[i].addr, self.heap[i + j - 1].addr, fun))

		if self.errAddr < 0 and self.errAddr2 < 0:
			return

		adr1 = 0
		adr2 = 0

		if self.errAddr > 0:
			adr1 = self.errAddr
			adr2 = adr1 + 1

		if self.errAddr2 > 0:
			adr2 = self.errAddr2
			if adr2 < adr1:
				adr2 = adr1 + 1

		while j < num:
			cmd = self.heap[i + j]
			if cmd.addr >= adr1 and cmd.addr < adr2:
				print("Modify of 0x{:X} by {}  {:d}".format(self.errAddr, fun, part))
				j = 0

				while j < num:
					rk = self.heap[i+j].instr
					print("\t addr {:x}    {}         {:x}:{:x} {:x}:{:x}".format(self.heap[i + j].addr, RecomputeRk(rk), rk.operand[0].ID, rk.operand[0].value, rk.operand[1].ID, rk.operand[1].value))

					#print(' '.join('{:02x}'.format(x) for x in self.heap[i + j].instr.bts))

					j += 1

				break
			j += 1
	
	def CheckRound1_1(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		
		if (op0.ID == OP_SUB and op1.ID == OP_MOV) and\
		   op0.operand[0].ID == 0x10 and (op0.operand[1].ID & 0x20) and\
		   op1.operand[0].ID in (0x32, 0x33) and\
		   op1.operand[1].ID == 0x10 and op0.operand[0].GetB(0) == 0x43 and\
		   op0.operand[1].value in (2, 4) and\
		   (op1.operand[0].value & 0xFFFFFF00) == 0x00004300 and op1.operand[0].val2 == 0:
		   
			#print("CheckRound1_1")
		   
			if op1.operand[1].GetB(0) in (0x42, 0x43):
				if op2.ID == OP_ADD and\
				   op2.operand[0].TID() == 3 and op2.operand[1].TID() == 2 and\
				   (op2.operand[0].value & 0xFFFFFF00) == 0x00004300 and\
				   op2.operand[0].val2 == 0 and op2.operand[1].value in (2,4):
					op0.ID = OP_PUSH
					op0.CopyOpFields(op1)
					op0.operand[0].ID = op1.operand[1].ID
					op0.operand[0].SetB(0, op1.operand[1].GetB(0))
					op0.operand[1] = OperandInfo()
					op1.ID = 0
					op2.ID = 0
					self.DebugErrModify(i, 3, 0)
					self.Cleaner(i, 10)
			else:
				op0.ID = OP_PUSH
				op0.CopyOpFields(op1)
				op0.operand[0].ID = op1.operand[1].ID
				op0.operand[0].SetB(0, op1.operand[1].GetB(0))
				op0.operand[1] = OperandInfo()
				op1.ID = 0
				self.DebugErrModify(i, 2, 1)
				self.Cleaner(i, 10)
	
	def CheckRound1_2(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		
		if (op0.ID == OP_PUSH and op1.ID == OP_MOV) and\
		   op0.operand[0].ID == 0x10 and\
		   (op1.operand[0].ID in (0x32, 0x33)) and\
		   op1.operand[1].ID == 0x10 and\
		   (op1.operand[0].value & 0xFFFFFF00) == 0x00004300 and op1.operand[0].val2 == 0:
		   
			#print("CheckRound1_2")
		   
			if UB(op1.operand[1].value) in (0x42, 0x43):
				if op2.ID == OP_ADD and\
					op2.operand[0].TID() == 3 and op2.operand[1].TID() == 2 and\
					(op2.operand[0].value & 0xFFFFFF00) == 0x00004300 and\
					op2.operand[0].val2 == 0 and (op2.operand[1].value in (2,4)):
					op0.ID = OP_PUSH
					op0.CopyOpFields(op1)
					op0.operand[0].SetB(0, op1.operand[1].GetB(0))
					op1.ID = 0
					op2.ID = 0
					self.DebugErrModify(i, 3, 0)
					self.Cleaner(i, 10)
			else:
				op0.ID = OP_PUSH
				op0.CopyOpFields(op1)
				op0.operand[0].SetB(0, op1.operand[1].GetB(0))
				op1.ID = 0
				self.DebugErrModify(i, 2, 1)
				self.Cleaner(i, 10)
				
	def CheckRound1_3(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		
		if op0.ID == OP_PUSH and op1.ID == OP_MOV and\
		   op0.operand[0].TID() == 2 and\
		   op1.operand[0].ID in (0x32, 0x33) and\
		   op1.operand[1].ID == 0x10 and\
		   (op1.operand[0].value & 0xFFFFFF00) == 0x00004300 and op1.operand[0].val2 == 0:
		   
			#print("CheckRound1_3")
		   
			if op1.operand[1].GetB(0) in (0x42, 0x43):
				if op2.ID == OP_ADD and\
					op2.operand[0].TID() == 3 and op2.operand[1].TID() == 2 and\
					(op2.operand[0].value & 0xFFFFFF00) == 0x00004300 and\
					op2.operand[0].val2 == 0 and op2.operand[1].value in (2,4):
					op0.ID = OP_PUSH
					op0.operand[0].val2 = 0
					op0.operand[0].value = 0
					op0.operand[0].ID = op1.operand[1].ID
					op0.operand[0].SetB(0, op1.operand[1].GetB(0))
					op1.ID = 0
					op2.ID = 0
					self.DebugErrModify(i, 3, 0)
					self.Cleaner(i, 10)
			else:
				
				op0.ID = OP_PUSH
				op0.operand[0].val2 = 0
				op0.operand[0].value = 0
				op0.operand[0].ID = op1.operand[1].ID
				op0.operand[0].SetB(0, op1.operand[1].GetB(0))
				op1.ID = 0
				self.DebugErrModify(i, 2, 1)
				self.Cleaner(i, 10)
	
	def CheckRound2_1(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		
		if op0.ID == OP_MOV and op1.ID == OP_ADD and\
		   op0.operand[0].ID == 0x10 and\
		   (op0.operand[1].ID in (0x32, 0x33)) and\
		   op1.operand[0].ID == 0x10 and op1.operand[1].TID() == 2 and\
		   (op0.operand[0].GetB(0) >> 4) != 4 and\
		   (op0.operand[1].value & 0xFFFFFF00) == 0x00004300 and op0.operand[1].val2 == 0 and\
		   op1.operand[0].GetB(0) == 0x43 and (op1.operand[1].value in (2, 4)):
			#print("CheckRound2_1 1")
			op0.ID = OP_POP
			op0.operand[1].ID = 0
			op0.operand[1].value = 0
			op0.operand[1].val2 = 0
			op1.ID = 0
			self.DebugErrModify(i, 2, 0)
			self.Cleaner(i, 10)
		   
		if op0.ID == OP_MOV and\
		   op0.operand[0].ID == 0x10 and\
		   op0.operand[1].ID in (0x32,0x33) and\
		   (UB(op0.operand[0].value) >> 4) == 4 and\
		   (op0.operand[1].value & 0xFFFFFF00) == 0x00004300 and op0.operand[1].val2 == 0:
			#print("CheckRound2_1 2")
			op0.ID = OP_POP
			op0.operand[1].ID = 0
			op0.operand[1].value = 0
			op0.operand[1].val2 = 0
			self.DebugErrModify(i, 1, 1)
			self.Cleaner(i, 10)
	
	def CheckRound3_1(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		op3 = self.heap[i+3].instr
		op4 = self.heap[i+4].instr
		op5 = self.heap[i+5].instr
		
		if op0.ID == OP_PUSH and op1.ID == OP_MOV and op2.ID == OP_ADD and\
			op3.ID in (OP_ADD, OP_SUB) and\
			op4.ID == OP_XCHG and op5.ID == OP_POP and\
		   op0.operand[0].ID == 0x10 and\
		   op1.operand[0].ID == 0x10 and\
		   op1.operand[1].ID == 0x10 and\
		   op2.operand[0].ID == 0x10 and\
		   op2.operand[1].TID() == 2 and\
		   op3.operand[0].ID == 0x10 and\
		   op3.operand[1].TID() == 2 and\
		   ((op4.operand[0].ID == 0x33 and op4.operand[1].ID == 0x10) or (op4.operand[1].ID == 0x33 and op4.operand[0].ID == 0x10)) and\
		   op5.operand[0].ID == 0x10 and\
		   op0.operand[0].GetB(0) != 0x43 and\
		   op1.operand[0].GetB(0) == op0.operand[0].GetB(0) and\
		   op1.operand[1].GetB(0) == 0x43 and\
		   op2.operand[0].GetB(0) == op0.operand[0].GetB(0) and\
		   op2.operand[1].value == 4 and\
		   op3.operand[0].GetB(0) == op0.operand[0].GetB(0) and\
		   (((op4.operand[0].value & 0xFFFFFF00) == 0x00004300 and op4.operand[0].val2 == 0 and\
		   op4.operand[1].GetB(0) == op0.operand[0].GetB(0)) or\
		   ((op4.operand[1].value & 0xFFFFFF00) == 0x00004300 and op4.operand[1].val2 == 0 and\
		   op4.operand[0].GetB(0) == op0.operand[0].GetB(0))) and\
		   op5.operand[0].GetB(0) == 0x43:
		   
			#print("CheckRound3_1")
			op0.ID = op3.ID
			op0.operand[0].ID = 0x10
			op0.operand[0].SetB(0, 0x43)
			op0.operand[1].ID = 0x23
			op0.operand[1].value = op3.operand[1].value
			op1.ID = 0
			op2.ID = 0
			op3.ID = 0
			op4.ID = 0
			op5.ID = 0
			self.DebugErrModify(i, 6, 0)
			self.Cleaner(i, 10)
	
	def CheckRound4_1(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		
		if op0.ID == OP_XOR and op1.ID == OP_XOR and op2.ID == OP_XOR and\
		   op0.operand[0].ID == op1.operand[1].ID and\
		   op1.operand[1].ID == op2.operand[0].ID and\
		   op0.operand[1].ID == op1.operand[0].ID and\
		   op1.operand[0].ID == op2.operand[1].ID and\
		   op0.operand[0].value == op1.operand[1].value and\
		   op0.operand[0].val2 == op1.operand[1].val2 and\
		   op1.operand[1].value == op2.operand[0].value and\
		   op1.operand[1].val2 == op2.operand[0].val2 and\
		   op0.operand[1].value == op1.operand[0].value and\
		   op0.operand[1].val2 == op1.operand[0].val2 and\
		   op1.operand[0].value == op2.operand[1].value and\
		   op1.operand[0].val2 == op2.operand[1].val2:		   
			#print("CheckXorXorXor1")
			op0.ID = OP_XCHG
			op0.operand[0].ID = op1.operand[0].ID
			op0.operand[0].value = op1.operand[0].value
			op0.operand[0].val2 = op1.operand[0].val2
			op0.operand[1].ID = op2.operand[0].ID
			op0.operand[1].value = op2.operand[0].value
			op0.operand[1].val2 = op2.operand[0].val2
			op1.ID = 0
			op2.ID = 0
			self.DebugErrModify(i, 3, 0)
			self.Cleaner(i, 10)

	def CheckRound4_2(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		
		if op0.ID == OP_PUSH and op1.ID == OP_MOV and op2.ID == OP_POP and\
		   op0.operand[0].ID == 0x10 and\
		   op1.operand[0].ID == 0x10 and\
		   op1.operand[1].ID == 0x33 and\
		   op2.operand[0].ID == 0x33 and\
		   op0.operand[0].GetB(0) != 0x43 and\
		   op0.operand[0].GetB(0) == op1.operand[0].GetB(0) and\
		   (op1.operand[1].value & 0xFFFFFF00) == 0x00004300 and\
		   op1.operand[1].val2 == 4 and\
		   (op2.operand[0].value & 0xFFFFFF00) == 0x00004300 and\
		   op2.operand[0].val2 == 0:
		   
			#print("CheckPushMovPop1")
			op0.ID = OP_XCHG
			op0.operand[1].ID = op2.operand[0].ID
			op0.operand[1].value = op2.operand[0].value
			op0.operand[1].val2 = op2.operand[0].val2
			op1.ID = 0
			op2.ID = 0
			self.DebugErrModify(i, 3, 0)
			self.Cleaner(i, 10)
	
	def CheckRound4_3(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		op3 = self.heap[i+3].instr
		op4 = self.heap[i+4].instr
		
		if op0.ID == OP_PUSH and op1.ID == OP_MOV and op2.ID == OP_MOV and op3.ID == OP_MOV and op4.ID == OP_POP and\
		   op0.operand[0].ID == 0x10 and op1.operand[0].ID == 0x10 and op3.operand[1].ID == 0x10 and\
		   op1.operand[0].ID == op3.operand[1].ID and\
		   op1.operand[1].ID == op2.operand[0].ID and\
		   op2.operand[1].ID == op3.operand[0].ID and\
		   op4.operand[0].ID == 0x10:
		   
			if FUN_10065850( op0.operand[0].GetB(0), op1.operand[0].GetB(0) ) and \
				op1.operand[0].GetB(0) == op3.operand[1].GetB(0) and\
				op1.operand[1].value == op2.operand[0].value and\
				op1.operand[1].val2 == op2.operand[0].val2 and\
				op2.operand[1].value == op3.operand[0].value and\
				op2.operand[1].val2 == op3.operand[0].val2 and\
				op4.operand[0].GetB(0) == op0.operand[0].GetB(0):
			
				#print("CheckPushMovMovMovPop1")
				op0.ID = OP_XCHG
				op0.CopyOpFields( op3 )
				op0.operand[0].ID = op3.operand[0].ID
				op0.operand[0].value = op3.operand[0].value
				op0.operand[0].val2 = op3.operand[0].val2
				op0.operand[1].ID = op2.operand[0].ID
				op0.operand[1].value = op2.operand[0].value
				op0.operand[1].val2 = op2.operand[0].val2
			
				if op0.operand[0].TID() == 3 and\
					op0.operand[0].GetB(1) == 0x43:
					if (op4.operand[0].value & 0xF) != 3:
						op0.operand[0].val2 = op0.operand[0].val2 - 2
					else:
						op0.operand[0].val2 = op0.operand[0].val2 - 4
			
				if op0.operand[1].TID() == 3 and\
					op0.operand[1].GetB(1) == 0x43:
					if (op4.operand[0].value & 0xF) != 3:
						op0.operand[1].val2 = op0.operand[1].val2 + 2
					else:
						op0.operand[1].val2 = op0.operand[1].val2 + 4
			
				op1.ID = 0
				op2.ID = 0
				op3.ID = 0
				op4.ID = 0
				self.DebugErrModify(i, 5, 0)
				self.Cleaner(i, 10)
	
	def CheckRound5_3(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		op3 = self.heap[i+3].instr
		op4 = self.heap[i+4].instr
		
		if op0.ID == OP_PUSH and op1.ID == OP_MOV and op2.ID == OP_MOV and\
		   IsOpClass(op3.ID, 1, 0, 1) and\
		   op4.ID == OP_POP and op0.operand[0].ID == 0x10 and\
		   op1.operand[0].ID == 0x10 and op1.operand[1].TID() == 2 and\
		   op2.operand[1].TID() == 2 and op3.operand[1].ID == 0x10 and\
		   op4.operand[0].ID == 0x10 and\
		   FUN_10065850(op0.operand[0].GetB(0), op1.operand[0].GetB(0)) and\
		   op2.operand[0].value == op3.operand[0].value and\
		   op2.operand[0].val2 == op3.operand[0].val2 and\
		   op3.operand[1].value == op1.operand[0].value and\
		   op3.operand[1].val2 == op1.operand[0].val2 and\
		   op4.operand[0].GetB(0) == op0.operand[0].GetB(0):
		   
			if op3.operand[0].TID() == 1:
				s,newval = ComputeVal(op3.ID, op3.operand[0].value & 0xF, op2.operand[1].value, op1.operand[1].value)
			elif op3.operand[0].TID() == 3:
				if op3.operand[0].GetB(1) == 0x43:
					if (op0.operand[0].value & 0xf) != 3:
						op3.operand[0].val2 = op3.operand[0].val2 - 2
					else:
						op3.operand[0].val2 = op3.operand[0].val2 - 4
				s,newval = ComputeVal(op3.ID, op3.operand[0].ID & 0xf, op2.operand[1].value, op1.operand[1].value)
			
			#print("CheckPushMovMovXX1")
			
			op0.ID = OP_MOV
			op0.CopyOpFields(op3)
			op0.operand[0].ID = op3.operand[0].ID
			op0.operand[0].value = op3.operand[0].value
			op0.operand[0].val2 = op3.operand[0].val2
			op0.operand[1].ID = op1.operand[1].ID
			op0.operand[1].value = newval
			op0.operand[1].val2 = 0
			op1.ID = 0;
			op2.ID = 0;
			op3.ID = 0;
			op4.ID = 0;
			self.DebugErrModify(i, 5, 0)
			self.Cleaner(i, 10)
	
	def CheckRound5_4(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		op3 = self.heap[i+3].instr
		op4 = self.heap[i+4].instr
		op5 = self.heap[i+5].instr

		if op0.ID == OP_PUSH and op1.ID == OP_MOV and op2.ID == OP_MOV and\
		   IsOpClass(op3.ID, 1, 0, 1) and\
		   IsOpClass(op4.ID, 1, 0, 1) and\
		   op5.ID == OP_POP and\
		   op0.operand[0].ID == 0x10 and op1.operand[0].ID == 0x10 and\
		  op1.operand[1].TID() == 2 and\
		  op2.operand[0].ID == 0x10 and op2.operand[1].TID() == 2 and\
		  op3.operand[0].ID == 0x10 and op3.operand[1].ID == 0x10 and\
		  op4.operand[0].ID == 0x10 and op4.operand[1].TID() == 2 and\
		  op5.operand[0].ID == 0x10 and\
		  FUN_10065850(op0.operand[0].GetB(0), op1.operand[0].GetB(0)) and\
		  op2.operand[0].GetB(0) == op3.operand[0].GetB(0) and\
		  op3.operand[0].GetB(0) != op1.operand[0].GetB(0) and\
		  op3.operand[0].GetB(0) == op4.operand[0].GetB(0) and\
		  op3.operand[1].GetB(0) == op1.operand[0].GetB(0) and\
		  op5.operand[0].GetB(0) == op0.operand[0].GetB(0):
			
			#print("CheckPushMovMovXXPop1")
					  
			local_14 = op2.operand[1].value
			_,local_14 = ComputeVal(op3.ID, op3.operand[0].value & 0xf, local_14, op1.operand[1].value)
			_,local_14 = ComputeVal(op4.ID, op4.operand[0].value & 0xf, local_14, op4.operand[1].value)
			
			op0.ID = OP_MOV
			op0.CopyOpFields(op3)
			op0.operand[0].ID = op3.operand[0].ID
			op0.operand[0].value = op3.operand[0].value
			op0.operand[0].val2 = op3.operand[0].val2
			op0.operand[1].ID = op1.operand[1].ID
			op0.operand[1].value = local_14
			op0.operand[1].val2 = 0
			op1.ID = 0
			op2.ID = 0
			op3.ID = 0
			op4.ID = 0
			op5.ID = 0
			self.DebugErrModify(i, 6, 0)
			self.Cleaner(i, 10)
	
	
	def CheckRound5_1(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
				
		if op0.ID == OP_PUSH and op1.ID == OP_POP and (\
		  (op0.operand[0].ID == 0x10 and op1.operand[0].ID == 0x33 and (op0.operand[0].value & 0xf) == 3) or\
		  (op0.operand[0].ID == 0x33 and op1.operand[0].ID == 0x10 and (op1.operand[0].value & 0xf) == 3) or\
		  (op0.operand[0].ID == 0x10 and op1.operand[0].ID == 0x32 and (op0.operand[0].value & 0xf) == 2) or\
		  (op0.operand[0].ID == 0x32 and op1.operand[0].ID == 0x10 and (op1.operand[0].value & 0xf) == 2) or\	
		  (op0.operand[0].ID == 0x10 and op1.operand[0].ID == 0x10) or\
		  (op0.operand[0].ID == 0x23 and op1.operand[0].ID == 0x10) or\
		  (op0.operand[0].ID == 0x22 and op1.operand[0].ID == 0x10) ):
		  
			#print("CheckPushPop1")
			op0.ID = OP_MOV
			op0.operand[1].ID = op0.operand[0].ID
			op0.operand[1].value = op0.operand[0].value
			op0.operand[1].val2 = op0.operand[0].val2
			op0.operand[0].ID = op1.operand[0].ID
			op0.operand[0].value = op1.operand[0].value
			op0.operand[0].val2 = op1.operand[0].val2
			op1.ID = 0
			self.DebugErrModify(i, 2, 0)
			self.Cleaner(i, 10)
	
	def CheckRound5_2(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		op3 = self.heap[i+3].instr
		
		if op0.ID == OP_PUSH and op2.ID == OP_POP and\
		     ( (op1.ID == OP_SUB and op3.ID == OP_ADD) or\
               (op1.ID == OP_ADD and op3.ID == OP_SUB) or\
			   (op1.ID == OP_XOR and op3.ID == OP_XOR) ) and\
		   (op0.operand[0].ID == 0x10 or op0.operand[0].TID() == 3) and\
		   op1.operand[0].TID() == 3 and\
		   op1.operand[1].TID() == 2 and\
           (op2.operand[0].ID == 0x10 or op2.operand[0].TID() == 3) and\
		   (op3.operand[0].ID == 0x10 or op3.operand[0].TID() == 3) and \
		   op3.operand[1].TID() == 2 and\
		   op3.operand[0].ID == op2.operand[0].ID and\
		   (op1.operand[0].value & 0xFFFFFF00) == 0x00004300 and\
		   op1.operand[0].val2 == 0 and\
		   op1.operand[1].value == op3.operand[1].value and\
		   op3.operand[0].value == op2.operand[0].value and\
		   op3.operand[0].val2 == op2.operand[0].val2:
		   
			#print("CheckPushXPopX1")
			op0.ID = OP_MOV
			op0.operand[1].ID = op0.operand[0].ID
			op0.operand[1].value = op0.operand[0].value
			op0.operand[1].val2 = op0.operand[0].val2
			op0.operand[0].ID = op2.operand[0].ID
			op0.operand[0].value = op2.operand[0].value
			op0.operand[0].val2 = op2.operand[0].val2
			op1.ID = 0
			op2.ID = 0
			op3.ID = 0
			self.DebugErrModify(i, 4, 0)
			self.Cleaner(i, 10)
	
	def CheckRound8_1(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		
		if ((op0.ID == OP_ADD and op2.ID == OP_SUB) or (op0.ID == OP_SUB and op2.ID == OP_ADD)) and\
		   op1.ID in (OP_ADD, OP_SUB) and\
		   op0.operand[1].TID() == 2 and\
		   op1.operand[1].TID() != 2 and\
		   op2.operand[1].TID() == 2 and\
		   op0.operand[0].ID == op1.operand[0].ID and\
		   op1.operand[0].ID == op2.operand[0].ID and\
		   op0.operand[0].value == op1.operand[0].value and\
		   op0.operand[0].val2 == op1.operand[0].val2 and\
		   op1.operand[0].value == op2.operand[0].value and\
		   op1.operand[0].val2 == op2.operand[0].val2 and\
		   op0.operand[1].value == op2.operand[1].value:
			
			#print("CheckAddSubSub1")
			op0.ID = op1.ID
			op0.operand[1].ID = op1.operand[1].ID
			op0.operand[1].value = op1.operand[1].value
			op0.operand[1].val2 = op1.operand[1].val2
			op1.ID = 0
			op2.ID = 0
			self.DebugErrModify(i, 3, 0)
			self.Cleaner(i, 10)
		   
	
	def CheckRound6_1(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		
		if op0.ID == OP_XCHG and IsOpClass(op1.ID, 0, 1, 1) and op2.ID == OP_XCHG and\
		 ((op0.operand[0].ID == op2.operand[0].ID and\
		   op0.operand[0].value == op2.operand[0].value and\
		   op0.operand[0].val2 == op2.operand[0].val2 and\
		   op0.operand[1].ID == op2.operand[1].ID and\
		   op0.operand[1].value == op2.operand[1].value and\
		   op0.operand[1].val2 == op2.operand[1].val2) or\
		  (op0.operand[0].ID == op2.operand[1].ID and\
		   op0.operand[0].value == op2.operand[1].value and\
		   op0.operand[0].val2 == op2.operand[1].val2 and\
		   op0.operand[1].ID == op2.operand[0].ID and\
		   op0.operand[1].value == op2.operand[0].value and\
		   op0.operand[1].val2 == op2.operand[0].val2)):
			if op0.operand[0].ID == op1.operand[0].ID and\
			   op0.operand[0].value == op1.operand[0].value and\
			   op0.operand[0].val2 == op1.operand[0].val2 and\
			   (op1.operand[1].ID == 0 or (op1.operand[1].ID >> 4) == 2):
				
				op0.ID = op1.ID
				op0.operand[0].ID = op0.operand[1].ID
				op0.operand[0].value = op0.operand[1].value
				op0.operand[0].val2 = op0.operand[1].val2
				op0.operand[1].ID = op1.operand[1].ID
				op0.operand[1].value = op1.operand[1].value
				op0.operand[1].val2 = op1.operand[1].val2
				op1.ID = 0
				op2.ID = 0
				self.Cleaner(i, 10)
			elif op0.operand[1].ID == op1.operand[0].ID and\
			   op0.operand[1].value == op1.operand[0].value and\
			   op0.operand[1].val2 == op1.operand[0].val2 and\
			   (op1.operand[1].ID == 0 or (op1.operand[1].ID >> 4) == 2):
			   
				op0.ID = op1.ID
				op0.operand[0].ID = op0.operand[0].ID
				op0.operand[0].value = op0.operand[0].value
				op0.operand[0].val2 = op0.operand[0].val2
				op0.operand[1].ID = op1.operand[1].ID
				op0.operand[1].value = op1.operand[1].value
				op0.operand[1].val2 = op1.operand[1].val2
				op1.ID = 0
				op2.ID = 0
				self.DebugErrModify(i, 3, 0)
				self.Cleaner(i, 10)

	def CheckRound6_2(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		op3 = self.heap[i+3].instr
		
		if op0.ID == OP_XCHG and IsOpClass(op1.ID, 0, 1, 1) and IsOpClass(op2.ID, 0, 1, 1) and op3.ID == OP_XCHG and\
         ((op0.operand[0].ID == op3.operand[0].ID and\
		   op0.operand[0].value == op3.operand[0].value and\
		   op0.operand[0].val2 == op3.operand[0].val2 and\
		   op0.operand[1].ID == op3.operand[1].ID and\
           op0.operand[1].value == op3.operand[1].value and\
		   op0.operand[1].val2 == op3.operand[1].val2) or\
		  (op0.operand[0].ID == op3.operand[1].ID and\
		   op0.operand[0].value == op3.operand[1].value and\
		   op0.operand[0].val2 == op3.operand[1].val2 and\
		   op0.operand[1].ID == op3.operand[0].ID and\
		   op0.operand[1].value == op3.operand[0].value and\
		   op0.operand[1].val2 == op3.operand[0].val2)):
			
			if op0.operand[0].ID == op1.operand[0].ID and\
			   op0.operand[0].value == op1.operand[0].value and\
			   op0.operand[0].val2 == op1.operand[0].val2 and\
			   (op1.operand[1].ID == 0 or (op1.operand[1].ID >> 4) == 2) and\
			   op2.operand[0].ID == op1.operand[0].ID and\
			   op2.operand[0].value == op1.operand[0].value and\
			   op2.operand[0].val2 == op1.operand[0].val2 and\
               (op2.operand[1].ID == 0 or (op2.operand[1].ID >> 4) == 2):
			   
				op0.ID = op1.ID
				op0.operand[0].ID = op0.operand[1].ID
				op0.operand[0].value = op0.operand[1].value
				op0.operand[0].val2 = op0.operand[1].val2
				op0.operand[1].ID = op1.operand[1].ID
				op0.operand[1].value = op1.operand[1].value
				op0.operand[1].val2 = op1.operand[1].val2
				
				op1.ID = op2.ID
				
				op1.operand[0].ID = op0.operand[0].ID
				op1.operand[0].value = op0.operand[0].value
				op1.operand[0].val2 = op0.operand[0].val2
				
				op1.operand[1].ID = op2.operand[1].ID
				op1.operand[1].value = op2.operand[1].value
				op1.operand[1].val2 = op2.operand[1].val2
			   
				op2.ID = 0
				op3.ID = 0
				self.DebugErrModify(i, 4, 0)
				self.Cleaner(i, 10)
			elif op0.operand[1].ID == op1.operand[0].ID and\
				 op0.operand[1].value == op1.operand[0].value and\
				 op0.operand[1].val2 == op1.operand[0].val2 and\
				 (op1.operand[1].ID == 0 or (op1.operand[1].ID >> 4) == 2):
				 
				op0.ID = op1.ID
				op0.operand[0].ID = op0.operand[0].ID
				op0.operand[0].value = op0.operand[0].value
				op0.operand[0].val2 = op0.operand[0].val2
				op0.operand[1].ID = op1.operand[1].ID
				op0.operand[1].value = op1.operand[1].value
				op0.operand[1].val2 = op1.operand[1].val2
				
				op1.ID = op2.ID;
				
				op1.operand[0].ID = op0.operand[0].ID
				op1.operand[0].value = op0.operand[0].value
				op1.operand[0].val2 = op0.operand[0].val2
				
				op1.operand[1].ID = op2.operand[1].ID
				op1.operand[1].value = op2.operand[1].value
				op1.operand[1].val2 = op2.operand[1].val2
			   
				op2.ID = 0
				op3.ID = 0
				self.DebugErrModify(i, 4, 1)
				self.Cleaner(i, 10)

	def CheckRound6_3(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		
		if op0.ID == OP_PUSH and op1.ID == OP_MOV and op2.ID == OP_POP:
			if (op0.operand[0].ID >> 4) == 1 and (op1.operand[1].ID >> 4) == 1:
				if op0.operand[0].ID == op1.operand[0].ID and\
				   op1.operand[1].ID == op2.operand[0].ID and\
				   op0.operand[0].value == op1.operand[0].value and\
				   op0.operand[0].val2 == op1.operand[0].val2 and\
				   op1.operand[1].value == op2.operand[0].value and\
				   op1.operand[1].val2 == op2.operand[0].val2:
				   
					op0.ID = OP_XCHG
					op0.operand[1].ID = op1.operand[1].ID
					op0.operand[1].value = op1.operand[1].value
					op0.operand[1].val2 = op1.operand[1].val2
					op1.ID = 0
					op2.ID = 0
					self.DebugErrModify(i, 3, 0)
					self.Cleaner(i, 10)
					
			elif (op0.operand[0].ID >> 4) == 3 and (op1.operand[1].ID >> 4) == 1:
				if op0.operand[0].ID == op1.operand[0].ID and\
				   op1.operand[1].ID == op2.operand[0].ID and\
				   op1.operand[1].value == op2.operand[0].value and\
				   op1.operand[1].val2 == op2.operand[0].val2:
					
					t = 2
					if (op0.operand[0].ID & 0xf) != 2:
						t = 4
					if (op0.operand[0].value & 0xFF00) == 0x4300 and\
					   (op0.operand[0].value & 0xFFFF0000) == (op1.operand[0].value & 0xFFFF0000) and\
					   op0.operand[0].val2 == op1.operand[0].val2 + t:
					   
						op0.ID = OP_XCHG
						op0.operand[1].ID = op1.operand[1].ID
						op0.operand[1].value = op1.operand[1].value
						op0.operand[1].val2 = op1.operand[1].val2
						op1.ID = 0
						op2.ID = 0
						self.DebugErrModify(i, 3, 1)
						self.Cleaner(i, 10)
						
					elif op0.operand[0].value == op1.operand[0].value and\
						 op0.operand[0].val2 == op1.operand[0].val2:
						 
						op0.ID = OP_XCHG
						op0.operand[1].ID = op1.operand[1].ID
						op0.operand[1].value = op1.operand[1].value
						op0.operand[1].val2 = op1.operand[1].val2
						op1.ID = 0
						op2.ID = 0
						self.DebugErrModify(i, 3, 2)
						self.Cleaner(i, 10)
						
						
			elif (op0.operand[0].ID >> 4) == 1 and (op1.operand[1].ID >> 4) == 3:
				if op0.operand[0].ID == op1.operand[0].ID and\
				   op1.operand[1].ID == op2.operand[0].ID and\
				   op0.operand[0].value == op1.operand[0].value and\
				   op0.operand[0].val2 == op1.operand[0].val2:
					
					t = 2
					if (op1.operand[1].ID & 0xf) != 2:
						t = 4
						
					if (op1.operand[1].value & 0xFF00) == 0x4300 and\
					   (op1.operand[1].value & 0xFFFF0000) == (op2.operand[0].value & 0xFFFF0000) and\
					   op1.operand[1].val2 == op2.operand[0].val2 + t:
					   
						op0.ID = OP_XCHG
						op0.operand[1].ID = op2.operand[0].ID
						op0.operand[1].value = op2.operand[0].value
						op0.operand[1].val2 = op2.operand[0].val2
						op1.ID = 0
						op2.ID = 0
						self.DebugErrModify(i, 3, 4)
						self.Cleaner(i, 10)
					elif op1.operand[1].value == op2.operand[0].value and\
						 op1.operand[1].val2 == op2.operand[0].val2:
						 
						op0.ID = OP_XCHG
						op0.operand[1].ID = op1.operand[1].ID
						op0.operand[1].value = op1.operand[1].value
						op0.operand[1].val2 = op1.operand[1].val2
						op1.ID = 0
						op2.ID = 0
						self.DebugErrModify(i, 3, 5)
						self.Cleaner(i, 10)
	
	
	def CheckRound7_1(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		op3 = self.heap[i+3].instr
		
		if op0.ID == OP_PUSH and op1.ID == OP_MOV and\
		   IsOpClass(op2.ID, 1, 0, 1) and op3.ID == OP_POP and\
		   op0.operand[0].ID == 0x10 and op1.operand[0].ID == 0x10 and\
		   op2.operand[1].ID == 0x10 and op3.operand[0].ID == 0x10 and\
		   FUN_10065850(op0.operand[0].GetB(0), op1.operand[0].GetB(0)) and\
		   op2.operand[1].GetB(0) == op1.operand[0].GetB(0) and\
		   op3.operand[0].GetB(0) == op0.operand[0].GetB(0):
			
			if op2.operand[0].TID() == 3 and op2.operand[0].GetB(1) == 0x43:
				t = 4
				if (op0.operand[0].value & 0xf) != 3:
					t = 2
				op2.operand[0].val2 -= t
			
			op0.ID = op2.ID
			op0.CopyOpFields(op2)
			op0.operand[0].ID = op2.operand[0].ID
			op0.operand[0].value = op2.operand[0].value
			op0.operand[0].val2 = op2.operand[0].val2
			op0.operand[1].ID = op1.operand[1].ID
			op0.operand[1].value = op1.operand[1].value
			op0.operand[1].val2 = op1.operand[1].val2
			op1.ID = 0
			op2.ID = 0
			op3.ID = 0
			self.DebugErrModify(i, 4, 0)
			self.Cleaner(i, 10)
	
	def CheckRound7_2(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		
		if op0.ID == OP_PUSH and IsOpClass(op1.ID, 0, 1, 1) and op2.ID == OP_POP and\
		   (op0.operand[0].ID == 0x10 or op0.operand[0].TID() == 3) and\
		   op1.operand[0].TID() in (1, 3) and\
		   (op2.operand[0].ID == 0x10 or op2.operand[0].TID() == 3) and\
		   (op1.operand[0].value & 0xFFFFFF00) == 0x00004300 and\
		   op2.operand[0].value == op0.operand[0].value and\
		   op2.operand[0].val2 == op0.operand[0].val2:
		
			if op1.operand[0].val2 == 1 and\
			   (op0.operand[0].GetB(0) >> 4) < 4 and\
			   op1.operand[0].ID == 0x31 and op0.operand[0].TID() == 1:
				
				op0.ID = op1.ID
				op0.operand[0].ID = op2.operand[0].ID
				op0.operand[0].SetB(0, (((op2.operand[0].GetB(0) >> 4) + 4) << 4) | 1 )
				op0.operand[1].ID = op1.operand[1].ID
				op0.operand[1].value = op1.operand[1].value
				op0.operand[1].val2 = op1.operand[1].val2
				op1.ID = 0
				op2.ID = 0
				self.DebugErrModify(i, 3, 0)
				self.Cleaner(i, 10)
			elif op1.operand[0].val2 == 0:
				op0.ID = op1.ID
				op0.CopyOpFields(op1)
				op0.operand[0].ID = op2.operand[0].ID
				
				if op2.operand[0].TID() == 1:
					op0.operand[0].SetB(0, ((op2.operand[0].GetB(0) >> 4) << 4) | (op1.operand[0].ID & 0xf) )
				else:
					op0.operand[0].ID = (op2.operand[0].TID() << 4 | (op1.operand[0].ID & 0xf) )
				
				op0.operand[1].ID = op1.operand[1].ID
				op0.operand[1].value = op1.operand[1].value
				op0.operand[1].val2 = op1.operand[1].val2
				op1.ID = 0
				op2.ID = 0
				self.DebugErrModify(i, 3, 1)
				self.Cleaner(i, 10)
				
		   
	def CheckRound7_3(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		op3 = self.heap[i+3].instr
		
		if op0.ID == OP_PUSH and IsOpClass(op1.ID, 0, 1, 1) and IsOpClass(op2.ID, 0, 1, 1) and op3.ID == OP_POP and\
		   op0.operand[0].ID == 0x10 and\
		   op1.operand[0].TID() in (1, 3) and\
		   op2.operand[0].TID() in (1, 3) and\
		   op3.operand[0].ID == 0x10 and\
		   (op1.operand[0].value & 0xFFFFFF00) == 0x00004300 and\
		   (op2.operand[0].value & 0xFFFFFF00) == 0x00004300 and\
		   op1.operand[0].ID == op2.operand[0].ID and\
		   op1.operand[0].value == op2.operand[0].value and\
		   op1.operand[0].val2 == op2.operand[0].val2 and\
		   op3.operand[0].value == op0.operand[0].value and\
		   op3.operand[0].val2 == op0.operand[0].val2:
			
			if op1.operand[0].val2 == 1 and (op0.operand[0].GetB(0) >> 4) < 4 and\
			   op1.operand[0].ID == 0x31 and op0.operand[0].TID() == 1:
				op0.ID = op1.ID
				op0.operand[0].ID = op3.operand[0].ID
				op0.operand[0].SetB(0, (((op3.operand[0].GetB(0) >> 4) + 4) << 4) | 1)
				op0.operand[1].ID = op1.operand[1].ID
				op0.operand[1].value = op1.operand[1].value
				op0.operand[1].val2 = op1.operand[1].val2
				op1.ID = op2.ID
				op1.operand[0].ID = op3.operand[0].ID
				op1.operand[0].SetB(0, (((op3.operand[0].GetB(0) >> 4) + 4) << 4) | 1)
				op1.operand[1].ID = op2.operand[1].ID
				op1.operand[1].value = op2.operand[1].value
				op1.operand[1].val2 = op2.operand[1].val2
				op2.ID = 0
				op3.ID = 0
				self.DebugErrModify(i, 4, 0)
				self.Cleaner(i, 10)
			elif op1.operand[0].val2 == 0:
				op0.ID = op1.ID
				op0.CopyOpFields(op1)
				op0.operand[0].ID = op3.operand[0].ID
				if op3.operand[0].TID() == 1:
					op0.operand[0].val2 = 0
					op0.operand[0].value = 0
					op0.operand[0].SetB(0, ((op3.operand[0].GetB(0) >> 4) << 4) | (op1.operand[0].ID & 0xf))
				else:
					op0.operand[0].ID = ((op3.operand[0].GetB(0) >> 4) << 4) | (op1.operand[0].ID & 0xf)
				op0.operand[1].ID = op1.operand[1].ID
				op0.operand[1].value = op1.operand[1].value
				op0.operand[1].val2 = op1.operand[1].val2
				op1.ID = op2.ID
				op1.CopyOpFields(op2)
				op1.operand[0].ID = op3.operand[0].ID
				if op3.operand[0].TID() == 1:
					op1.operand[0].val2 = 0
					op1.operand[0].value = 0
					op1.operand[0].SetB(0, ((op3.operand[0].GetB(0) >> 4) << 4) | (op2.operand[0].ID & 0xf))
				else:
					op1.operand[0].ID = ((op3.operand[0].GetB(0) >> 4) << 4) | (op2.operand[0].ID & 0xf)
				op1.operand[1].ID = op2.operand[1].ID
				op1.operand[1].value = op2.operand[1].value
				op1.operand[1].val2 = op2.operand[1].val2
				op2.ID = 0
				op3.ID = 0
				self.DebugErrModify(i, 4, 1)
				self.Cleaner(i, 10)
	
	def CheckRound7_4(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		op3 = self.heap[i+3].instr
		op4 = self.heap[i+4].instr
		if op0.ID == OP_PUSH and op1.ID == OP_MOV and\
		   (IsOpClass(op2.ID, 0, 1, 1) or FUN_10060650(op2)) and\
		   op3.ID == OP_MOV and op4.ID == OP_POP and\
		   op0.operand[0].ID == 0x10 and op1.operand[0].ID == 0x10 and\
		   op1.operand[1].ID == 0x10 and op2.operand[0].ID == 0x10 and\
		   op3.operand[0].ID == 0x10 and op3.operand[1].ID == 0x10 and\
		   op4.operand[0].ID == 0x10 and\
		   FUN_10065850(op0.operand[0].GetB(0), op1.operand[0].GetB(0)) and\
		   op1.operand[0].GetB(0) == op3.operand[1].GetB(0) and\
		   op1.operand[1].GetB(0) == op3.operand[0].GetB(0) and\
		   op2.operand[0].GetB(0) == op3.operand[1].GetB(0) and\
		   op4.operand[0].GetB(0) == op0.operand[0].GetB(0):
			op0.ID = op2.ID
			op0.CopyOpFields(op2)
			op0.operand[0].ID = op3.operand[0].ID
			op0.operand[0].value = op3.operand[0].value
			op0.operand[0].val2 = op3.operand[0].val2
			op0.operand[1].ID = op2.operand[1].ID
			op0.operand[1].value = op2.operand[1].value
			op0.operand[1].val2 = op2.operand[1].val2
			op1.ID = 0
			op2.ID = 0
			op3.ID = 0
			op4.ID = 0
			self.DebugErrModify(i, 5, 0)
			self.Cleaner(i, 10)
	
	def Round9_1(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		
		if op0.ID == OP_PUSH and op1.ID == OP_MOV and\
		   op0.operand[0].ID == 0x10 and op1.operand[0].ID == 0x10 and\
		   op1.operand[1].TID() in (1,2):
			if (op1.operand[1].TID() != 1 or op1.operand[0].GetB(0) != op1.operand[1].GetB(0)) and\
			   op0.operand[0].GetB(0) == op1.operand[0].GetB(0):
				loc14 = 0
				loc18 = 0
				loc1c = 0
				if op1.operand[1].TID() == 1 and op1.operand[0].GetB(0) != op1.operand[1].GetB(0) and\
				   op1.operand[0].GetB(0) == op0.operand[0].GetB(0):
					loc18 = 1
					loc1c = op1.operand[1].GetB(0)
				j = 0
				while j < self.count - i:
					ojp0 = self.heap[i + 2 + j].instr
					ojp1 = self.heap[i + 3 + j].instr
					if not IsOpClass(ojp0.ID, 1, 1, 1):
						loc14 = 1
						break
					
					if ojp0.operand[0].ID == 0x10 and ojp0.ID != OP_MOV and\
					   ojp0.operand[1].TID() in (2,0):
						if ojp0.operand[0].GetB(0) != op1.operand[0].GetB(0):
							loc14 = 1
							break
					else:
						if ojp0.operand[0].ID != 0x10 or ojp0.ID == OP_MOV or\
						   ojp0.operand[1].TID() != 1 or\
						   ojp0.operand[0].GetB(0) == ojp0.operand[1].GetB(0):
						   
							if ojp0.operand[0].ID == 0x10 and ojp0.operand[1].TID() == 3:
								if ojp0.operand[0].GetB(0) == op1.operand[0].GetB(0) or\
								   ojp0.operand[1].GetB(1) != op1.operand[0].GetB(0) or\
								   ojp0.operand[1].GetB(2) != 0 or\
								   ojp0.operand[1].GetB(3) != 0 or\
								   ojp0.operand[1].val2 != 0 or\
								   ojp1.operand[0].GetB(0) != ojp0.operand[1].GetB(1) or\
								   ojp1.ID != OP_POP or ojp1.operand[0].ID != 0x10 or\
								   ojp1.operand[0].GetB(0) != op0.operand[0].GetB(0):
									loc14 = 1
							elif ojp0.operand[1].ID == 0x10 and ojp0.operand[0].TID() == 3:
								if ojp0.operand[1].GetB(0) == op1.operand[0].GetB(0) or\
								   ojp0.operand[0].GetB(1) != op1.operand[0].GetB(0) or\
								   ojp0.operand[0].GetB(2) != 0 or\
								   ojp0.operand[0].GetB(3) != 0 or\
								   ojp0.operand[0].val2 != 0 or\
								   ojp1.operand[0].GetB(0) != ojp0.operand[0].GetB(1) or\
								   ojp1.ID != OP_POP or ojp1.operand[0].ID != 0x10 or\
								   ojp1.operand[0].GetB(0) != op0.operand[0].GetB(0):
									loc14 = 1
							elif ojp0.operand[1].TID() == 2 and ojp0.operand[0].TID() == 3:
								if ojp0.operand[0].GetB(1) != op1.operand[0].GetB(0) or\
								   ojp0.operand[0].GetB(2) != 0 or\
								   ojp0.operand[0].GetB(3) != 0 or\
								   ojp0.operand[0].val2 != 0 or\
								   ojp1.operand[0].GetB(0) != ojp0.operand[0].GetB(1) or\
								   ojp1.ID != OP_POP or ojp1.operand[0].ID != 0x10 or\
								   ojp1.operand[0].GetB(0) != op0.operand[0].GetB(0):
									loc14 = 1
							else:
								loc14 = 1
								break
							break
							
						if ojp0.operand[0].GetB(0) != op1.operand[0].GetB(0):
							loc14 = 1
							break
					
						loc18 += 1
						loc1c = ojp0.operand[1].GetB(0)
					j += 1

				if loc14 == 0 and loc18 == 1:
					ojp0 = self.heap[i + 2 + j].instr
					ojp1 = self.heap[i + 3 + j].instr
					
					op0.ID = ojp0.ID
					op0.CopyOpFields(ojp0)
					loc20 = 0
					k = 0
					while k < j + 1:
						okp0 = self.heap[i + 1 + k].instr
						if k == 0:
							if op1.operand[1].TID() == 1:
								op1.ID = 0
							else:
								loc20 = op1.operand[1].value
								okp0.ID = 0
						else:
							if okp0.operand[1].TID() != 1:
								_,loc20 = ComputeVal(okp0.ID, op1.operand[0].GetB(0) & 0xF, loc20, okp0.operand[1].value)
							okp0.ID = 0
						k += 1
					
					ojp0.ID = 0
					ojp1.ID = 0
					if ojp0.operand[1].TID() == 3:
						op0.operand[0].val2 = 0
						op0.operand[0].value = 0
						op0.operand[0].ID = ojp0.operand[0].ID
						op0.operand[0].value = ojp0.operand[0].value
						op0.operand[0].val2 = ojp0.operand[0].val2
						op0.operand[1].ID = ojp0.operand[1].ID
						op0.operand[1].value = 0
						op0.operand[1].val2 = 0
						op0.operand[1].SetB(1, loc1c)
						op0.operand[1].SetB(2, 0)
						op0.operand[1].SetB(3, 0)
						op0.operand[1].val2 = loc20
					else:
						op0.operand[0].val2 = 0
						op0.operand[0].value = 0
						op0.operand[0].ID = ojp0.operand[0].ID
						op0.operand[0].SetB(1, loc1c)
						op0.operand[0].SetB(2, 0)
						op0.operand[0].SetB(3, 0)
						op0.operand[0].val2 = loc20
						
						op0.operand[1].ID = ojp0.operand[1].ID
						op0.operand[1].value = 0
						op0.operand[1].val2 = 0
						op0.operand[1].value = ojp0.operand[1].value
						op0.operand[1].val2 = ojp0.operand[1].val2
					self.DebugErrModify(i, j + 4, 0)
					self.Cleaner(i, 10 + j)

	def Round9_2(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		op3 = self.heap[i+3].instr
		op4 = self.heap[i+4].instr
		op5 = self.heap[i+5].instr
		op6 = self.heap[i+6].instr

		if op0.ID == OP_PUSH and op1.ID == OP_MOV and\
		   op2.ID == OP_SHL and op3.ID == OP_ADD and op4.ID == OP_ADD and\
		   IsOpClass(op5.ID, 1, 0, 1) and op6.ID == OP_POP and\
		   op0.operand[0].ID == 0x10 and op1.operand[0].ID == 0x10 and\
		   op1.operand[1].ID == 0x10 and op2.operand[0].ID == 0x10 and\
		   op2.operand[1].TID() == 2 and op3.operand[0].ID == 0x10 and\
		   op3.operand[1].TID() == 2 and op4.operand[0].ID == 0x10 and\
		   op4.operand[1].ID == 0x10 and\
		   (op5.operand[1].TID() == 3 or op5.operand[0].TID() == 3) and\
		   op6.operand[0].ID == 0x10 and\
		   op0.operand[0].GetB(0) == op1.operand[0].GetB(0) and\
		   op1.operand[0].GetB(0) == op2.operand[0].GetB(0) and\
		   op2.operand[0].GetB(0) == op3.operand[0].GetB(0) and\
		   op3.operand[0].GetB(0) == op4.operand[0].GetB(0) and\
		   op1.operand[0].GetB(0) != op1.operand[1].GetB(0) and\
		   ((op5.operand[1].GetB(1) == op2.operand[0].GetB(0) and\
		     op5.operand[1].GetB(2) == 0 and op5.operand[1].GetB(3) == 0 and\
		     op5.operand[1].val2 == 0) or\
		    (op5.operand[0].GetB(1) == op2.operand[0].GetB(0) and\
		     op5.operand[0].GetB(2) == 0 and op5.operand[0].GetB(3) == 0 and\
			 op5.operand[0].val2 == 0)) and\
		   op6.operand[0].GetB(0) == op0.operand[0].GetB(0):
		   
			op0.ID = op5.ID
			
			if op5.operand[1].TID() == 3:
				if op5.operand[1].GetB(1) == 0x43:
					t = 4
					if (op0.operand[0].GetB(0) & 0xF) != 3:
						t = 2
					op5.operand[1].val -= t
					
				op0.CopyOpFields(op5)
				op0.operand[0].ID = op5.operand[0].ID
				op0.operand[0].value = op5.operand[0].value
				op0.operand[0].val2 = op5.operand[0].val2
				op0.operand[1].ID = op5.operand[1].ID
				op0.operand[1].value = 0
				op0.operand[1].val2 = 0
				op0.operand[1].SetB(1, op4.operand[1].GetB(0))
				op0.operand[1].SetB(2, op1.operand[1].GetB(0))
				op0.operand[1].SetB(3, op2.operand[1].GetB(0))
				op0.operand[1].val2 = op3.operand[1].value
			else:
				if op5.operand[0].GetB(1) == 0x43:
					t = 4
					if (op0.operand[0].GetB(0) & 0xF) != 3:
						t = 2
					op5.operand[0].val -= t
				
				op0.CopyOpFields(op5)
				op0.operand[1].ID = op5.operand[1].ID
				op0.operand[1].value = op5.operand[1].value
				op0.operand[1].val2 = op5.operand[1].val2
				op0.operand[0].ID = op5.operand[0].ID
				op0.operand[0].value = 0
				op0.operand[0].val2 = 0
				op0.operand[0].SetB(1, op4.operand[1].GetB(0))
				op0.operand[0].SetB(2, op1.operand[1].GetB(0))
				op0.operand[0].SetB(3, op2.operand[1].GetB(0))
				op0.operand[0].val2 = op3.operand[1].value
			
			op1.ID = 0
			op2.ID = 0
			op3.ID = 0
			op4.ID = 0
			op5.ID = 0
			op6.ID = 0
			self.DebugErrModify(i, 7, 0)
			self.Cleaner(i, 10)	
	
	def CheckRound11_1(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		
		if op0.ID == OP_PUSH and op1.ID == OP_MOV and\
		   op0.operand[0].ID == 0x10 and op1.operand[0].ID == 0x10 and\
		   op1.operand[1].TID() == 2 and FUN_10065850(op0.operand[0].GetB(0), op1.operand[0].GetB(0)):
			loc14 = 0
			j = 0
			while j < self.count - i:
				ojp0 = self.heap[i + 2 + j].instr
				ojp1 = self.heap[i + 3 + j].instr
				if not IsOpClass(ojp0.ID, 1, 1, 1):
					loc14 = 1
					break
				
				if ojp0.operand[0].ID != 0x10 or ojp0.ID == OP_MOV or\
                   ojp0.operand[1].TID() not in (0, 2):
					if ojp0.operand[0].ID == 0x10 and\
					   ojp0.operand[1].TID() == 1:
						if ojp0.operand[0].GetB(0) == op1.operand[0].GetB(0) or\
						   not FUN_10065850(ojp1.operand[0].GetB(0), ojp0.operand[1].GetB(0)) or\
						   ojp1.ID != OP_POP or ojp1.operand[0].ID != 0x10 or\
						   ojp1.operand[0].GetB(0) != op0.operand[0].GetB(0):
							loc14 = 1
					else:
						if ojp0.operand[0].TID() == 3 and ojp0.operand[1].TID() == 1:
							if not FUN_10065850(ojp1.operand[0].GetB(0), ojp0.operand[1].GetB(0)) or\
							   ojp1.ID != OP_POP or ojp1.operand[0].ID != 0x10 or\
							   ojp1.operand[0].GetB(0) != op0.operand[0].GetB(0):
								loc14 = 1
						else:
							loc14 = 1
							break
					break
				if ojp0.operand[0].GetB(0) != op1.operand[0].GetB(0):
					loc14 = 1
					break
				j += 1
				
			if loc14 == 0:
				ojp0 = self.heap[i + 2 + j].instr
				ojp1 = self.heap[i + 3 + j].instr

				op0.ID = ojp0.ID
				op0.CopyOpFields(ojp0)
				op0.op66 = ojp0.op66
				op0.opfx = ojp0.opfx
				op0.op2x3x6x = ojp0.op2x3x6x
				op0.operand[0].ID = ojp0.operand[0].ID
				op0.operand[0].value = ojp0.operand[0].value
				op0.operand[0].val2 = ojp0.operand[0].val2
				op0.operand[1].value = 0
				op0.operand[1].val2 = 0
				op1.ID = 0
				
				loc18 = op1.operand[1].value
				
				k = 0
				while k < j:
					okp = self.heap[i + 2 + k].instr
					_,loc18 = ComputeVal(okp.ID, op1.operand[0].value & 0xf, loc18, okp.operand[1].value);
					okp.ID = 0
					k += 1
					
				ojp0.ID = 0
				ojp1.ID = 0
				op0.operand[1].ID = op1.operand[1].ID
				op0.operand[1].value = loc18
				if op0.operand[0].TID() == 3 and op0.operand[0].GetB(1) == 0x43:
					if (ojp1.operand[0].value & 0xf) == 3:
						op0.operand[0].val2 -= 4
					else:
						op0.operand[0].val2 -= 2

				self.DebugErrModify(i, j + 4, 0)
				self.Cleaner(i, 10 + j)

	def Round12_1(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		
		if op0.ID == OP_PUSH and op1.ID == OP_SUB and op2.ID == OP_POP and\
		   op0.operand[0].TID() == 2 and op1.operand[0].TID() == 3 and\
		   op1.operand[1].TID() == 1 and op2.operand[0].TID() == 1 and\
		   op0.operand[0].value == 0 and op1.operand[0].GetB(1) == 0x43 and\
		   op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and\
		   op1.operand[0].val2 == 0 and op1.operand[1].GetB(0) != 0x43 and\
		   op1.operand[1].GetB(0) == op2.operand[0].GetB(0):
			op0.ID = OP_NEG
			op0.operand[0].ID = op1.operand[1].ID
			op0.operand[0].value = op1.operand[1].value
			op0.operand[0].val2 = op1.operand[1].val2
			op1.ID = 0
			op2.ID = 0
			self.DebugErrModify(i, 3, 0)
			self.Cleaner(i, 10)	
			
	def Round12_2(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		
		if op0.ID == OP_NOT:
			if op1.ID == OP_INC:
				if (op0.operand[0].TID() == 3 or op0.operand[0].TID() == 1) and\
				   op0.operand[0].ID == op1.operand[0].ID and\
				   op0.operand[0].value == op1.operand[0].value and\
				   op0.operand[0].val2 == op1.operand[0].val2:
					op0.ID = OP_NEG
					op1.ID = 0
					self.DebugErrModify(i, 2, 0)
					self.Cleaner(i, 10)
			elif op1.ID == OP_ADD:
				if op1.operand[1].TID() == 2 and op1.operand[1].value == 1 and\
				   op0.operand[0].TID() in (1, 3) and\
				   op0.operand[0].ID == op1.operand[0].ID and\
				   op0.operand[0].value == op1.operand[0].value and\
				   op0.operand[0].val2 == op1.operand[0].val2:
					op0.ID = OP_NEG
					op1.ID = 0
					self.DebugErrModify(i, 2, 1)
					self.Cleaner(i, 10)
				
			elif op1.ID == OP_SUB and\
			     op1.operand[1].TID() == 2 and\
				op0.operand[0].TID() in (1, 3) and\
				 op0.operand[0].ID == op1.operand[0].ID and\
			  (((op1.operand[1].ID & 0xf) == 1 and op1.operand[1].value == 0xff) or\
			     op1.operand[1].value == 0xffffffff) and\
				 op0.operand[0].value == op1.operand[0].value and\
				 op0.operand[0].val2 == op1.operand[0].val2:
				op0.ID = OP_NEG
				op1.ID = 0
				self.DebugErrModify(i, 2, 2)
				self.Cleaner(i, 10)	
			
	
	def Round12_3(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		
		if op1.ID == OP_NOT:
			if op0.ID == OP_DEC:
				if (op1.operand[0].TID() == 3 or op1.operand[0].TID() == 1) and\
				   op1.operand[0].ID == op0.operand[0].ID and\
				   op0.operand[0].value == op1.operand[0].value and\
				   op0.operand[0].val2 == op1.operand[0].val2:
					op0.ID = OP_NEG
					op1.ID = 0
					self.DebugErrModify(i, 2, 0)
					self.Cleaner(i, 10)
			elif op0.ID == OP_ADD:
				if op0.operand[1].TID() == 2 and\
				   op1.operand[0].TID() in (1,3) and\
				   op0.operand[0].ID == op1.operand[0].ID and\
			    (((op0.operand[1].ID & 0xf) == 1 and op0.operand[1].value == 0xff) or\
			       op0.operand[1].value == 0xffffffff) and\
				   op0.operand[0].value == op1.operand[0].value and\
				   op0.operand[0].val2 == op1.operand[0].val2:
					op0.ID = OP_NEG
					op0.operand[1].ID = 0
					op0.operand[1].val2 = 0
					op0.operand[1].value = 0
					op1.ID = 0
					self.DebugErrModify(i, 2, 1)
					self.Cleaner(i, 10)	
			elif op0.ID == OP_SUB and\
				op0.operand[1].TID() == 2 and op0.operand[1].value == 1 and\
				op1.operand[0].TID() in (1, 3) and\
				   op0.operand[0].ID == op1.operand[0].ID and\
				   op0.operand[0].value == op1.operand[0].value and\
				   op0.operand[0].val2 == op1.operand[0].val2:
				op0.ID = OP_NEG
				op0.operand[1].ID = 0
				op0.operand[1].val2 = 0
				op0.operand[1].value = 0
				op1.ID = 0
				self.DebugErrModify(i, 2, 2)
				self.Cleaner(i, 10)	

	def Round12_4(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		op3 = self.heap[i+3].instr
		
		if op0.ID == OP_PUSH and op1.ID == OP_SUB and op2.ID == OP_MOV and\
		   op3.ID == OP_ADD and op0.operand[0].TID() == 2 and\
		   op1.operand[0].TID() == 3 and (op1.operand[0].ID & 0xf) == 1 and\
		   op1.operand[1].TID() == 1 and\
		   op2.operand[0].TID() == 1 and op2.operand[1].TID() == 3 and\
		   (op2.operand[1].ID & 0xf) == 1 and\
		   op3.operand[0].TID() == 1 and op3.operand[1].TID() == 2 and\
		   op0.operand[0].value == 0 and op1.operand[0].GetB(1) == 0x43 and\
		   op1.operand[0].GetB(2) == 0 and op1.operand[0].GetB(3) == 0 and\
		   op1.operand[0].val2 == 0 and\
		   op1.operand[1].GetB(0) != 0x43 and\
		   op1.operand[1].GetB(0) == op2.operand[0].GetB(0) and\
		   op2.operand[1].GetB(1) == 0x43 and\
		   op2.operand[1].GetB(2) == 0 and\
		   op2.operand[1].GetB(3) == 0 and\
		   op2.operand[1].val2 == 0 and op3.operand[0].GetB(0) == 0x43 and\
		  ((op3.operand[1].value == 2 and (op0.operand[0].ID & 0xf) == 2) or\
		   (op3.operand[1].value == 4 and (op0.operand[0].ID & 0xf) == 3)):
			op0.ID = OP_NEG
			op0.operand[0].ID = op1.operand[1].ID
			op0.operand[0].value = op1.operand[1].value
			op0.operand[0].val2 = op1.operand[1].val2
			op1.ID = 0
			op2.ID = 0
			op3.ID = 0
			self.DebugErrModify(i, 4, 0)
			self.Cleaner(i, 10)	
		   

	def Round12_5(self, i):
		op0 = self.heap[i].instr
		op1 = self.heap[i+1].instr
		op2 = self.heap[i+2].instr
		op3 = self.heap[i+3].instr
		op4 = self.heap[i+4].instr
		
		if op0.ID == OP_PUSH and\
		   op1.ID == OP_MOV and\
		   op2.ID == OP_SUB and\
		   op3.ID in (OP_MOV, OP_XCHG) and\
		   op4.ID == OP_POP and\
		   op0.operand[0].TID() == 1 and op1.operand[0].TID() == 1 and\
		   op1.operand[1].TID() == 2 and op2.operand[0].TID() == 1 and\
		   op2.operand[1].TID() in (1,3) and\
		   op3.operand[0].TID() in (1,3) and\
		   op3.operand[1].TID() in (1,3) and\
		   op4.operand[0].TID() == 1 and\
		   op1.operand[1].value == 0 and\
		   FUN_10065850(op0.operand[0].GetB(0), op1.operand[0].GetB(0)) and\
		   op1.operand[0].GetB(0) == op2.operand[0].GetB(0) and\
		   op2.operand[0].GetB(0) != op2.operand[1].GetB(0) and\
		   op0.operand[0].GetB(0) == op4.operand[0].GetB(0):
			if op3.ID == OP_MOV and\
			   op2.operand[1].val2 == op3.operand[0].val2 and\
			   op2.operand[1].value == op3.operand[0].value and\
			   op3.operand[1].GetB(0) == op2.operand[0].GetB(0):
			   
				op0.ID = OP_NEG
				op0.CopyOpFields(op2)
				op0.operand[0].ID = op2.operand[1].ID
				op0.operand[0].value = op2.operand[1].value
				op0.operand[0].val2 = op2.operand[1].val2
				op1.ID = 0
				op2.ID = 0
				op3.ID = 0
				op4.ID = 0
				self.DebugErrModify(i, 5, 0)
				self.Cleaner(i, 10)
				
			elif op3.ID == OP_XCHG and\
			   ((op2.operand[1].ID == op3.operand[0].ID and\
			     op2.operand[1].val2 == op3.operand[0].val2 and\
				 op2.operand[1].value == op3.operand[0].value and\
				 op3.operand[1].GetB(0) == op2.operand[0].GetB(0)) or\
			    (op2.operand[1].ID == op3.operand[1].ID and\
				 op2.operand[1].val2 == op3.operand[1].val2 and\
		         op2.operand[1].value == op3.operand[1].value and\
				 op3.operand[0].GetB(0) == op2.operand[0].GetB(0))):
				 
				op0.ID = OP_NEG
				op0.CopyOpFields(op2)
				op0.operand[0].ID = op2.operand[1].ID
				op0.operand[0].value = op2.operand[1].value
				op0.operand[0].val2 = op2.operand[1].val2
				op1.ID = 0
				op2.ID = 0
				op3.ID = 0
				op4.ID = 0
				self.DebugErrModify(i, 5, 1)
				self.Cleaner(i, 10)
		   

	
	def Round1(self):
		i = 0
		while i < self.count:
			self.CheckRound1_1(i)
			self.CheckRound1_2(i)
			self.CheckRound1_3(i)
			i += 1
	
	def Round2(self):
		i = self.count - 1
		while i >= 0:
			self.CheckRound2_1(i)
			i -= 1
	
			
	def Round3(self):
		i = self.count - 1
		while i >= 0:
			self.CheckRound3_1(i)
			i -= 1
	
	def Round4(self):
		i = self.count - 1
		while i >= 0:
			self.CheckRound4_1(i)
			self.CheckRound4_2(i)
			self.CheckRound4_3(i)
			i -= 1
	
	def Round5(self):
		i = self.count - 1
		while i >= 0:
			self.CheckRound5_1(i)
			self.CheckRound5_2(i)
			self.CheckRound5_3(i)
			self.CheckRound5_4(i)
			i -= 1
	
	def Round6(self):
		i = self.count - 1
		while i >= 0:
			self.CheckRound6_1(i)
			self.CheckRound6_2(i)
			self.CheckRound6_3(i)
			i -= 1
	
	def Round7(self):
		i = 0
		while i < self.count:
			self.CheckRound7_1(i)
			self.CheckRound7_2(i)
			self.CheckRound7_3(i)
			self.CheckRound7_4(i)
			i += 1
	
	def Round8(self):
		i = 0
		while i < self.count:
			self.CheckRound8_1(i)
			i += 1
	
	def Round9(self):
		i = 0
		while i < self.count:			
			self.Round9_1(i)
			self.Round9_2(i)
			i += 1
	
	def Round11(self):
		i = self.count - 1
		while i >= 0:
			self.CheckRound11_1(i)
			i -= 1
	
	def Round12(self):
		i = 0
		while i < self.count:
			self.Round12_1(i)
			self.Round12_2(i)
			self.Round12_3(i)
			self.Round12_4(i)
			self.Round12_5(i)
			i += 1


	def Clear_MovV2(self):
		i = 0
		while i < self.count:
			op = self.heap[i].instr
			if op.ID == OP_MOV and op.operand[0].ID == 0x10 and op.operand[1].ID == 0x10 and\
			   op.operand[0].GetB(0) == op.operand[1].GetB(0):
			   op.ID = 0
			i += 1

		self.Cleaner()
	
	
	def SimpleA(self, a, vm, dbg = False):
		if dbg:
			self.RebuildInfo()
			print("")
			for l in self.GetListing(True, False):
				print(l)
		while True:
			cnt = self.count
			
			self.Round1()
			self.Round2()
			self.Round3()
			self.Round4()
			self.Round5()
			self.Round6()
			self.Round7()
			self.Round8()
			self.Round9()
			
			
			self.Round11()
			self.Round12()


			#self.Cleaner()

			#ipos = self.GetOpPos(0x10ee26fd)
			#if ipos >= 0:
			#	Recompute( self.heap[ipos:ipos + 20] )
			
			#print("cnt {} {}".format(cnt, self.count))

			if dbg:
				print("cnt {} {}".format(cnt, self.count))
				self.RebuildInfo()
				for l in self.GetListing(True, False):
					print(l)

			if cnt == self.count:
				self.CollapseArithmetic(vm.tp)

				if cnt == self.count:
					break
	
	def SimpleB(self, a, vm, dbg = False):
		pass
	
	def SimpleC(self, a, vm, dbg = False):
		if dbg:
			self.RebuildInfo()
			print("")
			for l in self.GetListing(True, False):
				print(l)
		while True:
			cnt = self.count

			self.Round1()
			self.Round2()
			self.Round3()
			self.Round4()
			self.Round5()
			self.Round6()
			self.Round7()
			self.Round8()
			self.Round9()

			self.Round11()
			self.Round12()

			# self.Cleaner()

			# ipos = self.GetOpPos(0x10ee26fd)
			# if ipos >= 0:
			#	Recompute( self.heap[ipos:ipos + 20] )

			# print("cnt {} {}".format(cnt, self.count))

			if dbg:
				print("cnt {} {}".format(cnt, self.count))
				self.RebuildInfo()
				for l in self.GetListing(True, False):
					print(l)

			if cnt == self.count:
				self.CollapseArithmetic(vm.tp)

				if cnt == self.count:
					self.Clear_MovV2()

				if cnt == self.count:
					break
	
	def Simple(self, vm, a, mode, dbg = False):
		if mode == 'A':
			self.SimpleA(a, vm, dbg)
		elif mode == 'B':
			self.SimpleB(a, vm, dbg)
		elif mode == 'C':
			self.SimpleC(a, vm, dbg)

	def GetListing(self, adr, jmp):
		outlst = list()

		for i in range(self.count):
			cmd = self.heap[i]
			bts = XrkAsm.AsmRk( cmd.instr )
			if bts:
				_, rk = XrkDecode(bts)

				txt = ""
				if adr:
					txt += "{:08X} \t".format(cmd.addr)

				txt += XrkText(rk)

				if jmp:
					if rk.ID == OP_CALL and rk.operand[0].TID() == 2:
						txt += "({:08X})".format( UINT(rk.operand[0].value + 5 + cmd.addr) )
					elif rk.ID == OP_JMP and rk.operand[0].TID() == 2:
						if rk.operand[0].ID & 0xF == 1:
							txt += "({:08X})".format(UINT(rk.operand[0].value + 1 + cmd.addr))
						else:
							txt += "({:08X})".format(UINT(rk.operand[0].value + 5 + cmd.addr))
					elif rk.ID > OP_JMP and rk.ID < OP_JCXZ and rk.operand[0].TID() == 2:
						if rk.operand[0].ID & 0xF == 1:
							txt += "({:08X})".format(UINT(rk.operand[0].value + 2 + cmd.addr))
						else:
							txt += "({:08X})".format(UINT(rk.operand[0].value + 6 + cmd.addr))

				outlst.append(txt)
			else:
				print("GetListing ERROR {:x} at {:x}".format(cmd.instr.ID, cmd.addr))
				print("\t ID {:x}   op0 {:x} : {:x} ({:x})   op1 {:x} : {:x} ({:x}) ".format(cmd.instr.ID, cmd.instr.operand[0].ID, cmd.instr.operand[0].value, cmd.instr.operand[0].val2,
																							 cmd.instr.operand[1].ID, cmd.instr.operand[1].value, cmd.instr.operand[1].val2))
				XrkAsm.dbg = True
				_ = XrkAsm.AsmRk(cmd.instr)
				XrkAsm.dbg = False
				break

		return outlst

	def RebuildInfo(self):
		for i in range(self.count):
			rk = self.heap[i].instr
			rk.opInfo = XrkAsm.FindInfo(rk)

	def FUN_1005d720(self):
		opz = self.heap[self.count - 1].instr

		i = self.count - 1
		while i >= 0:
			op = self.heap[i].instr
			if not IsOpClass(op.ID, 1, 1, 1):
				return (0, 0, 0)

			if IsOpClass(op.ID, 1, 0, 1):
				if op.operand[0].TID() not in (1,3):
					return (0, 0, 0)
				if op.operand[1].TID() != 2:
					return (0, 0, 0)

				if op.operand[0].value != opz.operand[0].value or\
				   op.operand[0].val2 != opz.operand[0].val2:
					return (0, 0, 0)

				if IsOpClass(op, 0, 1, 0):
					return (1, i, op.operand[1].value)

			if not IsOpClass(op, 0, 1, 0):
				if op.operand[0].TID() not in (1, 3):
					return (0, 0, 0)

				if op.operand[0].value != opz.operand[0].value or \
				   op.operand[0].val2 != opz.operand[0].val2:
					return (0, 0, 0)

			i -= 1
		return (2, 0, 0)

	def NextOpPos(self, op, startn = 0):
		i = startn
		while i < self.count:
			if self.heap[i].instr.ID == op:
				return i
			i += 1
		return -1

	def GetAddr(self, addr):
		for i in range(self.count):
			if self.heap[i].addr == addr:
				return self.heap[i]
		return None

	def FUN_1005da10(self, vm, opid, inz, mode):
		self.unk = 1
		opz = self.heap[self.count - 1].instr
		uvr4 = 0
		if opz.ID == OP_MOV:
			return (0, inz)
		elif opz.ID == OP_CMP:
			return (1, inz)
		elif opz.ID == OP_TEST:
			return (0x101, inz)
		elif opz.ID == OP_OR and opz.operand[0].TID() == TID_REG and opz.operand[1].TID() == TID_REG and \
				opz.operand[0].GetB(0) == opz.operand[1].GetB(0):
			return (1, inz)
		else:
			(a, b, val) = self.FUN_1005d720()
			if a == 0:
				self.Simple(vm, 0xfffe, mode)
				(a, b, val) = self.FUN_1005d720()
				if a == 0:
					return (0, inz)
			l = b
			FLG = EFlags()
			while l < self.count - 1:
				op = self.heap[l].instr
				if opz.operand[0].TID() == 1:
					CalcEFlags(op.ID, op.operand[0].GetB(0) & 0xF, val, op.operand[1].value, FLG)
					_, val = ComputeVal(op.ID, op.operand[0].GetB(0) & 0xF, val, op.operand[1].value)
				else:
					CalcEFlags(op.ID, op.operand[0].ID & 0xF, val, op.operand[1].value, FLG)
					_, val = ComputeVal(op.ID, op.operand[0].ID & 0xF, val, op.operand[1].value)

				inz = FUN_1005ddf0(opid, FLG)
				l += 1
		self.unk = 0
		return (1, inz)

	def NextOp0Reg(self, i, reg):
		t = i
		while i < self.count:
			cmd = self.heap[i]
			if cmd.instr.operand[0].ID == ID_REG and cmd.instr.operand[0].GetB(0) == reg:
				return (i, cmd)
			i += 1
		return (t, None)

	def NextOp1MemReg(self, i, reg):
		t = i
		while i < self.count:
			cmd = self.heap[i]
			if cmd.instr.operand[1].TID() == TID_MEM and cmd.instr.operand[1].GetB(1) == reg:
				return (i, cmd)
			i += 1
		return (t, None)

	def NextOp0MemReg(self, i, reg):
		t = i
		while i < self.count:
			cmd = self.heap[i]
			if cmd.instr.operand[0].TID() == TID_MEM and cmd.instr.operand[0].GetB(1) == reg:
				return (i, cmd)
			i += 1
		return (t, None)

CMDSimpler = Defus()
	
	