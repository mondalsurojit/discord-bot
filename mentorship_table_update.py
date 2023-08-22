# -*- coding: utf-8 -*-
"""Mentorship Table Update.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ze9jlVDMfMmqUPj57cLs8An8kSu3OnqA
"""

# !pip install supabase
# !pip install requests
# !pip install fuzzywuzzy
# !pip install mistune==3.0.1

import json, sys, re, os
import requests, mistune
from fuzzywuzzy import fuzz

# Setting up env variables
GITHUB_PAT="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"
SUPABASE_URL="https://kcavhjwafgtoqkqbbqrd.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjYXZoandhZmd0b3FrcWJicXJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODQ5NTQxMzIsImV4cCI6MjAwMDUzMDEzMn0.8PKGvntMY7kw5-wmvG2FBOCxf-OrA2yV5fnudeA6SVQ"

from supabase import create_client, Client
class SupabaseInterface:
    def __init__(self, table, url=None, key=None) -> None:

        # self.supabase_url = url if url else os.getenv("SUPABASE_URL")
        # self.supabase_key = key if key else os.getenv("SUPABASE_KEY")
        self.supabase_url = "https://kcavhjwafgtoqkqbbqrd.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjYXZoandhZmd0b3FrcWJicXJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODQ5NTQxMzIsImV4cCI6MjAwMDUzMDEzMn0.8PKGvntMY7kw5-wmvG2FBOCxf-OrA2yV5fnudeA6SVQ"
        self.table = table
        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    def read(self, query_key, query_value, columns="*"):
        data = self.client.table(self.table).select(columns).eq(query_key, query_value).execute()
        #data.data returns a list of dictionaries with keys being column names and values being row values
        return data.data

    def read_by_order_limit(self, query_key, query_value, order_column, order_by=False, limit=1, columns="*"):
        data = self.client.table(self.table).select(columns).eq(query_key, query_value).order(order_column).limit(limit).execute()
        return data.data

    def read_all(self):
        data = self.client.table(self.table).select("*").execute()
        return data.data

    def update(self, update, query_key, query_value):
        data = self.client.table(self.table).update(update).eq(query_key, query_value).execute()
        return data.data

    def insert(self, data):
        data = self.client.table(self.table).insert(data).execute()
        return data.data
    def delete(self):
        pass
    def select_by_node_id(self, node_id):
        # You might need to implement the select function or adjust based on your Supabase client's syntax
        data = self.client.table(self.table).select().eq("node_id", node_id).execute()
        return data.data
    def add_user(self, userdata):
        data = self.client.table("users").insert(userdata).execute()
        print(data.data)
        return data.data

    def user_exists(self, discord_id):
        data = self.client.table("users").select("*").eq("discord_id", discord_id).execute()
        if len(data.data)>0:
            return True
        else:
            return False

def send_get_request(url):
    headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {GITHUB_PAT}'
    #         'Authorization': 'Bearer
        }
    try:
        response = requests.get(url, headers=headers)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            return response.text
        else:
            # If the request was not successful, raise an exception or return None.
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # Handle any exceptions that occurred during the request (e.g., connection error, timeout).
        print(f"An error occurred: {e}")
        return None

def generate_file_tree():
    result = send_get_request("https://api.github.com/repos/Code4GovTech/c4gt-milestones/contents/docs/2023?ref=main")
    # print(result)
    productFolders = json.loads(result)
    folderStruct = dict()
    for pFolder in productFolders:
        folderStruct[pFolder["name"]] = dict()
        projectFolders = json.loads(send_get_request(pFolder["url"]))
        for project in projectFolders:
            # print(project, type(project))
            if isinstance(project, dict) and project["type"] == "dir":
                folderStruct[pFolder["name"]][project["name"]] = list()
    # print(folderStruct)
    return folderStruct

defaultText = '''---
title: Week 1
author: Yashi Gupta
---

## Milestones
- [ ] Give the description about Milestone 1
- [ ] Give the description about Milestone 2
- [ ] Give the description about Milestone 3
- [ ] Give the description about Milestone 4

## Screenshots / Videos

## Contributions

## Learnings'''
def is_default_text(markdown):
    if fuzz.ratio(markdown, defaultText)>90 :
        return True
    return False

def find_urls(obj, urls):

    if isinstance(obj, dict):
      if "url" in obj:
        urls.append(obj["url"])
      for value in obj.values():
        find_urls(value, urls)
    elif isinstance(obj, list):
      for value in obj:
        find_urls(value, urls)
    elif isinstance(obj, str):
        # print(obj)
        if '://' in obj or 'http' in obj or "pull" in obj:
            urls.append(obj)

def extract_github_pr_url(s):
    # Pattern to match the HTML PR URL
    html_pattern = r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    # Pattern to match the API PR URL
    api_pattern = r"https://api\.github\.com/repos/([^/]+)/([^/]+)/pulls/(\d+)"
    
    html_match = re.search(html_pattern, s)
    if html_match:
        return html_match.group(0)

    api_match = re.search(api_pattern, s)
    if api_match:
        # Convert API endpoint URL to its HTML counterpart
        return f"https://github.com/{api_match.group(1)}/{api_match.group(2)}/pull/{api_match.group(3)}"

    return ""

