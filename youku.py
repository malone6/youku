# -*- coding: utf-8 -*-
# 解析优酷视频真实地址，运行后直接粘贴优酷视频链接回车即可
# （pycharm中回车会直接跳转浏览器，可以粘贴连接后按下空格，再回车）
# 2017/4/12/22:50
# by malone
import requests,time,json,re

class Youku():

    def __init__(self):
        self.url_input = input("粘贴你想解析的优酷视频链接粘贴到此处，如:http://v.youku.com/v_show/id_XMTU3NTkxNDIwMA==.html,然后按回车键执行！"+'\n'+'>>>')
        # 浏览器头
        self.headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        # cookies中的cna，优酷请求不能禁用cookies，这是我的本地浏览器浏览优酷的cookies，直接复制过来用
        self.utid = 'onBdERfZriwCAW + uM3cVByOa'

    def get_video_info(self):
        video_id = self.extract_id()
        # 解析视频真实地址的最最最关键的请求！！！所有信息都在返回的json格式文件中。
        # 通过抓包过程中可以得到F12监控加载信息。Ctrl+F搜索json?vid=就可以看到返回的json信息，复制粘贴到json在线解析网站（www.json.cn）对照分析
        # 根据分析，包括四个参数，然后程序生成相应参数，构造URL并进行模拟请求，得到返回数据
        url = 'https://ups.youku.com/ups/get.json?vid={}&ccode=0401&client_ip=192.168.1.1&utid={}&client_ts={}'.format(video_id,self.utid,int(time.time()))
        response = requests.get(url,headers=self.headers).text
        self.parse_res(response)

    # 正则提取输入链接中的优酷视频唯一id
    def extract_id(self):
        video_url = self.url_input
        pattern = re.compile('id_(.*)\.html')
        video_id = pattern.findall(video_url)[0]
        return video_id

    def parse_res(self,response):
        #对json数据进行处理
        res_json = json.loads(response)
        video = res_json.get('data').get('video')
        print('\n''视频标题：',video.get('title'))
        if video.get('stream_types').get('default') != None:
            # 随便找了几个视频链接试了下，大部分视频格式是在json文件的'default'标签中
            print('\n','该视频有以下几种格式：',video.get('stream_types').get('default'),'\n')
        else:
            # 试了优酷首页的人民的名义，视频格式在'guoyu'标签中，这里直接连父标签打出来
            print('\n', '该视频有以下几种格式：', video.get('stream_types'), '\n')
            # print('\n','该视频有以下几种格式：',video.get('stream_types').get('guoyu'),'\n')
        for stream in res_json.get('data').get('stream'):
            print('*'*100)
            print('视频类型：',stream.get('stream_type'))
            print("视频总时长：",self.milliseconds_to_time(stream.get('milliseconds_video')))
            print('视频总大小:','%.2f MB'%(float(stream.get('size')/(1024**2))))
            self.get_seg(stream)

    # 信息中的视频时长是ms，用此函数转成时分秒的格式
    def milliseconds_to_time(self,milliseconds):
        seconds = milliseconds/1000
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%02d:%02d:%02d" % (h, m, s)

    # 每个视频分成若干段，用此函数获得各段的信息
    def get_seg(self,stream):
        seg_num = len(stream.get('segs'))
        print('+'*20,'该视频共%d段'%seg_num,'+'*20)
        for i in range(seg_num):
            seg = stream.get('segs')[i]
            print("第%d段时长："%(i+1),self.milliseconds_to_time(seg.get('total_milliseconds_video')))
            print("第%d段大小："%(i+1),'%.2f MB'%(float(seg.get('size')/(1024**2))))
            print("第%d段视频地址："%(i+1),seg.get('cdn_url'))

    # 根据上面的到的链接下载视频
    def video_download(self):
        pass

if __name__ == '__main__':
    youku = Youku()
    youku.get_video_info()
    exit = input('按任意键退出')
