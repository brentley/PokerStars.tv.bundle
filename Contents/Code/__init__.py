#import re
RE_THUMB_SUB = Regex(r'.*url\(([^\?)]+).*')
RE_PAGES_SUB = Regex(r'\?.*')
RE_LAST_PAGE_SUB = Regex(r'[0-9]+$')

PLUGIN_TITLE               = 'PokerStars.tv'
PLUGIN_PREFIX              = '/video/pokerstarstv'

# URLS
BASE_URL                   = 'http://www.pokerstars.tv'
CHANNELS_URL               = '%s/poker-channels' % BASE_URL
SCHEDULE_URL               = '%s/docs-pokerstarstv-schedule.html' % BASE_URL

# Default artwork and icon(s)
PLUGIN_ARTWORK             = 'art-default.jpg'
PLUGIN_ICON_DEFAULT        = 'icon-default.png'

EXCEPTIONS = ["ESPN Inside Deal","PokerStars Women","Sweat the Hand", "Editor's Picks", "EPTlive Berlin", "SCOOP 2011"]

###############################################################################
def Start():
  Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, L('pokerstars.tv'), PLUGIN_ICON_DEFAULT, PLUGIN_ARTWORK)
  Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')
  
  ObjectContainer.title1 = L('Pokerstars.tv')
  ObjectContainer.art = R(PLUGIN_ARTWORK)
  ObjectContainer.view_group = 'InfoList'

  DirectoryObject.thumb = R(PLUGIN_ICON_DEFAULT)

  HTTP.CacheTime = CACHE_1HOUR
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13'

###################################################################################################
def MainMenu():
    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(Spotlight), title="Spotlight"))
    
    channels = HTML.ElementFromURL(CHANNELS_URL, errors='ignore').xpath('//*/div[@id="template"]/ul/li/div[@class="content clearfix"]/a[@class="logo"]')
    for channel in channels:
        url      = channel.get('href')
        img      = channel.xpath('.//img')
        name     = img[0].get('alt').replace(' logo', '')
        thumb_url = img[0].get('src')
        if name not in EXCEPTIONS:
            oc.add(DirectoryObject(key=Callback(ChannelDetails, url=url, name=name, thumb_url=thumb_url),
                title=name, thumb=Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=PLUGIN_ICON_DEFAULT)))
        else:
            oc.add(DirectoryObject(key=Callback(ChannelVideos, url=url, channel_name=name, name=name),
                title=name, thumb=Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=PLUGIN_ICON_DEFAULT)))
      
    return oc
  
###################################################################################################
def ChannelDetails(url,name,thumb_url):
    oc = ObjectContainer(title2=name)
    url = url.replace('-2.html', '-full-episodes.html')
    if url[:7] == 'http://':
        the_url = url
    else:
        the_url = BASE_URL + url

    sections = HTML.ElementFromURL(the_url, errors='ignore').xpath('//*/div[@id="template"]/div[@id="clm-one"]/div/ul/li/a')
    for section in sections:
        url          = section.get('href')
        section_name = section.text.strip()
        oc.add(DirectoryObject(key=Callback(ChannelVideos, url=url, channel_name=name, name=section_name),
            title=section_name, thumb=Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=PLUGIN_ICON_DEFAULT)))
    
    return oc
  
###################################################################################################
def ChannelVideos(url,channel_name,name):
    oc = ObjectContainer(title2=name)
    videos = GetChannelVideos(url)
  
    for video in videos:
        url=video['url']
        if not url.startswith('http://'):
          url = BASE_URL + url
        oc.add(VideoClipObject(url=url, title=video['title'],
            thumb=Resource.ContentsOfURLWithFallback(url=video['thumb_url'] + '?maxwidth=512&maxheight=512', fallback=PLUGIN_ICON_DEFAULT)))

    if len(oc) == 0:
        return ObjectContainer(header="Empty", message="There aren't any items")
    else:
        return oc
  
###################################################################################################
def Spotlight():
    oc = ObjectContainer(title2=L('spotlight'))
    highlights = HTML.ElementFromURL(SCHEDULE_URL, errors='ignore').xpath('//*/div[@id="template"]/div[@id="clm-two"]/div/div[@class="content spotlight"]/ul/li')
    
    for highlight in highlights:
        title     = highlight.xpath('.//h3/a')[0].text.strip()
        link      = highlight.xpath('.//a[@class="thumb"]')[0]
        url       = link.get('href')
        if not url.startswith('http://'):
          url = BASE_URL + url
        thumb_url = link.xpath('.//img')[0].get('src')
        desc      = highlight.xpath('.//a[2]')[0].text.strip()
        is_video  = ( url.find('poker-video') != -1 )
    
        if is_video:
            oc.add(VideoClipObject(url=url, title=title, summary=desc,
                thumb=Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=PLUGIN_ICON_DEFAULT)))
        else:
            oc.add(DirectoryObject(key=Callback(ChannelDetails(url=url, name=title, thumb_url=thumb_url),
                title=title, thumb=Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=PLUGIN_ICON_DEFAULT))))
  
    if len(oc) == 0:
        return ObjectContainer(header="Empty", message="There aren't any items")
    else:
        return oc

###################################################################################################
def GetChannelVideos(url, is_sub_page=False ):
    videos = []
    the_url = BASE_URL + url
    page = HTML.ElementFromURL(the_url, errors='ignore')
    video_elements = page.xpath( '//*/div[@id="clm-two"]/div[2]/div[@class="content clearfix"]/div[@class="results_vidList"]/ul[@class="videos"]/li/a' )
    for video in video_elements:
        thumb_span = video.xpath('.//span[@class="thumb"]')[0]
        title_span = video.xpath('.//strong[@class="name"]')[0]
    
        videos.append({
            'title': title_span.text.strip(),
            'url': video.get('href'),
            'thumb_url' : RE_THUMB_SUB.sub(r'\1', thumb_span.get('style'))
            #'thumb_url': re.sub( r'.*url\(([^\?)]+).*', r'\1', thumb_span.get('style') )
            })
            
            
  
    if is_sub_page == False:
        # see if there are any other pages
        last_page = page.xpath( '//*/div[@id="clm-two"]/div[2]/div[@class="content clearfix"]/div[@class="results_vidList"]/ul[@class="pag"]/li[@class="last"]/a' )
  
    if len(last_page):
        last_page = last_page[0]
        
        #pages_url = re.sub( r'\?.*', '', url ) + re.sub( r'[0-9]+$', '', last_page.get('href') )
        pages_url = RE_PAGES_SUB.sub('', url) + RE_LAST_PAGE_SUB.sub('', last_page.get('href'))
        total_pages = int(last_page.text.strip())
        i = 2
        while (i <= total_pages):
            videos.extend( GetChannelVideos( pages_url + str(i), True ))
            i = i + 1

    return videos
