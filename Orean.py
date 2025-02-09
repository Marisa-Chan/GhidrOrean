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
import thfish
import thtiger
from thobfus import *

WRKDIR = "/home/marisa/ghidra_scripts"

DEBUG = 2

VMTYPE = 0


def GetVMSig(addr):
	global VMTYPE
	bts = GetBytes(addr, 15)
	
	#PUSH PUSH JMP
	if UB(bts[0]) == 0x68 and UB(bts[5]) == 0x68 and UB(bts[10]) == 0xe9:
		xlog("Wild machine found...")
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
				xlog("Risc machine found (Generic), searching type...")
				VMTYPE = 3
			if rki.ID == OP_CALL:
				if (rki.operand[0].ID >> 4) == 3:
					xlog("Risc machine found (Version 1)...")
					VMTYPE = 3
					return 3
				if (rki.operand[0].ID >> 4) == 1:
					xlog("Risc machine found (Version 2)...")
					VMTYPE = 4
					return 4
			if rki.ID == OP_RETN:
				xlog("Cisc machine found...")
				VMTYPE = 1
				return 1
		
		VMTYPE = 1
		return 1
	else:
		VMTYPE = 0
		return 0
	

def main(addr):
	xlogOpen(WRKDIR + "/TXT/console.log")

	bts = GetBytes(addr, 5)
	if UB(bts[0]) not in (0xe8, 0xe9):
		xlog("Instruction at {:08X} isn\'t JMP or CALL".format(addr))
		return
	if DEBUG >= 2:
		xlog("Get instruction byte {:02X}".format( UB(bts[0]) ))
	
	begaddr = UINT(addr + GetSInt(bts[1:]) + 5)
	
	vmSig = GetVMSig(begaddr)
	
	xlog("Machine type {:d}".format(vmSig))
	
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

			#xlog("step2")
			vm.Analyze()

		vm.MakeSpecialHandlers()

		if vm.IatAddr:

			xlog("ok {:08x}".format(vm.pushValue))
			vm.DeVirt(0x10000)
	elif vmSig == 5:
		vm = thtiger.TIGER(WRKDIR)

		if not vm.Step0(addr):
			return

		if not vm.Step1(vm.VMAddr):
			xlog("[Wild] Failed to load zero data")
			return

		if not vm.Step2():
			xlog("[Wild] Failed to process zero data")
			return


		if not vm.KeyWalk():
			xlog("[Wild] Failed keywalk searching")
			return

		if not vm.DeofusVM():
			xlog("[Wild] Can\'t deofuscate virtual machine")
			return

		if not vm.Trace():
			xlog("[Wild] Can\'t trace")
			return
	elif vmSig == 0:
		vm = thtiger.TIGER(WRKDIR)


		mblock = GetMemBlockInfo(begaddr)
		if not mblock:
			xlog("Can't get mem block at {:08X}".format(begaddr))
			return False

		xlog("Getting section {:08X} - {:08X}".format(mblock.addr, mblock.addr + mblock.size))

		vm.mblk.data = GetBytes(mblock.addr, mblock.size)
		vm.mblk.addr = mblock.addr
		vm.mblk.size = mblock.size

		vm.DumpHandler(begaddr, 1)

		for l in CMDSimpler.GetListing(True, False):
			xlog("{}".format(l))





main(UINT(currentAddress.getOffset()))