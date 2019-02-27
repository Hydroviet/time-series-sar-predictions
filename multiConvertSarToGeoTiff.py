import sarHelpers
from time import time
import os

dataDir = 'SarData';

for _, listFiles, __ in os.walk(dataDir):
    break

geopandasDataFilePath = 'GeoData/vnreservoirs'

triAnReservoirIdx = 7

start = time()
idx = 0

for dataPoint in listFiles:
    idx += 1
    filePath = dataDir + '/' + dataPoint
    outputDir = 'GeoTiffData/'+ dataPoint[:-5];
    print('[{0}/{1}] Processing {2}:'.format(idx, len(listFiles), filePath))
    if (dataPoint.endswith('.SAFE')):
        os.mkdir(outputDir)
        sarHelpers.preprocessSarFile(sarDownloadFilePath=filePath,
                                    geopandasDataFilePath=geopandasDataFilePath,
                                    geoDataIndex=triAnReservoirIdx,
                                    dstPath=(outputDir + '/data.tif'))
print('Execution time = %.3fs' % (time() - start))
