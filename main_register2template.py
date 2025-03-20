

import sys



template = ""

subject = 'Patient1'
data_dir = f'/deneb_disk/data_from_justin_03_11_2025/Data to be shared/{subject}/data'

all_te = [65, 80, 105, 130, 160, 200]

for te in all_te:
    for b in [0, 1000, 2000, 3000]:
        nii_file = f'{data_dir}/TE{te}_bval{b}.nii.gz'

        
        # Register the png file to the template
        # Use the following command to register the png file to the template
        # register2template.sh -i <input_file> -o <output_file> -t <template_file>
        # The output file will be saved in the same directory as the input file
        # The template file is the template image that you want to register the input file to
        # The input file is the png file that you want to register to the template
        # The output file is the registered png file    
