import logging
from typing import Literal

import demjson3
import requests
from requests import Response, Session

# from eastmoneypy import my_env
import time

logger = logging.getLogger(__name__)

my_env={
  "appkey": "",
  "header":"ct="
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
def add_symbols_to_group(
        codes, entity_type="stock", group_name=None, group_id=None, session: Session = None
):
    if not group_id:
        assert group_name is not None
        group_id = get_group_id(group_name, session=session)
        if not group_id:
            raise Exception(f"could not find group:{group_name}")
    codeList = [to_eastmoney_code(code, entity_type=entity_type) for code in codes]
    codeList = ",".join(codeList)
    # print(codeList)
    ts = current_timestamp()
    url = f"http://myfavor.eastmoney.com/v4/webouter/aslot?appkey={APIKEY}&cb=jQuery112404771026622113468_{ts - 10}&g={group_id}&scs={codeList}&_={ts}"

    if session:
        resp = session.get(url, headers=HEADER)
    else:
        resp = requests.get(url, headers=HEADER)
    # print(resp.text)
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
    # print(codeList)
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
    # print(codeList)
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
def buy(code:str, price:float,stock_num:int)->str:
    return commit_buy_or_sell_order(code, price,stock_num,'buy',order_type ="spo_order_limit")
def sell(code:str, price:float,stock_num:int)->str:
    return commit_buy_or_sell_order(code, price,stock_num,'sell',order_type ="spo_order_limit")
def commit_buy_or_sell_order(code:str, price:float,stock_num:int,buy_or_sell:Literal['buy', 'sell'] = 'buy',order_type:Literal['spo_order', 'spo_order_limit'] = "spo_order")->str:
    ts = current_timestamp()
    userid='2090094314376082'

    mktCode="1" if code.startswith("6") else "0"
    zjzh="241990400000029517"
    order_type="spo_order"  # spo_hold 持仓信息
    mmfx="1" if buy_or_sell == 'buy'  else "2" # 1:买 2：卖
    mmfx_zh="买入" if buy_or_sell == 'buy'  else "卖出" # 1:买 2：卖
    
    url = f"""https://simoper.eastmoney.com/oper_tzzh_v2?cb=jQuery1123026493533723791596_{ts - 10}&"""
    url += f"""userid={userid}&"""
    url += f"""zjzh={zjzh}&plat=2&ver=web20&"""
    url += f"""type={order_type}&mmfx={mmfx}&mktCode={mktCode}&"""
    url += f"""stkCode={code}&price={price}&wtsl={stock_num}&"""
    url += f"""r=9633477&_={ts}"""
    
    hd ="ct=RMw3jGQaWkKGz7v-DWWT-7G5pseKYoUAKCTo7nodiuc6r2wAgK_cGVYZg7WgnSRc8vLqXo96GiM5xZqn4HcgaZfkto1FFp9vWf5zY-tMJcWGRwLhIRtUFHMTb5nPyRYgP5yMvmC_VbXTZPx0XoL8XX_doVToX0x3VFomieXL98g; ut=FobyicMgeV7JB-nm6VZO-UUwigGmwZjvb9fFo6XVFphAB_tT-zJaKYv5-XvwIJapoJk8c6XLhbUn0JXDpCcLMhJtr_RkKChrx-GWuGUaxkFQmuBVK8hpClmiyU0vb_qQMqrXJw1aN43bapSm-lXpst5ZNoj6MH-N4sKuo2_KihUvoUYYGiB1iXGFM4FEuaCitSmpsM3cROAuMENGATxJR_lQ4HwNYIXhPc1jGwb7KyMta8QsdhYcKGOiHRxO_ASCJVt0kPFZSi1eDMBlU6pctRa2z34O4olufeQ2PIwAUHyUYyBPXwZTvts7YOqiPIW_NeepykUsfVNF0VgGIICQEKGMLTZ3vvYjns9on9IYHwZOCi8Y7SvTPL0XDrdeB8Vmj-FpMelG9-bkXHPaf6xfXFKxSg9ocCW0XbM1q0PtqRnVLLuvqxzMCRaiWxe7cW1wLgLoKEepXZU8zu9Kxr_Bih9zTZp9gROoPDnW1NGM4Cq3VvPG4BC05wm2I1KjOa_A3BL9sXcI5H8;"
    HEADER_NOW = {
        'Referer':'https://group.eastmoney.com/room/index.html',
        'Cookie':hd
    }
    resp = requests.get(url, headers=HEADER_NOW)
    if resp.status_code == 200:
        result = resp.text
        js_text = result[result.index("(") + 1: result.index(")")]
        ret = demjson3.decode(js_text)
        result = ret.get("result") 
        if result == 0:
            return f"{mmfx_zh}{code}, 下单成功"
        else:
            msg = ret.get("message")     
            return f"{mmfx_zh}{code}, 下单失败! 原因：{msg}"
    else:
        return f"请求失败！状态码：{resp.status_code}.{resp.content}"
    
def cancel_order(code:str,order_no:str)->str:
    # 
    ts = current_timestamp()
    userid='2090094314376082'
    
    
    mktCode="1" if code.startswith("6") else "0"
    zjzh="241990400000029517"
    # wth='242100200000068562'
    wth=order_no
    order_type="spo_cancel"  # 撤单
    mmfx="1"
    
    url = f"""https://simoper.eastmoney.com/oper_tzzh_v2?cb=jQuery1123026493533723791596_{ts - 10}&"""
    url += f"""userid={userid}&"""
    url += f"""zjzh={zjzh}&plat=2&ver=web20&"""
    url += f"""wth={wth}&"""
    url += f"""type={order_type}&mmfx={mmfx}&mktCode={mktCode}&"""
    url += f"""stkCode={code}&"""
    url += f"""r=9633477&_={ts}"""
    
    hd ="ct=RMw3jGQaWkKGz7v-DWWT-7G5pseKYoUAKCTo7nodiuc6r2wAgK_cGVYZg7WgnSRc8vLqXo96GiM5xZqn4HcgaZfkto1FFp9vWf5zY-tMJcWGRwLhIRtUFHMTb5nPyRYgP5yMvmC_VbXTZPx0XoL8XX_doVToX0x3VFomieXL98g; ut=FobyicMgeV7JB-nm6VZO-UUwigGmwZjvb9fFo6XVFphAB_tT-zJaKYv5-XvwIJapoJk8c6XLhbUn0JXDpCcLMhJtr_RkKChrx-GWuGUaxkFQmuBVK8hpClmiyU0vb_qQMqrXJw1aN43bapSm-lXpst5ZNoj6MH-N4sKuo2_KihUvoUYYGiB1iXGFM4FEuaCitSmpsM3cROAuMENGATxJR_lQ4HwNYIXhPc1jGwb7KyMta8QsdhYcKGOiHRxO_ASCJVt0kPFZSi1eDMBlU6pctRa2z34O4olufeQ2PIwAUHyUYyBPXwZTvts7YOqiPIW_NeepykUsfVNF0VgGIICQEKGMLTZ3vvYjns9on9IYHwZOCi8Y7SvTPL0XDrdeB8Vmj-FpMelG9-bkXHPaf6xfXFKxSg9ocCW0XbM1q0PtqRnVLLuvqxzMCRaiWxe7cW1wLgLoKEepXZU8zu9Kxr_Bih9zTZp9gROoPDnW1NGM4Cq3VvPG4BC05wm2I1KjOa_A3BL9sXcI5H8;"
    HEADER_NOW = {
        'Referer':'https://group.eastmoney.com/room/index.html',
        'Cookie':hd
    }
    resp = requests.get(url, headers=HEADER_NOW)
    
    result = resp.text
    js_text = result[result.index("(") + 1: result.index(")")]
    ret = demjson3.decode(js_text)
    result = ret.get("result") 
    if result == 0:
        return "撤单成功"
    else:
        msg = ret.get("message")     
        return f"撤单失败! 原因：{msg}"
def get_can_cancel_order():
    ts = current_timestamp()
    userid='2090094314376082'
    zjzh="241990400000029517"
    order_type="spo_orders_cancel"  # 挂单信息
    url = f"""https://simoper.eastmoney.com/oper_tzzh_v2?cb=jQuery1123026493533723791596_{ts - 10}&"""
    url+= f"""userid={userid}&"""
    url+= f"""zjzh={zjzh}&plat=2&ver=web20&"""
    url+= f"""type={order_type}&"""
    url+= f"""r=9633477&_={ts}"""
    
    hd ="ct=RMw3jGQaWkKGz7v-DWWT-7G5pseKYoUAKCTo7nodiuc6r2wAgK_cGVYZg7WgnSRc8vLqXo96GiM5xZqn4HcgaZfkto1FFp9vWf5zY-tMJcWGRwLhIRtUFHMTb5nPyRYgP5yMvmC_VbXTZPx0XoL8XX_doVToX0x3VFomieXL98g; ut=FobyicMgeV7JB-nm6VZO-UUwigGmwZjvb9fFo6XVFphAB_tT-zJaKYv5-XvwIJapoJk8c6XLhbUn0JXDpCcLMhJtr_RkKChrx-GWuGUaxkFQmuBVK8hpClmiyU0vb_qQMqrXJw1aN43bapSm-lXpst5ZNoj6MH-N4sKuo2_KihUvoUYYGiB1iXGFM4FEuaCitSmpsM3cROAuMENGATxJR_lQ4HwNYIXhPc1jGwb7KyMta8QsdhYcKGOiHRxO_ASCJVt0kPFZSi1eDMBlU6pctRa2z34O4olufeQ2PIwAUHyUYyBPXwZTvts7YOqiPIW_NeepykUsfVNF0VgGIICQEKGMLTZ3vvYjns9on9IYHwZOCi8Y7SvTPL0XDrdeB8Vmj-FpMelG9-bkXHPaf6xfXFKxSg9ocCW0XbM1q0PtqRnVLLuvqxzMCRaiWxe7cW1wLgLoKEepXZU8zu9Kxr_Bih9zTZp9gROoPDnW1NGM4Cq3VvPG4BC05wm2I1KjOa_A3BL9sXcI5H8;"
    HEADER_NOW = {
        'Referer':'https://group.eastmoney.com/room/index.html',
        'Cookie':hd
    }
    resp = requests.get(url, headers=HEADER_NOW)
    if resp.status_code == 200:
        print(resp.status_code )
        result = resp.text
        # print(result)
        js_text = result[result.index("(") + 1: result.index(")")]
        ret = demjson3.decode(js_text)
        data = ret.get("data") 
        msg = ret.get("message")        
        print(msg)        
        data =[{"code":item['stkCode'],"name":item['stkName'],"orderType":item['orderType'],"mmflag":item['mmflag'],"order_no":item['wth']} for item in data]
        return data
    else:
        result = resp.text
        # js_text = result[result.index("(") + 1: result.index(")")]
        ret = demjson3.decode(result)
        msg = ret.get("error")        
        print(msg)
        return None 
def get_position():
    ts = current_timestamp()
    userid='2090094314376082'
    zjzh="241990400000029517"
    order_type="spo_hold"  # spo_hold 持仓信息
    url = f"""https://simoper.eastmoney.com/oper_tzzh_v2?cb=jQuery1123026493533723791596_{ts - 10}&"""
    url+= f"""userid={userid}&"""
    url+= f"""zjzh={zjzh}&plat=2&ver=web20&"""
    url+= f"""type={order_type}&"""
    url+= f"""r=9633477&_={ts}"""
    
    hd ="ct=RMw3jGQaWkKGz7v-DWWT-7G5pseKYoUAKCTo7nodiuc6r2wAgK_cGVYZg7WgnSRc8vLqXo96GiM5xZqn4HcgaZfkto1FFp9vWf5zY-tMJcWGRwLhIRtUFHMTb5nPyRYgP5yMvmC_VbXTZPx0XoL8XX_doVToX0x3VFomieXL98g; ut=FobyicMgeV7JB-nm6VZO-UUwigGmwZjvb9fFo6XVFphAB_tT-zJaKYv5-XvwIJapoJk8c6XLhbUn0JXDpCcLMhJtr_RkKChrx-GWuGUaxkFQmuBVK8hpClmiyU0vb_qQMqrXJw1aN43bapSm-lXpst5ZNoj6MH-N4sKuo2_KihUvoUYYGiB1iXGFM4FEuaCitSmpsM3cROAuMENGATxJR_lQ4HwNYIXhPc1jGwb7KyMta8QsdhYcKGOiHRxO_ASCJVt0kPFZSi1eDMBlU6pctRa2z34O4olufeQ2PIwAUHyUYyBPXwZTvts7YOqiPIW_NeepykUsfVNF0VgGIICQEKGMLTZ3vvYjns9on9IYHwZOCi8Y7SvTPL0XDrdeB8Vmj-FpMelG9-bkXHPaf6xfXFKxSg9ocCW0XbM1q0PtqRnVLLuvqxzMCRaiWxe7cW1wLgLoKEepXZU8zu9Kxr_Bih9zTZp9gROoPDnW1NGM4Cq3VvPG4BC05wm2I1KjOa_A3BL9sXcI5H8;"
    HEADER_NOW = {
        'Referer':'https://group.eastmoney.com/room/index.html',
        'Cookie':hd
    }
    resp = requests.get(url, headers=HEADER_NOW)
    if resp.status_code == 200:
        print(resp.status_code )
        result = resp.text
        # print(result)
        js_text = result[result.index("(") + 1: result.index(")")]
        ret = demjson3.decode(js_text)
        data = ret.get("data") 
        msg = ret.get("message")        
        data =[{"code":item['stkCode'],"name":item['stkName'],"quantity":int(item['zqsl']),"quantity_can_use":int(item['kysl']),"purchase_price":float(item['cbj'])} for item in data]
        return data
    else:
        result = resp.text
        js_text = result[result.index("(") + 1: result.index(")")]
        ret = demjson3.decode(js_text)
        msg = ret.get("message")        
        print(msg)
        return None 
def get_balance_info() ->dict:
    ts = current_timestamp()
    userid='2090094314376082'
    zjzh="241990400000029517"
    order_type="spo_bal_info"  # spo_bal_info 账户信息
    url = f"""https://simoper.eastmoney.com/oper_tzzh_v2?cb=jQuery1123026493533723791596_{ts - 10}&"""
    url+= f"""userid={userid}&"""
    url+= f"""zjzh={zjzh}&plat=2&ver=web20&"""
    url+= f"""type={order_type}&"""
    url+= f"""r=9633477&_={ts}"""
    
    hd ="ct=RMw3jGQaWkKGz7v-DWWT-7G5pseKYoUAKCTo7nodiuc6r2wAgK_cGVYZg7WgnSRc8vLqXo96GiM5xZqn4HcgaZfkto1FFp9vWf5zY-tMJcWGRwLhIRtUFHMTb5nPyRYgP5yMvmC_VbXTZPx0XoL8XX_doVToX0x3VFomieXL98g; ut=FobyicMgeV7JB-nm6VZO-UUwigGmwZjvb9fFo6XVFphAB_tT-zJaKYv5-XvwIJapoJk8c6XLhbUn0JXDpCcLMhJtr_RkKChrx-GWuGUaxkFQmuBVK8hpClmiyU0vb_qQMqrXJw1aN43bapSm-lXpst5ZNoj6MH-N4sKuo2_KihUvoUYYGiB1iXGFM4FEuaCitSmpsM3cROAuMENGATxJR_lQ4HwNYIXhPc1jGwb7KyMta8QsdhYcKGOiHRxO_ASCJVt0kPFZSi1eDMBlU6pctRa2z34O4olufeQ2PIwAUHyUYyBPXwZTvts7YOqiPIW_NeepykUsfVNF0VgGIICQEKGMLTZ3vvYjns9on9IYHwZOCi8Y7SvTPL0XDrdeB8Vmj-FpMelG9-bkXHPaf6xfXFKxSg9ocCW0XbM1q0PtqRnVLLuvqxzMCRaiWxe7cW1wLgLoKEepXZU8zu9Kxr_Bih9zTZp9gROoPDnW1NGM4Cq3VvPG4BC05wm2I1KjOa_A3BL9sXcI5H8;"
    HEADER_NOW = {
        'Referer':'https://group.eastmoney.com/room/index.html',
        'Cookie':hd
    }
    resp = requests.get(url, headers=HEADER_NOW)
    if resp.status_code == 200:
        print(resp.status_code )
        result = resp.text
        # print(result)
        js_text = result[result.index("(") + 1: result.index(")")]
        ret = demjson3.decode(js_text)
        data = ret.get("data") 
        # [{'fdyk': '-839.17', 'fdykRat': '-0.30', 'kyye': '650368.12', 'mktVal': '348792.72', 'sdje': '74128.72', 'zhName': '', 'zjzh': '241990400000029517', 'zzc': '999160.83'}]     
        data =[{"account":item['zjzh'],"total_money":float(item['zzc']),"account_pct":float(item['fdykRat']),"account_return":float(item['fdyk']),"market_value":float(item['mktVal']),"can_use_money":float(item['kyye']),"freeze_money":float(item['sdje'])} for item in data]
        return data[0]
    else:
        result = resp.text
        js_text = result[result.index("(") + 1: result.index(")")]
        ret = demjson3.decode(js_text)
        msg = ret.get("message")        
        print(msg)
        return None 

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
        # del_all_from_group( group_name=group_new_name, entity_type="stock")
    
    # 图灵甄选全榜中包含全部的出票
    group_id_today = get_group_id(group_full_name,session)
    if not group_id_today:          
        create_group(group_full_name,session) 
    # 添加自选 
    group_name_list = [group_new_name,group_full_name] 
    for group_name in group_name_list:       
       print(add_symbols_to_group(symbol_list, group_name=group_name, entity_type="stock"))

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
    # group_name_new = "最新甄选"
    # gid = get_group_id(group_name_new,session)
    # print(del_group(group_name_new,gid,session))
    # create_group(group_name_new,session)   
    # print(get_groups())  
    # print(list_entities(group_name="今日甄选", session=session)) 
    # add_to_group('300735', group_name=group_name_new, entity_type="stock") 
    # resp =buy(code = "000001",price = 10.35, stock_num=500 )
    # print(resp ,type(resp), resp.text )
    sym =['000421', '002611', '600621', '000828', '002837', '003026', '002001', '603662', '600216', '000957', '600200', '002869', '002296', '300446', '300123', '002735', '300455', '600336', '603988', '600843', '002979', '300011', '600719', '001208', '600990', '600764', '600686', '600817', '603686', '001379', '002685', '301112', '000547', '000868', '000901', '002829', '603508', '603107', '000880', '000572', '603390', '600386', '300053', '300424']
    group_name="大笔买入"
    group_full_name=f"{group_name[:3]}全榜"
    group_new_name=group_name
    # print(get_group_id(group_new_name,session))
    print(update_em_favor_list(sym,group_full_name=group_full_name,group_new_name=group_new_name))
    
    # print(get_position())
    # print(get_can_cancel_order())
    # hangup_order =get_can_cancel_order()
    # for item in hangup_order:
    #     if item['mmflag'] == '0':
    #         print(cancel_order(code=item["code"],order_no=item["order_no"]))
    
    # print(get_balance_info())

    # print(commit_buy_or_sell_order(code = "603270",price = 19.40, stock_num=300,order_type ="spo_order_limit" ) )
    # print(buy(code = "603270",price = 19.40, stock_num=300 ) )
    # print(sell(code = "000099",price = 18.40, stock_num=100.0 ) )
    # print(get_can_cancel_order())
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # order_type="spo_order"
    # type: spo_zuhe_preview
    # type: spo_bal_info  #账户信息
    # type: spo_zuhe_detail_basic #组合基本信息
    # type: spo_hold #持仓信息
    # type: spo_bal_info
    # type: spo_order_limit
    # spo_orders_cancel  挂单
    # spo_orders_all 当日委托
    # spo_deal_today 当日成交
        
    # qgqp_b_id=106944163fc0ce0e2d79fe93ec6380a2; 
    # HAList=ty-1-603777-%u6765%u4F0A%u4EFD; 
    # mtp=1; 
    # sid=125682373; 
    # vtpst=|; 
    # st_si=61900645936017;
    # p_origin=https%3A%2F%2Fpassport2.eastmoney.com; 
    # st_asi=delete; 
    # ct=RMw3jGQaWkKGz7v-DWWT-7G5pseKYoUAKCTo7nodiuc6r2wAgK_cGVYZg7WgnSRc8vLqXo96GiM5xZqn4HcgaZfkto1FFp9vWf5zY-tMJcWGRwLhIRtUFHMTb5nPyRYgP5yMvmC_VbXTZPx0XoL8XX_doVToX0x3VFomieXL98g; ut=FobyicMgeV7JB-nm6VZO-UUwigGmwZjvb9fFo6XVFphAB_tT-zJaKYv5-XvwIJapoJk8c6XLhbUn0JXDpCcLMhJtr_RkKChrx-GWuGUaxkFQmuBVK8hpClmiyU0vb_qQMqrXJw1aN43bapSm-lXpst5ZNoj6MH-N4sKuo2_KihUvoUYYGiB1iXGFM4FEuaCitSmpsM3cROAuMENGATxJR_lQ4HwNYIXhPc1jGwb7KyMta8QsdhYcKGOiHRxO_ASCJVt0kPFZSi1eDMBlU6pctRa2z34O4olufeQ2PIwAUHyUYyBPXwZTvts7YOqiPIW_NeepykUsfVNF0VgGIICQEKGMLTZ3vvYjns9on9IYHwZOCi8Y7SvTPL0XDrdeB8Vmj-FpMelG9-bkXHPaf6xfXFKxSg9ocCW0XbM1q0PtqRnVLLuvqxzMCRaiWxe7cW1wLgLoKEepXZU8zu9Kxr_Bih9zTZp9gROoPDnW1NGM4Cq3VvPG4BC05wm2I1KjOa_A3BL9sXcI5H8; 
    # pi=2090094314376082%3Bm2090094314376082%3B%E8%82%A1%E5%8F%8B6L2020T796%3Bb9%2Ba%2Fdq8lFXF6%2BWEcRDkAxfEkaTZFBDhjcWzxzu717XBF1eXD8xow8cFqzODakfF8yUzUWcKdOn4632m85VsJmE%2B6O5kwLEkojaWkbzVpda%2BRsZSI4bw6TON7ha0ur%2Fgmb8rsilCPHMdkv9KUWckoWG1ff15kzH8d9dUU3rOlcRGKU4HWHxaW%2FtCyJ0p796nZekyCJMQ%3Be%2BFnc4R63uc8uDE2WM%2BZmtFS4X2IfyOM2mIY9IC4iQB6KV7SsPPCxphegpJb0TuxBg8lKpWCyudP425IE8L%2Bxx0UNAxtrcAVDpNX1J8NDfNU0SIfXqEzP5rnR9kGYkiLPw5PGT5OF9VHG08dH9h2jIDf8nyTRQ%3D%3D; uidal=2090094314376082%e8%82%a1%e5%8f%8b6L2020T796; rskey=W1xC3OGIwYTJ1eTJIOWlBUm8vbVlQVElOdz09WFt9j; st_pvi=41425149047457; st_sp=2024-07-29%2007%3A17%3A57; st_inirUrl=http%3A%2F%2Fguba.eastmoney.com%2F; st_sn=268; st_psi=20240729083616468-113200301712-2442525922    
    # {
    #     "cmtReal": "甘州图灵932",
    #     "comment": "甘州图灵932",
    #     "concerned": 0,
    #     "dealRate": 0,
    #     "dealWinCnt": 0,
    #     "dealfailCnt": 0,
    #     "introAuditSt": 2,
    #     "nameAuditSt": 2,
    #     "ownZuhe": 2,
    #     "permit": 0,
    #     "plate_group": [],
    #     "portfRat": 0,
    #     "rank_type": [],
    #     "startDate": "2024年07月18日",
    #     "syl_20r": 0,
    #     "syl_250r": 0,
    #     "syl_5r": 0,
    #     "syl_dr": 0,
    #     "userid": 2090094314376082,
    #     "username": "股友6L2020T796",
    #     "visitors": 2,
    #     "zhmcReal": "甘州图灵",
    #     "zsyl": 0,
    #     "zuheName": "甘州图灵",
    #     "zuhe_desc_flg": 4,
    #     "zuhe_name_flg": 4,
    #     "zzc": 1000000
    # }      

