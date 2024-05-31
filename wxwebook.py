import requests

class WeCom:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_message(self, message):
        """发送文本消息到企业微信群"""
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f'## <font color="warning">买入信号排行版</font> \n\n {message}'
            }
        }
        response = requests.post(self.webhook_url, json=data)
        return response.json()

# 使用示例
if __name__ == "__main__":
    # 替换为你的企业微信群Webhook URL
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=88aa58e5-818a-471d-8786-84ee85984467"
    wecom = WeCom(webhook_url)
    
    # 发送消息
    message = "Hello, 这是一条来自企业微信群Webhook的消息！"
    response = wecom.send_message(message)
    
    # 打印响应信息
    print(response)