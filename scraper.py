import concurrent.futures
from asyncio import sleep as asleep
from base64 import b64decode
from copy import deepcopy
from re import compile as recompile
from re import match as rematch
from re import sub as resub
from time import sleep, time

import chromedriver_autoinstaller
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from requests import get as rget
from requests import post as rpost
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from bypasser import ouo, rocklinks

post_id = " "
data_dict = {}
main_dict = {}
DDL_REGEX = recompile(r"DDL\(([^),]+)\, (([^),]+)), (([^),]+)), (([^),]+))\)")
POST_ID_REGEX = recompile(r'"postId":"(\d+)"')

scrapper_sites = [
    "sharespark",
    "teluguflix",
    "cinevood",
    "atishmkv",
    "taemovies",
    "toonworld4all",
    "skymovieshd",
    "animekaizoku",
    "animeremux",
    "mkvcinemas",
]

# human readable time for mkvcinemas


def get_readable_time(seconds: int) -> str:
    result = ""
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f"{days}d"
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f"{hours}h"
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f"{minutes}m"
    seconds = int(seconds)
    result += f"{seconds}s"
    return result


def looper(dict_key, click):
    payload_data = (
        DDL_REGEX.search(click).group(0).split("DDL(")[1].replace(")", "").split(",")
    )
    data = {
        "action": "DDL",
        "post_id": post_id,
        "div_id": payload_data[0].strip(),
        "tab_id": payload_data[1].strip(),
        "num": payload_data[2].strip(),
        "folder": payload_data[3].strip(),
    }
    new_num = data["num"].split("'")[1]
    data["num"] = new_num
    response = rpost(
        "https://animekaizoku.com/wp-admin/admin-ajax.php",
        headers={
            "x-requested-with": "XMLHttpRequest",
            "referer": "https://animekaizoku.com",
        },
        data=data,
    )
    loop_soup = BeautifulSoup(response.text, "html.parser")
    downloadbutton = loop_soup.find_all(class_="downloadbutton")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        [
            executor.submit(ouo_parse, dict_key, button, loop_soup)
            for button in downloadbutton
        ]


def ouo_parse(dict_key, button, loop_soup):
    try:
        ouo_encrypt = (
            recompile(r"openInNewTab\(([^),]+\)" ")")
            .search(str(loop_soup))
            .group(0)
            .strip()
            .split('"')[1]
        )
        ouo_decrypt = b64decode(ouo_encrypt).decode("utf-8").strip()
        try:
            decrypted_link = ouo(ouo_decrypt)
        except BaseException:
            decrypted_link = ouo_decrypt
        data_dict[dict_key].append([button.text.strip(), decrypted_link.strip()])
    except BaseException:
        looper(dict_key, str(button))


