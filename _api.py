from api import *

if __name__ == "__main__":
    sheet = GSheet(sheet_id='1aKNfgfVDxXygYfsmTkZvqF5ui_yjZ3y-ugLCB1Gh9ug')
    with open('out.json','w') as f:
        f.write(sheet.to_json())
    
    sheetload = Character.from_json(sheet.to_json())
    print(sheetload.abilities)