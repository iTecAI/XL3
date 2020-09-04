from pydantic import BaseModel, create_model

class ConnectionModel(BaseModel): # Connection model
    fingerprint: str

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

class SimpleResult(BaseModel):
    result: str

class StatusResponseModel(BaseModel):
    result: str
    endpoints: dict
    loggedIn: bool

class SettingResponseModel(BaseModel):
    result: str
    setting: str
    value: str

class AllSettingsResponseModel(BaseModel):
    result: str
    settings: dict

class PasswordCheckResponseModel(BaseModel):
    result: str
    match: bool