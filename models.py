from classes import BaseItem
from pydantic import BaseModel, create_model, validator
from typing import Any, Optional

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

class CompSectionResponseModel(BaseModel):
    result: str
    content: str

class CompSearchResponseModel(BaseModel):
    result: str
    search_results: list

class OwnedListResponseModel(BaseModel):
    result: str
    owned: str

class SingleCharacterResponseModel(BaseModel):
    result: str
    cid: str
    owner: str
    campaign: str
    public: bool
    data: str

class NewCharacterModel(BaseModel):
    url: str

class NewCharacterResponseModel(BaseModel):
    result: str
    cid: str

class MultipleCharacterResponseModel(BaseModel):
    result: str
    characters: str

class ModCharModel(BaseModel):
    path: str
    data: Any

class AtkModModel(BaseModel):
    action: str
    data: dict

class NewContainerModel(BaseModel):
    name: str

class RemContainerModel(BaseModel):
    index: int

class NewItemModel(BaseModel):
    name: str
    quantity: int
    cost: float
    weight: float
    containerIndex: int

class MoveItemModel(BaseModel):
    oldContainerIndex: int
    itemIndex: int
    newContainerIndex: int

class EditSpellModel(BaseModel):
    spellClass: str
    spellLevel: int
    spellIndex: int
    spellName: str

class NewSpellModel(BaseModel):
    spellClass: str
    spellLevel: int
    spellName: str

class NewCampaignModel(BaseModel):
    name: str
    password: str

class CampaignResponseModel(BaseModel):
    result: str
    campaign: dict

class NewCampaignResponseModel(BaseModel):
    result: str
    owned_campaigns: list
    new_campaign: dict

class MultipleCampaignResponseModel(BaseModel):
    result: str
    owned_campaigns: list
    participating_campaigns: list

class AddCharacterToCmpModel(BaseModel):
    charid: str

class BatchModel(BaseModel):
    batch: list

class BatchConfigModel(BaseModel):
    batch: dict

class CampaignSettingChangeModel(BaseModel):
    name: str
    value: Any

class AddMapToCmpModel(BaseModel):
    data: str
    rows: int
    columns: int
    name: str
    gridsize: int

class MapDataResponseModel(BaseModel):
    result: str
    data: dict

class MapModifyModel(BaseModel):
    path: str
    value: Any

class ObscureModel(BaseModel):
    x: int
    y: int
    w: int
    h: int

class EntityReferenceModel(BaseModel):
    eid: str

class JoinCampaignModel(BaseModel):
    campaign: str
    passhash: Optional[str] = None

class PassCheckResponseModel(BaseModel):
    result: str
    password_protected: bool

class NewHomebrewModel(BaseModel):
    url: str

class DelHomebrewModel(BaseModel):
    hid: str

class SearchCreaturesModel(BaseModel):
    search: str
    limit: int

class CreaturesResponseModel(BaseModel):
    result: str
    creatures: list

class AddCharacterToMapModel(BaseModel):
    charid: str
    x: int
    y: int

class ModifyEntityModel(BaseModel):
    entity: str
    batch: list

class NPCModel(BaseModel):
    x: int
    y: int
    data: dict