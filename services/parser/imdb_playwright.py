import re
import json
import asyncio
from typing import List, Optional
from urllib.parse import quote
import logging
from playwright.async_api import async_playwright

from .models import MovieSearchResult, MovieDetails

logger = logging.getLogger(__name__)

class IMDBPlaywrightParser:    
    BASE_URL = "https://www.imdb.com"
    SEARCH_URL = f"{BASE_URL}/find?q={{query}}&s=tt"
    
    async def search_movies(self, query: str) -> List[MovieSearchResult]:
        """Поиск фильмов на IMDb через браузер"""
        logger.info(f"🔍 Поиск: {query}")
        
        async with async_playwright() as p:

            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            

            url = self.SEARCH_URL.format(query=quote(query))
            logger.info(f"🌐 Загружаем: {url}")
            
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                

                await page.wait_for_selector('.ipc-metadata-list-summary-item', timeout=5000)
                
                results = []
                

                items = await page.query_selector_all('.ipc-metadata-list-summary-item')
                
                for item in items[:10]:
                    try:
                        
                        link = await item.query_selector('a.ipc-metadata-list-summary-item__t')
                        if not link:
                            link = await item.query_selector('a')
                        
                        if not link:
                            continue
                        
                        href = await link.get_attribute('href')
                        title = await link.text_content()
                        title = title.strip() if title else query
                        

                        movie_id_match = re.search(r'/title/(tt\d+)/', href)
                        if not movie_id_match:
                            continue
                        
                        movie_id = movie_id_match.group(1)
                        
                        
                        year = None
                        year_elem = await item.query_selector('.ipc-metadata-list-summary-item__li')
                        if year_elem:
                            year_text = await year_elem.text_content()
                            year_match = re.search(r'(\d{4})', year_text)
                            year = int(year_match.group(1)) if year_match else None
                        
                        
                        poster = await item.query_selector('img')
                        poster_url = None
                        if poster:
                            poster_url = await poster.get_attribute('src')
                            if not poster_url or 'images' in poster_url:
                                poster_url = await poster.get_attribute('loadlate')
                        
                        logger.info(f"🎬 Найден: {title} ({movie_id})")
                        
                        results.append(MovieSearchResult(
                            source='imdb',
                            source_id=movie_id,
                            title=title,
                            title_original=title,
                            year=year,
                            url=f"https://www.imdb.com/title/{movie_id}/",
                            poster_url=poster_url
                        ))
                        
                    except Exception as e:
                        logger.error(f"Ошибка парсинга элемента: {e}")
                        continue
                
                await browser.close()
                return results
                
            except Exception as e:
                logger.error(f"Ошибка загрузки страницы: {e}")
                await browser.close()
                return []
    
    async def get_movie_details(self, movie_id: str) -> Optional[MovieDetails]:
        url = f"https://www.imdb.com/title/{movie_id}/"
        logger.info(f"🔍 Получение деталей: {url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            try:

                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                

                try:
                    await page.wait_for_selector('h1', timeout=10000)
                except:
                    logger.warning("Не дождались h1, продолжаем...")
                

                json_ld = None
                try:
                    json_ld = await page.evaluate('''
                        () => {
                            const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                            for (const script of scripts) {
                                try {
                                    const data = JSON.parse(script.textContent);
                                    if (data['@type'] === 'Movie') {
                                        return data;
                                    }
                                } catch (e) {}
                            }
                            return null;
                        }
                    ''')
                except Exception as e:
                    logger.warning(f"Не удалось получить JSON-LD: {e}")
                
                if json_ld:
                    
                    title = json_ld.get('name', 'Unknown')
                    original_title = json_ld.get('alternateName', title)
                    
                    
                    year = None
                    date_published = json_ld.get('datePublished')
                    if date_published:
                        year_match = re.search(r'(\d{4})', date_published)
                        year = int(year_match.group(1)) if year_match else None
                    
                   
                    rating = None
                    votes = None
                    if 'aggregateRating' in json_ld:
                        rating = json_ld['aggregateRating'].get('ratingValue')
                        if rating:
                            try:
                                rating = float(rating)
                            except:
                                rating = None
                        votes = json_ld['aggregateRating'].get('ratingCount')
                    
                    
                    description = json_ld.get('description')
                    
                    
                    director = None
                    if 'director' in json_ld:
                        if isinstance(json_ld['director'], list):
                            director = json_ld['director'][0].get('name') if json_ld['director'] else None
                        else:
                            director = json_ld['director'].get('name')
                    
                  
                    genre = None
                    if 'genre' in json_ld:
                        if isinstance(json_ld['genre'], list):
                            genre = json_ld['genre'][0] if json_ld['genre'] else None
                        else:
                            genre = json_ld['genre']
                    
                 
                    poster_url = json_ld.get('image')
                    
                    logger.info(f"Получены данные (JSON-LD): {title} ({year})")
                    
                    await browser.close()
                    
                    return MovieDetails(
                        title=title,
                        title_original=original_title,
                        year=year,
                        genre=genre,
                        country="Unknown",
                        director=director,
                        description=description,
                        poster_url=poster_url,
                        duration=None,
                        imdb_rating=rating,
                        imdb_votes=votes
                    )
                
                
                else:
                    
                    title_elem = await page.query_selector('h1[data-testid="hero__primary-text"]')
                    if not title_elem:
                        title_elem = await page.query_selector('h1')
                    
                    title = await title_elem.text_content() if title_elem else "Unknown"
                    
                    
                    rating_elem = await page.query_selector('[data-testid="hero-rating-bar__aggregate-rating__score"]')
                    rating = None
                    if rating_elem:
                        rating_text = await rating_elem.text_content()
                        try:
                            rating = float(rating_text.split('/')[0])
                        except:
                            pass
                    
                    
                    desc_elem = await page.query_selector('[data-testid="plot-xl"]')
                    description = await desc_elem.text_content() if desc_elem else None
                    
                    
                    year = None
                    year_match = re.search(r'/(\d{4})/', url)
                    if year_match:
                        year = int(year_match.group(1))
                    
                    logger.info(f"Получены данные (HTML): {title}")
                    
                    await browser.close()
                    
                    return MovieDetails(
                        title=title,
                        title_original=title,
                        year=year,
                        genre=None,
                        country="Unknown",
                        director=None,
                        description=description,
                        poster_url=None,
                        duration=None,
                        imdb_rating=rating,
                        imdb_votes=None
                    )
                
            except Exception as e:
                logger.error(f"Ошибка получения деталей для {movie_id}: {e}")
                await browser.close()
                return None