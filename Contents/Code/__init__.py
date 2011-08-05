import re

VIDEO_PREFIX = '/video/aljazeera'

YOUTUBE_VIDEO_DETAILS = 'http://gdata.youtube.com/feeds/api/videos/%s?v=2&alt=jsonc'
YOUTUBE_VIDEO_PAGE = 'http://www.youtube.com/watch?v=%s'

YOUTUBE_QUERY = 'http://gdata.youtube.com/feeds/api/videos?q=%s&author=aljazeeraenglish&v=2&prettyprint=true&orderby=updated'
YOUTUBE_FEEDS = 'http://gdata.youtube.com/feeds/api/videos/-/%s?v=2&author=AljazeeraEnglish&prettyprint=true&orderby=updated'

YOUTUBE_VIDEO_FORMATS = ['Standard', 'Medium', 'High', '720p', '1080p']
YOUTUBE_FMT = [34, 18, 35, 22, 37]

NEWSTAG = ['africanews','americasnews','asia-pacificnews','asianews','europenews','middleeastnews','sportsnews']
PROGTAG = ['faultlines','rizkhan','oneonone','insidestory','101east','empireprog','witnessprog','countingcost','listeningpost','insideiraq','arabstreet','frostworld','fps','peoplepower']

BASEURL = 'http://english.aljazeera.net'
VIDEOURL = BASEURL + '/video/'
LIVEURL = BASEURL + '/watch_now'

NAME = 'Al Jazeera'
ART  = 'art-default.jpg'
ICON = 'icon-default.png'
SEARCH = 'icon-search.png'

####################################################################################################

def Start():
  Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, NAME, ICON, ART)

  Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

  MediaContainer.title1 = NAME
  MediaContainer.viewGroup = "List"
  MediaContainer.art = R(ART)
  RTMPVideoItem.thumb = R(ICON)
  DirectoryItem.thumb = R(ICON)
  VideoItem.thumb = R(ICON)

  HTTP.CacheTime = CACHE_1HOUR
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13'

####################################################################################################

def VideoMainMenu():
  dir = MediaContainer(viewGroup="List")
  dir.Append(RTMPVideoItem('rtmp://aljazeeraflashlivefs.fplive.net/aljazeeraflashlive-live', clip='aljazeera_english_1', live=True, title="Live"))
  dir.Append(Function(DirectoryItem(NewsMenu, title=L('News and Clips'))))
  dir.Append(Function(DirectoryItem(ProgMenu, title=L('Programmes'))))
  dir.Append(Function(InputDirectoryItem(Search, title="Search ...", prompt="Search", thumb=R(SEARCH))))
  return dir

####################################################################################################

def NewsMenu(sender):
  dir = MediaContainer(viewGroup="List", httpCookies=HTTP.GetCookiesForURL('http://www.youtube.com/'))

  video = JSON.ObjectFromURL("http://gdata.youtube.com/feeds/api/videos/7l8MhHkBjbk?v=2&alt=jsonc", encoding='utf-8')
  video_id = video['data']['id']
  title = video['data']['title']
  published = Datetime.ParseDate(video['data']['updated']).strftime('%a %b %d, %Y')
  summary = video['data']['description']     
  duration = int(video['data']['duration']) * 1000
  try:
    rating = float(video['data']['rating']) * 2
  except:
    rating = None
  thumb = video['data']['thumbnail']['sqDefault']

  dir.Append(Function(VideoItem(PlayVideo, title=title, subtitle=published, summary=summary, duration=duration, rating=rating, thumb=Function(Thumb, url=thumb)), video_id=video_id))

  for prog in NEWSTAG:
    infos = HTML.ElementFromURL(VIDEOURL).xpath('//td[@id="mItem_'+prog+'"]')[0]
    title = infos.text
    summary = ''

    dir.Append(Function(DirectoryItem(ParseFeed, title=title, summary=summary), url=YOUTUBE_FEEDS % prog))
  return dir

####################################################################################################

