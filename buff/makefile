all: libbuff.so test

libbuff.so: buff.o
	gcc -shared -Wl,-soname,libbuff -o libbuff.so buff.o -lbcm2835

buff.o: buff.c
	gcc -fPIC -O2 -std=c99 -c buff.c -o buff.o

test: buff.c
	gcc -o test buff.c -std=c99 -lbcm2835
