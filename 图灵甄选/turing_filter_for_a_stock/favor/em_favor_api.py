import logging

import demjson3
import requests
from requests import Response, Session

# from eastmoneypy import my_env
import time

logger = logging.getLogger(__name__)

my_env={
  "appkey": "",
  "header":""
}

APIKEY = my_env["appkey"]
HEADER = {
    'Referer':'https://quote.eastmoney.com/zixuan/',
    'Cookie':my_env['header']
}

def current_timestamp():
    return int(time.time() * 1000)

def parse_resp(resp: Response, key=None):
    if resp.status_code != 200:
        raise Exception(f"code:{resp.status_code},msg:{resp.content}")
    # {
    #   "re": true,
    #   "message": "",
    #   "result": {}
    # }
    result = resp.text
    js_text = result[result.index("(") + 1: result.index(")")]

    ret = demjson3.decode(js_text)
    logger.info(f"ret:{ret}")
    data = ret.get("data")
    if data and key:
        result_value = data.get(key)
    else:
        result_value = data

    resp.close()
    return ret["state"], result_value


def create_group(group_name, session: Session = None):
    ts = current_timestamp()
    url = f"http://myfavor.eastmoney.com/v4/webouter/ag?appkey={APIKEY}&cb=jQuery112404771026622113468_{ts - 10}&gn={group_name}&_={ts}"

    if session:
        resp = session.get(url, headers=HEADER)
    else:
        resp = requests.get(url, headers=HEADER)

    _, group = parse_resp(resp)
    return group


def get_groups(session: Session = None):
    ts = current_timestamp()
    ts_10 = ts -10
    url = f"http://myfavor.eastmoney.com/v4/webouter/ggdefstkindexinfos?appkey={APIKEY}&cb=jQuery112407703233916827181_{ts_10}&g=1&_={ts}"
    # HEADER['Referer']='https://quote.eastmoney.com/zixuan/'
    # HEADER['Cookie']="ct=TlTpWFhvjSJKB95m_keQV3dU_4GXll7NbyCQnkMGdSCRVm8ybxSZsqA_K5GPiHA_uaR80-iTSizqjvjSBqVG37kzLusjCOujGJ1PKksZUAY9ZQYgUqDo28AYNKA-cAJEHGDSiUBCEB9LEkt2hXmuHeU_9MXH9ErhOLs8pNgPQaI; ut=FobyicMgeV5AOMzpK3bVzMa2WswQh_7dk0H2cN1bvyTyE3Rvuf4IG77pU0-4ek82Kb2AawujzMU-ZBjEz6qcCrKX1Bh5Ua2c8bnD750oR_Myse6easKbITaEy2xVsjjguEbLShEnCKETW5FZY_N-6WBwHYX5k3y2QIt1Z9hu_qSAFfp2XGV8db1znyAPNkhifl2Akn2dBcienYgNDj3LV6TU6FvVPhRDM3TglwS4UhA8GKerVFyCa_FuZuZiVPF8dHyQH353enuYjk7ZwyPFgorCwEBEZ4ZH;"
    if session:
        resp = session.get(url, headers=HEADER)
    else:
        resp = requests.get(url, headers=HEADER)

    _, value = parse_resp(resp, key="ginfolist")
    return value


def rename_group(group_id, group_name, session: Session = None):
    ts = current_timestamp()
    url = f"http://myfavor.eastmoney.com/v4/webouter/mg?appkey={APIKEY}&cb=jQuery112406922055532444666_{ts - 10}&g={group_id}&gn={group_name}&_={ts}"

    if session:
        resp = session.get(url, headers=HEADER)
    else:
        resp = requests.get(url, headers=HEADER)

    ret, _ = parse_resp(resp)
    return ret


def del_group(group_name=None, group_id=None, session: Session = None):
    if not group_id:
        assert group_name is not None
        group_id = get_group_id(group_name, session=session)
        if not group_id:
            raise Exception(f"could not find group:{group_name}")

    ts = current_timestamp()
    url = f"http://myfavor.eastmoney.com/v4/webouter/dg?appkey={APIKEY}&cb=jQuery1124005355240135242356_{ts - 10}&g={group_id}&_={ts}"

    if session:
        resp = session.get(url, headers=HEADER)
    else:
        resp = requests.get(url, headers=HEADER)

    ret, _ = parse_resp(resp, key=None)
    return ret


def get_group_id(group_name, session=None):
    groups = get_groups(session=session)
    groups = [group for group in groups if group["gname"] == group_name]
    if groups:
        return groups[0]["gid"]
    return None


def list_entities(group_name=None, group_id=None, session: Session = None):
    if not group_id:
        assert group_name is not None
        group_id = get_group_id(group_name, session=session)
        if not group_id:
            raise Exception(f"could not find group:{group_name}")
    ts = current_timestamp()
    url = f"https://myfavor.eastmoney.com/v4/webouter/gstkinfos?appkey={APIKEY}&cb=jQuery112404771026622113468_{ts - 10}&g={group_id}&_={ts}"

    if session:
        resp = session.get(url, headers=HEADER)
    else:
        resp = requests.get(url, headers=HEADER)

    _, result = parse_resp(resp)
    datas = result["stkinfolist"]
    return [data["security"].split("$")[1] for data in datas]
