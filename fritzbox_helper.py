#!/usr/bin/env python
"""
  fritzbox_helper - A munin plugin for Linux to monitor AVM Fritzbox
  Copyright (C) 2015 Christian Stade-Schuldt
  Copyright (C) 2019 Rene Walendy
  Author: Christian Stade-Schuldt, Rene Walendy
  Like Munin, this plugin is licensed under the GNU GPL v2 license
  http://www.opensource.org/licenses/GPL-2.0

  Add the following section to your munin-node's plugin configuration:

  [fritzbox_*]
  env.fritzbox_ip [ip address of the fritzbox]
  env.fritzbox_password [fritzbox password]
  env.fritzbox_user [fritzbox user, set any value if not required]

  This plugin supports the following munin configuration parameters:
  #%# family=auto contrib
  #%# capabilities=autoconf

  The initial script was inspired by
  https://www.linux-tips-and-tricks.de/en/programming/389-read-data-from-a-fritzbox-7390-with-python-and-bash
  framp at linux-tips-and-tricks dot de
"""

import hashlib
import sys
import os

import requests
from lxml import etree

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:10.0) Gecko/20100101 Firefox/10.0"

def save_session_id(session_id, server, port, user):
  if '__' in server or '__' in user:
    raise Exception("Reserved string \"__\" in server or user name")
  statedir = os.environ['MUNIN_PLUGSTATE'] + '/fritzbox'
  if not os.path.exists(statedir):
    os.makedirs(statedir)
  statefilename = statedir + '/' + server + '__' + str(port) + '__' + user + '.sid'
  with open(statefilename, 'w') as statefile:
    statefile.write(session_id)

def load_session_id(server, port, user):
  statedir = os.environ['MUNIN_PLUGSTATE'] + '/fritzbox'
  statefilename = statedir + '/' + server + '__' + str(port) + '__' + user + '.sid'
  if not os.path.exists(statefilename):
    return None
  with open(statefilename, 'r') as statefile:
    session_id = statefile.readline()
  return session_id

def get_session_id(server, password, user='network-maint', port=80):
  """Obtains the session id after login into the Fritzbox.
  See https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/AVM_Technical_Note_-_Session_ID.pdf
  for deteils (in German).

  :param server: the ip address of the Fritzbox
  :param password: the password to log into the Fritzbox webinterface
  :param user: the user name to log into the Fritzbox webinterface
  :param port: the port the Fritzbox webserver runs on
  :return: the session id
  """

  headers = {"Accept": "application/xml",
             "Content-Type": "text/plain",
             "User-Agent": USER_AGENT}

  url = 'http://{}:{}/login_sid.lua'.format(server, port)
  try:
    r = requests.get(url, headers=headers)
    r.raise_for_status()
  except requests.exceptions.HTTPError as err:
    print(err)
    sys.exit(1)

  root = etree.fromstring(r.content)
  session_id = root.xpath('//SessionInfo/SID/text()')[0]
  if session_id == "0000000000000000":
    challenge = root.xpath('//SessionInfo/Challenge/text()')[0]
    challenge_bf = ('{}-{}'.format(challenge, password)).encode('utf-16le')
    m = hashlib.md5()
    m.update(challenge_bf)
    response_bf = '{}-{}'.format(challenge, m.hexdigest().lower())
  else:
    return session_id

  headers = {"Accept": "text/html,application/xhtml+xml,application/xml",
             "Content-Type": "application/x-www-form-urlencoded",
             "User-Agent": USER_AGENT}

  url = 'http://{}:{}/login_sid.lua?&response={}&username={}'.format(server, port, response_bf, user)
  try:
    r = requests.get(url, headers=headers)
    r.raise_for_status()
  except requests.exceptions.HTTPError as err:
    print(err)
    sys.exit(1)

  root = etree.fromstring(r.content)
  session_id = root.xpath('//SessionInfo/SID/text()')[0]
  if session_id == "0000000000000000":
    print("ERROR - No SID received because of invalid password")
    sys.exit(0)

  save_session_id(session_id, server, port, user)

  return session_id

