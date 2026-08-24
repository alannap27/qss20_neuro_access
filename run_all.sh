#!/usr/bin/env bash
# Rebuild every figure and table from the committed data.
# Scripts 01 and 02 are deliberately not in this loop. They regenerate the files
# in data/raw/ from sources that are not in the repository:
#   01_parse_atlas_pdf.py needs the WHO Neurology Atlas PDF (copyrighted)
#   02_build_dhs_inventory.py needs the DHS manifest (authenticated URLs)
# Both write outputs that are already committed; both refuse to run rather than
# fail if their input is missing, and both can be run by hand:
# python3 code/01_parse_atlas_pdf.py
# python3 code/02_build_dhs_inventory.py
# Everything from 03 onward runs offline against the contents of this repository.
set -e
cd "$(dirname "$0")"
for script in 03_clean_merge 04_analyze 05_atlas_descriptives 06_urban_rural \
              07_regression_and_interactions 08_regional_and_cadre \
              09_paired_and_dhs 10_robustness; do
  echo "=== code/${script}.py ==="
  python3 "code/${script}.py" > "output/log_${script}.txt" 2>&1
done
echo
echo "figures:"; ls -1 output/figures/*.png
echo "tables:";  ls -1 output/tables
