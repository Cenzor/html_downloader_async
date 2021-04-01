import argparse
import asyncio
import csv
from typing import List, Tuple
from .logger_config import configure_logger


logger = configure_logger(__name__)
# информация о url сайта, используемом прокси и причине возникновении ошибки.
bad_urls = 'bad_urls.log'


def get_args() -> Tuple[str, str, int, str, int]:
    """
    Функция парсит аргументы командной строки при запуске скрипта.
    Возвращает кортеж с переданными опциями (опциями по умолчанию).
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", dest="csv_file", action="store",
                        type=str, help="File name with sites. Default file"
                        " name 'sites.csv'", default="sites.csv")
    parser.add_argument("-d", "--dest", dest="dest_folder", action="store",
                        type=str, help="Destination folder. Default destina"
                        "tion folder is 'downloaded'",
                        default="downloaded")
    parser.add_argument("-s", "--poolsize", dest="poolsize", action="store",
                        type=int, help="Limiting connection pool size. "
                        " Default value is 100. If you explicitly want "
                        "not to have limits, pass 0.",
                        default=100)
    parser.add_argument("-p", "--proxy", dest="proxy_file", action="store",
                        type=str, help="File name with proxies. Default file"
                        " name 'proxies.txt'", default="proxies.txt")
    parser.add_argument("-t", "--timeout", dest="timeout", action="store",
                        type=int, help="Maximal number of seconds for reading "
                        "a portion of data from a peer", default=15)
    args = parser.parse_args()
    csv_file = args.csv_file
    dest_folder = args.dest_folder
    poolsize = args.poolsize
    proxy_file = args.proxy_file
    timeout = args.timeout
    logger.info(f'Initial params: csv_file={csv_file}, '
                f'dest_folder={dest_folder}, poolsize={poolsize}, '
                f'proxy_file={proxy_file}, timeout={timeout}.')
    return (csv_file, dest_folder, poolsize, proxy_file, timeout)


def get_sites(csv_file: str) -> List[str]:
    """
    Функция формирует список url из указанного файла.
    """
    urls: List[str] = []
    with open(csv_file, 'r') as f_in:
        reader = csv.DictReader(f_in, fieldnames=['site'], delimiter=';')
        for line in reader:
            if line['site'].startswith('#'):
                continue
            if line['site'].startswith(('http://', 'https://')):
                urls.append(line['site'].strip())
            else:
                urls.append('http://' + line['site'].strip())
    logger.info(f'Count of urls: {len(urls)}')
    return urls


def get_proxies(proxy_file: str) -> asyncio.Queue:
    """
    Функция формирует и возвращает очередь прокси
    """
    proxy_queue = asyncio.Queue()
    with open(proxy_file, 'r') as f_in:
        for line in f_in:
            proxy_queue.put_nowait(line.strip())
    return proxy_queue
