# -*- coding: utf8 -*-
import requests
import json
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# 企业微信配置
CORP_ID = "ww1dbedda07908486d"
CORP_SECRET = "QXZZIfixaUlxoLBR2SlFlrdcY1gFBloQEFzQROMshaA"
AGENT_ID = 1000002  # 确保这与获取SECRET的应用ID一致

def get_token():
    """获取企业微信访问令牌"""
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORP_ID}&corpsecret={CORP_SECRET}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        
        if token_data.get('errcode') != 0:
            logger.error(f"获取token失败: {token_data.get('errmsg')}")
            return None
        
        logger.info(f"成功获取token: {token_data.get('access_token')[:10]}...")
        return token_data.get('access_token')
    except requests.RequestException as e:
        logger.error(f"获取token请求异常: {str(e)}")
        return None

def send_text(token, title, content):
    """发送文本卡片消息"""
    if not token:
        logger.error("token为空，无法发送消息")
        return False
        
    send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
    
    data = {
        "touser": "@all",
        "msgtype": "textcard",
        "agentid": AGENT_ID,  # 使用全局变量确保一致性
        "textcard": {
            "title": title,
            "description": content,
            "url": "URL",
            "btntxt": "查看详情"
        },
        "enable_id_trans": 0,
        "enable_duplicate_check": 0,
        "duplicate_check_interval": 1800
    }
    
    try:
        # 记录发送的数据
        logger.info(f"发送消息内容: {json.dumps(data, ensure_ascii=False)}")
        
        response = requests.post(send_url, json=data, timeout=10)
        result = response.json()
        
        # 详细记录API响应
        logger.info(f"企业微信API响应: {json.dumps(result, ensure_ascii=False)}")
        
        if result.get('errcode') != 0:
            logger.error(f"发送消息失败: {result.get('errmsg')}")
            return False
        
        logger.info(f"消息发送成功，消息ID: {result.get('msgid')}")
        return True
    except requests.RequestException as e:
        logger.error(f"发送消息请求异常: {str(e)}")
        return False

# 提供多个入口函数以适应不同的云函数配置
def main_handler(event, context):
    return process_request(event, context)

def index(event, context):
    return process_request(event, context)

def main(event, context):
    return process_request(event, context)

# 原始入口点名称保留
def handler(event, context):
    return process_request(event, context)

# 实际处理请求的核心函数
def process_request(event, context):
    """处理请求的核心逻辑"""
    logger.info(f"收到请求: {json.dumps(event, ensure_ascii=False) if isinstance(event, dict) else str(event)}")
    
    # 设置默认响应
    response = {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps({
            "status": 1,
            "msg": "请求处理失败"
        }, ensure_ascii=False)
    }
    
    try:
        # 处理参数
        title = None
        content = None
        
        # 提取HTTP请求参数
        if isinstance(event, dict):
            # 尝试从URL查询参数中获取
            if 'queryStringParameters' in event:
                query_params = event.get('queryStringParameters', {})
                if query_params:
                    title = query_params.get('msgtitle')
                    content = query_params.get('msgcontent')
            
            # 尝试从请求体获取
            if not title and 'body' in event:
                try:
                    body = event['body']
                    if isinstance(body, str):
                        body_json = json.loads(body)
                        title = title or body_json.get('msgtitle')
                        content = content or body_json.get('msgcontent')
                except:
                    logger.warning("无法解析请求体JSON")
            
            # 尝试从直接事件对象获取
            if not title:
                title = event.get('msgtitle')
                content = event.get('msgcontent')
                
            # 腾讯云HTTP触发器特定格式
            if not title and 'queryString' in event:
                query_string = event.get('queryString', {})
                title = query_string.get('msgtitle')
                content = query_string.get('msgcontent')
            
            # 检查是否为测试事件
            if not title and ('key1' in event or 'key2' in event):
                logger.info("检测到测试事件，使用默认参数")
                title = "测试消息标题"
                content = "这是一条测试消息内容，来自腾讯云函数。"
        
        # 记录提取的参数
        logger.info(f"提取的参数 - 标题: {title}, 内容: {content}")
        
        # 参数检查
        if not title or not content:
            response['body'] = json.dumps({
                "status": 1,
                "msg": "缺少必要参数'msgtitle'或'msgcontent'"
            }, ensure_ascii=False)
            return response
        
        # 获取token并发送消息
        token = get_token()
        if not token:
            response['body'] = json.dumps({
                "status": 1,
                "msg": "获取企业微信访问令牌失败"
            }, ensure_ascii=False)
            return response
            
        send_result = send_text(token, title, content)
        if not send_result:
            response['body'] = json.dumps({
                "status": 1,
                "msg": "消息发送失败，请查看日志获取详细信息"
            }, ensure_ascii=False)
            return response
        
        # 消息发送成功
        response['body'] = json.dumps({
            "status": 0,
            "msg": "消息发送成功"
        }, ensure_ascii=False)
        return response
        
    except Exception as e:
        logger.error(f"处理请求时发生异常: {str(e)}", exc_info=True)
        response['body'] = json.dumps({
            "status": 1,
            "msg": f"服务器内部错误: {str(e)}"
        }, ensure_ascii=False)
        return response