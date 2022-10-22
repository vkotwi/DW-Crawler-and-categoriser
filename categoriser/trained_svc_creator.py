from pymongo import MongoClient

import numpy as np
import json as json
import re
import pickle
import csv
import time

import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from nltk.stem import WordNetLemmatizer

nltk.download('stopwords')
# nltk.download('word net')

from sklearn.datasets import load_files
from sklearn.metrics import classification_report, multilabel_confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.svm import SVC
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.preprocessing import LabelEncoder

import warnings

def warn(*args, **kwargs):
    pass


warnings.warn = warn

client = MongoClient('mongodb://localhost:27017/')

db_dataset = client["DWProject"]["DW_dataset"]
db_dataset_labelled = client["DWProject"]["DW_dataset_unlabelled"]

try:
    mlb = pickle.load(open('mlb.pkl', 'rb'))
except:
    print("Requires tv function. Please run tc.py first")
    sys.exit()


dataset1_data = db_dataset.find({'english': True}, {'data': 1}) # Get all entries
dataset1_categorise = db_dataset.find({'english': True}, {'categories': 1})
dataset2_data = db_dataset_labelled.find({'new': {'$exists': True}}, {'data': 1}) # Only get entries whose label has been verified
dataset2_categorise = db_dataset_labelled.find({'new': {'$exists': True}}, {'new': 1}) # Only get entries whose label has been verified

dataset = []
cleaned_dataset = []
categorises = []

# Add data and categories from each dataset to the dataset and categorises lists
for i in dataset1_data:
    dataset.append(i["data"])


for i in dataset1_categorise:
    categorises.append(i["categories"])


for i in dataset2_data:
    dataset.append(i["data"])


for i in dataset2_categorise:
    categorises.append(i["new"])

print("Dataset length:", len(dataset))
print("Categorises length", len(categorises))

stemmer = WordNetLemmatizer()

# Preproccesing
for entry in dataset:
    # Remove all the special characters
    entry = re.sub(r'\W', ' ', str(entry))

    # remove all single characters
    entry = re.sub(r'\s+[a-zA-Z]\s+', ' ', entry)

    # Remove single characters from the start
    entry = re.sub(r'\^[a-zA-Z]\s+', ' ', entry)

    # Substituting multiple spaces with single space
    entry = re.sub(r'\s+', ' ', entry, flags=re.I)

    # Removing prefixed 'b'
    entry = re.sub(r'^b\s+', '', entry)

    # Converting to Lowercase
    entry = entry.lower()

    # Lemmatization
    entry = entry.split()

    entry = [stemmer.lemmatize(word) for word in entry]

    entry = ' '.join(entry)

    cleaned_dataset.append(entry)


mlb = MultiLabelBinarizer()
tv = TfidfVectorizer(stop_words=stopwords.words('english'), max_df=0.9, min_df=1, max_features=3000)

x_vectorised = tv.fit_transform(cleaned_dataset)
y_binarised = mlb.fit_transform(categorises)

svc = OneVsRestClassifier(SVC(kernel='linear', probability=True, C=1.0, max_iter=3000))
trained_svc = svc.fit(x_vectorised, y_binarised)


print(trained_svc.score(x_vectorised, y_binarised))

svc_pkl_file = 'svc.pkl'
svc_pkl = open(svc_pkl_file, 'wb')
pickle.dump(trained_svc, svc_pkl)
svc_pkl.close()

tv_file = 'tv.pkl'
tv_pkl = open(tv_file, 'wb')
pickle.dump(tv, tv_pkl)
tv_pkl.close()

mlb_file = 'mlb.pkl'
mlb_pkl = open(mlb_file, 'wb')
pickle.dump(mlb, mlb_pkl)
mlb_pkl.close()

