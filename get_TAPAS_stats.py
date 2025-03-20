import requests
import json
import os

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

for repo in repos:
    repo_name = repo['name']

    clones_count_old = 0
    clones_unique_old = 0
    
    # Check if there is existing data
    if repo_name in accumulated_data:
        repo_data = accumulated_data[repo_name][0]
        clones_count_old = repo_data['clones_all']
        clones_unique_old = repo_data['clones_unique']
    
    traffic_url = f"https://api.github.com/repos/{org_name}/{repo_name}/traffic/clones"
    traffic_response = requests.get(traffic_url, headers=headers)
    
    if traffic_response.status_code == 200:
        clones_data = traffic_response.json()
        clones_count = clones_data['count']  # Total number of times the repo was cloned
        clones_unique = clones_data['uniques'] # Unique number of clones
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

    # remove old data
    accumulated_data[repo_name] = []
    
    accumulated_data[repo_name].append({
        'clones_all': clones_count+clones_count_old,
        'clones_unique': clones_unique+clones_unique_old,
        'downloads': download_count,
        'stargazers': repo['stargazers_count'],
        'forks': repo['forks_count'],
        'open_issues': repo['open_issues_count']
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

update_response = requests.patch(gist_url, headers=headers, data=json.dumps(update_gist_data))

if update_response.status_code == 200:
    print("Gist updated successfully!")
else:
    print("Failed to update the Gist.")

print(f"Total Stars: {total_stars}")
print(f"Total Forks: {total_forks}")
print(f"Total Issues: {total_issues}")