class Utils:

    def subset(product, borderRectInGeoCoor):
        from snappy import jpy
        from snappy import ProductIO
        from snappy import GPF
        from snappy import HashMap

        xmin = borderRectInGeoCoor[0]
        ymin = borderRectInGeoCoor[1]
        xmax = borderRectInGeoCoor[2]
        ymax = borderRectInGeoCoor[3]

        p1 = '%s %s' %(xmin, ymin)
        p2 = '%s %s' %(xmin, ymax)
        p3 = '%s %s' %(xmax, ymax)
        p4 = '%s %s' %(xmax, ymin)
        wkt = "POLYGON((%s, %s, %s, %s, %s))" %(p1, p2, p3, p4, p1)
        WKTReader = jpy.get_type('com.vividsolutions.jts.io.WKTReader')
        geom = WKTReader().read(wkt)

        HashMap = jpy.get_type('java.util.HashMap')
        GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

        parameters = HashMap()
        parameters.put('copyMetadata', True)
        parameters.put('geoRegion', geom)
        parameters.put('outputImageScaleInDb', False)
        subset = GPF.createProduct('Subset', parameters, product)
        return subset


    def calibrate(product):
        from snappy import jpy
        from snappy import ProductIO
        from snappy import GPF
        from snappy import HashMap

        parameters = HashMap()
        parameters.put('outputSigmaBand', True)
        parameters.put('outputImageScaleInDb', False)
        Calibrate = GPF.createProduct('Calibration', parameters, product)
        return Calibrate


    def terrainCorrection(product):
        from snappy import jpy
        from snappy import ProductIO
        from snappy import GPF
        from snappy import HashMap

        parameters = HashMap()
        parameters.put('demResamplingMethod', 'NEAREST_NEIGHBOUR')
        parameters.put('imgResamplingMethod', 'NEAREST_NEIGHBOUR')
        parameters.put('demName', 'SRTM 3Sec')
        parameters.put('pixelSpacingInMeter', 10.0)

        terrain = GPF.createProduct('Terrain-Correction', parameters, product)
        return terrain


    def speckleFilter(product):
        from snappy import jpy
        from snappy import ProductIO
        from snappy import GPF
        from snappy import HashMap

        parameters = HashMap()
        parameters.put('filter', 'Lee')
        parameters.put('filterSizeX', 5)
        parameters.put('filterSizeY', 5)
        parameters.put('dampingFactor', 2)
        parameters.put('edgeThreshold', 5000.0)
        parameters.put('estimateENL', True)
        parameters.put('enl', 1.0)

        Speckle = GPF.createProduct('Speckle-Filter', parameters, product)
        return Speckle


    def getGeoDataBorder(geopandasDataFilePath, geoDataIndex):
        '''
        Get border of geometry column in geopandas dataframe
        :type geopandasDataFilePath: string
        :type geoDataIndex: int

        :param geopandasDataFilePath: directory of geopandas dataframe file
        :param geoDataIndex: geoDataIndex of data needed to retrieve in geopandas Dataframe

        :return: List of xmin, xmax, ymin, ymax of border
        '''

        import geopandas as gpd
        from shapely.geometry import Polygon
        geoData = gpd.read_file(geopandasDataFilePath)
        geom = geoData.loc[geoDataIndex].geometry
        xmin, ymin, xmax, ymax = geom.bounds
        w, h = xmax - xmin, ymax - ymin
        xmin -= 0.05*w
        xmax += 0.05*w
        ymin -= 0.05*h
        ymax += 0.05*h
        return [xmin, ymin, xmax, ymax]


    def maskOutLake(watermask):
        import numpy as np
        from scipy.ndimage import measurements

        visited, label = measurements.label(watermask)
        area = measurements.sum(watermask, visited, index=np.arange(label + 1))
        largestElement = np.argmax(area)
        return np.where(visited==largestElement, 1, 0)


    def maskWater(vh, offset = -22):
        import numpy as np
        return np.where(vh < offset, 1, 0)


    def countPixel(mat):
        return len(np.where(mat==1))


    def createMaskLake(imgDir):
        ds = rasterio.open(imgDir)
        band = ds.read()
        waterMask = Utils.maskWater(band[0])
        return Utils.maskOutLake(waterMask)



