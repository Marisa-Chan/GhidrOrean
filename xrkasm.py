from xrktbl import *
from xrkutil import *
from xrkopr import *
from xrkdsm import *
import thobfus


class xrkAsm:
	dbg = False
	lookup = None
	tables = (OP_1B, OP_2B, OP_80x, OP_81x, OP_82x, OP_83x, OP_8Fx, OP_C0x,\ #8
			  OP_C1x, OP_D0x, OP_D1x, OP_D2x, OP_D3x, OP_C6x, OP_C7x, OP_D8Cx,\ #16
			  OP_D8x, OP_D9Cx, OP_D9x, OP_DACx, OP_DAx, OP_DBCx, OP_DBx, OP_DCCx,\ #24
			  OP_DCx, OP_DDCx, OP_DDx, OP_DECx, OP_DEx, OP_DFCx, OP_DFx, OP_F6x,\ #32
			  OP_F7x, OP_FEx, OP_FFx, OP_F20F1x, OP_F30f1x, OP_660f1x, OP_F20F2x, OP_F30F2x,\ #40
			  OP_660F2x, OP_F20F5x, OP_F30F5x, OP_660F5x, OP_F30F6x, OP_660F6x, OP_F20F7x, OP_F30F7x,\ #48
			  OP_660F7x, OP_F30FBx, OP_F20FCx, OP_F30FCx, OP_660FCx, OP_F20FDx, OP_F30FDx, OP_660FDx,\ #56
			  OP_F20FEx, OP_F30FEx, OP_660FEx, OP_F20FFx, OP_660FFx, OP_0FBAx)

	MtoID = None
	
	
	def __init__(self):
		self.lookup = dict()
		self.MtoID = dict()
		for tbl in self.tables:
			for te in tbl:
				if te.ID != OP_UNDEFINED:
					if te.ID not in self.lookup:
						self.lookup[te.ID] = list()
				
					self.lookup[te.ID].append(te)
					self.MtoID[ te.MNEM.upper() ] = te.ID


		
	def CheckOprType(self, inf, i, rk):
		opr = rk.operand[i]
		tp = opr.TID()
		itp = inf.operand[i] & 0x3f
		
		if self.dbg:
			print("CheckOprType: inf {:x} {:x} {:x} {:x} {:x} {:x}".format(inf.a1, inf.a2, inf.a3, inf.b1, inf.b2, inf.b3))
			print("\ti == {:d}     itp {:x}     tp {:x}".format(i, itp, tp))
			print("\topr.value {:x}".format((UB(opr.value) >> 4)))
		
		if itp == 1:
			return tp == 0xb
		elif itp == 2:
			return tp == 4
		elif itp == 3:
			return tp == 5
		elif itp == 4:
			return (tp == 1) or (tp == 3)
		elif itp == 5:
			return tp == 0xc
		elif itp == 6:
			return tp == 1
		elif itp == 8:
			return tp == 2
		elif itp == 9:
			return tp == 2
		elif itp == 0xc:
			return tp == 3
		elif itp in (0xd, 0xe):
			return (tp == 3) and (opr.value & 0xFFFFFF00) == 0
		elif itp == 0x11:
			return tp == 1
		elif itp == 0x12:
			return tp == 6
		elif itp == 0x14:
			return tp == 9
		elif itp == 0x15:
			return (tp == 6) or (tp == 3)
		elif itp == 0x16:
			return (tp == 3) and (opr.value & 0xFFFFFF00) == 0x6300 and opr.val2 == 0
		elif itp == 0x17:
			return (tp == 3) and (opr.value & 0xFFFFFF00) == 0x7300 and opr.val2 == 0
		elif itp in (0x18,0x19,0x1a,0x1b,0x1c,0x1d,0x1e,0x1f):
			if self.dbg:
				print((UB(opr.value) >> 4) == (itp - 0x18))
			return tp == 1 and (UB(opr.value) >> 4) == (itp - 0x18)
		elif itp in (0x20,0x21,0x22,0x23,0x24,0x25):
			return tp == 6 and (UB(opr.value) >> 4) == ((inf.operand[i] & 0x3f) - 0x20)
		elif itp == 0x26:
			return (tp == 2) and (opr.value == 1)
		elif itp in (0x27,0x28,0x29,0x2a,0x2b,0x2c,0x2d,0x2e):
			return tp == 7 and (UB(opr.value) >> 4) == ((inf.operand[i] & 0x3f) - 0x27)
		return False
		
		
	def CheckOperands(self, inf, rk):
		for i in range(4):
			
			rko = rk.operand[i]
			if inf.operand[i] == 0 and rko.ID != 0:
				return False
			if inf.operand[i] != 0 and rko.ID == 0:
				return False
			
			if inf.operand[i] == 0 and rko.ID == 0:
				continue
			
			isz = GetOperandSize(rk.op66, inf.operand[i], 0)
			
			if not self.CheckOprType(inf, i, rk):
				return False
			
			if self.dbg:
				print(">>>>>>>>>>CheckOprType pass")
				print("\tisz {:d}   rko.value {:x}".format(isz, rko.value))
			
			rkID = rko.TID()
			
			if rkID in (1,6,5,4,7,9,10):
				if (rko.value & 0xf) != isz:
					return False
			elif rkID == 2:
				if rko.ID & 0xF != isz:
					return False
					
				if (inf.b1 == 0 and inf.b2 in (0x83, 0x6a, 0x6b)) or\
					(inf.operand[i] & 0x3F) == 9:
					if isz == 1 and IsSignedOverflow(rko.value, 8):
						return False
					elif isz == 2 and IsSignedOverflow(rko.value, 16):
						return False
					elif isz == 3 and IsSignedOverflow(rko.value, 32):
						return False
				else:
					if isz == 1 and UINT(rko.value) > 0xFF:
						return False
					elif isz == 2 and UINT(rko.value) > 0xFFFF:
						return False
			else:
				if rko.ID & 0xF != isz:
					return False
				
			
		return True
	
	def RkToInf(self, rk):
		if rk.ID == OP_UNDEFINED:
			return None
		if not rk.ID in self.lookup:
			if self.dbg:
				print("RkToInf: Not in lookup")
			return None
		
		for inf in self.lookup[rk.ID]:
			if inf.ID == rk.ID and self.CheckOperands(inf, rk):
				return inf
		
		if self.dbg:
			print("RkToInf: Operand check error")
			for i in range(4):
				op = rk.operand[i]
				print("OP({:d}) ID {:x} val {:x} val2 {:x}".format(i, op.ID, op.value, op.val2))
		return None
	
	def GetIntSz(self, v):
		if v & 0x80000000:
			v = -1 -((~v) & 0x7FFFFFFF)
		i = abs(v)
		if i < 0x100:
			return 1
		elif i < 0x10000:
			return 2
		else:
			return 3
		
	
	def FUN_10091fd0(self, bts, rk):
		bts[0] &= 0x38
		if (rk.value & 0xFFFF00) == 0:
			bts[0] |= 5
			OutB(bts, 1, rk.val2, 4)
			return 5
		elif rk.GetB(1) == 0 or rk.GetB(1) == 0x43 or rk.GetB(2) != 0:
			if rk.GetB(1) == 0 and rk.GetB(2) != 0:
				bts[0] |= 4
				bts[1] = 5
				bts[1] |= ((rk.GetB(2) >> 4) & 7) << 3
				bts[1] |= UB(rk.GetB(3) << 6)
				OutB(bts, 2, rk.val2, 4)
				return 6
			else:
				bts[0] |= 4
				bts[1] = 0
				v1 = 0
				v2 = 0
				
				if rk.GetB(1) == 0:
					v1 = 5
				else:
					v1 = rk.GetB(1) >> 4
				
				if rk.GetB(2) == 0:
					v2 = 4
				else:
					v2 = rk.GetB(2) >> 4
				
				if rk.val2 == 0 and rk.GetB(1) != 0x53:
					bts[1] |= v1 & 7
					bts[1] |= UB((v2 & 7) << 3)
					bts[1] |= UB(rk.GetB(3) << 6)
					return 2
				else:
					sz = self.GetIntSz(rk.val2)
					if sz == 1:
						bts[0] |= 0x40
						bts[1] |= v1 & 7
						bts[1] |= UB((v2 & 7) << 3)
						bts[1] |= UB(rk.GetB(3) << 6)
						bts[2] = UB(rk.val2)
						return 3
					else:
						bts[0] |= 0x80
						bts[1] |= v1 & 7
						bts[1] |= UB((v2 & 7) << 3)
						bts[1] |= UB(rk.GetB(3) << 6)
						OutB(bts, 2, rk.val2, 4)
						return 6
		elif rk.val2 == 0 and rk.GetB(1) != 0x53:
			bts[0] |= rk.GetB(1) >> 4
			return 1
		else:
			sz = self.GetIntSz(rk.val2)
			if sz == 1:
				bts[0] |= 0x40
				bts[0] |= (rk.GetB(1) >> 4) & 7
				bts[1] = UB(rk.val2)
				return 2
			else:
				bts[0] |= 0x80
				bts[0] |= (rk.GetB(1) >> 4) & 7
				OutB(bts, 1, rk.val2, 4)
				bts[1] = UB(rk.val2)
				return 5
	
	def AsmOperand(self, bts, oprOff, opr, i, rk):
		iopr = opr & 0x3F
		rko = rk.operand[i]
		rkidf = (rko.ID & 0xf)
		if iopr == 1:
			if rkidf == 4:
				OutB(bts, 0, rko.value, 4)
				OutB(bts, 4, rko.val2, 2)
				return 6
			elif rkidf == 3:
				OutB(bts, 0, rko.value, 2)
				OutB(bts, 2, rko.val2, 2)
				return 4
			else:
				print("AsmOperand Error1")
				return 0
		elif iopr in (2, 3, 6, 0x12, 0x14):
			bts[0] &= 0xc7
			bts[0] |= ((rko.GetB(0) >> 4) & 7) << 3
			return 0
		elif iopr == 4:
			if rk.op67 == 0:
				if rko.TID() == 1:
					bts[0] &= 0x38
					bts[0] |= 0xc0
					bts[0] |= (rko.GetB(0) >> 4) & 7
					return 1
				if rko.TID() == 3:
					return self.FUN_10091fd0(bts, rko)
			else:
				print("AsmOperand Error2")
				return 0
		elif iopr in (5, 0x15, 0x16,0x17,0x18,0x19,0x1a,0x1b,0x1c,0x1d,0x1e,0x1f,0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x29,0x2a,0x2b,0x2c,0x2d,0x2e):
			return 0
		elif iopr in (8, 9):
			if rkidf == 1:
				bts[oprOff] = UB(rko.value)
				return 1
			elif rkidf == 2:
				OutB(bts, oprOff, rko.value, 2)
				return 2
			else:
				OutB(bts, oprOff, rko.value, 4)
				return 4
		elif iopr == 0xc:
			if rk.op67 == 0:
				if rko.TID() == 3:
					return self.FUN_10091fd0(bts, rko)
				
			print("AsmOperand Error3")
			return 0
		elif iopr in (0xd,0xe):
			if rk.op67 == 0:
				OutB(bts, 0, rko.val2, 4)
				return 4
			else:
				OutB(bts, 0, rko.val2, 2)
				return 2
		elif iopr == 0x11:
			if rk.op67 == 0:
				if rko.TID() == 4:
					bts[0] &= 0x38
					bts[0] |= 0xc0
					bts[0] |= (UB(rko.value) >> 4) & 7
					return 1
				
			print("AsmOperand Error4")
			return 0	
		elif iopr == 0x15:
			if rko.TID() in (9, 3):
				return 1
			return 0
		else:
			print("AsmOperand Error")
			return 0

	def FindInfo(self, rk):
		inf = self.RkToInf(rk)
		if not inf:
			if rk.ID != OP_XCHG:
				return None

			t = rk.operand[0]
			rk.operand[0] = rk.operand[1]
			rk.operand[1] = t

			inf = self.RkToInf(rk)
			if not inf:
				return None
		return inf

	def AsmRk(self, rk):
		inf = self.FindInfo(rk)
		if not inf:
			return None

		if self.dbg:
			print("Selected {} {:x},{:x},{:x} {:x},{:x},{:x}  ({:x},{:x},{:x},{:x})".format(inf.MNEM, inf.a1, inf.a2, inf.a3, inf.b1, inf.b2, inf.b3, inf.operand[0], inf.operand[1], inf.operand[2], inf.operand[3]))
		
		out = bytearray(64)
		off = 0
		
		if rk.opfx != 0:
			out[off] = UB(rk.opfx)
			off += 1
		if rk.op2x3x6x != 0:
			out[off] = UB(rk.op2x3x6x)
			off += 1
		if rk.op67 != 0:
			out[off] = UB(rk.op67)
			off += 1
		if rk.op66 != 0:
			out[off] = UB(rk.op66)
			off += 1
		
		if inf.a3 != 0:
			out[off] = UB(inf.a3)
			off += 1
		
		if inf.b1 != 0:
			out[off] = UB(inf.b1)
			off += 1
		
		out[off] = UB(inf.b2)
		off += 1
		
		if inf.b3 < 8:
			out[off] = inf.b3 << 3
		else:
			out[off] = inf.b3
			off += 2
		
		oprOff = 0
		for i in range(4):
			if inf.operand[i] != 0:
				oprOff += self.AsmOperand(RWSlice(out, off), oprOff, inf.operand[i], i, rk)
		
		return out[:oprOff + off]

	def MnemToOP(self, mnem):
		m = mnem.upper()
		if m == "SAL":
			m = "SHL"
		if m == "PUSHFD":
			m = "PUSHF"
		if m in self.MtoID:
			return self.MtoID[m]
		return 0

