from pydantic import BaseModel, create_model

class ConnectionModel(BaseModel): # Connection model
    fingerprint: str
    publicKey: str

class LoginModel(BaseModel): # Login model
    fingerprint: str
    username: str
    hashword: str

class SignUpModel(BaseModel): # Login model
    fingerprint: str
    username: str
    hashword: str
    name: str

class ClientSettingsModel(BaseModel):
    value: str

class PasswordCheckModel(BaseModel):
    hashword: str

class PasswordChangeModel(BaseModel):
    hashword: str
    new_hashword: str