def post_page_content(server, session_id, page, port=80, data={}, exceptions=False):
  """Sends a POST request to the Fritzbox and returns the response

  :param server: the ip address of the Fritzbox
  :param session_id: a valid session id
  :param page: the page you are regquesting
  :param port: the port the Fritzbox webserver runs on
  :param data: POST data in a map
  :return: the content of the page
  """

  data['sid'] = session_id

  headers = {"Accept": "application/json",
             "Content-Type": "application/x-www-form-urlencoded",
             "User-Agent": USER_AGENT}

  url = 'http://{}:{}/{}'.format(server, port, page)
  try:
    r = requests.post(url, headers=headers, data=data)
    r.raise_for_status()
  except requests.exceptions.HTTPError as err:
    if exceptions:
      raise err
    print(err)
    sys.exit(1)
  return r.content

def get_page_content(server, session_id, page, port=80, params=None, exceptions=False):
    """Fetches a page from the Fritzbox and returns its content

    :param server: the ip address of the Fritzbox
    :param session_id: a valid session id
    :param page: the page you are regquesting
    :param port: the port the Fritzbox webserver runs on
    :param params: GET parameters in a map
    :return: the content of the page
    """

    headers = {"Accept": "application/xml",
               "Content-Type": "text/plain",
               "User-Agent": USER_AGENT}

    url = 'http://{}:{}/{}?sid={}'.format(server, port, page, session_id)
    if params:
      paramsStr = "&"
      l = len(params)
      i = 0
      for k,v in params.items():
        paramsStr += k + '=' + str(v)
        i += 1
        if i < l:
          paramsStr += '&'
      url = url + paramsStr
    try:
      r = requests.get(url, headers=headers)
      r.raise_for_status()
    except requests.exceptions.HTTPError as err:
      if exceptions:
        raise err
      print(err)
      sys.exit(1)
    return r.content

def get_xhr_content(server, session_id, page, port=80, exceptions=False):
    """Fetches the xhr content from the Fritzbox and returns its content

    :param server: the ip address of the Fritzbox
    :param session_id: a valid session id
    :param page: the page you are regquesting
    :param port: the port the Fritzbox webserver runs on
    :return: the content of the page
    """

    headers = {"Accept": "application/xml",
               "Content-Type": "application/x-www-form-urlencoded",
               "User-Agent": USER_AGENT}

    url = 'http://{}:{}/data.lua'.format(server, port)
    data = {"xhr": 1,
            "sid": session_id,
            "lang": "en",
            "page": page,
            "xhrId": "all",
            "no_sidrenew": ""
            }
    try:
        r = requests.post(url, data=data, headers=headers)
    except requests.exceptions.HTTPError as err:
        if exceptions:
            raise err
        print(err)
        sys.exit(1)
    return r.content

# TODO deduplicate these methods

def get_page_with_login(server, user, password, page, port=80, params=None):
  session_id = load_session_id(server, port, user)
  if session_id != None:
    try:
      return get_page_content(server, session_id, page, port, params, exceptions=True)
    except requests.exceptions.HTTPError as e:
      code = e.response.status_code
      if code != 403:
        print(err)
        sys.exit(1)
  session_id = get_session_id(server, password, user, port)
  return get_page_content(server, session_id, page, port, params)

def post_page_with_login(server, user, password, page, port=80, data=None):
  session_id = load_session_id(server, port, user)
  if session_id != None:
    try:
      return post_page_content(server, session_id, page, port, data, exceptions=True)
    except requests.exceptions.HTTPError as e:
      code = e.response.status_code
      if code != 403:
        print(err)
        sys.exit(1)
  session_id = get_session_id(server, password, user, port)
  return post_page_content(server, session_id, page, port, params)
