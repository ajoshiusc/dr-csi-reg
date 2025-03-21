

import sys

from registration import nonlin_register

template = "/deneb_disk/data_from_justin_03_11_2025/Data to be shared/Patient1/data/TE160_bval500.nii.gz"

subject = 'Patient1'
data_dir = f'/deneb_disk/data_from_justin_03_11_2025/Data to be shared/{subject}/data'

all_te = [65, 80, 105, 130, 160, 200]

for te in all_te:
    for b in [0, 1000, 2000, 3000]:
        nii_file = f'{data_dir}/TE{te}_bval{b}.nii.gz'

        nonlin_register(nii_file, template, f'{nii_file}.reg.nii.gz')
        print(f'{nii_file}.reg.nii.gz saved')
  