from SmartApi import SmartConnect
import os
import pyotp
API_KEY ="Y8r5TcWG"
TOTP_SECRET = "NPWR5ZRP33TM64JQOM6B54VRJM"
CLIENT_CODE = "AABM100190"
PASSWORD = "3641"
print(API_KEY,TOTP_SECRET,CLIENT_CODE,PASSWORD)
obj = SmartConnect(api_key=API_KEY)
totp = pyotp.TOTP(TOTP_SECRET).now()
ses=obj.generateSession(CLIENT_CODE, PASSWORD, totp)
print(ses.get("status'))