def ProgMenu(sender):
  dir = MediaContainer(viewGroup="InfoList")
  for prog in PROGTAG:
    infos = HTML.ElementFromURL(VIDEOURL).xpath('//div[@id="mInfo_'+prog+'"]')[0]
    title = infos.xpath('.//a')[0].text
    thumb = BASEURL+infos.xpath('.//image')[0].get('src')
    summary = infos.text_content()

    dir.Append(Function(DirectoryItem(ParseFeed, title=title, summary=summary, thumb=Function(Thumb, url=thumb)), url=YOUTUBE_FEEDS % prog))
  return dir

####################################################################################################

def GetSummary(videoid):
  try:
    details = JSON.ObjectFromURL(YOUTUBE_VIDEO_DETAILS%videoid)
    return str(details['entry']['media$group']['media$description']['$t'])
  except:
    return ''

####################################################################################################

def Thumb(url):
  try:
    data = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
    return DataObject(data, 'image/jpeg')
  except:
    return Redirect(R(ICON))

####################################################################################################

def ParseFeed(sender=None, url=''):
  dir = MediaContainer(viewGroup='InfoList', httpCookies=HTTP.GetCookiesForURL('http://www.youtube.com/'))

  if url.find('?') > 0:
    url = url + '&alt=json'
  else:
    url = url + '?alt=json'

  rawfeed = JSON.ObjectFromURL(url, encoding='utf-8')
  if rawfeed['feed'].has_key('entry'):
    for video in rawfeed['feed']['entry']:
      if video.has_key('yt$videoid'):
        video_id = video['yt$videoid']['$t']
      else:
        try:
          video_page = video['media$group']['media$player'][0]['url']
        except:
          video_page = video['media$group']['media$player']['url']
        video_id = re.search('v=([^&]+)', video_page).group(1)
      title = video['title']['$t']

      try:
        published = Datetime.ParseDate(video['published']['$t']).strftime('%a %b %d, %Y')
      except: 
        published = Datetime.ParseDate(video['updated']['$t']).strftime('%a %b %d, %Y')
      try: 
        summary = video['content']['$t']
      except:
        summary = video['media$group']['media$description']['$t']

      duration = int(video['media$group']['yt$duration']['seconds']) * 1000

      try:
        rating = float(video['gd$rating']['average']) * 2
      except:
        rating = None

      thumb = video['media$group']['media$thumbnail'][0]['url']

      dir.Append(Function(VideoItem(PlayVideo, title=title, subtitle=published, summary=summary, duration=duration, rating=rating, thumb=Function(Thumb, url=thumb)), video_id=video_id))

  if len(dir) == 0:
    return MessageContainer(L('Error'), L('This query did not return any result'))
  else:
    return dir

####################################################################################################

def Search(sender, query=''):
  dir = MediaContainer()
  dir = ParseFeed(url=YOUTUBE_QUERY % (String.Quote(query, usePlus=False)))
  return dir

####################################################################################################

def PlayVideo(sender, video_id):
  yt_page = HTTP.Request(YOUTUBE_VIDEO_PAGE % (video_id), cacheTime=1).content

  fmt_url_map = re.findall('"url_encoded_fmt_stream_map".+?"([^"]+)', yt_page)[0]
  fmt_url_map = fmt_url_map.replace('\/', '/').split(',')

  fmts = []
  fmts_info = {}

  for f in fmt_url_map:
#    (fmt, url) = f.split('|')
#    fmts.append(fmt)
#    fmts_info[str(fmt)] = url
    map = {}
    params = f.split('\u0026')
    for p in params:
      (name, value) = p.split('=')
      map[name] = value
    quality = int(map['itag'])
    fmts_info[quality] = String.Unquote(map['url'])
    fmts.append(quality)

  index = YOUTUBE_VIDEO_FORMATS.index(Prefs['youtube_fmt'])
  if YOUTUBE_FMT[index] in fmts:
    fmt = YOUTUBE_FMT[index]
  else:
    for i in reversed( range(0, index+1) ):
      if str(YOUTUBE_FMT[i]) in fmts:
        fmt = YOUTUBE_FMT[i]
        break
      else:
        fmt = 5

  url = (fmts_info[int(fmt)]).decode('unicode_escape')
#  Log("  VIDEO URL --> " + url)
  return Redirect(url)
