"""
Full Text Scraper
Extracts full text from publisher websites using the links PubMed provides
"""
import requests
from bs4 import BeautifulSoup
import time
from typing import Optional, Dict
import re


class FullTextScraper:
    """
    Scrape full text from publisher websites
    Handles common publishers: Oxford, Springer, Elsevier, PMC, etc.
    """
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        
        # Rate limiting
        self.last_request_time = {}
        self.min_delay = 2  # 2 seconds between requests to same domain
    
    def extract_full_text(self, url: str, provider: str = "") -> Optional[Dict]:
        """
        Extract full text from a publisher URL
        
        Returns:
            Dict with: full_text, tables (if found), success
        """
        # Rate limit by domain
        domain = self._get_domain(url)
        self._rate_limit(domain)
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15, allow_redirects=True)
            
            if response.status_code != 200:
                return None
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try provider-specific extraction
            if "pmc" in url.lower() or "ncbi" in url.lower():
                return self._extract_pmc(soup, url)
            elif "oxford" in url.lower():
                return self._extract_oxford(soup)
            elif "springer" in url.lower():
                return self._extract_springer(soup)
            elif "sciencedirect" in url.lower() or "elsevier" in url.lower():
                return self._extract_elsevier(soup)
            elif "wiley" in url.lower():
                return self._extract_wiley(soup)
            else:
                # Generic extraction
                return self._extract_generic(soup)
        
        except Exception as e:
            print(f"    Failed to scrape {url[:50]}...: {e}")
            return None
    
    def _extract_pmc(self, soup, url: str) -> Optional[Dict]:
        """Extract from PMC (PubMed Central) - most reliable"""
        try:
            # PMC has well-structured HTML
            article = soup.find('div', class_='jig-ncbiinpagenav') or soup.find('article')
            
            if not article:
                return None
            
            # Get full text
            paragraphs = article.find_all(['p', 'div'], class_=['p', 'abstract', 'sec'])
            full_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            # Extract tables
            tables = []
            for table in article.find_all('table'):
                table_text = []
                for row in table.find_all('tr'):
                    cells = [cell.get_text(strip=True) for cell in row.find_all(['th', 'td'])]
                    table_text.append(' | '.join(cells))
                
                tables.append('\n'.join(table_text))
            
            return {
                "full_text": full_text[:50000],  # Limit to 50k chars
                "tables": tables,
                "success": True,
                "source": "PMC"
            }
        except Exception as e:
            return None
    
    def _extract_oxford(self, soup) -> Optional[Dict]:
        """Extract from Oxford Academic"""
        try:
            # Oxford uses specific class names
            article = soup.find('div', class_='widget-ArticleFulltext') or soup.find('section', class_='abstract')
            
            if not article:
                return None
            
            # Get text from sections
            sections = article.find_all(['p', 'div'], class_=['chapter-para', 'abstract'])
            full_text = ' '.join([s.get_text(strip=True) for s in sections])
            
            # Tables
            tables = []
            for table in soup.find_all('table', class_='table'):
                table_text = self._parse_table(table)
                if table_text:
                    tables.append(table_text)
            
            return {
                "full_text": full_text[:50000],
                "tables": tables,
                "success": True,
                "source": "Oxford"
            }
        except:
            return None
    
    def _extract_springer(self, soup) -> Optional[Dict]:
        """Extract from Springer"""
        try:
            article = soup.find('div', class_='c-article-body') or soup.find('article')
            
            if not article:
                return None
            
            paragraphs = article.find_all('p')
            full_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            tables = []
            for table in soup.find_all('table'):
                table_text = self._parse_table(table)
                if table_text:
                    tables.append(table_text)
            
            return {
                "full_text": full_text[:50000],
                "tables": tables,
                "success": True,
                "source": "Springer"
            }
        except:
            return None
    
    def _extract_elsevier(self, soup) -> Optional[Dict]:
        """Extract from Elsevier/ScienceDirect"""
        try:
            # Elsevier often blocks scraping, but try anyway
            article = soup.find('div', id='body') or soup.find('div', class_='Body')
            
            if not article:
                return None
            
            paragraphs = article.find_all('p')
            full_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            return {
                "full_text": full_text[:50000],
                "tables": [],
                "success": True,
                "source": "Elsevier"
            }
        except:
            return None
    
    def _extract_wiley(self, soup) -> Optional[Dict]:
        """Extract from Wiley"""
        try:
            article = soup.find('section', class_='article-section__content') or soup.find('article')
            
            if not article:
                return None
            
            paragraphs = article.find_all('p')
            full_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            tables = []
            for table in soup.find_all('table'):
                table_text = self._parse_table(table)
                if table_text:
                    tables.append(table_text)
            
            return {
                "full_text": full_text[:50000],
                "tables": tables,
                "success": True,
                "source": "Wiley"
            }
        except:
            return None
    
    def _extract_generic(self, soup) -> Optional[Dict]:
        """Generic extraction for unknown publishers"""
        try:
            # Try to find article content
            article = (soup.find('article') or 
                      soup.find('div', class_=re.compile('article|content|body', re.I)) or
                      soup.find('main'))
            
            if not article:
                # Fallback to all paragraphs
                article = soup
            
            paragraphs = article.find_all('p')
            full_text = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50])
            
            if len(full_text) < 500:  # Too short, probably failed
                return None
            
            return {
                "full_text": full_text[:50000],
                "tables": [],
                "success": True,
                "source": "Generic"
            }
        except:
            return None
    
    def _parse_table(self, table) -> str:
        """Parse HTML table to text"""
        try:
            rows = []
            for tr in table.find_all('tr'):
                cells = [cell.get_text(strip=True) for cell in tr.find_all(['th', 'td'])]
                if cells:
                    rows.append(' | '.join(cells))
            return '\n'.join(rows) if rows else None
        except:
            return None
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL for rate limiting"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return "unknown"
    
    def _rate_limit(self, domain: str):
        """Rate limit requests to same domain"""
        if domain in self.last_request_time:
            time_since_last = time.time() - self.last_request_time[domain]
            if time_since_last < self.min_delay:
                time.sleep(self.min_delay - time_since_last)
        
        self.last_request_time[domain] = time.time()


# Singleton instance
_scraper = None

def get_full_text_scraper():
    """Get singleton scraper instance"""
    global _scraper
    if _scraper is None:
        _scraper = FullTextScraper()
    return _scraper
