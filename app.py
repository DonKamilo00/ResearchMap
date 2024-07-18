# app.py
from flask import Flask, render_template, request, jsonify
import requests
import networkx as nx

app = Flask(__name__)

OPENALEX_API_URL = "https://api.openalex.org"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('query', '')
    response = requests.get(f"{OPENALEX_API_URL}/authors", params={
        'search': query,
        'per-page': 10
    })
    data = response.json()
    researchers = [{'id': author['id'], 'name': author.get('display_name', 'Unknown')} for author in data.get('results', [])]
    return jsonify(researchers)

@app.route('/network')
def network():
    researcher_id = request.args.get('researcher')
    print(f"Received researcher ID: {researcher_id}")
    G = nx.Graph()

    try:
        # Get researcher details
        response = requests.get(f"{OPENALEX_API_URL}/authors/{researcher_id}")
        response.raise_for_status()
        researcher_data = response.json()
        
        name = researcher_data.get('display_name', 'Unknown')
        works_url = researcher_data.get('works_api_url', '')
        
        G.add_node(researcher_id, name=name, profile_link=works_url)

        # Get works
        works_response = requests.get(works_url, params={'per-page': 100})
        works_response.raise_for_status()
        works_data = works_response.json()
        
        collaborators = {}
        for work in works_data.get('results', []):
            for authorship in work.get('authorships', []):
                coauthor_id = authorship.get('author', {}).get('id')
                coauthor_name = authorship.get('author', {}).get('display_name', 'Unknown')
                if coauthor_id and coauthor_id != researcher_id:
                    if coauthor_id not in collaborators:
                        collaborators[coauthor_id] = {'name': coauthor_name, 'count': 1}
                    else:
                        collaborators[coauthor_id]['count'] += 1

        # Add top collaborators to the graph
        top_collaborators = sorted(collaborators.items(), key=lambda x: x[1]['count'], reverse=True)[:20]
        for coauthor_id, info in top_collaborators:
            G.add_node(coauthor_id, name=info['name'], profile_link=f"{OPENALEX_API_URL}/authors/{coauthor_id}")
            G.add_edge(researcher_id, coauthor_id, weight=info['count'])

    except requests.RequestException as e:
        print(f"Error fetching data for researcher {researcher_id}: {str(e)}")
    except Exception as e:
        print(f"Unexpected error for researcher {researcher_id}: {str(e)}")

    network_data = nx.node_link_data(G)
    print(f"Network data: {network_data}")
    return jsonify(network_data)

if __name__ == '__main__':
    app.run(debug=True)