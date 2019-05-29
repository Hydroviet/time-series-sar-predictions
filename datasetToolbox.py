import os
import rasterio
import numpy
from matplotlib import pyplot as plt
import h5py

geoTiffPath = './GeoTiffData/'

def inside(arr, x, y):
    m, n = arr.shape
    if (x < 0) or (y < 0) or (x >= m) or (y >= n):
        return False
    return True

def isValidWaterPixel(arr, x, y):
    return inside(arr, x, y) and arr[x, y] != 0;

def isBelongedToBoundary(arr, x, y):
    if isValidWaterPixel(arr, x, y):
        return False
    return isValidWaterPixel(arr, x - 1, y) or isValidWaterPixel(arr, x + 1, y) or isValidWaterPixel(arr, x, y - 1) or isValidWaterPixel(arr, x, y + 1)

def getListBoundaryPositionFrom2DArray(arr):
    m, n = arr.shape
    result = []
    for i in range(m):
        for j in range(n):
            if isBelongedToBoundary(arr, i, j):
                result.append((i, j))
    return result

def getTileFromCenterPoint(arr, x, y, xSize = 400, ySize = 400):
    topLeftX = max(x - xSize // 2, 0)
    topLeftY = max(y - ySize // 2, 0)
    m, n = arr.shape
    bottomRightX = min(topLeftX + xSize, m - 1)
    bottomRightY = min(topLeftY + ySize, n - 1)
    topLeftX = bottomRightX - xSize
    topLeftY = bottomRightY - ySize
    return ((topLeftX, topLeftY), (bottomRightX, bottomRightY))


def randomizePositionOnBoundary(img, nRandom = 50, xSize = 400, ySize = 400):
    from random import random
    listBoundaryPosition = getListBoundaryPositionFrom2DArray(img)
    n = len(listBoundaryPosition)
    step = n // nRandom
    listRandomizedTiles = []

    for i in range(nRandom):
        pos = round(min(n - 1, i * step + random() * step - 1))
        x, y = listBoundaryPosition[pos]
        listRandomizedTiles.append(getTileFromCenterPoint(img, x, y, xSize, ySize))

    return listRandomizedTiles

def getSortedGeoTiffListByDate():
    for _, listFile, __ in os.walk(geoTiffPath):
        break
    listFile.sort()
    print('Detected {0} point of data!'.format(len(listFile)))
    return listFile

def getAllWaterBodySarGeotiffImage(path, filename = 'data_waterBody.tif'):
    try:
        ds = rasterio.open(geoTiffPath + path + '/' + filename).read()
        return ds
    except Exception as e:
        print(e)
    return []

def getAllRawGeotiffImage(path, filename = 'data.tif'):
    try:
        ds = rasterio.open(geoTiffPath + path + '/' + filename).read()
        return ds
    except Exception as e:
        print(e)
    return []

def normalizeWaterBody(img):
    # m, n = img.shape
    # for i in range(m):
    #     for j in range(n):
    #         if (img[i, j] < 0):
    #             img[i, j] = 1
    #         else:
    #             img[i, j] = 0
    return img

def saveDataToFile(data, fn, root = './output/'):
    h5f = h5py.File(root + fn, 'w')
    h5f.create_dataset('data', data=data)
    h5f.close()

def generateContinousDatasetByFiles(listFile, count = 5, nRandom = 10, xSize = 400, ySize = 400):
    # input = append(count * xSize * ySize)
    # output = append(xSize * ySize)
    print('-----------------------------------------------------')

    print('Config:')
    print('- Input: {0} data point(s)'.format(count))
    print('- Size: {0} x {1}'.format(xSize, ySize))
    print('- Randomized Tile on Boundary: {0} tile(s)'.format(nRandom))

    print('-----------------------------------------------------')

    data = []
    
    if len(listFile) < count:
        return data
    for i in range(len(listFile) - count):
        print('[{0}/{1}] Generating from {2}...'.format(i + 1, len(listFile) - count, listFile[i]))
        # Save randomized Tile in dataPoint
        # dataPoint = []

        # read on (count) continous point of time into geoTiffData
        geoTiffData = []
        for j in range(i, i + count + 1):
            geoTiffData.append(getAllRawGeotiffImage(listFile[j]))

        # Get number of bands in sar images (usually = 2). All of them will be used.
        nBands, _, __ = geoTiffData[0].shape

        waterBodySample = getAllWaterBodySarGeotiffImage(listFile[0])

        # Now generate dataset!
        for band in range(nBands):
            # get list randomzied tile based on boundary of the first point in series
            listRandomizedTiles = randomizePositionOnBoundary(waterBodySample[band], nRandom, xSize, ySize)
            # Now save all randomized tiles to dataPoint
            idRandom = 0
            for tile in listRandomizedTiles:
                idRandom += 1
                # Extract position
                topLeft, bottomRight = tile
                topLeftX, topLeftY = topLeft
                bottomRightX, bottomRightY = bottomRight
                # Add all tile to continousData
                continousData = numpy.zeros((count + 1, xSize, ySize))
                for j in range(count + 1):
                    extractedData = geoTiffData[j][band, topLeftX:bottomRightX, topLeftY:bottomRightY]
                    continousData[j, :, :] = extractedData
                    
                # # Now add to dataPoint
                # if len(dataPoint) == 0:
                #     dataPoint = [continousData]
                # else:
                #     dataPoint = numpy.append(dataPoint, [continousData], axis=0)

                # Save Datapoint (continousData)
                fn = '{0}_{1}_{2}_{3}.hdf5'.format(i+1, listFile[i], band + 1, idRandom)
                saveDataToFile(continousData, fn)
                print('--> Saved to: {0}'.format(fn))
                # return continousData              
                del continousData
                # break
            # break
        del geoTiffData
        # break
        # # Almost done. Add dataPoint to timeSeries dataset
        # if len(data) == 0:
        #     data = dataPoint
        # else:
        #     data = numpy.append(data, dataPoint, axis=0)
        # print('Appended!')

    # Done
    # return data
