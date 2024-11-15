from xrkutil import *
from xrkdsm import *

class RISC:
	heap = None
	heapSize = 0
	beginAddr = 0
	
	def Step1(self, addr):
		bs = GetBytes(addr, 5)
		
		if UB(bs[0]) != 0xe9:
			print("Instruction at {:08X} isn\'t JMP XXXXXXXX".format(addr))
			return False
			
		self.beginAddr = addr
		
		modAddr = UINT(addr + 5 + GetSInt(bs[1:6]))
		
		mblock = GetMemBlockInfo(modAddr)
		if not mblock:
			print("Instruction at {:08X}: Unknown Module".format(modAddr))
			return False
		
		DumpBlock(1, mblock.addr, mblock.size)
		
		tmp = GetBytes(modAddr, 16)
		_,rk = XrkDecode(tmp)
		print(hex(rk.operand[0].value))
		
		
		
		