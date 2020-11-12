import scrapy
import re

from typing import Union, List
from w3lib import html
from urllib.parse import urlparse

def get_rent_id(url: str) -> str:
    u = urlparse(url)
    r = re.search('/rent-detail-(.*).html', u[2])
    return r.group(1) 


def get_domain(url: str) -> str:
    t = urlparse(url)
    return str(t[0]) + "://" + str(t[1])

def remove_tags(data: Union[str, List[str]]) -> Union[str,List[str]]:
    if not data:
        data = ''
    if isinstance(data, str):
        return html.remove_tags(data)
    elif isinstance(data, List):
        return list(map(html.remove_tags, data))
    else:
        raise TypeError('Should be string or list of string')

class A591Spider(scrapy.Spider):
    name = '591'
    #allowed_domains = ['591.com.tw']
    start_urls = ['https://rent.591.com.tw/?kind=0&region=1&other=lease&rentprice=,35000&area=10,']

    def parse(self, response):
        CONTENT = "div#content ul"
        IMG = "li.pull-left.imageBox img.boxImg.lazy"
        LINK = "li.pull-left.infoContent a"

        content = response.css(CONTENT)
        # Parse each line
        for l in content[0:1]:
            img = l.css(IMG)
            link = l.css(LINK).xpath("@href").get()
            rent_id = get_rent_id(link)
            yield {
                "path_img": img.xpath("@data-original").extract(),
                "title" : img.xpath("@title").extract(),
                "link": link,
                "rent_id": rent_id
            }
            yield scrapy.Request(url="https:" + link, callback=self.parse_annonce)
    
    def parse_annonce(self, response):
        # Get summary data
        TITLE = "span.houseInfoTitle"
        PRICE = "div.detailInfo.clearfix div.price.clearfix i"
        PRICE_DETAILS = "div.detailInfo.clearfix div.explain::text"
        UL_BOX_INFO = "div.detailInfo.clearfix ul.attr li"
        LAST_UPDATE = "div.detailInfo.clearfix div.explain.clearfix span.ft-lt"
        DATE = "div.detailInfo.clearfix div.explain.clearfix span.ft-lt"
        
        # Get details
        DETAILS = "ul.clearfix.labelList.labelList-1 li.clearfix"
        FACILITIES = "ul.facility.clearfix li.clearfix"
        LIFE = "div.lifeBox"
        INTRO = "div.houseIntro"
        LANDLORD = "div.avatarRight"
        NUM = "span.num img"
        MAP_IFRAME = "iframe.myframe"

        link_iframe = response.css(MAP_IFRAME).attrib['src']
        rent_id = get_rent_id(response.url)

        def process_facility(sel: scrapy.selector.Selector) -> str:
            exist = True
            class_no = sel.xpath('.//span[@class="no"]')
            if class_no: 
                exist = False
            return '{facility}: {exist}'.format(
                facility=remove_tags(sel.get()),
                exist=exist
                )

        yield {
            "rent_id": rent_id,
            "title_annonce": remove_tags(response.css(TITLE).get()),
            "price": remove_tags(response.css(PRICE).get()),
            "price_details": remove_tags(response.css(PRICE_DETAILS).get()),
            "box_info": remove_tags(response.css(UL_BOX_INFO).getall()),
            "last_update": remove_tags(response.css(LAST_UPDATE).get()),
            "date": remove_tags(response.css(DATE).get()),
            "details": remove_tags(response.css(DETAILS).getall()),
            "facilities": list(map(process_facility, response.css(FACILITIES))),
            "life": remove_tags(response.css(LIFE).get()),
            "intro": remove_tags(response.css(INTRO).get()),
            "landlord": remove_tags(response.css(LANDLORD).get()),
            "phone_num_link": response.css(NUM).attrib['src']
        }

        url_iframe = get_domain(response.url) + "/" + link_iframe
        yield scrapy.Request(
            url=url_iframe,
            callback=self.parse_iframe,
            cb_kwargs={"rent_id": rent_id})

    def parse_iframe(self, response, rent_id):
        URL_GGMAPS = "div.propMapBarMap iframe"
        url_ggmaps = response.css(URL_GGMAPS).attrib['src']

        # Extract coordinate
        t  = urlparse(url_ggmaps)
        re_result = re.search(r'&q=(\d*\.{0,1}\d*,\d*\.{0,1}\d*&{0})&', t.query)

        yield {
            "rent_id": rent_id,
            "coord": re_result.group(1),
        }