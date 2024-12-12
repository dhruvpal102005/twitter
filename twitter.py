from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app, resources={r"/twitter": {"origins": "*"}})

# Load API key
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "5d54c973b7msh2418c169d4909b0p1e5362jsn1123fc1cd8ae")
if not RAPIDAPI_KEY:
    raise EnvironmentError("RAPIDAPI_KEY is not set. Please set it in your environment variables.")

def get_user_data(username):
    """Fetch user profile data from the Twitter API."""
    try:
        url = "https://twitter-api47.p.rapidapi.com/v2/user/by-username"
        querystring = {"username": username}
        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': "twitter-api47.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching user data: {e}")
        return None

def get_recent_posts(username, user_id, count=10):
    """Fetch recent tweets of the user from the Twitter API."""
    try:
        url = "https://twitter-api47.p.rapidapi.com/v2/user/tweets"
        querystring = {"userId": user_id, "count": count}
        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': "twitter-api47.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        posts = []

        if 'tweets' in data:
            for tweet in data['tweets'][:count]:
                text = tweet.get('legacy', {}).get('full_text', 'No tweet text available')
                created_at = tweet.get('legacy', {}).get('created_at', 'Unknown time')
                posts.append({
                    "Text": text,
                    "CreatedAt": created_at
                })

        return posts
    except requests.exceptions.RequestException as e:
        print(f"Error fetching recent tweets: {e}")
        return []

def user_information_final(username):
    """Aggregate user profile and tweet data."""
    user_data = get_user_data(username)
    if not user_data:
        return {"error": f"Unable to fetch the data for the username: {username}"}

    # Extract basic user information
    data = user_data.get('legacy', {})
    user_info = {
        "Username": data.get("screen_name", "N/A"),
        "Name": data.get("name", "N/A"),
        "Bio": data.get("description", "N/A"),
        "Followers": data.get("followers_count", 0),
        "Following": data.get("friends_count", 0),
        "NumberOfPosts": data.get("statuses_count", 0),
        "Verified": "Yes" if data.get("verified") else "No",
        "AccountPrivacy": "Public" if not data.get("protected") else "Private",
    }

    # Fetch and process recent tweets
    user_id = user_data.get('rest_id', None)
    if not user_id:
        return {"error": "User ID not found in the data."}

    posts = get_recent_posts(username, user_id)
    captions = [
        {
            "PostNumber": index + 1,
            "Text": post.get("Text", "No tweet text available"),
            "CreatedAt": post.get("CreatedAt", "Unknown time"),
        }
        for index, post in enumerate(posts)
    ]

    return {
        "ProfileInfo": user_info,
        "Captions": captions,
    }

@app.route('/twitter', methods=['POST'])
def twitter():
    """Endpoint to process Twitter user data."""
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Username is required.'}), 400

    user_data = user_information_final(username)
    if "error" in user_data:
        return jsonify({'error': user_data['error']}), 404

    return jsonify({'result': user_data})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
