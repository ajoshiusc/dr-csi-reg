import os

from registration import nonlin_register
from multiprocessing import Pool

def process_file(te_b):
    te1, b = te_b
    nii_file = f"{data_dir}/TE{te1}_bval{b}.nii.gz"

    if os.path.exists(nii_file) and not os.path.exists(nii_file.replace(".nii.gz", ".reg.nii.gz")):
        nonlin_register(
            moving=nii_file,
            fixed=template,
            output=nii_file.replace(".nii.gz", ".reg.nii.gz"),
        )
        print(f"{nii_file}.reg.nii.gz saved")


template = "/deneb_disk/data_from_justin_03_11_2025/Data to be shared/Patient1/data/TE160_bval500.nii.gz"

subject = "wip_patient2"
res = [2.3, 2.3, 5]
all_te = [63, 80, 105, 130, 160, 200, 300]
data_dir = f"/deneb_disk/data_from_justin_03_11_2025/Data to be shared/{subject}/data"

#all_te = [65, 80, 105, 130, 160, 200]


#with Pool(5) as pool:
#    pool.map(process_file, [(te, b) for te in all_te for b in [0, 300, 500, 1000, 1500]])

for te in all_te:
    for b in [0, 300, 500, 1000, 1500]:
        process_file((te, b))
