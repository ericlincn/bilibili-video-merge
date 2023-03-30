import os
import json
import shutil
import requests
import math
import re

class VideoInfo:
    title:str
    video:str
    sound:str
    aid:str
    cid:str
    bvid:str
    def toString(self):
        return self.title, self.video, self.sound, self.aid, self.cid, self.bvid

def getFileList(root, onlyDir = False, fullPath = True):
    files = os.listdir(root)
    output = []
    for f in files:
        if fullPath == True:
            fullUrl = os.path.join(root, f)
        else:
            fullUrl = f
        if onlyDir == True:
            if os.path.isdir(fullUrl): output.append(fullUrl)
        else:
            output.append(fullUrl)
    return output

def getVideoInfoListFromLocal(urlList):
    list = []
    for url in urlList:
        vi = getVideoInfoFromLocal(url)
        if vi: list.append(vi)
    return list

def getVideoInfoFromLocal(localUrl):
    files = getFileList(localUrl, False, False)
    vi = VideoInfo()

    for file in files:
        ext = os.path.splitext('#' + file)[-1]
        full:str = os.path.join(localUrl, file)
        if ext == '.videoInfo':
            with open(full, 'r', encoding='utf-8') as f:
                content = f.read()
                jsonData = json.loads(content)
                vi.title = "P" + str(jsonData['p']) + " " + jsonData['tabName']
                vi.title = vi.title.replace(" ", "_")
                vi.aid = jsonData['aid']
                vi.cid = jsonData['cid']
                vi.bvid = jsonData['bvid']
        if ext == '.m4s':
            if full.find('30064.m4s') >= 0:
                vi.video = full
            elif full.find('30280.m4s') >= 0:
                vi.sound = full
    return vi

def fixFileBits(url, newFileUrl):
    with open(url, 'rb') as f:
        for i in range(0, 12):
            content = f.read(1)
            if content:
                # print(i, content, str(content))
                # if str(content) == "b'\\x00'":
                if str(content) != "b'0'":
                    f.seek(i)
                    break
        # print(f.read(1))
        with open(newFileUrl, 'wb') as write:
            shutil.copyfileobj(f, write)

def saveSubtitles(aid, cid, newFileUrl):
    apiUrl = 'https://api.bilibili.com/x/player/v2?aid='+str(aid)+'&cid='+str(cid)
    res = requests.get(apiUrl)
    jsonData = json.loads(res.content)
    subList = jsonData['data']['subtitle']['subtitles']
    if res.status_code == 200:
        if len(subList) > 0:
            subUrl = "https:" + subList[0]['subtitle_url']
            res = requests.get(subUrl)
            if res.status_code == 200:
                # print(res.content.decode('utf-8'))
                with open(newFileUrl, 'w', encoding='utf-8') as f:
                    subData = str(res.content.decode('utf-8'))
                    subData = json.loads(subData)
                    srtData = jsonToSrt(subData['body'])
                    f.write(srtData)

def jsonToSrt(data):
    srt = ''
    i = 1
    for d in data:
        start = d['from']
        stop = d['to']
        content = d['content']
        srt +='{}\n'.format(i)
        hour = math.floor(start) // 3600
        minute = (math.floor(start) - hour * 3600) // 60
        sec = math.floor(start) - hour * 3600 - minute * 60
        minisec = int(math.modf(start)[0] * 100)
        srt += str(hour).zfill(2) + ':' + str(minute).zfill(2) + ":" + str(sec).zfill(2) + ',' + str(minisec).zfill(2)
        srt += ' --> '
        hour = math.floor(stop) // 3600
        minute = (math.floor(stop) - hour * 3600) // 60
        sec = math.floor(stop) - hour * 3600 - minute * 60
        minisec = abs(int(math.modf(stop)[0] * 100 - 1))
        srt += str(hour).zfill(2) + ':' + str(minute).zfill(2) + ":" + str(sec).zfill(2) + ',' + str(minisec).zfill(2)
        srt += '\n' + content + '\n\n'
        i += 1
    return srt

def saveVideo(video, sound, ffmpeg, dstUrl:str):
    cmd = ffmpeg + ' -loglevel error -y'
    cmd += ' -i ' + video
    cmd += ' -i ' + sound
    cmd += ' -codec copy ' + dstUrl
    # print(cmd)
    re = os.system(cmd)
    return re

def getVideoInfoListFromUrl(url:str):
    bvid = url.split('/')[4]
    res = requests.get(url)
    if res.status_code == 200:
        a = re.search(r"window\.__INITIAL_STATE__=(.*?);", res.text).group(1)
        aid = a[7:16]
        getVideoInfoByID(bvid, aid)

def getVideoInfoByID(bvid, aid):
    apiUrl = 'https://api.bilibili.com/x/player/pagelist?bvid=' + str(bvid)
    res = requests.get(apiUrl)
    if res.status_code == 200:
        data = json.loads(res.text)['data']
        for i in range(0, len(data)):
            vi = VideoInfo()
            vi.bvid = bvid
            vi.aid = aid
            vi.cid = data[i]['cid']
            vi.title = "P" + str(i+1) + " " + data[i]['part']
            vi.title = vi.title.replace(" ", "_")
            vi.video=None
            vi.sound=None
            print(vi.toString())
            # getVideoUrlByID(vi.bvid, vi.cid)

def getVideoUrlByID(bvid, cid):
    # fnval=80:音视频分离m4s，=112:flv，=1:单文件360p流畅mp4
    apiUrl = 'https://api.bilibili.com/x/player/playurl?fnval=80&eq=64&cid='+str(cid)+'&bvid='+str(bvid)
    headers = {
        'referer':'https://www.bilibili.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0',
    }
    res = requests.get(apiUrl, headers=headers)
    if res.status_code == 200:
        data = json.loads(res.text)['data']['dash']
        print(data['video'][0])


biliLocalUrl = 'C:\\Users\\eric\\Videos\\bilibili'
cacheUrl = 'E:\\projects\\221122_biliVideos\\downloads'
ffmpeg = 'E:\\projects\\221122_biliVideos\\ffmpeg.exe'
cacheVideoUrl = os.path.join(cacheUrl, 'v.m4s')
cacheSoundUrl = os.path.join(cacheUrl, 's.m4s')
videoFolderList = getFileList(biliLocalUrl, True)
videoInfoList = getVideoInfoListFromLocal(videoFolderList)

def process(videoInfo:VideoInfo):
    print(videoInfo.toString())

    fixFileBits(videoInfo.video, cacheVideoUrl)
    fixFileBits(videoInfo.sound, cacheSoundUrl)
    subtitleUrl = os.path.join(cacheUrl, videoInfo.title + '.srt')
    saveSubtitles(videoInfo.aid, videoInfo.cid, subtitleUrl)

    videoUrl = os.path.join(cacheUrl, videoInfo.title + '.mp4')
    response = saveVideo(cacheVideoUrl, cacheSoundUrl, ffmpeg, videoUrl)
    if response == 0:
        try:
            os.remove(cacheVideoUrl)
            os.remove(cacheSoundUrl)
        except BaseException as e:
            print(e)

        global currentIndex
        currentIndex += 1

        if currentIndex <= len(videoInfoList) - 1:
            process(videoInfoList[currentIndex])

currentIndex = 0
process(videoInfoList[currentIndex])