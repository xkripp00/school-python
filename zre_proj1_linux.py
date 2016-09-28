#!/usr/bin/env python2.7

import sys
import math
from scipy.io import wavfile
from scipy import signal
import numpy

# fcia na vytvorenie vektoru a 
def vytvor_a(A, n):
	a = []
	a.append(1.0)
	for i in A:
		a.append(i[n])
	return a

# fcia na vytvorenie vektoru whwre
def vytvor_where(nv, l, lram):
	w = []
	if(l == 0):
		return w
	else:
		p = nv
		while(p < lram):
			w.append(p)
			p += l
		return w

# fcia z modulu utility ###################################
def float2pcm(sig, dtype="int16"):
	sig = numpy.asarray(sig)
	if(sig.dtype.kind != 'f'):
		raise TypeError("'sig' must be a float array")
	dtype = numpy.dtype(dtype)
	if(dtype.kind != 'i'):
		raise TypeError("'dtype' must be signed integer type")
	return(sig * numpy.iinfo(dtype).max).astype(dtype)

# fcia #####################################################
def syntetizuj(A, G, L, P, lram):
	Nram = len(G)
	init = numpy.zeros((P, 1), dtype = numpy.int16)
	ss = numpy.empty(0, dtype = numpy.float16)
	nextvoiced = 1
	
	for n in range(Nram):
		a = vytvor_a(A, n)
		a = numpy.array(a)
		g = numpy.array([G[n]])
		l = L[n]
		if(l == 0):
			excit = numpy.random.standard_normal((lram,)).astype('float16')
		else:
			where = vytvor_where(nextvoiced, l, lram)
			nextvoiced = where[-1] + l - lram
			excit = numpy.zeros((1, lram), dtype = numpy.float16)
			for iii in where:
				excit[0,iii-1] = 1.0
		# koniec if ################################
		
		power = 0
		# excit je rozdielne pole, podla numpy.random alebo numpy.zeros
		if(len(excit) == lram):
			for i in excit:
				power += i*i
		else:
			for j in excit[0]:
				power += j*j

		power = power / lram

		if(len(excit) == lram):
			for i in range(len(excit)):
				excit[i] = excit[i] / math.sqrt(power)
		else:
			for j in range(len(excit[0])):
				excit[0,j] = excit[0,j] / math.sqrt(power)

		synt, final = signal.lfilter(g, a, excit, zi=signal.lfilter_zi(g,a) * numpy.take(excit, [0], axis=-1), axis=-1)
		
		ss = numpy.append(ss, synt)
		init = final	
	# koniec for########################################
	return ss

def main():
	if(len(sys.argv) != 5):
		print("Nespravny pocet parametrov!")
		sys.exit(1)
	cb_lpc = str(sys.argv[1])
	cb_gain = str(sys.argv[2])
	in_cod = str(sys.argv[3])
	out_wav = str(sys.argv[4])
	
	cb512 = numpy.loadtxt(cb_lpc)
	gcb128 = numpy.loadtxt(cb_gain)
	
	asym, gsym, L = numpy.loadtxt(in_cod, unpack = True)
	asym = [int(i) for i in asym]
	gsym = [int(i) for i in gsym]
	L = [int(i) for i in L]
	
	Gdecoded = []
	for i in gsym:
		Gdecoded.append(gcb128[i-1])
	
	Adecoded = []
	for i in cb512:
		pom_pole = []
		for j in asym:
			pom_pole.append(i[j-1])
		Adecoded.append(pom_pole)
	
	vysl = syntetizuj(Adecoded, Gdecoded, L, 10, 160)
	
	wavfile.write(out_wav, 8000, float2pcm(vysl, "int16"))

if __name__ == "__main__":
	main()