def return_ast(md):
    markdown = mistune.create_markdown(renderer=None)
    return markdown(md)

def isPrUrl(url):
    # if a url ends in 'pull/number' it's a pull request
    pattern = r"pull/\d+"
    match = re.search(pattern, url)
    return match is not None

def getPR(PRurl):
    components = PRurl.split('/')
    owner, repo,number = components[-4], components[-3], components[-1]
    url = url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{number}'

    headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {GITHUB_PAT}'
        }

    try:
        response = requests.get(url, headers=headers)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            return response.json()
        else:
            # If the request was not successful, raise an exception or return None.
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # Handle any exceptions that occurred during the request (e.g., connection error, timeout).
        print(f"An error occurred: {e}")
        return None

def get_commits(commits_url):
    headers = {
            'Accept': 'application/vnd.github+json',
            # 'Authorization': f'Bearer {os.getenv("GITHUB_PAT")}'
            'Authorization': f'Bearer {GITHUB_PAT}'
        }
    try:
        response = requests.get(commits_url, headers=headers)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            return response.json()
        else:
            # If the request was not successful, raise an exception or return None.
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # Handle any exceptions that occurred during the request (e.g., connection error, timeout).
        print(f"An error occurred while fetching commits: {e}")
        return None

def get_comments(comments_url):
    headers = {
            'Accept': 'application/vnd.github+json',
            # 'Authorization': f'Bearer {os.getenv("GITHUB_PAT")}'
            'Authorization': f'Bearer {GITHUB_PAT}'
        }
    try:
        response = requests.get(comments_url, headers=headers)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            return response.json()
        else:
            # If the request was not successful, raise an exception or return None.
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # Handle any exceptions that occurred during the request (e.g., connection error, timeout).
        print(f"An error occurred while fetching comments: {e}")
        return None

def addPullRequest(pull, project,week):
    p = {
                            "pr_url": pull["url"],
                            "pr_id": pull["id"],
                            "pr_node_id": pull["node_id"],
                            "html_url": pull["html_url"],
                            "status": pull["state"],
                            "title": pull["title"],
                            "raised_by_username": pull["user"]["login"],
                            "raised_by_id": pull["user"]["id"],
                            "body": pull["body"],
                            "created_at": pull["created_at"],
                            "updated_at": pull["updated_at"],
                            "closed_at": pull["closed_at"],
                            "merged_at": pull["merged_at"],
                            "assignees": pull["assignees"],
                            "requested_reviewers": pull["requested_reviewers"],
                            "labels": pull["labels"],
                            "review_comments_url": pull["review_comments_url"],
                            "comments_url": pull["comments_url"],
                            "repository_id": pull["base"]["repo"]["id"],
                            "repository_owner_name": pull["base"]["repo"]["owner"]["login"],
                            "repository_owner_id": pull["base"]["repo"]["owner"]["id"],
                            "repository_url": pull["base"]["repo"]["html_url"],
                            "merged_by_username":pull["merged_by"]["login"] if pull.get("merged_by") else None,
                            "merged_by_id":pull["merged_by"]["id"] if pull.get("merged_by") else None,
                            "merged": pull["merged"] if pull.get("merged") else None,
                            "number_of_commits": pull["commits"],
                            "number_of_comments": pull["comments"] ,
                            "lines_of_code_added": pull["additions"] ,
                            "lines_of_code_removed": pull["deletions"] ,
                            "number_of_files_changed": pull["changed_files"],
                            "project_folder_label": project,
                            "week_number": week

                    }
    try:
        print("Adding PR")
        print(SupabaseInterface("mentorship_program_website_pull_request").insert(p))
    except Exception as e1:
        try:
          print(f"could not add pr, updating, {e1}")
          SupabaseInterface("mentorship_program_website_pull_request").update(p, "pr_id", p["pr_id"])
        except Exception as e:
           print(e)

def addComments(comments, pr_id):
    for comment in comments:
        c = {
            "comment_id": comment["id"],
            "url": comment["url"],
            "html_url": ["html_url"],
            "commented_by_username": comment["user"]["login"],
            "commented_by_id": comment["user"]["id"],
            "created_at": comment["created_at"],
            "updated_at": comment["updated_at"],
            "body": comment["body"],
            "pr_id": pr_id,
        }
        try:
            SupabaseInterface("mentorship_program_website_comments").insert(c)
        except Exception as e:
            try:
                SupabaseInterface("mentorship_program_website_comments").update(c, "comment_id", c["comment_id"])
            except Exception as e:
                print("Comment Error", e)
                return


def insertMilestones(data):
    try:
        SupabaseInterface("mentorship_program_website_has_updated").insert(data)
    except Exception as e:
        try:
          SupabaseInterface("mentorship_program_website_has_updated").update(data, "project_folder", data["project_folder"])
        except Exception as e:
          print(e)
          return

