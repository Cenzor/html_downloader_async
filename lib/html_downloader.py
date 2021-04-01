# -*- coding: utf-8 -*-
import asyncio
import aiohttp
import os
import re
import string
from aiohttp import ClientSession
from aiohttp.client_exceptions import (
    ClientConnectionError, ClientPayloadError, TooManyRedirects
)
from asyncio.exceptions import TimeoutError
from datetime import datetime
from pathlib import Path
from typing import List
from urllib.parse import urlparse

import html2text
import tqdm

from lib.logger_config import configure_logger
from lib.tools import bad_urls


logger = configure_logger(__name__)


class HtmlDownloader:
    """
    Класс выполняет запросы к сайтам и скачивает первую страницу сайта.
    """

    def __init__(self, urls: List[str], dest_folder: str, poolsize: int,
                 timeout: int, proxy_queue):
        """
        Конструктор. Инициализация переменных, старт времени начала работы.
        """
        self.start_time = datetime.now()
        self.urls: List[str] = urls
        self.dest_folder: str = dest_folder
        self.poolsize: int = poolsize
        self.timeout = timeout
        self.proxy_queue = proxy_queue

    def run(self):
        """
        Точка входа: организует и запускает цикл событий
        """
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(
            self.fetch_all()
        )
        loop.run_until_complete(
            asyncio.wait(
                [future]
            )
        )

    async def fetch_all(self):
        """
        Функция создаёт список задач и запускает их
        """
        tasks = []
        timeout = aiohttp.ClientTimeout(total=None, sock_read=self.timeout)
        conn = aiohttp.TCPConnector(limit=self.poolsize)
        async with ClientSession(connector=conn, timeout=timeout) as session:
            for url in self.urls:
                task = asyncio.ensure_future(
                    self.fetch(url, session)
                )
                tasks.append(task)
            _ = await asyncio.gather(*tasks, self.tq(len(tasks)))

    async def fetch(self, url: str, session):
        """
        Метод выполняет get-запрос к сайту и сохраняет ответ в файл,
        если запрос вернул ошибку - в файл логируется/записывается
        ссылка и причина
        """
        try:
            proxy = await self.proxy_queue.get()
            proxy_url = 'http://' + proxy
            async with session.get(url, proxy=proxy_url) as response:
                try:
                    text = await response.text()
                except UnicodeDecodeError:
                    reason = "The content of the site is not text data"
                    await self.save_bad_url(url, reason, proxy)
                    return
                except ClientPayloadError:
                    reason = "Invalid compression or Malformed chunked " \
                        "encoding or Not enough data that satisfy " \
                        "Content-Length HTTP header."
                    await self.save_bad_url(url, reason, proxy)
                    return
                if int(response.status) in range(400, 600):
                    reason = 'HTTP_STATUS_CODE'
                    await self.save_bad_url(url, reason, proxy,
                                            response.status)
                    return
                await self.save_to_file(text, url, proxy)
        except ClientConnectionError:
            reason = "Cannot connect to host"
            await self.save_bad_url(url, reason, proxy)
        except TooManyRedirects:
            reason = "Too many redirects"
            await self.save_bad_url(url, reason, proxy)
        except TimeoutError:
            reason = "Timeout error"
            await self.save_bad_url(url, reason, proxy)
        except ValueError:
            reason = "URL should be absolute"
            await self.save_bad_url(url, reason, proxy)
        except Exception:
            reason = "Unhandled exception"
            await self.save_bad_url(url, reason, proxy)
        finally:
            await self.proxy_queue.put(proxy)

    async def save_to_file(self, page_source: str, url: str, proxy: str):
        """
        Метод сохраняет исходный код страницы и текст страницы
        """
        path = os.path.join(self.dest_folder, urlparse(url).netloc)
        Path(path).mkdir(parents=True, exist_ok=True)
        filename = url.replace('http://', '').replace('https://', '')
        filename = re.sub('/', '.', filename)
        path = os.path.join(path, filename)
        page_text = await self.get_page_text(page_source)
        with open(path+'.html', 'w') as f_html, \
             open(path+'.txt', 'w') as f_txt:
            f_html.write(page_source)
            f_txt.write(page_text)
        logger.debug(f'{filename} saved successfully. Proxy {proxy}')

    async def get_page_text(self, page_source: str) -> str:
        """
        Метод очищает исходный текст страницы от html-содержимого
        """
        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        text = h.handle(page_source)
        printable = set(string.printable +
                        'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
                        'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
        clean_text = ''.join(filter(lambda x: x in printable, text))
        clean_text = re.sub('[\r\t\n]', '', clean_text)
        clean_text = re.sub(' +', ' ', clean_text)
        return clean_text

    async def save_bad_url(self, url: str, reason: str, proxy: str, code=None):
        """
        Метод сохраняет в файл ссылку на сайт и причину,
        по которой не удалось сохранить содержимое сайта
        """
        with open(bad_urls, 'a') as f_out:
            if code:
                entry = f'{url} {reason}:{code}. Proxy: {proxy}'
            else:
                entry = f'{url} {reason}. Proxy: {proxy}'
            logger.error(entry)
            f_out.write(entry + '\n')

    async def tq(self, tasks_length):
        """
        Метод реализует статус-бар
        """
        for _ in tqdm.tqdm(range(tasks_length)):
            await asyncio.sleep(0.1)
