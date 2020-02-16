import requests


class Authentication:
    def __init__(self, ip_address=None, port=None, username=None, password=None, base_url=None):
        self._username = username
        self._password = password
        self._sid = None
        self._session_expire = True

        if base_url:
            if base_url.endswith('/'):
                self._base_url = '%swebapi/' % base_url
            else:
                self._base_url = '%s/webapi/' % base_url
        else:
            if not ip_address:
                raise AuthenticationError('Missing both base_url and ip_address on Authentication')
            if not port:
                port = 5000
            self._base_url = 'http://%s:%s/webapi/' % (ip_address, port)

        self.full_api_list = {}
        self.app_api_list = {}

    def login(self, application):
        login_api = 'auth.cgi?api=SYNO.API.Auth'
        param = {'version': '2', 'method': 'login', 'account': self._username,
                 'passwd': self._password, 'session': application, 'format': 'cookie'}

        if not self._session_expire:
            if self._sid is not None:
                self._session_expire = False
                return 'User already logged'
        else:
            session_request = requests.get(self._base_url + login_api, param)
            self._sid = session_request.json()['data']['sid']
            self._session_expire = False
            return 'User logging... New session started!'

    def logout(self, application):
        logout_api = 'auth.cgi?api=SYNO.API.Auth'
        param = {'version': '2', 'method': 'logout', 'session': application}

        response = requests.get(self._base_url + logout_api, param)
        if response.json()['success'] is True:
            self._session_expire = True
            self._sid = None
            return 'Logged out'
        else:
            self._session_expire = True
            self._sid = None
            return 'No valid session is open'

    def get_api_list(self, app=None):
        query_path = 'query.cgi?api=SYNO.API.Info'
        list_query = {'version': '1', 'method': 'query', 'query': 'all'}

        response = requests.get(self._base_url + query_path, list_query).json()

        if app is not None:
            for key in response['data']:
                if app.lower() in key.lower():
                    self.app_api_list[key] = response['data'][key]
        else:
            self.full_api_list = response['data']

        return

    def show_api_name_list(self):
        prev_key = ''
        for key in self.full_api_list:
            if key != prev_key:
                print(key)
                prev_key = key
        return

    def show_json_response_type(self):
        for key in self.full_api_list:
            for sub_key in self.full_api_list[key]:
                if sub_key == 'requestFormat':
                    if self.full_api_list[key]['requestFormat'] == 'JSON':
                        print(key + '   Returns JSON data')
        return

    def search_by_app(self, app):
        print_check = 0
        for key in self.full_api_list:
            if app.lower() in key.lower():
                print(key)
                print_check += 1
                continue
        if print_check == 0:
            print('Not Found')
        return

    def request_data(self, api_name, api_path, req_param, method=None, response_json=True):  # 'post' or 'get'

        # Convert all booleen in string in lowercase because Synology API is waiting for "true" or "false"
        for k,v in req_param.items():
            if isinstance(v, bool):
                req_param[k] = str(v).lower()

        if method is None:
            method = 'get'

        req_param['_sid'] = self._sid

        if method is 'get':
            url = ('%s%s' % (self._base_url, api_path)) + '?api=' + api_name
            response = requests.get(url, req_param)

            if response_json is True:
                return response.json()
            else:
                return response

        elif method is 'post':
            url = ('%s%s' % (self._base_url, api_path)) + '?api=' + api_name
            response = requests.post(url, req_param)

            if response_json is True:
                return response.json()
            else:
                return response

    @property
    def sid(self):
        return self._sid

    @property
    def base_url(self):
        return self._base_url

class AuthenticationError(Exception):
    pass