class GitHubCommitProcessor:
    def __init__(self):
        self.supabase = SupabaseInterface("mentorship_program_website_commits")

    def process_commit_from_pr(self, commit_data, project_folder_name, pr_id):
        print(commit_data)
        # Extract relevant commit data
        data = {
            # "id": commit_data["id"],
            "node_id": commit_data["node_id"],
            "url": commit_data["url"],
            "html_url": commit_data["html_url"],
            "comment_count": commit_data["commit"]["comment_count"],
            "date": commit_data["commit"]["author"]["date"],
            "author_id": commit_data["author"]["id"],
            "author_username": commit_data["author"]["login"],
            "author_email": commit_data["commit"]["author"]["email"],
            "committer_id": commit_data["committer"]["id"],
            "committer_username": commit_data["committer"]["login"],
            "committer_email": commit_data["commit"]["committer"]["email"],
            "project_folder_name": project_folder_name,
            "pr_id": pr_id,
            "additions": commit_data["stats"]["additions"],
            "deletions": commit_data["stats"]["deletions"],
            "files":commit_data["files"]

        }

        # Check if the commit data already exists in Supabase
        existing_data = self.supabase.read("node_id", data["node_id"])

        if existing_data:
            # Update the data if it exists
            self.supabase.update(data, "node_id", data["node_id"])
        else:
            # Insert new data if it doesn't exist
            self.supabase.insert(data)

def get_commit_api_endpoint_url(s: str) -> str:
    # Define patterns for both types of URLs
    html_pattern = r'https://github\.com/([\w\-]+)/([\w\-]+)/commit/([0-9a-f]{40})'
    api_pattern = r'https://api\.github\.com/repos/([\w\-]+)/([\w\-]+)/commits/([0-9a-f]{40})'

    # First check if the API pattern is already present
    api_match = re.search(api_pattern, s)
    if api_match:
        return api_match.group(0)  # Return the full API endpoint URL

    # Check for the HTML pattern
    html_match = re.search(html_pattern, s)
    if html_match:
        owner, repo, sha = html_match.groups()
        return f'https://api.github.com/repos/{owner}/{repo}/commits/{sha}'

    # If no matches, return an empty string or raise an exception
    return ''

directories = generate_file_tree()

print(directories)

files = [
    "2023-07-07.md",
    "2023-07-14.md",
    "2023-07-21.md",
    "2023-07-28.md",
    "2023-08-04.md",
    "2023-08-11.md",
    "2023-08-18.md",
    "2023-08-25.md",
    "2023-09-01.md"
]

productNumber = 1
allPullRequests = SupabaseInterface("mentorship_program_website_pull_request").read_all()
allPullRequestIds = [pull["pr_id"] for pull in allPullRequests]
for product, projects in directories.items():
# await ctx.send(f'{product}: {productNumber}/{len(directories.keys())}')
    productNumber+=1
    for project in projects.keys():
        pullRequestToWeekMapping = dict()
        week = 1
        data = {
                "project_folder": project,
                "product": product,
                "all_links": []
            }
        for filename in files:
            url = f'https://raw.githubusercontent.com/Code4GovTech/c4gt-milestones/main/docs/2023/{product}/{project}/updates/{filename}'
            url = requests.utils.quote(url, safe='/:')
            # await ctx.send(project)
            print(project)
            markdown = send_get_request(url)
            if is_default_text(markdown=markdown):
                data[f"week{week}_is_default_text"] =True
            else:
                data[f"week{week}_is_default_text"]=False
            urls = []
            find_urls(return_ast(markdown), urls)
            data["all_links"]+=urls
            for url in urls:
                # if ' ' in url:
                # print(url, isPrUrl(url))
                if extract_github_pr_url(url):
                    url = extract_github_pr_url(url)
                    if url not in pullRequestToWeekMapping:
                        pullRequestToWeekMapping[url] = week
                    pull = getPR(url)
                    print(pull["node_id"] if pull else "No Pull")
                    if pull and isinstance(pull, dict):
                        if pull["id"] in allPullRequestIds:
                            continue
                        try:
                            addPullRequest(pull, project, pullRequestToWeekMapping[url])
                            if "comments_url" in pull:
                                comments_url = pull["comments_url"]
                                comments = get_comments(comments_url)
                                addComments(comments, pull["id"])
                            if "commits_url" in pull:
                                commits_url = pull["commits_url"]
                                commits = get_commits(commits_url)
                                print(len(commits), type(commits))
                                for commit in commits:
                                  commit_true = get_commits(commit["url"])
                                #   print(commit_true)
                                  GitHubCommitProcessor().process_commit_from_pr(commit_true, project, pull["id"])

                        except Exception as e:
                            print(e)
                            continue
                elif get_commit_api_endpoint_url(url):
                  commit_url = get_commit_api_endpoint_url(url)
                  commit = get_commits(commit_url)
                  GitHubCommitProcessor().process_commit_from_pr(commit, project, None)
            week+=1


        insertMilestones(data)