XrkAsm = xrkAsm()


def Recompute(lst, dbg = False):
	outlst = list()
	for i,cmd in enumerate(lst):

		bts = XrkAsm.AsmRk(cmd.instr)
		if bts:
			_,rk = XrkDecode(bts)
			if not dbg:
				print("({:d}) {:x} {}         {:x}:{:x} {:x}:{:x}".format(i, cmd.addr, XrkText(rk), rk.operand[0].ID, rk.operand[0].value, rk.operand[1].ID, rk.operand[1].value) )
			outlst.append(rk)
			if dbg:
				if len(bts) != len(cmd.instr.bts):
					print("({:d}) {:x} {}         {:x}:{:x} {:x}:{:x}".format(i, cmd.addr, XrkText(rk), rk.operand[0].ID,
																			 rk.operand[0].value, rk.operand[1].ID,
																			 rk.operand[1].value))
					print(' '.join('{:02x}'.format(x) for x in bts))
					print(' '.join('{:02x}'.format(x) for x in cmd.instr.bts))
					print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> len")
				else:
					for z in range(len(bts)):
						if bts[z] != cmd.instr.bts[z]:
							print("({:d}) {:x} {}         {:x}:{:x} {:x}:{:x}".format(i, cmd.addr, XrkText(rk),
																					 rk.operand[0].ID,
																					 rk.operand[0].value,
																					 rk.operand[1].ID,
																					 rk.operand[1].value))
							print(' '.join('{:02x}'.format(x) for x in bts))
							print(' '.join('{:02x}'.format(x) for x in cmd.instr.bts))
							print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> code")

							break
			#rk = cmd.instr
			#print("{:x}:{:x}({:x}) {:x}:{:x}".format( rk.operand[0].ID, rk.operand[0].value, rk.operand[0].val2, rk.operand[1].ID, rk.operand[1].value) )
		else:
			print("Recompute ERROR {:x} at {:x}".format(cmd.instr.ID, cmd.addr))
			XrkAsm.dbg = True
			bts = XrkAsm.AsmRk(cmd.instr)
			break
	#thobfus.CMDSimpler.CheckRound11_1(23, True)
	return outlst

def RecomputeRk(RK):
	bts = XrkAsm.AsmRk(RK)
	if bts:
		_,rk = XrkDecode(bts)
		return XrkText(rk)
	else:
		return ""