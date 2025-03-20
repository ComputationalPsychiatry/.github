import requests
import json
import os
from datetime import datetime

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_ID = os.getenv("GIST_ID")

headers = {'Authorization': f'token {GITHUB_TOKEN}'}

# Fetch the existing Gist content
gist_url = f"https://api.github.com/gists/{GIST_ID}"
gist_response = requests.get(gist_url, headers=headers)
gist_data = gist_response.json()

filename = "stats.json"
accumulated_data = {}
# Assuming the Gist contains JSON data
if gist_response.status_code == 200 and gist_data.get('files'):
    # Extract the filename (assuming there's only one file in the Gist)
    filename = list(gist_data['files'].keys())[0]
    existing_content = gist_data['files'][filename]['content']
    
    # Load existing data from the Gist
    accumulated_data = json.loads(existing_content)
else:
    accumulated_data = {}

org_name = "ComputationalPsychiatry"
repos_url = f"https://api.github.com/orgs/{org_name}/repos"
repos_response = requests.get(repos_url)
repos = repos_response.json()

total_stars = sum(repo['stargazers_count'] for repo in repos)
total_forks = sum(repo['forks_count'] for repo in repos)
total_issues = sum(repo['open_issues_count'] for repo in repos)

current_date = datetime.now().strftime('%Y-%m-%d')

for repo in repos:
    repo_name = repo['name']
    
    # Check if the current date is already in the accumulated data
    if repo_name in accumulated_data:
        dates = [entry['date'] for entry in accumulated_data[repo_name]]
        if current_date in dates:
            print(f"Repo: {repo_name} - Entry for {current_date} already exists, skipping.")
            continue
    
    traffic_url = f"https://api.github.com/repos/{org_name}/{repo_name}/traffic/clones"
    traffic_response = requests.get(traffic_url, headers=headers)

    #print(f"Status Code: {traffic_response.status_code}")
    
    if traffic_response.status_code == 200:
        clones_data = traffic_response.json()
        clones_count = clones_data['count']  # Total number of times the repo was cloned
    else:
        clones_count = 0
        print(f"Repo: {repo_name} - Clones data unavailable (requires admin access)")

    # Track download counts for release assets
    releases_url = f"https://api.github.com/repos/{org_name}/{repo_name}/releases"
    releases_response = requests.get(releases_url, headers=headers)
    download_count = 0
    
    if releases_response.status_code == 200:
        releases = releases_response.json()
        for release in releases:
            for asset in release.get('assets', []):
                download_count += asset['download_count']
    else:
        print(f"Repo: {repo_name} - Release data unavailable (requires admin access)")

    # Update the accumulated data
    if repo_name not in accumulated_data:
        accumulated_data[repo_name] = []
    
    accumulated_data[repo_name].append({
        'date': current_date,
        'clones': clones_count,
        'downloads': download_count
    })

# Update the Gist with the new data
updated_content = json.dumps(accumulated_data, indent=4)
update_gist_data = {
    "files": {
        filename: {
            "content": updated_content
        }
    }
}

# print(f"Json: {json.dumps(update_gist_data)}")

update_response = requests.patch(gist_url, headers=headers, data=json.dumps(update_gist_data))

if update_response.status_code == 200:
    print("Gist updated successfully!")
else:
    print("Failed to update the Gist.")

print(f"Total Stars: {total_stars}")
print(f"Total Forks: {total_forks}")
print(f"Total Issues: {total_issues}")