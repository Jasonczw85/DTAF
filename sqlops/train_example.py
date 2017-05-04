#!usr/bin/env python  
#-*- coding: utf-8 -*-  
  
import sys  
import os  
import time  
from sklearn import datasets, metrics  
import numpy as np  
import cPickle as pickle  
import pdb
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score

from sklearn import preprocessing
from sklearn.ensemble import ExtraTreesClassifier
import skflow


reload(sys)  
sys.setdefaultencoding('utf8')  
  
# Multinomial Naive Bayes Classifier  
def naive_bayes_classifier(train_x, train_y):  
    from sklearn.naive_bayes import MultinomialNB  
    model = MultinomialNB(alpha=0.01)  
    model.fit(train_x, train_y)  
    return model  
  
  
# KNN Classifier  
def knn_classifier(train_x, train_y):  
    from sklearn.neighbors import KNeighborsClassifier  
    model = KNeighborsClassifier()  
    model.fit(train_x, train_y)  
    return model  
  
  
# Logistic Regression Classifier  
def logistic_regression_classifier(train_x, train_y):  
    from sklearn.linear_model import LogisticRegression  
    model = LogisticRegression(penalty='l2')  
    model.fit(train_x, train_y)  
    return model  
  
  
# Random Forest Classifier  
def random_forest_classifier(train_x, train_y):  
    from sklearn.ensemble import RandomForestClassifier  
    model = RandomForestClassifier(n_estimators=8)  
    model.fit(train_x, train_y)  
    return model  
  
  
# Decision Tree Classifier  
def decision_tree_classifier(train_x, train_y):  
    from sklearn import tree  
    model = tree.DecisionTreeClassifier()  
    model.fit(train_x, train_y)  
    return model  
  
  
# GBDT(Gradient Boosting Decision Tree) Classifier  
def gradient_boosting_classifier(train_x, train_y):  
    from sklearn.ensemble import GradientBoostingClassifier  
    model = GradientBoostingClassifier(n_estimators=200)  
    model.fit(train_x, train_y)  
    return model  
  
  
# SVM Classifier  
def svm_classifier(train_x, train_y):  
    from sklearn.svm import SVC  
    model = SVC(kernel='rbf', probability=True)  
    model.fit(train_x, train_y)  
    return model  
  
# SVM Classifier using cross validation  
def svm_cross_validation(train_x, train_y):  
    from sklearn.grid_search import GridSearchCV  
    from sklearn.svm import SVC  
    model = SVC(kernel='rbf', probability=True)  
    param_grid = {'C': [1e-3, 1e-2, 1e-1, 1, 10, 100, 1000], 'gamma': [0.001, 0.0001]}  
    grid_search = GridSearchCV(model, param_grid, n_jobs = 1, verbose=1)  
    grid_search.fit(train_x, train_y)  
    best_parameters = grid_search.best_estimator_.get_params()  
    for para, val in best_parameters.items():  
        print para, val  
    model = SVC(kernel='rbf', C=best_parameters['C'], gamma=best_parameters['gamma'], probability=True)  
    model.fit(train_x, train_y)  
    return model  
  
def read_data(data_file):  
    import gzip  
    f = gzip.open(data_file, "rb")  
    train, val, test = pickle.load(f)  
    f.close()  
    train_x = train[0]  
    train_y = train[1]  
    test_x = test[0]  
    test_y = test[1]  
    return train_x, train_y, test_x, test_y  


    
def read_raw_data():
    a = []
    pathSigIn = 'dailysignalfiles/'
    pathAlphaIn = 'sort/'
    for i in os.listdir(pathSigIn):
        a.append(i)

    a.sort()
    dfx = pd.DataFrame()
    dfz = pd.DataFrame()

    for i in a:
    
        try:
            data_reader = pd.read_csv(pathSigIn+i, iterator=True, header=None)
            df = data_reader.get_chunk()    
    
        except:
            continue
    
        dfy = pd.DataFrame()
        dfy[['']] = df[[1]]
        dfy[['']] = df[[2]]
        dfy[['']] = df[[5]]
        dfy[['']] = df[[6]]
        dfy[['']] = df[[10]]
        dfy[['']] = df[[11]]
        dfy[['']] = df[[12]]
        
                
        dfy.insert(7, '', df[9]>df[7])
        
        print i, len(dfy)
        dfz = dfz.append(dfy)
        #print dfz
        
    #pdb.set_trace()
    dfz.to_csv('dailysignalfiles/testdata.csv')


    
    
def split_data():
    dataset_path = 'dailysignalfiles/testdata.csv'
    reader = pd.read_csv(dataset_path, iterator=True)
    
    loop = 1
    chunkSize = 8000
    chunks = []
    while loop:
        try:
            
            if loop%800 == 0:
                chunk = reader.get_chunk(chunkSize)
                chunks.append(chunk)
            loop += 1
            #print loop
            if loop > 7000:
                loop = 0
                
        except StopIteration:
            loop = 0
            print "Iteration is stopped."
            
    data = pd.concat(chunks, ignore_index=True)
    
    
    #pdb.set_trace()
    feature_names = data.columns[2:-1].tolist()
    #feature_names = data.columns[1:-1].tolist()
    
    print "feature names:"
    print feature_names
    
    
    X = data[feature_names].values
    y = data[''].values.astype(int)

    model = ExtraTreesClassifier()
    model.fit(X, y)
    
    print "ExtraTreesClassifier feature importances"
    print model.feature_importances_
    
    classifier = skflow.TensorFlowDNNClassifier(hidden_units=[10, 20, 10], n_classes=3)
    classifier.fit(X, y)
    score = metrics.accuracy_score(classifier.predict(X), y)
    print("TensorFlowDNNClassifier Accuracy: %f" % score)
    
    
    # 随机数生成种子
    seed = 5
    test_size = 0.2
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = test_size , random_state = seed)
    
    return X_train, X_test, y_train, y_test

    
