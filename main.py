import re

import bypasser
import ddl
from ddl import ddllist
from scraper import scrapper, scrapper_sites

# handle ineex


def handleIndex(ele):
    return bypasser.scrapeIndex(ele)


# loop thread
def loopthread(url):
    if url in [None, ""]:
        return

    urls = []
    for ele in url.split():
        if "http://" in ele or "https://" in ele:
            urls.append(ele)
    if len(urls) == 0:
        return

    if bypasser.ispresent(ddllist, urls[0]):
        pass
    elif bypasser.ispresent(scrapper_sites, urls[0]):
        pass
    else:
        pass

    link = ""
    for ele in urls:
        if re.search(r"https?:\/\/(?:[\w.-]+)?\.\w+\/\d+:", ele):
            return handleIndex(ele)
        elif bypasser.ispresent(ddllist, ele):
            try:
                temp = ddl.direct_link_generator(ele)
            except Exception as e:
                temp = "**Error**: " + str(e)
        elif bypasser.ispresent(scrapper_sites, ele):
            try:
                temp = scrapper(ele)
            except Exception as e:
                temp = "**Error**: " + str(e)
        else:
            try:
                temp = bypasser.shortners(ele)
            except Exception as e:
                temp = "**Error**: " + str(e)
        if temp is not None:
            link = link + temp + " "
    return link
