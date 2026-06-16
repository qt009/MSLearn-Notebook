from azure.identity import DefaultAzureCredential
def getAccessToken():
    cred = DefaultAzureCredential()
    token = cred.get_token("https://learn.microsoft.com/.default")
    return token.token