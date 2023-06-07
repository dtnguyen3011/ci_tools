import unittest
from unittest import mock
import delete_tags
from http.client import HTTPResponse
from io import BytesIO


class FakeSocket:
    def __init__(self, response_bytes):
        self._file = BytesIO(response_bytes)

    def makefile(self, *args, **kwargs):
        return self._file


def prepare_http_response(file_path):
    file = open(file_path, mode='r')
    all_of_it = file.read()
    file.close()

    http_response_bytes = all_of_it.encode()
    source = FakeSocket(http_response_bytes)
    response = HTTPResponse(source)
    response.begin()

    return response


class TestDeleteTags(unittest.TestCase):

    @mock.patch("http.client.HTTPSConnection.getresponse")
    def test_get_filtered_tags_fail(self, mock_getresponse):
        mock_getresponse.return_value = prepare_http_response(".\\resource\\get_filtered_tags_fail.txt")

        filtered_tags = delete_tags.get_filtered_tags("test", "null", "null", "null")

        self.assertTrue(len(filtered_tags) == 0)

    @mock.patch("http.client.HTTPSConnection.getresponse")
    def test_get_filtered_tags_single_page(self, mock_getresponse):
        mock_getresponse.return_value = prepare_http_response(".\\resource\\get_filtered_tags_single_page.txt")

        filtered_tags = delete_tags.get_filtered_tags("test", "null", "null", "null")

        self.assertTrue(len(filtered_tags) == 2)

    @mock.patch("http.client.HTTPSConnection.getresponse")
    def test_get_filtered_tags_multi_page(self, mock_getresponse):
        mock_getresponse.side_effect = [prepare_http_response(".\\resource\\get_filtered_tags_multi_page_1.txt"),
                                        prepare_http_response(".\\resource\\get_filtered_tags_multi_page_2.txt")]

        filtered_tags = delete_tags.get_filtered_tags("test", "null", "null", "null")

        self.assertTrue(len(filtered_tags) == 4)

    @mock.patch("http.client.HTTPSConnection.getresponse")
    def test_delete_tags_fail(self, mock_getresponse):
        mock_getresponse.side_effect = [prepare_http_response(".\\resource\\get_filtered_tags_single_page.txt"),
                                        prepare_http_response(".\\resource\\delete_tags_fail.txt"),
                                        prepare_http_response(".\\resource\\delete_tags_fail.txt")]

        filtered_tags = delete_tags.get_filtered_tags("test", "null", "null", "null")
        delete_tags.delete_tags(filtered_tags, "null", "null", "null", False)

    @mock.patch("http.client.HTTPSConnection.getresponse")
    def test_delete_tags_pass(self, mock_getresponse):
        mock_getresponse.side_effect = [prepare_http_response(".\\resource\\get_filtered_tags_single_page.txt"),
                                        prepare_http_response(".\\resource\\delete_tags_pass.txt"),
                                        prepare_http_response(".\\resource\\delete_tags_pass.txt")]

        filtered_tags = delete_tags.get_filtered_tags("test", "null", "null", "null")
        delete_tags.delete_tags(filtered_tags, "null", "null", "null", False)


if __name__ == '__main__':
    unittest.main()
