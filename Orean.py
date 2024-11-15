#TODO write a description for this script
#@author 
#@category _NEW_
#@keybinding 
#@menupath 
#@toolbar logo/orean.png
#@runtime Jython


#TODO Add User Code Here

import struct
from xrkdsm import *
from xrkutil import *
import thrisc
import thcisc

WRKDIR = "/home/marisa/ghidra_scripts"

DEBUG = 2

VMTYPE = 0


def GetVMSig(addr):
	global VMTYPE
	bts = GetBytes(addr, 15)
	
	#PUSH PUSH JMP
	if UB(bts[0]) == 0x68 and UB(bts[5]) == 0x68 and UB(bts[10]) == 0xe9:
		print("Fish machine found...")
		VMTYPE = 5
		return 5
	elif UB(bts[0]) == 0x68 and UB(bts[5]) == 0xe9:
		raddr = UINT(addr + 10 + GetSInt(bts[6:10]))
		rentr = GetBytes(raddr, 0x210)
		i = 0
		while i < 0x200:
			ln, rki = XrkDecode(rentr[i:])
			i += ln
			
			if rki.ID == OP_NOP:
				print("Risc machine found (Generic), searching type...")
				VMTYPE = 3
			if rki.ID == OP_CALL:
				if (rki.operand[0].ID >> 4) == 3:
					print("Risc machine found (Version 1)...")
					VMTYPE = 3
					return 3
				if (rki.operand[0].ID >> 4) == 1:
					print("Risc machine found (Version 2)...")
					VMTYPE = 4
					return 4
			if rki.ID == OP_RETN:
				print("Cisc machine found...")
				VMTYPE = 1
				return 1
		
		VMTYPE = 1
		return 1
	else:
		VMTYPE = 0
		return 0
	

def main(addr):
	bts = GetBytes(addr, 5)
	if UB(bts[0]) not in (0xe8, 0xe9):
		print("Instruction at {:08X} isn\'t JMP or CALL".format(addr))
		return
	if DEBUG >= 2:
		print("Get instruction byte {:02X}".format( UB(bts[0]) ))
	
	begaddr = UINT(addr + GetSInt(bts[1:]) + 5)
	
	vmSig = GetVMSig(begaddr)
	
	print("Machine type {:d}".format(vmSig))
	
	if vmSig in (3, 4):
		vm = thrisc.RISC()
		vm.Step1(addr)
		
	elif vmSig == 1:
		vm = thcisc.CISC(WRKDIR)
		if not vm.Step0(begaddr):
			return

		testAddr = vm.Step1(addr)

		if testAddr == False or not vm.LoadIat(testAddr):
			vm.Step3(0, 0, 0, 0, 0)

			#if not vm.Step2(addr):

			#print("step2")
			vm.Analyze()

		vm.MakeSpecialHandlers()

		if vm.IatAddr:

			print("ok {:08x}".format(vm.pushValue))
			vm.DeVirt(0x10000)





main(UINT(currentAddress.getOffset()))