import re
import collections
import heapq

import numpy as np
from nltk.corpus import stopwords
from nltk import PorterStemmer
import pysolr
import pprint


def association_main(query, results):
    tokens = []
    token_doc_id_map = {}

    #stop words
    stop_words = []
    stop_words = set(stopwords.words('english'))

    for result in results:
        token_list = []
        doc_tokens = []
        text = result['content']  # duplicate the value
        digest1 = ''
        digest1 = result['digest']

        text = re.sub(r'[\n]', ' ', str(text))  # Remove end of line escape character
        text = re.sub(r'[^\w\s]', '', text)  # Remove characters other than alphabets, numbers
        text = re.sub(r'[,-]', ' ', text)
        text = re.sub('[0-9]', '', text)
        text = text.lower() # Convert letters to lowercase
        token_list = text.split(' ')  # Split words on spaces
        for token in token_list:
            if token not in stop_words and token != '' and not token.isnumeric():
                doc_tokens.append(token)
        tokens.append(doc_tokens)
        token_doc_id_map[result['digest'][0]] = doc_tokens


    vocabulary = set([token for doc_tokens in tokens for token in doc_tokens])
    assoc_list = []
    for index, vocab in enumerate(vocabulary):
        for word in query.split(' '):
            c1, c2, c3 = 0, 0, 0
            for doc_id, tokens_this_doc in token_doc_id_map.items():
                count0 = tokens_this_doc.count(vocab)
                count1 = tokens_this_doc.count(word)
                c1 += count0 * count1
                c2 += count0 * count0
                c3 += count1 * count1
            c1 /= (c1 + c2 + c3)
            if c1 != 0:
                assoc_list.append((vocab, word, c1))
    assoc_list.sort(key = lambda x: x[2],reverse=True)
    i=2;
    while(i<5):
        query += ' '+str(assoc_list[i][0])
        i +=1
    print("Final query : ",query)
    return query
