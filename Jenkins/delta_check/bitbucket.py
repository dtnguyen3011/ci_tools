"""Bitbucket API interaction
"""
import json
import requests
import urllib3
from typing import Generator


class Activity:
  # TODO: Initialize object fields explicitly
  def __init__(self, obj: dict):
    self.__dict__.update(obj)

  def __str__(self):
    return str(f'Activity({self.__dict__})')


class Comment:
  """Represents Bitbucket Activity comment object

  {
      "properties": {
          "key": "value"
      },
      "id": 1,
      "version": 1,
      "text": "A measured reply.",
      "author": {
          "name": "jcitizen",
          "emailAddress": "jane@example.com",
          "id": 101,
          "displayName": "Jane Citizen",
          "active": true,
          "slug": "jcitizen",
          "type": "NORMAL"
      },
      "createdDate": 1578626654547,
      "updatedDate": 1578626654547,
      "comments": [
          {
              "properties": {
                  "key": "value"
              },
              "id": 1,
              "version": 1,
              "text": "An insightful comment.",
              "author": {
                  "name": "jcitizen",
                  "emailAddress": "jane@example.com",
                  "id": 101,
                  "displayName": "Jane Citizen",
                  "active": true,
                  "slug": "jcitizen",
                  "type": "NORMAL"
              },
              "createdDate": 1578626654545,
              "updatedDate": 1578626654545,
              "comments": [],
              "tasks": [],
              "severity": "NORMAL",
              "state": "OPEN",
              "permittedOperations": {
                  "editable": true,
                  "deletable": true
              }
          }
      ],
      "tasks": [],
      "severity": "NORMAL",
      "state": "OPEN",
      "permittedOperations": {
          "editable": true,
          "deletable": true
      }
  }
  """

  # TODO: Initialize object fields explicitly
  def __init__(self, obj: dict):
    self.__dict__.update(obj)

  def __contains__(self, item):
    return item in self.text

  def __str__(self):
    return str(f'Comment({self.__dict__})')


class PullRequest:
  """Represents Bitbucket pull request object

  {
      "id": 101,
      "version": 1,
      "title": "Talking Nerdy",
      "description": "It’s a kludge, but put the tuple from the database in the cache.",
      "state": "OPEN",
      "open": true,
      "closed": false,
      "createdDate": 1359075920,
      "updatedDate": 1359085920,
      "fromRef": {
          "id": "refs/heads/feature-ABC-123",
          "repository": {
              "slug": "my-repo",
              "name": null,
              "project": {
                  "key": "PRJ"
              }
          }
      },
      "toRef": {
          "id": "refs/heads/master",
          "repository": {
              "slug": "my-repo",
              "name": null,
              "project": {
                  "key": "PRJ"
              }
          }
      },
      "locked": false,
      "author": {
          "user": {
              "name": "tom",
              "emailAddress": "tom@example.com",
              "id": 115026,
              "displayName": "Tom",
              "active": true,
              "slug": "tom",
              "type": "NORMAL"
          },
          "role": "AUTHOR",
          "approved": true,
          "status": "APPROVED"
      },
      "reviewers": [
          {
              "user": {
                  "name": "jcitizen",
                  "emailAddress": "jane@example.com",
                  "id": 101,
                  "displayName": "Jane Citizen",
                  "active": true,
                  "slug": "jcitizen",
                  "type": "NORMAL"
              },
              "lastReviewedCommit": "7549846524f8aed2bd1c0249993ae1bf9d3c9998",
              "role": "REVIEWER",
              "approved": true,
              "status": "APPROVED"
          }
      ],
      "participants": [
          {
              "user": {
                  "name": "dick",
                  "emailAddress": "dick@example.com",
                  "id": 3083181,
                  "displayName": "Dick",
                  "active": true,
                  "slug": "dick",
                  "type": "NORMAL"
              },
              "role": "PARTICIPANT",
              "approved": false,
              "status": "UNAPPROVED"
          },
          {
              "user": {
                  "name": "harry",
                  "emailAddress": "harry@example.com",
                  "id": 99049120,
                  "displayName": "Harry",
                  "active": true,
                  "slug": "harry",
                  "type": "NORMAL"
              },
              "role": "PARTICIPANT",
              "approved": true,
              "status": "APPROVED"
          }
      ],
      "links": {
          "self": [
              {
                  "href": "http://link/to/pullrequest"
              }
          ]
      }
  }
  """

  # TODO: Initialize object fields explicitly
  def __init__(self, bitbucket_api, obj: dict):
    self.bitbucket_api = bitbucket_api
    self.__dict__.update(obj)
    self.url = f'{self.bitbucket_api.url}/pull-requests/{self.id}'

  # TODO: Implement get_activities
  def get_activities(self, start: int = 0, batch: int = 25) -> Activity:
    pass

  # TODO: Annotate return type to include None
  def get_comment(self, comment_id: int) -> Comment:
    if comment_id:
      result = self.bitbucket_api.get(f'{self.url}/comments/{comment_id}')
      if result.status_code == 200:
        return Comment(result.json())

  # TODO: rewrite this to use get_activities and Activity class
  def get_comments(self, start: int = 0, batch: int = 25) -> Generator[Comment, None, None]:
    """Get all comments using paged API

    Params:
      start: start page of request
      batch: batch size for get request

    Yields:
      Comment
    """
    result = self.bitbucket_api.get(f'{self.url}/activities?limit={batch}&start={start}')
    result = result.json()
    commented_activities = [activity for activity in result['values'] if activity['action'] == 'COMMENTED']
    for activity in commented_activities:
      yield Comment(activity['comment'])

    if not result['isLastPage']:
      yield from self.get_comments(start=result['nextPageStart'])

  def delete_comment(self, comment: Comment) -> bool:
    result = self.bitbucket_api.delete(f'{self.url}/comments/{comment.id}?version={comment.version}')
    if result.status_code == 204:
      return True
    return False

  # TODO: Annotate return type to include None
  def create_comment(self, text: str) -> Comment:
    payload = {'text': text}
    result = self.bitbucket_api.post(f'{self.url}/comments', payload)
    if result.status_code == 201:
      return Comment(result.json())

  # TODO: Annotate return type to include None
  def update_comment(self, comment: Comment, text: str) -> Comment:
    payload = {'text': text, 'version': comment.version}
    result = self.bitbucket_api.put(f'{self.url}/comments/{comment.id}', payload)
    if result.status_code == 200:
      return Comment(result.json())

  def __str__(self):
    return str(f'PullRequest({self.__dict__})')


