import os
import rasterio
import numpy
from matplotlib import pyplot as plt

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


def randomizePositionOnBoundary(img, nRandom = 50):
    from random import random
    listBoundaryPosition = getListBoundaryPositionFrom2DArray(img)
    n = len(listBoundaryPosition)
    step = n // nRandom
    listRandomizedTiles = []

    for i in range(nRandom):
        pos = round(min(n - 1, i * step + random() * step - 1))
        x, y = listBoundaryPosition[pos]
        listRandomizedTiles.append(getTileFromCenterPoint(img, x, y))

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

def normalizeWaterBody(img):
    m, n = img.shape
    for i in range(m):
        for j in range(n):
            if (img[i, j] < 0):
                img[i, j] = 1
            else:
                img[i, j] = 0
    return img

def generateContinousDatasetByFiles(listFile, count = 5, xSize = 400, ySize = 400):
    # input = append(count * xSize * ySize)
    # output = append(xSize * ySize)
    data = []
    if len(listFile) < count:
        return data
    for i in range(len(listFile) - count):
        print('[{0}/{1}] Generating from {2}...'.format(i + 1, len(listFile) - count, listFile[i]))
        # Save randomized Tile in dataPoint
        dataPoint = []

        # Number of random on boundary
        nRandom = 50

        # read on (count) continous point of time into geoTiffData
        geoTiffData = []
        for j in range(i, i + count + 1):
            geoTiffData.append(getAllWaterBodySarGeotiffImage(listFile[j]))

        # Get number of bands in sar images (usually = 2). All of them will be used.
        nBands, _, __ = geoTiffData[0].shape

        # Now generate dataset!
        for band in range(nBands):
            # get list randomzied tile based on boundary of the first point in series
            listRandomizedTiles = randomizePositionOnBoundary(geoTiffData[0][band], nRandom)
            # Now save all randomized tiles to dataPoint
            for tile in listRandomizedTiles:
                # Extract position
                topLeft, bottomRight = tile
                topLeftX, topLeftY = topLeft
                bottomRightX, bottomRightY = bottomRight

                # Add all tile to continousData
                continousData = []
                for j in range(count + 1):
                    if len(continousData) == 0:
                        continousData = [normalizeWaterBody(geoTiffData[j][band][topLeftX:bottomRightX, topLeftY:bottomRightY])]
                    else:
                        continousData = numpy.append(continousData, [normalizeWaterBody(geoTiffData[j][band][topLeftX:bottomRightX, topLeftY:bottomRightY])], axis=0)

                # Now add to dataPoint
                if len(dataPoint) == 0:
                    dataPoint = [continousData]
                else:
                    dataPoint = numpy.append(dataPoint, [continousData], axis=0)

        # Almost done. Add dataPoint to timeSeries dataset
        if len(data) == 0:
            data = dataPoint
        else:
            data = numpy.append(data, dataPoint, axis=0)
        print('Appended!')

    # Done
    return data
