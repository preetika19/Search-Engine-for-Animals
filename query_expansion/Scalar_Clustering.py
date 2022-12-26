import json
import numpy as np
import re
from nltk.corpus import stopwords

def scalar_main(query, results):
    stop_words = set(stopwords.words('english'))

    Query = query.split(" ")

    URL_Lists = []
    Documents_terms = []
    doc_dict = {}
    print("-----------------------------------")
    print("-----------------------------------")

    for doc_no, doc in enumerate(results):
        Documents_terms.extend(doc['content'][0].replace("\n", " ").split(" "))
        doc_dict[doc_no] = doc['content'][0].replace("\n", " ").split(" ")
    Doc_Terms = []
    for term in Documents_terms:
        if term not in Doc_Terms:
            Doc_Terms.append(term)

    Vocab_dict = {}
    AllDoc_vector = np.zeros(len(Doc_Terms))
    for i, term in enumerate(Doc_Terms):
        Vocab_dict[i] = term
    from collections import Counter
    count_dict  = Counter(Documents_terms)

    Relevant_Docs=[]
    NonRelevant_Docs=[]
    count_relevant_docs = 8
    for i, doc in doc_dict.items():
        if i < count_relevant_docs:
            Relevant_Docs.append(doc)
        else:
            NonRelevant_Docs.append(doc)

    AllDoc_vector = np.zeros(len(Doc_Terms))
    Vector_Relevant = []
    for docs in Relevant_Docs:
        rel_vec = np.zeros(len(Doc_Terms))
        for term in docs:
            count = docs.count(term)
            rel_vec[Doc_Terms.index(term)] = count
        Vector_Relevant.append(rel_vec)

    M1 = np.array(Vector_Relevant)
    M1 = M1.transpose()
    Correlation_Matrix = np.matmul(M1, M1.transpose())
    shape_M = Correlation_Matrix.shape

    for i in range(shape_M[0]):
        for j in range(shape_M[1]):
            if Correlation_Matrix[i][j]!=0:
                Correlation_Matrix[i][j] =  Correlation_Matrix[i][j]/( Correlation_Matrix[i][j]+ Correlation_Matrix[i][i]+ Correlation_Matrix[j][j])

    CM = Correlation_Matrix
    indices_query = []
    for q in Query:
        indices_query.append(Doc_Terms.index(q))

    for i in indices_query:
        max_cos = 0
        max_index = 0
        for j in range(shape_M[1]):
            if i==j:
                continue
            cos = np.dot(CM[i], CM[j]) / (np.sqrt(np.dot(CM[i],CM[i])) * np.sqrt(np.dot(CM[j],CM[j])))
            if np.isnan(cos):
                continue

            if cos > max_cos:
                max_cos = cos
                max_index = j
        Query.append(Doc_Terms[max_index])
    new_query = " ".join(Query)
    print("Expanded query", new_query)
    return new_query
