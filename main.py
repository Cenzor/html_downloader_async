from datetime import datetime
from pathlib import Path
from typing import List
from lib.html_downloader import HtmlDownloader
from lib.logger_config import configure_logger
from lib.tools import get_args, get_sites, bad_urls, get_proxies


logger = configure_logger(__name__)


if __name__ == '__main__':
    st: datetime = datetime.now()
    if Path(bad_urls).is_file():
        Path(bad_urls).unlink()
    csv_file, dest_folder, poolsize, proxy_file, timeout = get_args()
    Path(dest_folder).mkdir(parents=True, exist_ok=True)
    urls: List[str] = get_sites(csv_file)
    proxies_queue = get_proxies(proxy_file)
    html_downloader = HtmlDownloader(urls, dest_folder, poolsize, timeout,
                                     proxies_queue)
    html_downloader.run()
    logger.debug(f'Elapsed time: {datetime.now() - st}')
