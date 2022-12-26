import re
import collections
import heapq
import json

import numpy as np
from nltk.corpus import stopwords
from nltk import PorterStemmer
import pprint

class Element:

    def __init__(self, u, v, value):
        self.u = u
        self.v = v
        self.value = value

    def __lt__(self, other):
        return self.value < other.value

    def __le__(self, obj):
        """self <= obj."""
        return self.value <= obj.value

    def __eq__(self, obj):
        """self == obj."""
        if not isinstance(obj, Element):
            return False
        return self.value == obj.value

    def __ne__(self, obj):
        """self != obj."""
        if not isinstance(obj, Element):
            return True
        return self.value != obj.value

    def __gt__(self, obj):
        """self > obj."""
        return self.value > obj.value

    def __ge__(self, obj):
        """self >= obj."""
        return self.value >= obj.value

    def __repr__(self):
        return '<Element(u="{}", v="{}", value=("{}"))>'.format(self.u, self.v, self.value)

def metric_cluster_main(query, results):
    stop_words = set(stopwords.words('english'))
    tokens = []
    token_counts = {}
    tokens_map = {}
    document_ids = []
    stem_map = {}


    #tokenize all the result texts one by one and the list of tokens to tokens list
    for result in results:
        document_id = result['digest'][0]
        document_ids.append(document_id)
        token_list = []
        doc_tokens = []
        text = result['content'][0]  # duplicate the value
        text = re.sub(r'[\n]', ' ', str(text))  # Remove end of line escape character
        text = re.sub(r'[^\w\s]', '', text)  # Remove characters other than alphabets, numbers
        text = re.sub(r'[,-]', ' ', text)
        text = re.sub('[0-9]', '', text)
        text = text.lower() # Convert letters to lowercase
        token_list = text.split(' ')  # Split words on spaces
        for token in token_list:
            if token not in stop_words and token != '' and not token.isnumeric():
                doc_tokens.append(token)
        count = collections.Counter(doc_tokens)
        for token in doc_tokens:
            if token not in tokens_map:
                tokens_map[token]={document_id: count[token]}
            elif document_id not in tokens_map[token]:
                tokens_map[token][document_id]=count[token]
            else:
                tokens_map[token][document_id]+=count[token]
        tokens.append(doc_tokens)

    porter_stemmer = PorterStemmer()
    for doc_tokens in tokens:
        for token in doc_tokens:
            stem = porter_stemmer.stem(token)
            if stem not in stem_map:
                stem_map[stem] = set()
            stem_map[stem].add(token)

    matrix = np.zeros((len(stem_map), len(stem_map))).tolist()
    stems = stem_map.keys()
    for i, stem_i in enumerate(stems):
        for j, stem_j in enumerate(stems):
            if i==j:
                continue

            cuv = 0.0
            i_strings = stem_map[stem_i]
            j_strings = stem_map[stem_j]

            for string1 in i_strings:
                for string2 in j_strings:
                    i_map = tokens_map[string1]
                    j_map = tokens_map[string2]
                    for document_id in i_map:
                        if document_id in j_map:
                            if i_map[document_id] - j_map[document_id] != 0:
                                cuv += 1 / abs( i_map[document_id] - j_map[document_id] )

            matrix[i][j] = Element(stem_i, stem_j, cuv)

    normalized_matrix = np.zeros((len(stem_map), len(stem_map))).tolist()
    for i, stem_i in enumerate(stems):
        for j, stem_j in enumerate(stems):
            if i==j:
                continue

            cuv = 0.0
            if matrix[i][j] != 0:
                cuv = matrix[i][j].value / ( len(stem_map[stem_i]) * len(stem_map[stem_j]) )

            normalized_matrix[i][j] = Element(stem_i, stem_j, cuv)

    query = query.lower()
    strings = set()
    for string in query.split(' '):
        strings.add(string)
    top_n=3
    elements = np.zeros((len(strings), top_n)).tolist()
    index = 0
    queue = []
    for string in strings:
        queue = []
        i = -1
        porter_stemmer = PorterStemmer()

        if porter_stemmer.stem(string) in stems:
            i = list(stems).index(porter_stemmer.stem(string))

        if i==-1:
            continue

        for j in range(len(normalized_matrix[i])):
            if normalized_matrix[i][j] == 0 \
                or (normalized_matrix[i][j].u in strings and normalized_matrix[i][j].u != string) \
                or (normalized_matrix[i][j].v in strings and normalized_matrix[i][j].v != string):
                continue

            if normalized_matrix[i][j].v in tokens_map:
                heapq.heappush(queue, normalized_matrix[i][j])

            else:
                heapq.heappush(queue, \
                    Element(normalized_matrix[i][j].u, \
                        next(iter( stem_map[ normalized_matrix[i][j].v ] )), \
                        normalized_matrix[i][j].value))

            if len(queue) > top_n:
                heapq.heappop(queue)

        for k in range(top_n):
            elements[index][k] = heapq.heappop(queue)
        index+=1

    metric_clusters = elements
    metric_clusters2 = [elem for cluster in metric_clusters for elem in cluster]
    metric_clusters2.sort(key=lambda x:x.value,reverse=True)
    i=0;
    while(i<3):
        query += ' '+ str(metric_clusters2[i].v)
        i+=1
    print("Expand query:",query)
    return query
