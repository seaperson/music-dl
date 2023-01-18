#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@author: HJK
@file: migu
@time: 2019-08-25
"""

import copy
from .. import config
from ..api import MusicApi
from ..song import BasicSong
from urllib.parse import urlparse
import click
from ..exceptions import RequestError, ResponseError, DataError
import logging


class MiguApi(MusicApi):
    session = copy.deepcopy(MusicApi.session)
    session.headers.update(
        {"referer": "http://music.migu.cn/", "User-Agent": config.get("ios_useragent")}
    )


class MiguSong(BasicSong):
    def __init__(self):
        super(MiguSong, self).__init__()
        self.content_id = ""
        self.__initialize()

    def __initialize(self):
        self.headers = {
            'Referer': 'https://m.music.migu.cn/',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Mobile Safari/537.36'
        }
        self.search_url = 'http://pd.musicapp.migu.cn/MIGUM3.0/v1.0/content/search_all.do'
        self.player_url = 'https://app.pd.nf.migu.cn/MIGUM3.0/v1.0/content/sub/listenSong.do?channel=mx&copyrightId={copyrightId}&contentId={contentId}&toneFlag={toneFlag}&resourceType={resourceType}&userId=15548614588710179085069&netType=00'
def get_song_detail():
    r = ""
    while True:
        id = yield r
        if not id:
            continue
        # 请求详情
        params = {
            "copyrightId": id,
            "resourceType":2
        }
        r = (
            MiguApi.request(
                "https://c.musicapp.migu.cn/MIGUM2.0/v1.0/content/resourceinfo.do",
                method="GET",
                data=params,
            )
            .get("resource", [])
        )
def migu_search(keyword) -> list:
    """ 搜索音乐 """
    number = config.get("number") or 5
    params = {
        "text": keyword,
        "pageNo": 1,
        "pageSize": number,
        "searchSwitch": '{"song":1}',
    }

    songs_list = []
    MiguApi.session.headers.update(
        {"referer": "http://music.migu.cn/", "User-Agent": config.get("ios_useragent")}
    )
    res_data = (
        MiguApi.request(
            "https://pd.musicapp.migu.cn/MIGUM3.0/v1.0/content/search_all.do",
            method="GET",
            data=params,
        )
        .get("songResultData", {})
        .get("result", [])
    )

    # 启动生成器
    #g = get_song_detail()
    #g.send(None)
    songs_detail = []
    try:
        for item in res_data:
            #print(item)
            # 获得歌手名字
            singers = [s.get("name", "") for s in item.get("singers", [])]
            song = MiguSong()
            song.source = "MIGU"
            song.id = item.get("id", "")
            song.title = item.get("name", "")
            song.singer = "、".join(singers)
            albums = item.get("albums", [])
            if len(albums) > 0:
                song.album = albums[0].get("name", "")
            img_items = item.get("imgItems", [])
            if len(img_items) > 0:
                song.cover_url = img_items[0].get("img", "")
            song.lyrics_url = item.get("lyricUrl", item.get("trcUrl", ""))
            # song.duration = item.get("interval", 0)
            # 特有字段
            song.content_id = item.get("contentId", "")
            # 歌曲详情
            #r = g.send(item.get("copyrightId",""))
            """
            param = {
               "copyrightId": item.get("copyrightId",""),
               "resourceType":2
            }
            r = (
                MiguApi.request(
                "https://c.musicapp.migu.cn/MIGUM2.0/v1.0/content/resourceinfo.do",
                method="GET",
                data=param,
               )
               .get("resource", [])
             )
            rate_list = r[0].get("newRateFormats",[])
            last_rate = rate_list[len(rate_list)-1]
             #click.echo(last_rate)
            android_url = last_rate.get("androidUrl","")
            o = urlparse(android_url)
            url = "https://freetyst.nf.migu.cn"+o.path
            song.song_url = url
            song.size = round(int(last_rate.get("androidSize",0)) / 1048576,2)
            song.ext = last_rate.get("androidFileType","")
            """
             #click.echo(song)

             #click.echo(songs_list)
             # 品质从高到低排序

            rate_list = sorted(
               item.get("rateFormats", []), key=lambda x: int(x["size"]), reverse=True
            )

            for rate in rate_list:
                if (int(rate['size']) == 0) or (not rate.get('formatType', '')) or (
                not rate.get('resourceType', '')): continue
                url = "https://app.pd.nf.migu.cn/MIGUM3.0/v1.0/content/sub/listenSong.do?channel=mx&copyrightId={copyrightId}&contentId={contentId}&toneFlag={toneFlag}&resourceType={resourceType}&userId=15548614588710179085069&netType=00".format(
                 copyrightId=item.get("copyrightId", ""),
                 contentId=song.content_id,
                 toneFlag=rate.get("formatType", "SQ"),
                 resourceType=rate.get("resourceType", "E"),
                 )
                song.song_url = url
                if not url: continue
                file_size = round(int(rate.get("size", 0)) / 1048576, 2)
                song.size = file_size
                if song.available:
                  #song.size = round(int(rate.get("size", 0)) / 1048576, 2)
                  ext = "flac" if rate.get("formatType", "") == "SQ" else "mp3"
                  song.ext = rate.get("fileType", ext)
                  break
            songs_list.append(song)
        #click.echo(song)
    except Exception as e:
        print(e)
        logging.exception(e)
        raise DataError(e)
    #g.close()
    #click.echo(songs_list)
    
    return songs_list


search = migu_search
