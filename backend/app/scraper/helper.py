from backend.app.core.config import Config
def getAccessToken():
    cred = Config.get_credentials()
    token = cred.get_token("https://learn.microsoft.com/.default")
    return token.token