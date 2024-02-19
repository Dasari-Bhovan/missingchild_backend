import cv2 as cv
from mtcnn.mtcnn import MTCNN
from keras_facenet import FaceNet
import numpy as np

from sklearn.preprocessing import LabelEncoder
import pickle

embedder = FaceNet()


def get_embedding(face_img):
    face_img = face_img.astype("float32")  # 3D(160x160x3)
    face_img = np.expand_dims(face_img, axis=0)
    # 4D (Nonex160x160x3)
    yhat = embedder.embeddings(face_img)
    return yhat[0]


encoder = LabelEncoder()


def predict_img(file1):
    detector = MTCNN()
    with open("custom_train_data_set.pkl", "rb") as file:
        model = pickle.load(file)
    t_im = cv.imread(file1)
    t_im = cv.cvtColor(t_im, cv.COLOR_BGR2RGB)
    try:
        x, y, w, h = detector.detect_faces(t_im)[0]["box"]
        t_im = t_im[y : y + h, x : x + w]
        t_im = cv.resize(t_im, (160, 160))
        test_im = get_embedding(t_im)
        test_im = [test_im]
        loaded_data = np.load("custom_training_embeddings.npz")
        # print(loaded_data)
        # Access the 'Y' array
        Y = loaded_data["arr_1"]
        encoder.fit(Y)
        # print(test_im)
        ypreds = model.predict(test_im)
        print(ypreds)
        y_pro=model.predict_proba(test_im)
        print(y_pro)
        final = encoder.inverse_transform(ypreds)
        if y_pro[0][ypreds[0]]>0.45:
            final = encoder.inverse_transform(ypreds)
        else:
            final=["No image matched_0"]
    except:
        final=["No face found_0"]
    print(final)
    return final[0] 

