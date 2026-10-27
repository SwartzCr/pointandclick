# Hotel Paradiso, Room 714 - ScummC build
#
#   make                  build build/tentacle.000 + build/tentacle.001
#   make assets           regenerate assets/ from tools/ (needs Python 3 + Pillow)
#   make clean
#
# Point SCUMMC at your ScummC build directory (the one containing scc, sld,
# cost and char) and SCUMMC_INC at ScummC's include/ directory.

SCUMMC     ?= $(HOME)/deps/scummc/build.vm/x86_64-gnu-gcc-13.3.0-release
SCUMMC_INC ?= $(SCUMMC)/../../include

SCC  = $(SCUMMC)/scc
SLD  = $(SCUMMC)/sld
COST = $(SCUMMC)/cost
CHAR = $(SCUMMC)/char
SOUN = $(SCUMMC)/soun

B = build

# ScummVM has no generic SCUMM v6 entry, so the output poses as Day of the
# Tentacle: files named tentacle.00x, encrypted with DOTT's 0x69 key.
OUT = $(B)/tentacle

SCC_FLAGS = -V 6 -I $(SCUMMC_INC) -I src -I $(B) -R assets -R $(B)

ROOBJS = $(B)/interface.roobj $(B)/hotel.roobj $(B)/bathroom.roobj $(B)/title.roobj $(B)/gameover.roobj

all: $(OUT).000

$(B):
	mkdir -p $(B)

$(B)/font.char: assets/font.bmp | $(B)
	$(CHAR) -ochar $@ -ibmp $< -ibmp-base 32

# Player costumes: the bathrobe and the bellhop uniform. Both use the same
# animation names, so either can be swapped onto the actor.
$(B)/%.cost $(B)/%_anim.sch: assets/%.scost $(wildcard assets/*/*.bmp) | $(B)
	cd assets && $(COST) -o ../$(B)/$*.cost -header ../$(B)/$*_anim.sch \
	    -prefix $*_anim_ $*.scost

# The rooms reference the charset and costume by name, so build those first
$(B)/interface.roobj: src/interface.scc src/hotel.sch $(B)/font.char $(B)/guest.cost $(B)/guest_anim.sch \
                    $(B)/bellhop.cost $(B)/bellhop_dirty.cost \
                    $(B)/candy.soun $(B)/rustle.soun
	$(SCC) -o $@ $(SCC_FLAGS) $<

$(B)/hotel.roobj: src/hotel.scc src/hotel.sch $(wildcard assets/*.bmp assets/objects/*.bmp) assets/hotel.box \
                $(B)/tv.soun $(B)/safe.soun $(B)/fridge.soun $(B)/drawer.soun $(B)/bed.soun $(B)/clowns.soun $(B)/phone_dial.soun $(B)/phone_hang.soun $(B)/knock.soun $(B)/honk.soun $(B)/chop.soun $(B)/sniff.soun $(B)/swoop.soun $(B)/lamp_click.soun $(B)/tv_off.soun $(B)/curtains.soun $(B)/painting.soun $(B)/party.soun $(B)/guest_anim.sch \
                $(B)/clown1.cost $(B)/clown1_anim.sch $(B)/clown2.cost $(B)/clown3.cost | $(B)
	$(SCC) -o $@ $(SCC_FLAGS) $<

$(B)/bathroom.roobj: src/bathroom.scc src/hotel.sch $(wildcard assets/*.bmp assets/objects/*.bmp) \
                   assets/bathroom.box $(B)/flush.soun $(B)/cabinet.soun $(B)/unscrew.soun $(B)/shower_curtain.soun $(B)/sink.soun $(B)/duck.soun | $(B)
	$(SCC) -o $@ $(SCC_FLAGS) $<

$(B)/gameover.roobj: src/gameover.scc src/hotel.sch assets/gameover.bmp $(wildcard assets/objects/gameover_*.bmp) \
                     $(B)/gameover.soun | $(B)
	$(SCC) -o $@ $(SCC_FLAGS) $<

$(B)/title.roobj: src/title.scc src/hotel.sch assets/title.bmp assets/cursor.bmp $(B)/theme.soun | $(B)
	$(SCC) -o $@ $(SCC_FLAGS) $<

# Sound effects: 8-bit PCM .voc files wrapped into SOUN resources
$(B)/%.soun: assets/%.voc | $(B)
	$(SOUN) -o $@ -voc $<

$(OUT).000: $(ROOBJS)
	$(SLD) -o $(OUT) -key 0x69 $(ROOBJS)
	@rm -f $(OUT).sou
	@echo "Built $(OUT).000 and $(OUT).001 - add the build/ folder to ScummVM."

assets:
	python3 tools/make_assets.py assets

clean:
	rm -rf $(B)

.PHONY: all assets clean