def del_from_group(
        code, entity_type="stock", group_name=None, group_id=None, session: Session = None
):
    if not group_id:
        assert group_name is not None
        group_id = get_group_id(group_name, session=session)
        if not group_id:
            raise Exception(f"could not find group:{group_name}")
    code = to_eastmoney_code(code, entity_type=entity_type)
    ts = current_timestamp()
    url = f"http://myfavor.eastmoney.com/v4/webouter/ds?appkey={APIKEY}&cb=jQuery112404771026622113468_{ts - 10}&g={group_id}&sc={code}&_={ts}"

    if session:
        resp = session.get(url, headers=HEADER)
    else:
        resp = requests.get(url, headers=HEADER)

    return parse_resp(resp)
def del_symbols_from_group(
        codes, entity_type="stock", group_name=None, group_id=None, session: Session = None
):
    if not group_id:
        assert group_name is not None
        group_id = get_group_id(group_name, session=session)
        if not group_id:
            raise Exception(f"could not find group:{group_name}")
    codeList = [to_eastmoney_code(code, entity_type=entity_type) for code in codes]
    codeList = ",".join(codeList)
    print(codeList)
    ts = current_timestamp()
    url = f"http://myfavor.eastmoney.com/v4/webouter/dslot?appkey={APIKEY}&cb=jQuery112404771026622113468_{ts - 10}&g={group_id}&scs={codeList}&_={ts}"

    if session:
        resp = session.get(url, headers=HEADER)
    else:
        resp = requests.get(url, headers=HEADER)

    return parse_resp(resp)
def del_all_from_group(entity_type="stock", group_name=None, group_id=None, session: Session = None):
    if not group_id:
        assert group_name is not None
        group_id = get_group_id(group_name, session=session)
        if not group_id:
            raise Exception(f"could not find group:{group_name}")
    codes = list_entities(group_name, session=session)
    codeList = [to_eastmoney_code(code, entity_type=entity_type) for code in codes]
    codeList = ",".join(codeList)
    print(codeList)
    ts = current_timestamp()
    url = f"http://myfavor.eastmoney.com/v4/webouter/dslot?appkey={APIKEY}&cb=jQuery112404771026622113468_{ts - 10}&g={group_id}&scs={codeList}&_={ts}"

    if session:
        resp = session.get(url, headers=HEADER)
    else:
        resp = requests.get(url, headers=HEADER)

    return parse_resp(resp)


    return parse_resp(resp)
def add_to_group(
        code, entity_type="stock", group_name=None, group_id=None, session: Session = None
):
    if not group_id:
        assert group_name is not None
        group_id = get_group_id(group_name, session=session)
        if not group_id:
            raise Exception(f"could not find group:{group_name}")
    code = to_eastmoney_code(code, entity_type=entity_type)
    ts = current_timestamp()
    url = f"http://myfavor.eastmoney.com/v4/webouter/as?appkey={APIKEY}&cb=jQuery112404771026622113468_{ts - 10}&g={group_id}&sc={code}&_={ts}"

    if session:
        resp = session.get(url, headers=HEADER)
    else:
        resp = requests.get(url, headers=HEADER)

    return parse_resp(resp)


def to_eastmoney_code(code, entity_type="stock"):
    if entity_type == "stock":
        code_ = int(code)
        # 上海
        if 600000 <= code_ <= 800000:
            return f"1%24{code}"
        else:
            return f"0%24{code}"
    if entity_type == "block":
        return f"90${code}"
    if entity_type == "stockhk":
        return f"116%24{code}"
    if entity_type == "stockus":
        return f"105%24{code}"
    assert False

def update_em_favor_list(symbol_list:list[str],group_full_name:str ,group_new_name:str):
    # 添加到东方财富自选股
    session = requests.Session()
    # 最新甄选中只包含最新的出票
    group_id_new = get_group_id(group_new_name,session)
    if not group_id_new: 
        create_group(group_new_name,session)
    else:
        # 删除上一榜出票
        stocks = list_entities(group_name=group_new_name, session=session)
        del_all_from_group( group_name=group_new_name, entity_type="stock")
        # for symbol in stocks:            
            # del_from_group(symbol, group_name=group_new_name, entity_type="stock")
    #     del _group(group_new_name, group_id_new ,session)
    #     create_group(group_new_name,session)
    
    # 图灵甄选全榜中包含全部的出票
    group_id_today = get_group_id(group_full_name,session)
    if not group_id_today:          
        create_group(group_full_name,session) 
    # 添加自选         
    for symbol in symbol_list:
        add_to_group(symbol, group_name=group_new_name, entity_type="stock")
        add_to_group(symbol, group_name=group_full_name, entity_type="stock")  

__all__ = [
    "create_group",
    "get_groups",
    "rename_group",
    "del_group",
    "get_group_id",
    "add_to_group",
    "list_entities",
    "to_eastmoney_code",
]

if __name__ == "__main__":
    
    # create_group("111")
    # print(add_to_group("MSFT", group_name="111", entity_type="stockus"))
    # del_group("111")

    # print(add_to_group("430047", group_name="111", entity_type="stock"))
    session = requests.Session()
    # print(get_groups(session=session))
    # print(list_entities(group_name="自选股", session=session))
   

    # create_group("932",session)
    # stocks=['000001','300641','600895','601777','600611','000868','002823','300397']
    # for stock in stocks:
    #   add_to_group(stock, group_name="932", entity_type="stock")  
    # del_group("932",session)
    # create_group("932",session)
    # for stock in stocks[::-1]:
    #   add_to_group(stock, group_name="932", entity_type="stock")      
    group_name_new = "最新甄选"
    # gid = get_group_id(group_name_new,session)
    # print(del_group(group_name_new,gid,session))
    # create_group(group_name_new,session)   
    # print(get_groups())  
    # print(list_entities(group_name="今日甄选", session=session)) 
    add_to_group('300735', group_name=group_name_new, entity_type="stock")  
