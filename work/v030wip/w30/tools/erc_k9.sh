#!/bin/sh
# ERC with the KiCad 9 CLI, read-only: KiCad 7 stays installed and the schematic is checked in a scratch copy
# (never saved by KiCad 9). The KiCad 9 .deb from ppa:kicad/kicad-9.0-releases is only unpacked (dpkg -x), not installed.
#   usage: erc_k9.sh <outputs/amiga_scandoubler/hardware> <k9root (dpkg -x dir)> <scratch dir> <report>
# needs: apt-get install libprotobuf32t64 libnng1 libgit2-1.7
set -e
H=$(realpath "$1");K=$(realpath "$2");W=$3;R=$(realpath -m "$4")
mkdir -p "$W";cp "$H"/*.kicad_sch "$W"/;cp "$H"/amiga_scandoubler_v030wip.kicad_pro "$W"/amiga_scandoubler.kicad_pro
printf '(sym_lib_table\n  (version 7)\n  (lib (name "Amiga")(type "KiCad")(uri "%s/Amiga.kicad_sym")(options "")(descr ""))\n)\n' "$H" > "$W"/sym-lib-table
printf '(fp_lib_table\n  (version 7)\n  (lib (name "Amiga")(type "KiCad")(uri "%s/Amiga.pretty")(options "")(descr ""))\n)\n' "$H" > "$W"/fp-lib-table
export LD_LIBRARY_PATH=$(dirname "$(find "$K" -name 'libkicommon.so*' | head -1)")
cd "$W" && "$K"/usr/bin/kicad-cli sch erc --severity-all --units mm -o "$R" amiga_scandoubler.kicad_sch
