from collections import OrderedDict
from os import getenv

import requests
from dotenv import load_dotenv

from bot import utils

load_dotenv()


class APIClientException(Exception):
    pass


class BaseAPIClient:
    """
    Base client class of the MusicBucket App API
    """
    DATE_FORMAT = '%Y-%m-%d'
    url = f'{getenv("API_URL")}'
    token = getenv('API_TOKEN')

    def _get_url(self, endpoint_url: str):
        """This method must be implemented in all the API Classes that inherits from this"""
        raise NotImplementedError

    def process_request(self, url, method='get', params=None, data=None, json=None, headers=None, is_json=True,
                        extra_snake_case=False, auth=None, files=None):
        if not headers:
            headers = {}
        if not files:
            files = {}
        if self.token:
            headers['Authorization'] = 'Token {}'.format(self.token)

        response = requests.request(
            method=method, url=url, params=params, data=data, json=json,
            auth=auth, headers=headers, files=files,
        )
        processed_response = self.process_response(response, is_json, extra_snake_case)
        return processed_response

    def process_response(self, response, is_json, extra_snake_case):
        try:
            response.raise_for_status()
        except Exception as e:
            raise APIClientException(e) from e
        if is_json and response.content:
            return self._format_response(response.json(object_pairs_hook=OrderedDict), extra_snake_case)
        return response.content

    def _format_response(self, response, extra_snake_case):
        if isinstance(response, dict):
            if extra_snake_case:
                return OrderedDict(
                    [(utils.to_snake_case(k), self._format_response(v, extra_snake_case)
                    if isinstance(v, list) or isinstance(v, dict) else v)
                     for k, v in response.items()])
            else:
                return OrderedDict(
                    [(utils.to_snake_case(k), self._format_response(v, extra_snake_case) if isinstance(v, list) else v)
                     for k, v in response.items()])
        if isinstance(response, list):
            return [self._format_response(item, extra_snake_case) for item in response]
        return response
