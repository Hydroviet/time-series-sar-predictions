import datasetToolbox as toolbox
import numpy
from time import time
import h5py

start = time()

print('Generate Dataset...')
listFile = toolbox.getSortedGeoTiffListByDate()
data = numpy.array(toolbox.generateContinousDatasetByFiles(listFile))
print(data.shape)
h5f = h5py.File('data.h5', 'w')
h5f.create_dataset('data', data=data)
h5f.close()

print('Execution time = %.3fs' % (time() - start))
