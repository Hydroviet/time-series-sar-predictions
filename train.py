import os
import numpy as np
import tensorflow as tf

'''
import keras
from keras.layers import BatchNormalization, TimeDistributed
'''

import tensorflow.keras as keras
from tensorflow.python.keras.layers import BatchNormalization, TimeDistributed
from tensorflow.python.keras.utils import Sequence
from tensorflow.python.keras.layers import Dropout
from tensorflow.python.keras import backend as K


from modis_utils.generators import OneOutputGenerator
from modis_utils.misc import get_data_test, get_target_test, cache_data, restore_data
from modis_utils.model.core import compile_model, conv_lstm_2D, conv_2D
from modis_utils.model.loss_function import mse_with_mask, mse_with_mask_batch
from modis_utils.model.eval import predict_and_visualize_by_data_file_one_output
from tensorflow.python.keras import optimizers

def PSNRLoss(y_true, y_pred):
    return -10. * K.log(K.mean(K.square(y_pred - y_true))) / K.log(10.)

def trainByCompileParams(type, lr):
	print('Training with {0}, lr = {1}'.format(type, lr))
	class MyGenerator(Sequence):
	    def __init__(self, data_filenames, batch_size):
	        self.data_filenames = data_filenames
	        self.batch_size = batch_size

	    def __len__(self):
	        return len(self.data_filenames)
	    
	    def __getitem__(self, idx):         
	        data = restore_data('output/{0}'.format(self.data_filenames[idx]))
	        i = idx 
	        batch_X = np.expand_dims(np.expand_dims(data[:-1,:,:], axis=0), axis=-1)
	        batch_Y = np.expand_dims(np.expand_dims(data[-1,:,:], axis=0), axis=-1) 
	        
	        __max__ = 17.0
	        __min__ = -34.0
	        __range__ = __max__ - __min__
	        
	        X = (batch_X - __min__) / __range__
	        Y = (batch_Y - __min__) / __range__
	        
	        return (X, Y)


	listFile = os.listdir('output/')
	nTrain = int(len(listFile) * 0.60)
	nVal = int(len(listFile) * 0.3)
	trainFiles = listFile[:nTrain]
	valFiles = listFile[nTrain:nTrain+nVal]
	testFiles = listFile[nTrain+nVal:]

	trainGenerator = MyGenerator(trainFiles, 1)
	valGenerator = MyGenerator(valFiles, 1)


	input_timesteps = 12
	img_height = 128
	img_width = 128


	# default: adam
	opt = optimizers.Adam(lr=lr)
	if (type == 'sgd'):	
		opt = optimizers.SGD(lr=lr)

	input_shape = (input_timesteps, img_height, img_width, 1)
	compile_params = {'optimizer': opt, 'loss': 'mse', 'metrics': [PSNRLoss]}

	# Model architecture
	source = keras.Input(name='seed', shape=input_shape, dtype=tf.float32)
	model = conv_lstm_2D(filters=64, kernel_size=3, strides=1,padding='same')(source)
	model = BatchNormalization()(model)
	model = conv_lstm_2D(filters=64, kernel_size=3, strides=1,padding='same')(model)
	model = BatchNormalization()(model)
	model = conv_lstm_2D(filters=64, kernel_size=3, strides=1,padding='same')(model)
	model = BatchNormalization()(model)
	model = conv_lstm_2D(filters=64, kernel_size=3, strides=1,padding='same')(model)
	model = BatchNormalization()(model)
	model = conv_lstm_2D(filters=64, kernel_size=3, strides=1,padding='same', return_sequences=False)(model)
	model = BatchNormalization()(model)

	predict_img = conv_2D(filters=1, kernel_size=3, strides=1,padding='same')(model)
	model = keras.Model(inputs=[source], outputs=[predict_img])

	model = compile_model(model, compile_params)
	model.fit_generator( generator=trainGenerator, steps_per_epoch=nTrain, epochs=60, validation_data=valGenerator, validation_steps=2000)

	modelFn = 'model_{0}_{1}.h5'.format(type, str(lr).replace('.', ''))

	model.save(modelFn)

	print('Trained to {0}'.format(modelFn))

	del model

listParams = [
	# {
	# 	'type': 'adam',
	# 	'lr': 0.0001,
	# },
	# {
	# 	'type': 'adam',
	# 	'lr': 0.00005,
	# },
	# {
	# 	'type': 'adam',
	# 	'lr': 0.00001,
	# },
	# {
	# 	'type': 'sgd',
	# 	'lr': 0.0001,
	# },
	{
		'type': 'sgd',
		'lr': 0.00005,
	},
	{
		'type': 'sgd',
		'lr': 0.00001,
	},
]

for params in listParams:
	trainByCompileParams(params['type'], params['lr'])