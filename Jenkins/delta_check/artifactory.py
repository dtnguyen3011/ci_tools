import requests
from restapi import RestAPI


class ArtifactoryRequestError(Exception):
  def __init__(self, result: requests.Response):
    result_payload = None
    try:
      result_payload = result.json()
    except:
      result_payload = result
    super().__init__(f'Could not get info from Artifactory API: {result_payload}')


class ArtifactoryStorageAPI(RestAPI):
  """Artifactory Storage API

  https://www.jfrog.com/confluence/display/JFROG/Artifactory+REST+API#ArtifactoryRESTAPI-ARTIFACTS&STORAGE
  """

  def __init__(self, url: str, repo: str, username: str = None, password: str = None,
               verify_ssl: bool = True):
    super().__init__(f'{url}/{repo}', username, password, verify_ssl)
    self.repo = repo
    self.storage_api_url = f'{url}/api/storage'

  def get_info(self, path: str = '') -> dict:
    """Get info about path in Artifactory repo with storage API
    """
    result = super().get(f'{self.storage_api_url}/{self.repo}/{path}')
    if result.status_code == 200:
      return result.json()
    raise ArtifactoryRequestError(result)

  def get_artifact(self, file_path: str) -> str:
    """Get artifact
    """
    result = super().get(f'{self.url}/{file_path}')
    if result.status_code == 200:
      return result.text
    raise ArtifactoryRequestError(result)

  def check_exitsFile(self, file_path: str) -> str:
    """check exits file on Artifactory
    """
    result = requests.head(f'{self.url}/{file_path}', auth=(self.username, self.password))
    if result.status_code == 200:
      return result.status_code
    raise ArtifactoryRequestError(result)