# TODO: Inherit from RestAPI
class BitbucketAPI:
  """Bitbucket API object

  https://docs.atlassian.com/bitbucket-server/rest/6.10.0/bitbucket-rest.html
  """

  def __init__(self, bitbucket_url: str, username: str, password: str, project: str, repo: str,
               verify_ssl: bool = True):
    self.bitbucket_url = bitbucket_url
    self.url = f'{bitbucket_url}/rest/api/1.0/projects/{project}/repos/{repo}'
    self.username = username
    self.password = password
    self.session = requests.Session()
    retries = urllib3.Retry(total=3,
                            backoff_factor=5,
                            status_forcelist=[500, 502, 503, 504])
    self.session.auth = (self.username, self.password)
    self.session.verify = verify_ssl
    if not self.session.verify:
      urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    self.session.mount(self.bitbucket_url, requests.adapters.HTTPAdapter(max_retries=retries))

  def get(self, url: str) -> requests.Response:
    """REST GET call
    """
    result = self.session.get(url)
    return result

  def post(self, url: str, data: dict) -> requests.Response:
    """REST POST call
    """
    payload = json.dumps(data)
    headers = {'content-type': 'application/json'}
    result = self.session.post(url, payload, headers=headers)
    return result

  def put(self, url: str, data: dict) -> requests.Response:
    """REST PUT call
    """
    payload = json.dumps(data)
    headers = {'content-type': 'application/json'}
    result = self.session.put(url, payload, headers=headers)
    return result

  def delete(self, url: str) -> requests.Response:
    """REST DELETE call
    """
    result = self.session.delete(url)
    return result

  def get_pr(self, pr_id: int) -> PullRequest:
    """Get pull request by id
    """
    request_url = f'{self.url}/pull-requests/{pr_id}'
    result = self.get(request_url)
    if 200 == result.status_code:
      return PullRequest(self, result.json())

    if result.status_code in [401, 404]:
      try:
        json_result = result.json()
      except Exception:
        raise Exception(f'Error getting PR from Bitbucket url "{request_url}":, {result} ({result.text})')
      raise Exception(f'Error getting PR from Bitbucket url "{request_url}":, {json_result}')
