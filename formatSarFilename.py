import os

root = './GeoTiffData'

for _, dirs, __ in os.walk(root):
    break

for dir in dirs:
    src = os.path.join(root, dir)
    dateTime = dir.split('_')[4]
    dst = os.path.join(root, dateTime)
    print('{0} -> {1}'.format(src, dst))
    os.rename(src, dst)
