from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class BaseParser(ABC):
    """Базовый класс для всех парсеров"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers=self.default_headers,
            timeout=self.timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def search_movies(self, query: str) -> List:
        """Поиск фильмов по названию"""
        pass
    
    @abstractmethod
    async def get_movie_details(self, source_id: str) -> Optional[Any]:
        """Получение детальной информации о фильме"""
        pass
    
    async def fetch_html(self, url: str, custom_headers: Dict = None) -> Optional[str]:
        """Получение HTML страницы с повторными попытками"""
        max_retries = 3
        headers = custom_headers or self.default_headers
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Fetching {url} (attempt {attempt + 1})")
                async with self.session.get(url, headers=headers) as response:
                    logger.debug(f"Response status: {response.status}")
                    
                    if response.status == 200:
                        html = await response.text()
                        logger.debug(f"Successfully fetched {url} ({len(html)} bytes)")
                        return html
                    elif response.status == 202:
                        logger.warning(f"HTTP 202 - страница еще обрабатывается, ждем...")
                        await asyncio.sleep(2)
                        continue
                    elif response.status == 429:  # Too Many Requests
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited. Waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout for {url}, attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                return None
                
        return None
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Парсинг HTML в BeautifulSoup объект"""
        return BeautifulSoup(html, 'lxml')