import datasetToolbox as toolbox
import numpy
from time import time
import h5py

start = time()

print('Generate Dataset...')
listFile = toolbox.getSortedGeoTiffListByDate()
print('***********************************')
print('List DataPoint: ')
for file in listFile:
	print(file)
toolbox.generateContinousDatasetByFiles(listFile, 12, 100, 128, 128)
# print(data.shape)
# h5f = h5py.File('data2.h5', 'w')
# h5f.create_dataset('data', data=data)
# h5f.close()

print('Execution time = %.3fs' % (time() - start))
