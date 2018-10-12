#!/usr/bin/python
# -*- coding: utf-8 -*-
# 解析优酷视频真实地址，运行后直接粘贴优酷视频链接回车即可
# （pycharm中回车会直接跳转浏览器，可以粘贴连接后按下空格，再回车）
# 2017-08-07 modify by xzh 改为python2.7 增加下载功能
# 2018-10-12 xzh 修复下载功能
# https://github.com/malone6/youku
# 2017/4/12/22:50
# by malone

# 其他项目中使用直接按 class HomePage()中的方法即可，删除class Youku()不需解析部分，自定义方法解析json

import requests
import time
import json
import re
import urllib
import urllib2
import traceback
import os
# from fake_useragent import UserAgent
from user_agent import generate_user_agent, generate_navigator
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class Youku():

    errcount=0

    def __init__(self):
        # self.url_input = input(
        #     "粘贴你想解析的优酷视频链接粘贴到此处，如:http://v.youku.com/v_show/id_XMTU3NTkxNDIwMA==.html,然后按回车键执行！" + '\n' + '>>>')
        self.headers = {"accept-encoding": "gzip, deflate, sdch",
                        "accept-language": "zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4",
                        "user-agent": generate_user_agent(),
                        }
        # cookies中的cna，优酷请求不能禁用cookies，这是我的本地浏览器浏览优酷的cookies，直接复制过来用，默认对其url编码
        self.utid = urllib.pathname2url('/BYpE8JTKjkCAWXmx6LC8rxi')
        print self.utid
        # self.utid = 'onBdERfZriwCAW+uM3cVByOa'

        # 下载的格式
        # self.download_stream_type = 'mp4hd2'
        self.download_stream_type = 'mp4sd'

    def get_cna(self):
        response = requests.get('http://log.mmstat.com/eg.js').text
        re_obj = re.search('Etag="(.*)"', response)
        cna = re_obj.group(1)
        self.utid = urllib.pathname2url(cna)
        print self.utid
        '''默认对cna解码后传到全局变量中，替代原有的utid'''

    def get_video_info(self, video_url, retry=0):
        try:
            # 爬取过快cookie会被禁用，直接报错，此处except切换cookie
            video_id = self.extract_id(video_url)
            # 解析视频真实地址的最最最关键的请求！！！所有信息都在返回的json格式文件中。
            # 通过抓包过程中可以得到F12监控加载信息。Ctrl+F搜索json?vid=就可以看到返回的json信息，复制粘贴到json在线解析网站（www.json.cn）对照分析
            # 根据分析，包括四个参数，然后程序生成相应参数，构造URL并进行模拟请求，得到返回数据
            print '正在使用的cookie：', self.utid
            # url = 'https://ups.youku.com/ups/get.json?vid={}&ccode=0501&client_ip=192.168.1.1&utid={}&client_ts={}'.format(
            #     video_id, self.utid, int(time.time()))
            # 2018-10-12 xzh 
            # https://g.alicdn.com/player/ykplayer/0.5.61/youku-player.min.js
            # grep -oE '"[0-9a-zA-Z+/=]{256}"' youku-player.min.js
            ckey  = "7B19C0AB12633B22E7FE81271162026020570708D6CC189E4924503C49D243A0DE6CD84A766832C2C99898FC5ED31F3709BB3CDD82C96492E721BDD381735026"

            url = 'https://ups.youku.com/ups/get.json?vid={}&ccode=0502&client_ip=192.168.1.1&utid={}&client_ts={}&ckey={}'.format(
                video_id, self.utid, int(time.time()),ckey)
            # 在headers中增加反盗链
            headers = dict(
                self.headers, **{"referer": 'http://v.youku.com/v_show/id_{}.html'.format(video_id)})
            response = requests.get(url, headers=headers).text
            # print "response", response
            res_json = json.loads(response)
            if 'error' in res_json['data']:
                error = res_json['data']['error']
                # print(error)
                if str(error['code']) == '-6004':
                    '''之前有过这个url编码的错误，再次测试遇不到了。先放着，试了几次没遇到，等遇到再解决'''
                    if retry == 0:
                        print('cookie出错，对URL编码的cookie进行解码')
                        self.utid = urllib.url2pathname(self.utid)
                        return self.get_video_info(video_url, retry=1)
                    elif retry == 1:
                        print('解码后的cookie仍然不能使用，可能cookie被禁，现重新获取cookie')
                        self.get_cna()
                        return self.get_video_info(video_url)
                elif str(error['code']) == '-3307':
                    # 黄金会员才可观看
                    print('黄金会员视频无法获得视频源', error['note'])
                    pass
                elif str(error['code']) == '-2004':
                    # 登录账号订阅up主才可观看
                    print('订阅视频无法获得视频源', error['note'])
            else:
                self.parse_res(res_json)
        except:
            self.errcount +=1
            print "get_video_info error", traceback.format_exc()
            print 'cookie被禁，现重新获取cookie'
            time.sleep(3)
            self.get_cna()
            if self.errcount >3:
                return
            return self.get_video_info(video_url)

    def extract_id(self, video_url):
        '''
        正则提取输入链接video_url中的优酷视频唯一id
        '''
        result = re.search('id_(.*)\.html', video_url)
        if result:
            video_id = result.group(1)
            return video_id
        else:
            print('请检查url格式是否有误（url中是否包含了视频id）', '\n',
                  '格式应如：http://v.youku.com/v_show/id_XMTU2NTk5MDgxMg==.html')
            exit()

    def parse_res(self, res_json):
        '''
        这个只是尝试解析，应根据项目需要定制自己要的视频源
        '''
        video = res_json.get('data').get('video')
        print '\n''视频标题：', video.get('title')
        if video.get('stream_types').get('default') != None:
            # 随便找了几个视频链接试了下，大部分视频格式是在json文件的'default'标签中
            print '\n', '该视频有以下几种格式：', video.get('stream_types').get('default'), '\n'
        else:
            # 试了优酷首页的人民的名义，视频格式在'guoyu'标签中，这里直接连父标签打出来
            print '\n', '该视频有以下几种格式：', video.get('stream_types'), '\n'
        for stream in res_json.get('data').get('stream'):
            print '*' * 100
            print '视频类型：', stream.get('stream_type')
            print "视频总时长：", self.milliseconds_to_time(stream.get('milliseconds_video'))
            print '视频总大小:', '%.2f MB' % (float(stream.get('size') / (1024 ** 2)))
            self.get_seg(stream)

        self.video_download(res_json)

    # 信息中的视频时长是ms，用此函数转成时分秒的格式
    def milliseconds_to_time(self, milliseconds):
        seconds = milliseconds / 1000
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%02d:%02d:%02d" % (h, m, s)

    # 每个视频分成若干段，用此函数获得各段的信息
    def get_seg(self, stream):
        seg_num = len(stream.get('segs'))
        print '+' * 20, '该视频共%d段' % seg_num, '+' * 20
        for i in range(seg_num):
            seg = stream.get('segs')[i]
            print "第%d段时长：" % (i + 1), self.milliseconds_to_time(seg.get('total_milliseconds_video'))
            print "第%d段大小：" % (i + 1), '%.2f MB' % (float(seg.get('size') / (1024 ** 2)))
            print "第%d段视频地址：" % (i + 1), seg.get('cdn_url')

    # 根据上面的链接下载视频
    def video_download(self, res_json):
        parts = []
        video = res_json.get('data').get('video')
        filename = video.get('title')
        # print '\n', "下载视频=>保存的文件名", filename
        # if os.path.exists(filename):
        #     print 'warring:文件名已经存在了..'
        #     return
        for stream in res_json.get('data').get('stream'):
            if stream.get('stream_type') == self.download_stream_type:
                print "下载视频 start..下载格式：%s " % (self.download_stream_type)
                seg_num = len(stream.get('segs'))
                for i in range(seg_num):
                    print "第%d段 dowloading" % (i + 1)
                    seg = stream.get('segs')[i]
                    url = seg.get('cdn_url')
                    f = urllib2.urlopen(url)
                    data = f.read()
                    filenamepart = filename + "-%d" % (i + 1) + ".flv"
                    parts.append(filenamepart)
                    with open(filenamepart, "wb") as code:
                        code.write(data)
                    print "第%d段 dowloading end" % (i + 1)

        print parts
        self.ffmpeg_concat(filename, parts)

    def ffmpeg_concat(self, filename, parts):
        """合并视频flv，到mp4
        https://www.cnbeining.com/2014/05/dealing-with-cat-all-on-video-non-destructive-merge-mainly-h-264-problem/
        https://stackoverflow.com/questions/18452058/ffmpeg-concat-videos-and-images
        """
        if not parts:
            print "warring: parts is None"
            return

        try:
            f = open(filename + '.txt', 'w')
            ff = ''
            for partname in parts:
                ff = ff + 'file \'' + str(os.getcwd()) + \
                    os.sep + str(partname) + '\'\n'
                ff = ff.encode("utf8")

            f.write(ff)
            f.close()

            print 'Concating videos begin..%s.mp4' % filename
            os.system('ffmpeg -f concat -i "' + str(os.getcwd()) + os.sep +
                      str(filename) + '.txt"' + ' -c copy "' + filename + '".mp4')

            time.sleep(5)
            self.clear_ffmpeg_concat(filename, parts)
            print 'Concating videos end..%s.mp4' % filename
        except Exception, e:
            print e
            print "ffmpeg_concat error", traceback.format_exc()

    def clear_ffmpeg_concat(self, filename, parts):
        try:
            os.remove(str(os.getcwd()) + os.sep + str(filename) + '.txt')
            for partname in parts:
                os.remove(str(os.getcwd()) + os.sep + str(partname))
        except Exception, e:
            print e
            print "clear_ffmpeg_concat error", traceback.format_exc()

    def concat_test(self):
        filename = 'xinxinrui'
        os.system('ffmpeg -f concat -i "' + str(os.getcwd()) + os.sep +
                  str(filename) + '.txt"' + ' -c copy "' + filename + '".mp4')


class HomePage():
    '''获取首页所有视频的源地址，其他项目中使用直接按此方法即可'''

    def gethomepage(self):
        response = requests.get('http://www.youku.com/')
        obj = re.compile('http://v.youku.com/v_show/id_.*?.html')
        # 获取主页所有的视频url
        url_list = obj.findall(response.text)
        print url_list, len(url_list)
        res = Youku()
        count = 1
        for url in url_list:
            print count, url
            # time.sleep(0.2)
            res.get_video_info(url)
            count += 1


if __name__ == '__main__':
    url_input = raw_input(
        "粘贴你想解析的优酷视频链接粘贴到此处，"
        "如:http://v.youku.com/v_show/id_XMTU2NTk5MDgxMg==.html,然后按回车键执行！" + '\n' + '>>>')
    # # url_input='http://v.youku.com/v_show/id_XMTU3NTkxNDIwMA==.html'
    # # url_input = 'http://m.youku.com/video/id_XMjk0NDIwNTk3Ng==.html'
    youku = Youku()
    youku.get_video_info(url_input)
    # youku.concat_test()

'''
if __name__ == '__main__':
    # 一次获取首页所有视频地址，进行测试
    homepage = HomePage()
    homepage.gethomepage()
'''
