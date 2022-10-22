# https://stackabuse.com/text-classification-with-python-and-scikit-learn/
from pymongo import MongoClient

import numpy as np
#import pandas as pd
import json as json
import re
import pickle
import csv
import time

import matplotlib.pyplot as plt

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
nltk.download('stopwords')
# nltk.download('word net')

from sklearn.datasets import load_files
from sklearn.metrics import classification_report, multilabel_confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold 
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
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
db_dataset = client["DWProject"]["DW_dataset"]
db_dataset_unlabelled = client["DWProject"]["DW_dataset_unlabelled"]

x_cleaned = []
y_raw = []


db_raw = db_dataset.find({'english': True}, {'url': 1, 'data': 1, 'categories': 1, 'relevant': 1})

db_raw_unlabelled = db_URLs.find({'english': True}, {'url': 1, 'data': 1, 'categories': 1, 'relevant': 1})

stemmer = WordNetLemmatizer()

# Preproccesing
for entry in db_raw:
    if entry["relevant"] == True:
        y_raw.append(entry["categories"])
    else:
        #y_raw.append(["other"])
        y_raw.append([])

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



# Binarises target labels for model
mlb = MultiLabelBinarizer()
y_binarised = mlb.fit_transform(y_raw)

# Contains list of training sets, each set's x values is differnt as based on number of features
training_sets_list = []
testing_sets_list = []
num_features = [1500, 3000, 5000, 8000, 10000, 12000, 15000, 20000]

for num in num_features:
    ###
    # The bag of words approach works fine for converting text to numbers. However, it has one drawback. It assigns
    # a score to a word based on its occurrence in a particular document. It doesn't take into account the fact
    # that the word might also be having a high frequency of occurrence in other documents as well. TFIDF resolves
    # this issue by multiplying the term frequency of a word by the inverse document frequency. The TF stands for
    # "Term Frequency" while IDF stands for "Inverse Document Frequency".

    tv = TfidfVectorizer(stop_words=stopwords.words('english'), max_df=0.7, min_df=1, max_features=num)
    x_vectorised = tv.fit_transform(x_cleaned)#.toarray()
    #x_parsed = x_vectorised.toarray()
    # Creates new dataset for each max_features in vectorised x
    #dataset = pd.DataFrame({"data": x_vectorised, "categories": y_binarised}).sample(frac=1)
    #time.sleep(100)
    # Splits dataset into multiple training and testing sets
    training_sets = []
    testing_sets = []

    kf5 = KFold(n_splits=5, shuffle = True)

    i = 0
    for train_index, test_index in kf5.split(x_vectorised):
        #res = next(kf5.split(dataset), None)
        x_train, x_test = x_vectorised[train_index], x_vectorised[test_index]
        y_train, y_test = y_binarised[train_index], y_binarised[test_index]
        training_sets.append([x_train, y_train])
        testing_sets.append([x_test, y_test])
        i += 1
        
    training_sets_list.append(training_sets)
    testing_sets_list.append(testing_sets)

print("======== SVC ========")


x_train = training_sets[j][0]
y_train = training_sets[j][1]
x_test = testing_sets[j][0]
y_test = testing_sets[j][1]

# dual = True cause samples < features
svc = OneVsRestClassifier(SVC(kernel=kernel, probability=True, C=1.0, max_iter=3000)) # penalty='l1',
#svc = LinearSVC(C=1.0, penalty='l1', max_iter=3000, dual=False, multi_class='ovr')
trained_svc = svc.fit(x_train, y_train)
y_pred = trained_svc.predict(x_test)

score = trained_svc.score(x_test, y_test)

#file.write(w)
print(w)
print("")

avg_score_list = []
avg_kernel_score_list = []


file = open('results.txt', 'w')
t = '{:0.2f}'
s = '{:0.5f}'
# poly slower than linear and rbf
for kernel in ('linear', 'poly', 'rbf', 'sigmoid'):
    print("Kernel:", kernel)
    avg_kernel_score = 0
    
    for i in range(0, len(training_sets_list)):  # for each number of features
        w = "Kernel: " + str(kernel) + ", max features: " + str(s.format(num_features[i])) + "\n"
        file.write(w)
        
        print("Max number of features:", num_features[i])
        training_sets = training_sets_list[i]
        testing_sets = testing_sets_list[i]
        # TODO: filter out non english words
        # TODO: make sure at least 1 object from each category in each
        avg_score = 0
        
        start_timer = time.time()
        
        for j in range(0, len(training_sets)): # for each train/test set (fold)
            #x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2)
            print("KFold:", j)

            x_train = training_sets[j][0]
            y_train = training_sets[j][1]
            x_test = testing_sets[j][0]
            y_test = testing_sets[j][1]

            # dual = True cause samples < features
            svc = OneVsRestClassifier(SVC(kernel=kernel, C=1.0, max_iter=3000)) # penalty='l1',
            #svc = LinearSVC(C=1.0, penalty='l1', max_iter=3000, dual=False, multi_class='ovr')
            trained_svc = svc.fit(x_train, y_train)
            y_pred = trained_svc.predict(x_test)

            score = trained_svc.score(x_test, y_test)
            w = "Score for fold "+ str(j) + ": " + str(s.format(score)) + "\n"
            avg_score += score
            #file.write(w)
            print(w)
            print("")
            
        end_timer = time.time()

        
        time_taken = t.format((end_timer - start_timer))
        
        w = "Average score for " + str(num_features[i]) + " feature words: " + str(s.format(avg_score/5)) + "\n" + "Time taken: " + time_taken + "\n" + "\n"
        file.write(w)
        print(w)
        print("")
        print("")
        avg_score_list.append(avg_score)
        avg_kernel_score += avg_score
        
    w = "Average score for kernel: " + str(s.format(avg_kernel_score/8)) + "\n" + "\n"+ "\n"
    file.write(w)
    print("")
    print("")

file.close()

