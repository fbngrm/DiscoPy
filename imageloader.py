#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests


class ImageHandler(object):

    def get_file(self, filepath, url, headers=None, params=None):
        response = requests.get(
            url, headers=headers, params=params, stream=True)

        if response.status_code == 200 or response.status_code == 301 or \
            response.status_code == 307:
            with open(unicode(filepath), 'wb') as file_:
                for chunk in response.iter_content():
                    file_.write(chunk)
        else:
            raise Exception(
                'unable to fetch image: %s %s' %
                (url, response.status_code))
