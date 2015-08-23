# This file is part of bling.

# Bling is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Bling is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Bling.  If not, see <http://www.gnu.org/licenses/>.

all: libbuff.so test

libbuff.so: buff.o
	gcc -shared -Wl,-soname,libbuff -o libbuff.so buff.o -lbcm2835

buff.o: buff.c
	gcc -fPIC -O2 -std=c99 -c buff.c -o buff.o

test: buff.c
	gcc -o test buff.c -std=c99 -lbcm2835
