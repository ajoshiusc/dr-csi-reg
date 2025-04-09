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



subject_list = ["wip_patient2", "Patient1", "Sub1 (H)", "wip_sub6 (H)", "wip_sub8 (H)"]
subject1 = subject_list[3]

template = f"/project/ajoshi_27/data/data_from_justin_03_11_2025/Data to be shared/{subject1}/data/TE160_bval500.nii.gz"


for subject in [subject1]:

    #subject = "wip_patient2"
    res = [2.3, 2.3, 5]

    data_dir = f'/project/ajoshi_27/data/data_from_justin_03_11_2025/Data to be shared/{subject}/data'

    # load the list of mat files and get the values of TEs from the file names
    all_te = []
    for filename in os.listdir(data_dir):
        if filename.endswith('.mat'):
            # extract the TE value from the filename
            te = int(filename.split('TE')[1].split('.')[0])
            all_te.append(te)
    all_te = sorted(all_te)
    #print all the TE values
    print('TE values:', all_te)



    #all_te = [63, 80, 105, 130, 160, 200, 300]
    #data_dir = f"/project/ajoshi_27/data/data_from_justin_03_11_2025/Data to be shared/{subject}/data"

    #all_te = [65, 80, 105, 130, 160, 200]


    with Pool(12) as pool:
        pool.map(process_file, [(te, b) for te in all_te for b in [0, 300, 500, 1000, 1500]])

    #for te in all_te:
    #    for b in [0, 300, 500, 1000, 1500]:
    #        process_file((te, b))


