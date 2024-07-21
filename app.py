from flask import Flask, render_template, request, jsonify
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

OPENALEX_API_URL = "https://api.openalex.org"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('query', '')
    app.logger.info(f"Search request received for query: {query}")
    response = requests.get(f"{OPENALEX_API_URL}/authors", params={
        'search': query,
        'per-page': 10
    })
    data = response.json()
    researchers = [{
        'id': author['id'],
        'name': author.get('display_name', 'Unknown'),
        'institution': author.get('last_known_institution', {}).get('display_name', 'Unknown'),
        'profile_url': author.get('works_api_url', '').replace('works', 'authors')
    } for author in data.get('results', [])]
    app.logger.info(f"Returning {len(researchers)} results")
    return jsonify(researchers)

@app.route('/network')
def network():
    researcher_id = request.args.get('researcher')
    app.logger.info(f"Network request received for researcher ID: {researcher_id}")
    
    try:
        # Get researcher details
        response = requests.get(f"{OPENALEX_API_URL}/authors/{researcher_id}")
        response.raise_for_status()
        researcher_data = response.json()
        
        name = researcher_data.get('display_name', 'Unknown')
        institution = researcher_data.get('last_known_institution', {}).get('display_name', 'Unknown')
        profile_url = researcher_data.get('works_api_url', '').replace('works', 'authors')
        works_url = researcher_data.get('works_api_url', '')
        
        root = {
            "id": researcher_id,
            "name": name,
            "institution": institution,
            "profile_url": profile_url,
            "children": []
        }

        # Get works
        works_response = requests.get(works_url, params={'per-page': 100})
        works_response.raise_for_status()
        works_data = works_response.json()
        
        collaborators = {}
        for work in works_data.get('results', []):
            for authorship in work.get('authorships', []):
                coauthor = authorship.get('author', {})
                coauthor_id = coauthor.get('id')
                coauthor_name = coauthor.get('display_name', 'Unknown')
                coauthor_institution = coauthor.get('last_known_institution', {}).get('display_name', 'Unknown')
                coauthor_profile_url = coauthor.get('works_api_url', '').replace('works', 'authors')
                if coauthor_id and coauthor_id != researcher_id:
                    if coauthor_id not in collaborators:
                        collaborators[coauthor_id] = {
                            'name': coauthor_name,
                            'institution': coauthor_institution,
                            'profile_url': coauthor_profile_url,
                            'count': 1
                        }
                    else:
                        collaborators[coauthor_id]['count'] += 1

        # Add all collaborators as children of the root
        for coauthor_id, info in collaborators.items():
            root["children"].append({
                "id": coauthor_id,
                "name": info['name'],
                "institution": info['institution'],
                "profile_url": info['profile_url'],
                "value": info['count']
            })

        app.logger.info(f"Returning network data with {len(root['children'])} collaborators")
        return jsonify(root)

    except requests.RequestException as e:
        app.logger.error(f"Error fetching data for researcher {researcher_id}: {str(e)}")
        return jsonify({"error": "Failed to fetch researcher data"}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error for researcher {researcher_id}: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True)