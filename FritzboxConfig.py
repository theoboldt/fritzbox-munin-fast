import os

class FritzboxConfig:
  """the server address of the Fritzbox (ip or name)"""
  server = "fritz.box"
  """the port the Fritzbox webserver runs on"""
  port = 443
  """the user name to log into the Fritzbox webinterface"""
  user = ""
  """the password to log into the Fritzbox webinterface"""
  password = ""
  useTls = True
  certificateFile = os.getenv('MUNIN_CONFDIR') + '/box.cer'

  # default constructor
  def __init__(self):
      if os.getenv('fritzbox_ip'):
        self.server = os.getenv('fritzbox_ip')
      self.user = os.getenv('fritzbox_user')
      self.password = os.getenv('fritzbox_password')
      if os.getenv('fritzbox_certificate'):
        self.certificateFile = os.getenv('fritzbox_certificate')
      if os.getenv('fritzbox_use_tls'):
        self.useTls = os.getenv('fritzbox_use_tls') == 'true'