def partial_fit():

    thresh = 0.5  
    model_save_file = None  
    model_save = {}  
      
    #test_classifiers = ['NB', 'KNN', 'LR', 'RF', 'DT', 'SVM', 'GBDT']  
    test_classifiers = ['NB', 'KNN', 'LR', 'RF', 'DT']  
    
    classifiers = {'NB':naive_bayes_classifier,   
                  'KNN':knn_classifier,  
                   'LR':logistic_regression_classifier,  
                   'RF':random_forest_classifier,  
                   'DT':decision_tree_classifier,  
                  'SVM':svm_classifier,  
                'SVMCV':svm_cross_validation,  
                 'GBDT':gradient_boosting_classifier  
    }  

    dataset_path = 'dailysignalfiles/testdata.csv'
    #data = pd.read_csv(dataset_path, nrows=10000)
    reader = pd.read_csv(dataset_path, iterator=True)
    
    loop = True
    chunkSize = 50000
    pdb.set_trace()
    from sklearn.linear_model import PassiveAggressiveClassifier  
    from sklearn.linear_model import SGDClassifier
    from sklearn.cluster import MiniBatchKMeans
    from sklearn.decomposition import IncrementalPCA
    
    #model = PassiveAggressiveClassifier()  
    #model = SGDClassifier()
    #model = MiniBatchKMeans()
    model = IncrementalPCA()
    
    the_first = True
    while loop:
        try:
            data = reader.get_chunk(chunkSize)
            feature_names = data.columns[2:-1].tolist()
            
            X = data[feature_names].values
            y = data['profilo'].values.astype(int)

            seed = 5
            test_size = 0.2
            train_x, test_x, train_y, test_y = train_test_split(X, y, test_size = test_size , random_state = seed)
            
            num_train, num_feat = train_x.shape  
            num_test, num_feat = test_x.shape  
            is_binary_class = (len(np.unique(train_y)) == 2)  
            print '******************** Data Info *********************'  
            print '#training data: %d, #testing_data: %d, dimension: %d' % (num_train, num_test, num_feat)  
              
            #for classifier in test_classifiers:  
                #print '******************* %s ********************' % classifier  
            start_time = time.time()  
                
            try:
            
                #from sklearn.ensemble import RandomForestClassifier  
                #model = RandomForestClassifier(n_estimators=8)  
                #model.partial_fit(train_x, train_y)  
                if the_first:
                    class_y = np.unique(y)
                    #class_y = None
                else:
                    class_y = None
                    
                #model.partial_fit(train_x, train_y, classes=class_y) 
                model.partial_fit(train_x, train_y)
                print "Is the first class?", the_first
                
                the_first = False
                
                
                #print "classes: ", np.unique(y)
                #print np.array([0, 1])
            except:
                continue
                
            print 'training took %fs!' % (time.time() - start_time) 
            #print("{} score".format(model.score(test_x, test_y)))
            
            predict = model.predict(test_x)  

            if model_save_file != None:  
                model_save[classifier] = model  
            if is_binary_class:  
                precision = metrics.precision_score(test_y, predict)  
                recall = metrics.recall_score(test_y, predict)  
                print 'precision: %.2f%%, recall: %.2f%%' % (100 * precision, 100 * recall)  
            accuracy = metrics.accuracy_score(test_y, predict)  
            print 'accuracy: %.2f%%' % (100 * accuracy)   
            
            
            if model_save_file != None:  
                pickle.dump(model_save, open(model_save_file, 'wb'))             
            
        except StopIteration:
            loop = False
            print "Iteration is stopped."
            
    
if __name__ == '__main__':  
    data_file = "mnist.pkl.gz"  
    thresh = 0.5  
    model_save_file = None  
    model_save = {}  
      
    test_classifiers = ['NB', 'KNN', 'LR', 'RF', 'DT', 'SVM', 'GBDT']  
    classifiers = {'NB':naive_bayes_classifier,   
                  'KNN':knn_classifier,  
                   'LR':logistic_regression_classifier,  
                   'RF':random_forest_classifier,  
                   'DT':decision_tree_classifier,  
                  'SVM':svm_classifier,  
                'SVMCV':svm_cross_validation,  
                 'GBDT':gradient_boosting_classifier  
    }  

    
    print 'reading training and testing data...' 


    pdb.set_trace()
    partial_fit()
    
    train_x, test_x, train_y, test_y = split_data()  
     
    num_train, num_feat = train_x.shape  
    num_test, num_feat = test_x.shape  
    is_binary_class = (len(np.unique(train_y)) == 2)  
    print '******************** Data Info *********************'  
    print '#training data: %d, #testing_data: %d, dimension: %d' % (num_train, num_test, num_feat)  
      
    for classifier in test_classifiers:  
        print '******************* %s ********************' % classifier  
        start_time = time.time()  
        
        try:
            model = classifiers[classifier](train_x, train_y)  
        except:
            continue
            
        print 'training took %fs!' % (time.time() - start_time)  
        predict = model.predict(test_x)  
        if model_save_file != None:  
            model_save[classifier] = model  
        if is_binary_class:  
            precision = metrics.precision_score(test_y, predict)  
            recall = metrics.recall_score(test_y, predict)  
            print 'precision: %.2f%%, recall: %.2f%%' % (100 * precision, 100 * recall)  
        accuracy = metrics.accuracy_score(test_y, predict)  
        print 'accuracy: %.2f%%' % (100 * accuracy)   
  
    if model_save_file != None:  
        pickle.dump(model_save, open(model_save_file, 'wb'))  