def getGeoTiffImage(sarDownloadFilePath, geopandasDataFilePath, geoDataIndex, dstPath=None):
    '''
    Get GeoTiff image from a .SAFE folder extracted after download
    :type sarDownloadFilePath: string or list of string
    :type geopandasDataFilePath: string
    :type geoDataIndex: int
    :type dstPath: string

    :param sarDownloadFilePath: directory (or list of directory) of .SAFE folder(s)
    :param geopandasDataFilePath: directory of geopandas dataframe file
    :param geoDataIndex: geoDataIndex of data needed to retrieve in geopandas Dataframe
    :param dstPath: directory of destination file, must have '.tif' extension


    :return: None

    :example: sarHelpers.getGeoTiffImage(sarDownloadFilePath='S1A_IW_GRDH_1SDV_20170221T225238_20170221T225303_015388_019405_9C41.SAFE',
                                           geopandasDataFilePath='mekongReservoirs',
                                           geoDataIndex=0,
                                           dstPath='geotiff/1.tif')
    '''

    from snappy import jpy
    from snappy import ProductIO
    from snappy import GPF
    from snappy import HashMap

    s1meta = "manifest.safe"
    s1product = "%s/%s" % (sarDownloadFilePath, s1meta)
    reader = ProductIO.getProductReader("SENTINEL-1")
    product = reader.readProductNodes(s1product, None)
    parameters = HashMap()

    borderRectInGeoCoor = Utils.getGeoDataBorder(geopandasDataFilePath, geoDataIndex)
    subset = Utils.subset(product, borderRectInGeoCoor)
    calibrate = Utils.calibrate(subset)
    terrain = Utils.terrainCorrection(calibrate)
    terrainDB = GPF.createProduct("LinearToFromdB", parameters, terrain)
    speckle = Utils.speckleFilter(terrainDB)

    if dstPath is None:
    	dstPath = sarImgPath[:-4] + '.tif'

    ProductIO.writeProduct(speckle, dstPath, 'GeoTiff')

    product.dispose()
    subset.dispose()
    calibrate.dispose()
    terrain.dispose()
    speckle.dispose()
    del product, subset, calibrate, terrain, terrainDB, speckle
    return dstPath


def getWaterBody(sarRaster):
    '''
    Get water body of reservoir from a raster
    :type sarRaster: rasterio.io.DatasetReader (result of rasterio.open('filename'))

    :param sarRaster: raster object when loading sentinel-1 .tif image by rasterio

    :return: numpy array
    '''

    import rasterio
    import numpy as np
    from time import time

    ds = sarRaster
    band = ds.read()

    waterMask = Utils.maskWater(band[0])
    maskLake = Utils.maskOutLake(waterMask)
    waterBodyBand = np.where(maskLake == 1, band, 0)
    del maskLake, band, waterMask
    return waterBodyBand


def getWaterBodyFromFile(sarImgDir):
    '''
    Get water body of reservoir from a tif image
    :type sarImgDir: string

    :param sarImgDir: directory to sentinel-1 .tif image

    :return: numpy array
    '''

    import rasterio
    import numpy as np

    ds = rasterio.open(sarImgDir)
    return getWaterBody(ds)


def getWaterBodyFromFileAndSave(sarImgDir, sarImgDst):
    '''
    Get water body of reservoir from a tif image and save result as a .tif image
    :type sarImgDir: string
    :type sarImgDst: string

    :param sarImgDir: directory to sentinel-1 .tif image
    :param sarImgDst: directory to water body image

    :return: string - directory to water body image
    '''

    import rasterio
    import numpy as np

    ds = rasterio.open(sarImgDir)
    profile = ds.profile
    print('Getting water body')
    waterBody = getWaterBody(ds)
    with rasterio.open(sarImgDst, 'w', **profile) as dst:
        dst.write(waterBody)
    del waterBody, ds, dst
    return sarImgDst


