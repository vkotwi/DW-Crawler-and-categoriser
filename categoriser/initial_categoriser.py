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

db_URLs = client["DWProject"]["DW_URLs"]
db_dataset_unlabelled = client["DWProject"]["DW_dataset_unlabelled"]

try:
    db_dataset_unlabelled.create_index('url',  unique=True)
except:
    print("Already unique")

try:
    svc = pickle.load(open('trained_svc.pkl', 'rb'))
except:
    print("Requires trained model. Please run tc.py first")
    sys.exit()

try:
    tv = pickle.load(open('tv.pkl', 'rb'))
except:
    print("Requires tv function. Please run tc.py first")
    sys.exit()

try:
    mlb = pickle.load(open('mlb.pkl', 'rb'))
except:
    print("Requires tv function. Please run tc.py first")
    sys.exit()


c = db_URLs.find({'checked': {'$exists': False}, 'status': 200}).count()
print(c, "documents to process")

r = int(c / 100)
print(r, "loops")

t = '{:0.2f}'

print("Labelling...")
start_timer = time.time()
for t in range(0, c):
    x_unlabelled_raw = db_URLs.find({'checked': {'$exists': False}, 'status': 200}, {'url': 1, 'data': 1}).limit(c)

    x_data = db_URLs.find({'checked': {'$exists': False}, 'status': 200}, {'url': 1, 'data': 1}).limit(100) # needed cause x_unlabelled_raw empties after loop

    x_cleaned = []

    stemmer = WordNetLemmatizer()

    # Preproccesing
    for entry in x_unlabelled_raw:
        #print(entry["url"])
         # Remove all the special characters
        entry = re.sub(r'\W', ' ', str(entry["data"]))
        
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
            
        x_cleaned.append(entry)


    x_vectorised = tv.transform(x_cleaned)

    y_pred = svc.predict(x_vectorised)
    y_pred_labelled = mlb.inverse_transform(y_pred)

    #print(mlb.inverse_transform(y_pred))

    #print(y_pred_labelled)

    for i in range(0, len(x_cleaned)):
        #print('url', x_data[i]["url"])
        #print('data', x_data[i]["data"])
        #print('categories', y_pred_labelled[i])

        try:
            db_URLs.update_one(
                {'url': x_data[i]['url']},
                {
                    '$set': {
                        'checked': True
                    }
                }
            )
        except Exception as e:
            print("ERROR:", e)
            i = input(">>> ")
            #exit()
        
        try:
            db_dataset_unlabelled.insert_one({
                    'url': x_data[i]["url"],
                    'data': x_data[i]["data"],
                    'categories': y_pred_labelled[i]
                }
            )
        except Exception as e:
            print("ERROR:", e)
            i = input(">>> ")
            #exit()

        
    break

end_timer = time.time()
print("Lablling of database took", (end_timer - start_timer), "seconds")
client.close()