def scrapper(link):
    if "sharespark" in link:
        gd_txt = ""
        res = rget("?action=printpage;".join(link.split("?")))
        soup = BeautifulSoup(res.text, "html.parser")
        for br in soup.findAll("br"):
            next_s = br.nextSibling
            if not (next_s and isinstance(next_s, NavigableString)):
                continue
            next2_s = next_s.nextSibling
            if next2_s and isinstance(next2_s, Tag) and next2_s.name == "br":
                if str(next_s).strip():
                    List = next_s.split()
                    if rematch(r"^(480p|720p|1080p)(.+)? Links:\Z", next_s):
                        gd_txt += (
                            f'<b>{next_s.replace("Links:", "GDToT Links :")}</b>\n\n'
                        )
                    for s in List:
                        ns = resub(r"\(|\)", "", s)
                        if rematch(r"https?://.+\.gdtot\.\S+", ns):
                            r = rget(ns)
                            soup = BeautifulSoup(r.content, "html.parser")
                            title = soup.select('meta[property^="og:description"]')
                            gd_txt += f"<code>{(title[0]['content']).replace('Download ' , '')}</code>\n{ns}\n\n"
                        elif rematch(r"https?://pastetot\.\S+", ns):
                            nxt = resub(r"\(|\)|(https?://pastetot\.\S+)", "", next_s)
                            gd_txt += f"\n<code>{nxt}</code>\n{ns}\n"
        return gd_txt

    elif "teluguflix" in link:
        gd_txt = ""
        r = rget(link)
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.select('a[href*="gdtot"]')
        gd_txt = f"Total Links Found : {len(links)}\n\n"
        for no, link in enumerate(links, start=1):
            gdlk = link["href"]
            t = rget(gdlk)
            soupt = BeautifulSoup(t.text, "html.parser")
            title = soupt.select('meta[property^="og:description"]')
            gd_txt += f"{no}. <code>{(title[0]['content']).replace('Download ' , '')}</code>\n{gdlk}\n\n"
            asleep(1.5)
        return gd_txt
    elif "cinevood" in link:
        prsd = ""
        links = []
        res = rget(link)
        soup = BeautifulSoup(res.text, "html.parser")
        x = soup.select('a[href^="https://filepress"]')
        for a in x:
            links.append(a["href"])
        for o in links:
            res = rget(o)
            soup = BeautifulSoup(res.content, "html.parser")
            title = soup.title
            prsd += f"{title}\n{o}\n\n"
        return prsd
    elif "atishmkv" in link:
        prsd = ""
        links = []
        res = rget(link)
        soup = BeautifulSoup(res.text, "html.parser")
        x = soup.select('a[href^="https://gdflix"]')
        for a in x:
            links.append(a["href"])
        for o in links:
            prsd += o + "\n\n"
        return prsd
    elif "taemovies" in link:
        gd_txt, no = "", 0
        r = rget(link)
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.select('a[href*="shortingly"]')
        gd_txt = f"Total Links Found : {len(links)}\n\n"
        for a in links:
            glink = rocklinks(a["href"])
            t = rget(glink)
            soupt = BeautifulSoup(t.text, "html.parser")
            title = soupt.select('meta[property^="og:description"]')
            no += 1
            gd_txt += (
                f"{no}. {(title[0]['content']).replace('Download ' , '')}\n{glink}\n\n"
            )
        return gd_txt
    elif "toonworld4all" in link:
        gd_txt, no = "", 0
        client = requests.session()
        r = client.get(link).text
        soup = BeautifulSoup(r, "html.parser")
        for a in soup.find_all("a"):
            c = a.get("href")
            if "redirect/main.php?" in c:
                download = rget(c, stream=True, allow_redirects=False)
                link = download.headers["location"]
                g = rocklinks(link)
                if "gdtot" in g:
                    t = client.get(g).text
                    soupt = BeautifulSoup(t, "html.parser")
                    title = soupt.title
                    no += 1
                    gd_txt += f"{(title.text).replace('GDToT | ' , '')}\n{g}\n\n"
        return gd_txt
    elif "skymovieshd" in link:
        gd_txt = ""
        res = rget(link, allow_redirects=False)
        soup = BeautifulSoup(res.text, "html.parser")
        a = soup.select('a[href^="https://howblogs.xyz"]')
        t = soup.select('div[class^="Robiul"]')
        gd_txt += f"<i>{t[-1].text.replace('Download ', '')}</i>\n\n"
        gd_txt += f"<b>{a[0].text} :</b> \n"
        nres = rget(a[0]["href"], allow_redirects=False)
        nsoup = BeautifulSoup(nres.text, "html.parser")
        atag = nsoup.select('div[class="cotent-box"] > a[href]')
        for no, link in enumerate(atag, start=1):
            gd_txt += f"{no}. {link['href']}\n"
        return gd_txt
    elif "animekaizoku" in link:
        global post_id
        gd_txt = ""
        try:
            website_html = rget(link).text
        except BaseException:
            return "Please provide the correct episode link of animekaizoku"
        try:
            post_id = (
                POST_ID_REGEX.search(website_html).group(0).split(":")[1].split('"')[1]
            )
            payload_data_matches = DDL_REGEX.finditer(website_html)
        except BaseException:
            return "Something Went Wrong !!"

        for match in payload_data_matches:
            payload_data = match.group(0).split("DDL(")[1].replace(")", "").split(",")
            payload = {
                "action": "DDL",
                "post_id": post_id,
                "div_id": payload_data[0].strip(),
                "tab_id": payload_data[1].strip(),
                "num": payload_data[2].strip(),
                "folder": payload_data[3].strip(),
            }
            del payload["num"]
            link_types = (
                "DDL"
                if payload["tab_id"] == "2"
                else "WORKER"
                if payload["tab_id"] == "4"
                else "GDRIVE"
            )
            response = rpost(
                "https://animekaizoku.com/wp-admin/admin-ajax.php",
                headers={
                    "x-requested-with": "XMLHttpRequest",
                    "referer": "https://animekaizoku.com",
                },
                data=payload,
            )
            soup = BeautifulSoup(response.text, "html.parser")
            downloadbutton = soup.find_all(class_="downloadbutton")

            with concurrent.futures.ThreadPoolExecutor() as executor:
                for button in downloadbutton:
                    if button.text == "Patches":
                        pass
                    else:
                        dict_key = button.text.strip()
                        data_dict[dict_key] = []
                        executor.submit(looper, dict_key, str(button))
            main_dict[link_types] = deepcopy(data_dict)
            data_dict.clear()

        for key in main_dict:
            gd_txt += f"----------------- <b>{key}</b> -----------------\n"
            dict_data = main_dict[key]

            if bool(dict_data) == 0:
                gd_txt += "No Links Found\n"
            else:
                for y in dict_data:
                    gd_txt += f"\n○ <b>{y}</b>\n"
                    for no, i in enumerate(dict_data[y], start=1):
                        try:
                            gd_txt += f"➥ {no}. <i>{i[0]}</i> : {i[1]}\n"
                        except BaseException:
                            pass
                    asleep(5)
                gd_txt += "\n"
                return gd_txt
    elif "animeremux" in link:
        gd_txt, no = "", 0
        r = rget(link)
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.select('a[href*="urlshortx.com"]')
        gd_txt = f"Total Links Found : {len(links)}\n\n"
        ptime = 0
        for a in links:
            link = a["href"]
            x = link.split("url=")[-1]
            t = rget(x)
            soupt = BeautifulSoup(t.text, "html.parser")
            title = soupt.title
            no += 1
            gd_txt += f"{no}. {title.text}\n{x}\n\n"
            ptime += 1
            if ptime == 3:
                ptime = 0
                asleep(5)
        return gd_txt
    elif "mkvcinemas" in link:
        start = time()
        try:
            soup = BeautifulSoup(rget(link).content, "html.parser")
            links = []
            for link in soup.find_all("a", class_="gdlink"):
                links.append(link.get("href"))

            for link in soup.find_all("a", class_="button"):
                links.append(link.get("href"))

            melob_links = []
            count = -1
            for l in links:
                count += 1
                id = BeautifulSoup(rget(links[count]).content, "html.parser").find_all(
                    "input"
                )[1]["value"]
                link = f"https://martu.site{id}"
                melob_links.append(link)
        except Exception as err:
            return f"Error: {err}"

        bypassed_links = []
        failed_links = []
        chromedriver_autoinstaller.install()
        for link in melob_links:
            generater = '//*[@id="generater"]'
            showlink = '//*[@id="showlink"]'
            landing = '//*[@id="landing"]/div[2]/center/img'
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-dev-shm-usage")
            wd = webdriver.Chrome(options=chrome_options)
            try:
                wd.get(link)
                sleep(3)
                WebDriverWait(wd, 10).until(
                    ec.element_to_be_clickable((By.XPATH, landing))
                ).click()
                WebDriverWait(wd, 10).until(
                    ec.element_to_be_clickable((By.XPATH, generater))
                ).click()
                WebDriverWait(wd, 10).until(
                    ec.element_to_be_clickable((By.XPATH, showlink))
                ).click()
                wd.current_window_handle
                IItab = wd.window_handles[1]
                wd.switch_to.window(IItab)
                print(f"Bypassed : {wd.current_url}")
                bypassed_links.append(wd.current_url)
            except Exception as err:
                print(f"MKVCinema Melob Error: {err}")
                failed_links.append(link)
        if len(failed_links) == len(melob_links):
            return "Scrapping has failed!"

        bypassed_msg = ""
        for bypsd_link in bypassed_links:
            bypassed_msg += f"{bypsd_link}\n"
        timelog = get_readable_time(time() - start)
        return f"Bypassed Result:\n\n{bypassed_msg}\n\nTime Taken: {timelog}"
