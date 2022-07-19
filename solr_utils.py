"""
Miscellaneous utilities for querying and adding data to the
cersi-reddit Solr instance. Assumes it is running on port 8983

Author: Alexandra DeLucia
"""
import urllib.request
from http.client import RemoteDisconnected
import json
from itertools import islice
import logging
logging.basicConfig(level=logging.INFO)


class SolrHelper:
    def __init__(self, endpoint, logger=None):
        self.endpoint = endpoint
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger()
        self.handlers = ["select", "query", "mlt"]
    
    @staticmethod
    def split_every(n, iterable):
        """
        https://stackoverflow.com/questions/1915170/split-a-generator-iterable-every-n-items-in-python-splitevery
        """
        iterable = iter(iterable)
        yield from iter(lambda: list(islice(iterable, n)), [])

    def read_response(self, request):
        try:
            with urllib.request.urlopen(request) as f:
                res = json.loads(f.read())
        except (urllib.error.HTTPError, UnicodeEncodeError, RemoteDisconnected) as err:
            self.logger.error(f"{err} with payload. Check Solr logs.")
            self.logger.debug(f"{request.data=}")
            return
        return res

    def query_server(self, query, handler="select"):
        """
        https://solr.apache.org/guide/7_1/json-request-api.html
    
        Query server via JSON format
        """
        if handler not in self.handlers:
            raise ValueError(f"Handler needs to be one of {self.handlers}")
        payload = json.dumps(query).encode('utf-8')  # needs to be bytes
        req = urllib.request.Request(
            url=f"{self.endpoint}/{handler}",
            method="GET",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "charset": "utf-8",
                "Accept": "application/json"
            }
        )
        return self.read_response(req)

    def query_server_url(self, query):
        """
        https://solr.apache.org/guide/7_1/json-request-api.html
    
        Query server via URL
        """
        req = urllib.request.Request(
            url=f"{self.endpoint}/select?{query}",
            method="GET"
        )
        return self.read_response(req)

    def send_to_server(self, payload, atomic_update=False):
        """
        https://solr-user.lucene.apache.narkive.com/9l6Xezxy/atomic-update-error-with-json-handler

        Payload should be in JSON format (bytes)
        """
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        #     payload = json.dumps(payload).encode('utf-8')  # needs to be bytes
        url = f"{self.endpoint}/update/json/docs"
        if atomic_update:
            url = f"{self.endpoint}/update/json"
        req = urllib.request.Request(
            url=url,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "charset": "utf-8",
                "Accept": "application/json"
            }
        )
        return self.read_response(req)
    
    def get_loaded_documents(self, num_rows=1000000, fields=[]):
        """Return the IDs of all loaded documents along with other fields"""
        cursor = "*"
        next_cursor_mark = ""
        fields = ["id"] + fields
        while cursor != next_cursor_mark:
            # Update cursor (only after first iteration)
            if next_cursor_mark != "":
                cursor = next_cursor_mark
            # Create query
            query = urllib.parse.urlencode({
                "q": "*",
                "fl": ",".join(fields),
                "rows": num_rows,
                "cursorMark": cursor,
                "sort": "id asc"},
                encoding="utf-8")
            res = self.query_server_url(query)
            # Update next_cursor_mark and return results
            next_cursor_mark = res["nextCursorMark"]
            loaded_docs = res["response"]["docs"]
            yield loaded_docs
    
    def force_commit(self):
        """
        Trigger commit of all pending documents
        https://stackoverflow.com/questions/7815628/most-simple-way-url-to-trigger-solr-commit-of-all-pending-docs
        """
        req = urllib.request.Request(
            url=f"{self.endpoint}/update?commit=true",
            method="GET"
        )
        return self.read_response(req)
