import cv2 as cv
from mtcnn.mtcnn import MTCNN
from keras_facenet import FaceNet
import numpy as np 

from sklearn.preprocessing import LabelEncoder
import pickle

embedder = FaceNet()

def get_embedding(face_img):
    face_img = face_img.astype('float32') # 3D(160x160x3)
    face_img = np.expand_dims(face_img, axis=0)
    # 4D (Nonex160x160x3)
    yhat= embedder.embeddings(face_img)
    return yhat[0] 

encoder = LabelEncoder()

def predict_img(file):
    detector = MTCNN()
    with open('custom_data_set.pkl', 'rb') as file:
        model = pickle.load(file)
    t_im=cv.imread(file)
    t_im=cv.cvtColor(t_im,cv.COLOR_BGR2RGB)
    x,y,w,h=detector.detect_faces(t_im)[0]['box']
    t_im = t_im[y:y+h, x:x+w]
    t_im = cv.resize(t_im, (160,160))
    test_im = get_embedding(t_im)
    test_im = [test_im]
    loaded_data = np.load('custom_embeddings.npz')
    print(loaded_data)
    # Access the 'Y' array
    Y = loaded_data['arr_1']
    encoder.fit(Y)
    ypreds = model.predict(test_im)
    final=encoder.inverse_transform(ypreds)
    print(final)