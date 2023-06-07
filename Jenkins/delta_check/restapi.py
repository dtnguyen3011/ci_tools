import requests
import urllib3


class RestAPI:
  """Basic REST API
  """

  def __init__(self, url: str, username: str = None, password: str = None, verify_ssl: bool = True):
    self.url = url
    self.username = username
    self.password = password

    self.session = requests.Session()
    retries = urllib3.Retry(total=5,
                            backoff_factor=5,
                            status_forcelist=[500, 502, 503, 504])

    if username and password:
      self.session.auth = (self.username, self.password)

    self.session.verify = verify_ssl
    if not self.session.verify:
      urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    self.session.mount(self.url, requests.adapters.HTTPAdapter(max_retries=retries))

  def get(self, url: str = None) -> requests.Response:
    """REST GET call
    """
    result = self.session.get(url or self.url)
    return result

  def post(self, payload: str, headers: dict, url: str = None) -> requests.Response:
    """REST POST call
    """
    result = self.session.post(url or self.url, payload, headers=headers)
    return result

  def put(self, payload: dict, headers: dict, url: str = None) -> requests.Response:
    """REST PUT call
    """
    result = self.session.put(url or self.url, payload, headers=headers)
    return result

  def delete(self, url: str = None) -> requests.Response:
    """REST DELETE call
    """
    result = self.session.delete(url or self.url)
    return result

if __name__ == '__main__':
  pass