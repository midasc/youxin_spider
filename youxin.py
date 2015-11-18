#!/usr/bin/python
#coding=utf-8

import sys
import re
import requests
import json
import time
from pymongo import MongoClient
from bs4 import BeautifulSoup

reload(sys)
sys.setdefaultencoding('utf-8')

def get_ip(url):
    client = MongoClient('192.168.31.121',27017)
    db = client.crawler_proxy
    collect = db.proxy
    z = 0
    while True:
        oneIp = collect.find()[z:z+1]
        print oneIp
        for n in oneIp:
            ip = n['_id']
        proxies ={"http":"http://"+str(ip),}
        try:
            response = requests.get(url,proxies=proxies,timeout=2)
            if response.status_code==200:
                print "成功！      IP:",ip
                return proxies               #返回有效代理IP
            else:
                print "失败！ IP：",ip
                z += 1
                continue
        except Exception,e:
            print ip,e
            z += 1
            continue


proxy = get_ip('http://www.xin.com/c/10000000.html')

def get_soup(url):
    global proxy
    try:
        s = requests.Session()
        response = s.get(url,proxies=proxy)
        if response.status_code==403:
            proxy = get_ip('http://www.xin.com/c/10000000.html')       #原ip被封时，换有效代理
            response = s.get(url,proxies=proxy)
        else:
            pass
    except:
        time.sleep(5)
        s = requests.Session()
        proxy = get_ip('http://www.xin.com/c/10000000.html')       #代理库更新时重新获取ip
        response = s.get(url,proxies=proxy)
    return BeautifulSoup(response.content,'html.parser')


def get_information(rt_id):
    dic = {}
    url = "http://www.xin.com/c/"+str(rt_id)+".html"
    print url
    contents = get_soup(url)

    dic['urlId'] = rt_id   #URL编号
    dic['testResult'] = ''    #体验报告

    try:
        brand1 = contents.find('div',class_="msg fr").find_all('tr')   #品牌
        brand2 = brand1[5].find_all('td')
        rt_brand = brand2[1].get_text()
        dic['brand'] = rt_brand
    except:
        dic['brand'] = ''

    try:
        price = contents.find('div',class_="wan_1").em.get_text().replace('￥','').replace('万','')  #售价
        dic['price'] = price
    except:
        dic['price'] = ''

    try:
        rawPrice = contents.find('div',class_="wan_2").find('del').get_text()    #原价
        dic['rawPrice'] = rawPrice
    except:
        dic['rawPrice'] = ''

    try:
        model = contents.find("div",class_="tit").h1.get_text()     #款式
        dic['model'] = model

        dic['title'] = model   #标题
    except:
        dic['model'] = ''

    dic['sourceUrl'] = url    #来源网页

    try:
        city = contents.find('b',class_="btn-ads").get_text()  #城市
        dic['city'] = city
    except:
        dic['city'] = ''

    try:
        carLocation = contents.find('div',class_="company").find_all('p')[1].get_text()   #看车地点
        dic['carLocation'] = carLocation
    except:
        dic['carLocation'] = ''


    try:
        contit = contents.find('ul',class_="contit")
        br = contit.find_all('li')
        try:
            dic['licensePlateTime'] = br[0].em.get_text()     #上牌时间
        except:
            dic['licensePlateTime'] = ''
        try:
            dic['mileage'] = br[1].em.get_text().replace('万公里','')    #行驶里程
        except:
            dic['mileage'] = ''
    except:
        dic['licensePlateTime'] = ''
        dic['mileage'] = ''

    dic['timeline'] = []  #车辆历史
    dic['assessment'] = ''    #体检报告

    try:
        lights = []
        highlights = contents.find('div',class_="configur").find_all('li')  #配置亮点
        for x in highlights:
            light = x.get_text().replace('\n','')
            lights.append(light)
        dic['highligts'] = lights
    except:
        dic['highligts'] = []

    try:
        times = contents.find('div',class_='msg fl').find_all('tr')
        try:
            inspectionExpireTime = times[4].find_all('td')[1].get_text()   #年检到期时间
            dic['inspectionExpireTime'] = inspectionExpireTime
        except:
            dic['inspectionExpireTime'] = ''
        try:
            insuranceExpireTime = times[3].find_all('td')[1].get_text()
            dic['insuranceExpireTime'] = insuranceExpireTime   #保险到期时间
        except:
            dic['insuranceExpireTime'] = ''
    except:
        dic['inspectionExpireTime'] = ''
        dic['insuranceExpireTime'] = ''
    return dic

def get_url():
    count = 0

    client = MongoClient('localhost',27017)
    db = client.test_database
    rt_posts = db.posts12
    db_count = rt_posts.find().count()
    print "原有记录条数：",db_count

    lastInfo = rt_posts.find_one({'_id':db_count})        #上次爬取的最后一条信息
    print lastInfo
    try:
        beginId = lastInfo['urlId']+1
        print "应该从这个URL编号开始爬取：", beginId
    except:
        beginId = 10000000
        print "从第一个URL开始爬。。。",beginId

    posts = db.posts12

    while True:
        rt_dic = get_information(beginId)
        if rt_dic['brand']=='' or rt_dic['price']=='':
            count = count+1
            print "单次累计无效页面条数：",count
            
            while count == 10:
                beginId = beginId-9
                print aa,"下一次应该从这个URL开始爬信息：",beginId
                print "现有记录条数：",posts.find().count()
                return beginId             
        else:
            db_count = db_count + 1
            rt_dic['_id'] = db_count   #数据库唯一标识符
            posts.insert(rt_dic)
            count = 0
        beginId = beginId + 1

if __name__=="__main__":
    get_url()



