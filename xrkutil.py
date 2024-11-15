from __main__ import *
import re
import collections

class ROSlice(collections.Sequence):
	def __init__(self, alist, start, alen = 0):
		self.alist = alist
		self.start = start
		if alen > 0:
		  self.alen = alen
		else:
		  self.alen = len(alist) - start

	def __len__(self):
		return self.alen

	def adj(self, i):
		if i<0: i += self.alen
		return i + self.start

	def __getitem__(self, key):
		if isinstance(key, int):
			return self.alist[self.adj(key)]
		elif isinstance(key, slice):
			s = self.start
			l = self.alen
			if key.start:
				s += key.start
			if key.stop and key.stop < l:
				l = key.stop
		
			return ROSlice(self.alist, s, l)	
	
	
class RWSlice(ROSlice):

    def __setitem__(self, i, v):
        self.alist[self.adj(i)] = v

    def __delitem__(self, i, v):
        del self.alist[self.adj(i)]
        self.alen -= 1

    def insert(self, i, v):
        self.alist.insert(self.adj(i), v)
        self.alen += 1

class BlkInfo():
	addr = 0
	size = 0
	def __init__(self, a = 0, s = 0):
		self.addr = a
		self.size = s

def ByteSlice(a, f, to):
	ar = bytearray(to - f)
	for i in range(f, to):
		ar[i - f] = a[i] & 0xFF
	return ar

BITS = 32


def UB(byte):
	return byte & 0xff

def UWORD(w):
	return w & 0xFFFF

def UINT(i):
	return i & 0xFFFFFFFF

def GetDWORD(bts):
	return UB(bts[0]) | UB(bts[1]) << 8 | UB(bts[2]) << 16 | UB(bts[3]) << 24

def GetWORD(bts):
	return UB(bts[0]) | UB(bts[1]) << 8

def GetSInt(bts):
	tmp = 0
	for i, b in enumerate(bts):
		tmp |= (b & 0xff) << (i * 8)
	
	sbit = 1 << ((len(bts) * 8) - 1)
	
	if tmp & (sbit):
		return (tmp & (sbit - 1)) - sbit
	return int(tmp)

def OutB(bts, pos, i, sz):
	u = i & 0xFFFFFFFF
	for j in range(sz):
		bts[j + pos] = (u >> (j * 8)) & 0xFF
	

def IsSignedOverflow(i, bits):
	SGN = 1 << (bits - 1)
	if i > 0:
		M = SGN - 1
		FM = SGN | M
		HP = i & (~FM)
		if HP and not ((i & SGN) and HP == (0xFFFFFFFF & (~FM))):
			return True
	elif i < -SGN:
		return True
	return False
	

def Addr(a, b):
	if isinstance(a, ghidra.program.model.address.Address):
		a = a.getOffset()
	if isinstance(b, ghidra.program.model.address.Address):
		b = b.getOffset()
	return toAddr((a + b) & ((1 << (BITS - 1)) - 1))


class MMBlock:
	data = None
	addr = 0
	size = 0

MemBlocks = dict()

def DumpBlock(i, start, sz):
	t = MMBlock()
	t.data = GetBytes(start, sz)
	t.addr = start
	t.size = sz
	
	MemBlocks[i] = t

def GetBytes(addr, ln):
	t = getBytes(toAddr(addr), ln)
	u = bytearray(ln)
	for i,b in enumerate(t):
		u[i] = b & 0xFF
	return u

def GetMemBlockInfo(addr):
	blk = getMemoryBlock(toAddr(addr))
	return BlkInfo(blk.getStart().getOffset(), blk.getSize())


def SPLIT(s, d):
	return filter(None, re.split("|".join(d), s) )
	