"""Web page scraper for document ingestion."""
from typing import List, Optional
from langchain_community.document_loaders import WebBaseLoader
from langchain.schema import Document
from bs4 import BeautifulSoup
import requests
from utils.logger import get_logger
from utils.error_handlers import DocumentProcessingError

logger = get_logger(__name__)


class WebScraper:
    """Scrape web pages for document ingestion."""
    
    def __init__(self, headers: Optional[dict] = None):
        """
        Initialize web scraper.
        
        Args:
            headers: Custom HTTP headers
        """
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        logger.info("Initialized web scraper")
    
    def scrape_url(self, url: str) -> Document:
        """
        Scrape single URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            Document object
        """
        try:
            logger.info(f"Scraping URL: {url}")
            
            loader = WebBaseLoader(url)
            documents = loader.load()
            
            if documents:
                doc = documents[0]
                doc.metadata.update({
                    'source': url,
                    'type': 'web'
                })
                logger.info(f"Successfully scraped {url}")
                return doc
            else:
                raise DocumentProcessingError(f"No content extracted from {url}")
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            raise DocumentProcessingError(f"Failed to scrape URL: {e}")
    
    def scrape_urls(self, urls: List[str]) -> List[Document]:
        """Scrape multiple URLs."""
        documents = []
        
        for url in urls:
            try:
                doc = self.scrape_url(url)
                documents.append(doc)
            except Exception as e:
                logger.error(f"Skipping {url}: {e}")
                continue
        
        logger.info(f"Scraped {len(documents)}/{len(urls)} URLs")
        return documents
    
    def extract_links(self, url: str) -> List[str]:
        """Extract all links from a page."""
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http'):
                    links.append(href)
            
            logger.info(f"Extracted {len(links)} links from {url}")
            return links
            
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []