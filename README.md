# Usage instruction

## Preparing your data
Download Sentinel-1 images of Tonlesap in each month in 2017, each month one pair of images which can be merged together.
Sample data can be downloaded [here](https://studenthcmusedu-my.sharepoint.com/:f:/g/personal/1512489_student_hcmus_edu_vn/EsDLezEZJkBJkuzf5bsD-CYBPsm8104mON-sHjf4LZLmrA?e=nYStgC)

## Moving data to accordant directory
Moving data to accordant directory. To do this, run:
`./PrepairData/prepairData.sh`

## Subsetting, merging and resampling data
Run:
`./PrepairData/preprocess_SAR_image.sh`

Working flow pictures can be found at [readme](https://github.com/Hydroviet/SAR_Image/tree/master/readme) directory
