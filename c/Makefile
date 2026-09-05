# Depend de la bibliotheque C du depot SI (si_value) -- suppose SI/ et
# NUC/ clones cote a cote (depots freres). Surcharger SI_DIR si different :
#   make SI_DIR=/chemin/vers/SI test
SI_DIR ?= ../../SI

CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -O2 -Iinclude -I$(SI_DIR)/c/include
LDLIBS := -lm

SRC := src/nuc_periodic_table.c src/nuc_lara.c src/nuc_filiation.c src/nuc_bateman.c
OBJ := $(SRC:.c=.o)

SI_SRC := $(SI_DIR)/c/src/si_value.c
SI_OBJ := si_value.o

.PHONY: all test clean

all: libnuc.a

$(SI_OBJ): $(SI_SRC)
	$(CC) $(CFLAGS) -c -o $@ $<

libnuc.a: $(OBJ) $(SI_OBJ)
	ar rcs $@ $(OBJ) $(SI_OBJ)

test: tests/test_nuc.c libnuc.a
	$(CC) $(CFLAGS) -o tests/test_nuc tests/test_nuc.c libnuc.a $(LDLIBS)
	./tests/test_nuc

clean:
	rm -f $(OBJ) $(SI_OBJ) libnuc.a tests/test_nuc
