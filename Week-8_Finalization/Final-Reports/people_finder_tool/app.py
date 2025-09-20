from flask import Flask, render_template, request, flash
import requests
import os
from dotenv import load_dotenv
import base64
from io import BytesIO
from PIL import Image
import face_recognition

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')  # For flash messages

# Your API Keys
GITHUB_API_TOKEN = os.getenv('GITHUB_API_TOKEN', '')


@app.route('/')
def index():
    """Displays the main search page."""
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    """Handles the search request and fetches data from various sources."""
    # Get form data
    name = request.form['name'].strip()
    age = request.form.get('age', '').strip()
    gender = request.form.get('gender', '').strip()
    location = request.form.get('location', '').strip()

    if not name:
        return render_template('index.html', error="Please enter at least a name.")

    # Handle image upload
    uploaded_image_data = None
    if 'comparison_image' in request.files:
        image_file = request.files['comparison_image']
        if image_file and image_file.filename != '':
            try:
                image = Image.open(image_file.stream)
                buffered = BytesIO()
                image.save(buffered, format="JPEG")
                uploaded_image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
            except Exception as e:
                flash(f"Error processing image: {str(e)}", "warning")

    # Prepare query
    query_parts = [name]
    if age and age.lower() not in ['n/a', 'na', 'not applicable', '']:
        query_parts.append(age)
    if location and location.lower() not in ['n/a', 'na', 'not applicable', '']:
        query_parts.append(location)
    query = " ".join(query_parts)

    results = {}

    # Store form data for display
    results['form_data'] = {
        'name': name,
        'age': age,
        'gender': gender,
        'location': location
    }

    # 1. GitHub search
    github_results = search_github(name)
    results['github'] = github_results

    # 2. Face comparison (if image uploaded + github avatar found)
    if uploaded_image_data and github_results.get('found') and github_results.get('avatar_url'):
        try:
            profile_image_response = requests.get(github_results['avatar_url'])
            profile_img_array = face_recognition.load_image_file(BytesIO(profile_image_response.content))
            uploaded_img_array = face_recognition.load_image_file(BytesIO(base64.b64decode(uploaded_image_data)))

            uploaded_face_encodings = face_recognition.face_encodings(uploaded_img_array)
            profile_face_encodings = face_recognition.face_encodings(profile_img_array)

            if uploaded_face_encodings and profile_face_encodings:
                face_distance = face_recognition.face_distance(
                    [uploaded_face_encodings[0]],
                    profile_face_encodings[0]
                )
                if len(face_distance) > 0:
                    similarity_score = max(0, min(100, (1 - face_distance[0]) * 100))
                    results['face_comparison'] = {
                        'similarity': round(similarity_score, 2),
                        'uploaded_image': uploaded_image_data,
                        'profile_image': base64.b64encode(profile_image_response.content).decode('utf-8'),
                        'faces_detected': True
                    }
                else:
                    results['face_comparison'] = {'error': 'Could not calculate similarity'}
            else:
                results['face_comparison'] = {
                    'similarity': 0,
                    'uploaded_image': uploaded_image_data,
                    'profile_image': base64.b64encode(profile_image_response.content).decode('utf-8'),
                    'faces_detected': False,
                    'error': 'No faces detected in one or both images'
                }
        except Exception as e:
            results['face_comparison'] = {
                'error': f'Image comparison failed: {str(e)}'
            }

    # 3. Dork search links
    results['google_dork'] = generate_google_dork_link(query)
    results['facebook_dork'] = generate_facebook_dork_link(query)
    results['linkedin_dork'] = generate_linkedin_dork_link(query)
    results['instagram_dork'] = generate_instagram_dork_link(query)

    # 4. Advanced searches
    results['advanced_searches'] = generate_advanced_searches(name, age, location, gender)

    return render_template('results.html', query=query, results=results)


# ---------------- GitHub API ----------------
def search_github(username):
    """Fetches public profile data from GitHub."""
    url = f"https://api.github.com/users/{username}"
    headers = {}
    if GITHUB_API_TOKEN:
        headers["Authorization"] = f"token {GITHUB_API_TOKEN}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return {
                'found': True,
                'name': data.get('name'),
                'login': data.get('login'),
                'avatar_url': data.get('avatar_url'),
                'bio': data.get('bio'),
                'html_url': data.get('html_url'),
                'public_repos': data.get('public_repos'),
                'followers': data.get('followers'),
                'blog': data.get('blog')
            }
        else:
            return {'found': False, 'error': f'Profile not found (Error {response.status_code})'}
    except requests.exceptions.RequestException as e:
        return {'found': False, 'error': f'Network error: {str(e)}'}


# ---------------- Search Link Generators ----------------
def generate_google_dork_link(query):
    dork = f'site:facebook.com OR site:linkedin.com OR site:twitter.com OR site:instagram.com OR site:github.com "{query}"'
    return f"https://www.google.com/search?q={requests.utils.quote(dork)}"


def generate_facebook_dork_link(query):
    dork = f'site:facebook.com "{query}"'
    return f"https://www.google.com/search?q={requests.utils.quote(dork)}"


def generate_linkedin_dork_link(query):
    dork = f'site:linkedin.com/in OR site:linkedin.com/pub "{query}"'
    return f"https://www.google.com/search?q={requests.utils.quote(dork)}"


def generate_instagram_dork_link(query):
    dork = f'site:instagram.com "{query}"'
    return f"https://www.google.com/search?q={requests.utils.quote(dork)}"


def generate_advanced_searches(name, age, location, gender):
    searches = {'name_only': f'"{name}"'}

    if location and location.lower() not in ['n/a', 'na', 'not applicable', '']:
        searches['name_location'] = f'"{name}" "{location}"'

    if age and age.lower() not in ['n/a', 'na', 'not applicable', '']:
        searches['name_age'] = f'"{name}" "{age} years"'

    if gender and gender.lower() not in ['n/a', 'na', 'not applicable', '']:
        searches['name_gender'] = f'"{name}" "{gender}"'

    details = [name]
    if age and age.lower() not in ['n/a', 'na', 'not applicable', '']:
        details.append(age)
    if location and location.lower() not in ['n/a', 'na', 'not applicable', '']:
        details.append(location)
    if gender and gender.lower() not in ['n/a', 'na', 'not applicable', '']:
        details.append(gender)

    searches['all_details'] = " ".join([f'"{d}"' for d in details])

    return searches


if __name__ == '__main__':
    app.run(debug=True)