def mergeGeoTiff(sarImgDir1, sarImgDir2, sarImgDst):
    '''
    Function to merge two geotiff images
    :type sarImgDir1: string
    :type sarImgDir2: string
    :type sarImgDst: string

    :param sarImgDir1: directory to first sentinel-1 .tif image
    :param sarImgDir2: directory to second sentinel-1 .tif image
    :param sarImgDst: directory to destination of merged image

    :return: string - directory to destination of merged image
    '''

    import rasterio
    from rasterio.merge import merge
    import numpy as np

    ds1 = rasterio.open(sarImgDir1)
    ds2 = rasterio.open(sarImgDir2)

    dest, outTransform = merge([ds1, ds2])
    profile = ds1.profile
    profile['transform'] = outTransform
    profile['height'] = dest.shape[1]
    profile['width'] = dest.shape[2]

    with rasterio.open(sarImgDst, 'w', **profile) as dst:
        dst.write(dest)
    return sarImgDst


def resize(sarImgDir, imgDst=None, maxSize=400):
    '''
    Get water body of reservoir from a tif image
    :type sarImgDir: string
    :type imgDst: string
    :type maxSize: int

    :param sarImgDir: directory to sentinel-1 .tif image
    :param imgDst: directory to resized image. If none, use default name
    :param maxSize: maximum value of width and height after resizing

    :return: string - directory to resized image
    '''

    import math
    from snappy import jpy
    from snappy import ProductIO
    from snappy import GPF
    from snappy import HashMap

    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
    HashMap = jpy.get_type('java.util.HashMap')

    p = ProductIO.readProduct(sarImgDir)
    firstBand = p.getBands()[0]
    width = firstBand.getRasterWidth()
    height = firstBand.getRasterHeight()
    ratio = width/height

    parameters = HashMap()
    if ratio <= 1:
        parameters.put('targetHeight', maxSize)
        parameters.put('targetWidth', math.ceil(maxSize*ratio))
    else:
        parameters.put('targetWidth', maxSize)
        parameters.put('targetHeight', math.ceil(maxSize/ratio))
    product = GPF.createProduct('Resample', parameters, p)

    if imgDst is None:
        sourceName = imgDir.split('/')[:-4]
        imgDst = sourceName + '_resized.tif'
    ProductIO.writeProduct(product, imgDst, 'GeoTiff')
    del p, product
    return imgDst


def preprocessSarFile(sarDownloadFilePath, geopandasDataFilePath, geoDataIndex, dstPath=None):
    '''
    Get GeoTiff image from a .SAFE folder or a list of .SAFE foloder extracted after download
    :type sarDownloadFilePath: string or list of string
    :type geopandasDataFilePath: string
    :type geoDataIndex: int
    :type dstPath: string

    :param sarDownloadFilePath: directory (or list of directory) of .SAFE folder(s)
    :param geopandasDataFilePath: directory of geopandas dataframe file
    :param geoDataIndex: geoDataIndex of data needed to retrieve in geopandas Dataframe
    :param dstPath: directory of destination file, must have '.tif' extension

    :return: string - directory to resized image

    :example: sarHelpers.preprocessSarFile(sarDownloadFilePath=['SARData/S1A_IW_GRDH_1SDV_20170221T225238_20170221T225303_015388_019405_9C41.SAFE',
                                                                'SARData/S1A_IW_GRDH_1SDV_20170221T225303_20170221T225328_015388_019405_0815.SAFE'],
                                           geopandasDataFilePath='GeoData/mekongReservoirs',
                                           geoDataIndex=0,
                                           dstPath='GeoTiff/out.tif')

              sarHelpers.preprocessSarFile(sarDownloadFilePath='SARData/S1A_IW_GRDH_1SDV_20170221T225238_20170221T225303_015388_019405_9C41.SAFE',
                                           geopandasDataFilePath='GeoData/mekongReservoirs',
                                           geoDataIndex=0,
                                           dstPath='GeoTiff1/out.tif')
    '''
    import subprocess
    from time import time
    filenamePrefix = dstPath[:-4]
    rawImg = getGeoTiffImage(sarDownloadFilePath=sarDownloadFilePath,
                            geopandasDataFilePath=geopandasDataFilePath,
                            geoDataIndex=geoDataIndex,
                            dstPath=dstPath)
    print('Raw Tiff saved at {0}'.format(rawImg))
    waterBodyFilename = getWaterBodyFromFileAndSave(rawImg, filenamePrefix + '_waterBody.tif')
    print('Water Body saved at {0}'.format(waterBodyFilename))
