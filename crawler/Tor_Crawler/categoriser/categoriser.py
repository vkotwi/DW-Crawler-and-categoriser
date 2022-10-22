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

#db = client["DWProject"]["DW_URLs"]
db = client["DWProject"]["DW_dataset_unlabelled"]
db_new = client["DWProject"]["DW_URLs_labelled"]


svc = pickle.load(open('svc.pkl', 'rb'))
tv= pickle.load(open('tv.pkl', 'rb'))
mlb = pickle.load(open('mlb.pkl', 'rb'))

# Must be done twice as connection seems to close once the the data is accessed in a for loop
data = db.find({'labels': {'$exists': False}}, {'data': 1}).limit(1000) # Get all unlabelled entries
urls = db.find({'labels': {'$exists': False}}, {'url': 1}).limit(1000)

cleaned_data = []
categorises = []

stemmer = WordNetLemmatizer()

# Preproccesing
for entry in data:
    # Remove all the special characters
    entry = re.sub(r'\W', ' ', str(entry['data']))

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

    cleaned_data.append(entry)

tv = TfidfVectorizer(stop_words=stopwords.words('english'), max_df=0.9, min_df=1, max_features=3000)
x_vectorised = tv.fit_transform(cleaned_data)

y_pred = svc.predict(x_vectorised)
y_pred_labelled = mlb.inverse_transform(y_pred)

print(y_pred)
print(y_pred_labelled)

#inc = 0
#for i in urls:
#    d = {"url": i["url"], "labels": y_pred_labelled[inc]}
#    db_new.insert_one(d)
#    #db.update_one({'url': i["url"]}, {'$set': {'labels': y_pred_labelled[inc]}})
#    inc = inc + 1


