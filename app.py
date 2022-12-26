from flask import Flask, render_template, url_for
import pysolr
import re
from flask import request, jsonify
from flask_cors import CORS
import json

import spellchecker
from query_expansion.Association_Cluster import association_main
from query_expansion.Metric_Clusters import metric_cluster_main
from query_expansion.Scalar_Clustering import scalar_main
from spellchecker import SpellChecker
solr = pysolr.Solr('http://localhost:8983/solr/my_core/', always_commit=True, timeout=10)
app = Flask(__name__)
CORS(app)
app.config["DEBUG"] = True

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/app', methods=['GET'])
def get_query():
    if 'query' in request.args and 'type' in request.args:
        query = ' '.join(['content:' + each_query for each_query in str(request.args['query']).split()])
        orig_query = str(request.args['query'])
        print(orig_query)
        type =  str(request.args['type'])
        total_results = 20

        solr_results = get_results_from_solr(query, total_results)
        sort = True
        if type == 'no_filter':
            sort = False

        api_resp = parse_solr_results(solr_results, sort)

        if type == "no_filter":
            result = api_resp
        elif type == "page_rank":
            result = get_pagerank_results(api_resp)
        elif "clustering" in type:
            result = get_clustering_results(api_resp, type)
        elif type == "hits":
            result = get_hits_results(api_resp)
        elif type == "association_qe":
            expanded_query = association_main(orig_query.lower(), solr_results)
            expanded_query = ' '.join(['content:' + x for x in expanded_query.split()])
            solr_res_after_qe = get_results_from_solr(expanded_query, 20)
            api_resp = parse_solr_results(solr_res_after_qe, sort)
            result = api_resp
        elif type == "metric_qe":
            expanded_query = metric_cluster_main(orig_query.lower(), solr_results)
            expanded_query = ' '.join(['content:' + x for x in expanded_query.split()])
            solr_res_after_qe = get_results_from_solr(expanded_query, 20)
            api_resp = parse_solr_results(solr_res_after_qe, sort)
            result = api_resp
        elif type == "scalar_qe":
            expanded_query = scalar_main(orig_query.lower(), solr_results)
            expanded_query = ' '.join(['content:' + x for x in expanded_query.split()])
            solr_res_after_qe = get_results_from_solr(expanded_query, 20)
            api_resp = parse_solr_results(solr_res_after_qe, sort)
            result = api_resp
        return jsonify(result)
    else:
        return "Error: No query or type provided"

def get_results_from_solr(query, no_of_results):
    results = solr.search(query, search_handler="/select", **{
        "wt": "json",
        "rows": no_of_results
    })
    return results

def parse_solr_results(solr_results, sort = False):
    if solr_results.hits == 0:
        return jsonify("query out of scope")
    else:
        api_resp = list()
        rank = 0
        for result in solr_results:
            rank += 1
            title = ""
            url = ""
            content = ""
            score = [0]
            if 'title' in result:
                title = result['title']
            if 'url' in result:
                url = result['url']
            if 'score' in result:
                score = result['score'][0]
            if 'content' in result:
                content = result['content'][0]
                meta_info = content[:200]
                meta_info = meta_info.replace("\n", " ")
                meta_info = " ".join(re.findall("[a-zA-Z]+", meta_info))
            link_json = {
                "title": title,
                "url": url,
                "meta_info": meta_info,
                "rank": rank,
                "score" : score
            }
            api_resp.append(link_json)
    return api_resp

def get_pagerank_results(pages):
    pages.sort(key=lambda x: x["score"], reverse=True)
    return pages

def get_clustering_results(clust_inp, param_type):
    if param_type == "flat_clustering":
        f = open('Clustering/clustering_f.txt')
        lines = f.readlines()
        f.close()
    elif param_type == "hierarchical_clustering":
        f = open('Clustering/clustering_h.txt')
        lines = f.readlines()
        f.close()
    cluster_map = {}
    for line in lines:
        line = line.replace("\n","")
        line_split = line.split(",")
        if line_split[1] == "":
            line_split[1] = "99"
        cluster_map.update({line_split[0]: line_split[1]})

    for curr_resp in clust_inp:
        curr_url = curr_resp["url"]
        curr_cluster = cluster_map.get(curr_url[0], "99")
        curr_resp.update({"cluster": curr_cluster})
        curr_resp.update({"done": "False"})

    clust_resp = []
    curr_rank = 1
    for curr_resp in clust_inp:
        if curr_resp["done"] == "False":
            curr_cluster = curr_resp["cluster"]
            curr_resp.update({"done": "True"})
            curr_resp.update({"rank": str(curr_rank)})
            curr_rank += 1
            clust_resp.append({"title": curr_resp["title"], "url": curr_resp["url"],
                               "meta_info": curr_resp["meta_info"], "rank": curr_resp["rank"]})
            for remaining_resp in clust_inp:
                if remaining_resp["done"] == "False":
                    if remaining_resp["cluster"] == curr_cluster:
                        remaining_resp.update({"done": "True"})
                        remaining_resp.update({"rank": str(curr_rank)})
                        curr_rank += 1
                        clust_resp.append({"title": remaining_resp["title"], "url": remaining_resp["url"],
                                           "meta_info": remaining_resp["meta_info"], "rank": remaining_resp["rank"]})

    return clust_resp

def get_hits_results(clust_inp):
    authority_score_file = open("HITS/authorities_scores.txt", 'r').read()
    authority_score_dict = json.loads(authority_score_file)

    clust_inp = sorted(clust_inp, key=lambda x: authority_score_dict.get(x['url'][0], 0.0), reverse=True)
    return clust_inp


if __name__ == '__main__':
    app.debug=True
    app.run()