from SmartApi import SmartConnect
import os
import pyotp
API_KEY = os.getenv('API_KEY')
TOTP_SECRET = os.getenv('TOTP_SECRET')
CLIENT_CODE = os.getenv('CLIENT_CODE')
PASSWORD = os.getenv('PASSWORD')
print(API_KEY,TOTP_SECRET,CLIENT_CODE,PASSWORD)
obj = SmartConnect(api_key=API_KEY)
totp = pyotp.TOTP(TOTP_SECRET).now()
obj.generateSession(CLIENT_CODE, PASSWORD, totp)
