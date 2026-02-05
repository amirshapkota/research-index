"""
NepJOL Scraper Service
Scrapes publication data from https://nepjol.info/
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import time
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class NepJOLScraper:
    """
    Service to scrape publications from Nepal Journals Online (NepJOL)
    """
    
    BASE_URL = "https://nepjol.info"
    
    def __init__(self, delay: float = 1.0):
        """
        Initialize scraper with rate limiting
        
        Args:
            delay: Delay between requests in seconds (default: 1.0)
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        """
        Make HTTP request with rate limiting and error handling
        """
        try:
            time.sleep(self.delay)  # Rate limiting
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def get_all_journals(self) -> List[Dict]:
        """
        Get list of all journals from NepJOL homepage
        
        Returns:
            List of journal dictionaries with name and URL
        """
        journals = []
        soup = self._make_request(self.BASE_URL)
        
        if not soup:
            return journals
        
        # Find all h3 tags (each contains a journal)
        h3_tags = soup.find_all('h3')
        
        for h3 in h3_tags:
            # Each h3 contains an <a> tag with journal name and URL
            title_link = h3.find('a')
            if title_link and title_link.get('href'):
                href = title_link.get('href', '')
                # Filter out non-journal links (like homepage link)
                if 'index.php' in href and '/index.php/index' not in href:
                    journal_url = urljoin(self.BASE_URL, href)
                    journal_name = title_link.text.strip()
                    
                    # Extract short name from URL (e.g., 'ajmr' from '/index.php/ajmr')
                    short_name = href.split('/')[-1] if '/' in href else ''
                    
                    journals.append({
                        'name': journal_name,
                        'url': journal_url,
                        'short_name': short_name
                    })
                
        logger.info(f"Found {len(journals)} journals")
        return journals
    
    def get_journal_details(self, journal_url: str) -> Optional[Dict]:
        """
        Get journal metadata including description, ISSN, and other details
        
        Args:
            journal_url: URL of the journal page
            
        Returns:
            Dictionary with journal details or None
        """
        soup = self._make_request(journal_url)
        
        if not soup:
            return None
        
        details = {'url': journal_url}
        
        # Journal description/about section
        description = ''
        about_section = soup.find('div', class_='description')
        if not about_section:
            about_section = soup.find('div', class_='journal_description')
        if not about_section:
            about_section = soup.find('section', class_='about')
        
        if about_section:
            description = about_section.get_text(separator=' ', strip=True)
        
        # Try meta description as fallback
        if not description:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '')
        
        details['description'] = description
        
        # ISSN
        issn = ''
        issn_tag = soup.find(text=lambda x: x and 'ISSN' in str(x))
        if issn_tag:
            # Extract ISSN number from text like "ISSN: 1234-5678"
            import re
            match = re.search(r'ISSN[:\s]+([0-9]{4}-[0-9]{3}[0-9X])', issn_tag)
            if match:
                issn = match.group(1)
        details['issn'] = issn
        
        # Cover image
        cover_image_url = None
        imgs = soup.find_all('img', src=lambda x: x and ('homepageImage' in str(x) or 'cover' in str(x).lower()))
        if imgs:
            img_src = imgs[0].get('src', '')
            if img_src:
                cover_image_url = urljoin(self.BASE_URL, img_src)
        details['cover_image_url'] = cover_image_url
        
        return details
    
    def get_journal_cover_image(self, journal_url: str) -> Optional[str]:
        """
        Get journal cover image URL
        
        Args:
            journal_url: URL of the journal page
            
        Returns:
            Cover image URL or None
        """
        soup = self._make_request(journal_url)
        
        if not soup:
            return None
        
        # Look for cover images (homepage image or issue cover)
        imgs = soup.find_all('img', src=lambda x: x and ('homepageImage' in str(x) or 'cover' in str(x).lower()))
        
        if imgs:
            img_src = imgs[0].get('src', '')
            if img_src:
                return urljoin(self.BASE_URL, img_src)
        
        return None
    
    def get_journal_issues(self, journal_url: str) -> List[Dict]:
        """
        Get all issues for a specific journal
        
        Args:
            journal_url: URL of the journal page
            
        Returns:
            List of issue dictionaries with volume/issue numbers parsed
        """
        issues = []
        soup = self._make_request(journal_url)
        
        if not soup:
            return issues
        
        import re
        
        # Method 1: Look for obj_issue_toc divs (current and past issues)
        issue_divs = soup.find_all('div', class_='obj_issue_toc')
        
        for issue_div in issue_divs:
            # Find issue link
            issue_link = issue_div.find('a', href=lambda x: x and '/issue/view/' in x)
            if not issue_link:
                continue
                
            issue_url = urljoin(self.BASE_URL, issue_link.get('href', ''))
            
            # Try to get title from image alt text or parent section
            issue_title = ''
            
            # Check image alt text (format: "View Vol. 1 (2025)")
            img = issue_link.find('img')
            if img and img.get('alt'):
                alt_text = img.get('alt', '').strip()
                # Extract from "View Vol. 1 (2025)"
                if 'Vol' in alt_text:
                    issue_title = alt_text.replace('View', '').strip()
            
            # Check parent section for current_issue_title
            if not issue_title:
                parent_section = issue_div.find_parent('section', class_='current_issue')
                if parent_section:
                    title_div = parent_section.find('div', class_='current_issue_title')
                    if title_div:
                        issue_title = title_div.get_text(strip=True)
            
            # Parse volume and issue number from title
            volume = None
            issue_number = None
            year = None
            
            # Try to extract volume (e.g., "Vol. 1" or "Volume 1")
            vol_match = re.search(r'Vol\.?\s*(\d+)', issue_title, re.IGNORECASE)
            if vol_match:
                volume = int(vol_match.group(1))
            
            # Try to extract issue number (e.g., "No. 1" or "Issue 1")
            issue_match = re.search(r'(?:No\.?|Issue)\s*(\d+)', issue_title, re.IGNORECASE)
            if issue_match:
                issue_number = int(issue_match.group(1))
            
            # Try to extract year (e.g., "(2025)")
            year_match = re.search(r'\((\d{4})\)', issue_title)
            if year_match:
                year = int(year_match.group(1))
            
            # Get published date from the issue div
            pub_date = None
            published_span = issue_div.find('span', class_='value')
            if published_span:
                pub_date = published_span.get_text(strip=True)
            
            issues.append({
                'title': issue_title if issue_title else 'Issue',
                'url': issue_url,
                'volume': volume,
                'issue_number': issue_number,
                'year': year,
                'published_date': pub_date
            })
        
        # Method 2: If no issues found, look for direct issue links in archive
        if not issues:
            issue_links = soup.find_all('a', href=lambda x: x and '/issue/view/' in x)
            
            for link in issue_links:
                issue_url = urljoin(self.BASE_URL, link.get('href', ''))
                issue_title = link.text.strip()
                
                # Parse volume and issue number from title
                volume = None
                issue_number = None
                
                vol_match = re.search(r'Vol\.?\s*(\d+)', issue_title, re.IGNORECASE)
                if vol_match:
                    volume = int(vol_match.group(1))
                
                issue_match = re.search(r'(?:No\.?|Issue)\s*(\d+)', issue_title, re.IGNORECASE)
                if issue_match:
                    issue_number = int(issue_match.group(1))
                
                issues.append({
                    'title': issue_title,
                    'url': issue_url,
                    'volume': volume,
                    'issue_number': issue_number,
                    'year': None,
                    'published_date': None
                })
        
        return issues
    
    def get_articles_from_issue(self, issue_url: str) -> List[Dict]:
        """
        Get all articles from a specific issue
        
        Args:
            issue_url: URL of the issue page
            
        Returns:
            List of article dictionaries
        """
        articles = []
        soup = self._make_request(issue_url)
        
        if not soup:
            return articles
        
        # Find all article entries (class="obj_article_summary")
        article_sections = soup.find_all('div', class_='obj_article_summary')
        
        for section in article_sections:
            article_data = self._parse_article_summary(section)
            if article_data:
                articles.append(article_data)
        
        logger.info(f"Found {len(articles)} articles in issue")
        return articles
    
    def _parse_article_summary(self, article_section) -> Optional[Dict]:
        """
        Parse article summary from issue page
        
        Args:
            article_section: BeautifulSoup tag containing article info
            
        Returns:
            Dictionary with article metadata or None
        """
        try:
            # Title and URL (h3.title > a)
            title_tag = article_section.find('h3', class_='title')
            if not title_tag or not title_tag.find('a'):
                return None
            
            title_link = title_tag.find('a')
            title = title_link.text.strip()
            article_url = urljoin(self.BASE_URL, title_link.get('href', ''))
            
            # Authors (div.authors inside div.meta)
            authors_text = ''
            authors_tag = article_section.find('div', class_='authors')
            if authors_tag:
                authors_text = authors_tag.text.strip()
            
            # Pages (div.pages inside div.meta)
            pages = ''
            pages_tag = article_section.find('div', class_='pages')
            if pages_tag:
                pages = pages_tag.text.strip()
            
            # DOI - may not be on summary page
            doi = ''
            doi_tag = article_section.find('a', class_='doi')
            if doi_tag:
                doi_href = doi_tag.get('href', '')
                # Extract DOI from URL like https://doi.org/10.xxxx
                if 'doi.org/' in doi_href:
                    doi = doi_href.split('doi.org/')[-1]
            
            # PDF URL (a.obj_galley_link.pdf inside ul.galleys_links)
            pdf_url = ''
            pdf_link = article_section.find('a', class_='obj_galley_link')
            if pdf_link and 'pdf' in pdf_link.get('class', []):
                pdf_url = urljoin(self.BASE_URL, pdf_link.get('href', ''))
            
            return {
                'title': title,
                'url': article_url,
                'authors': authors_text,
                'pages': pages,
                'doi': doi,
                'pdf_url': pdf_url
            }
        except Exception as e:
            logger.error(f"Error parsing article: {str(e)}")
            return None
    
    def get_article_details(self, article_url: str) -> Optional[Dict]:
        """
        Get full details of a specific article using meta tags
        
        Args:
            article_url: URL of the article page
            
        Returns:
            Dictionary with complete article metadata
        """
        soup = self._make_request(article_url)
        
        if not soup:
            return None
        
        try:
            article_data = {'url': article_url}
            
            # Helper function to get meta tag content
            def get_meta(name):
                meta = soup.find('meta', attrs={'name': name})
                return meta.get('content', '') if meta else ''
            
            # Title from meta tag or h1
            title = get_meta('citation_title')
            if not title:
                title_tag = soup.find('h1')
                title = title_tag.text.strip() if title_tag else ''
            article_data['title'] = title
            
            # Authors with affiliations and ORCID from meta tags and page content
            authors = []
            author_metas = soup.find_all('meta', attrs={'name': 'citation_author'})
            institution_metas = soup.find_all('meta', attrs={'name': 'citation_author_institution'})
            
            # Extract ORCID IDs from links on the page
            orcid_links = soup.find_all('a', href=lambda x: x and 'orcid.org' in str(x))
            orcid_ids = []
            for link in orcid_links:
                href = link.get('href', '')
                # Extract ORCID from URL like https://orcid.org/0000-0001-2345-6789
                if 'orcid.org/' in href:
                    orcid_id = href.split('orcid.org/')[-1].strip('/')
                    orcid_ids.append(orcid_id)
            
            for i, author_meta in enumerate(author_metas):
                author_name = author_meta.get('content', '')
                affiliation = ''
                if i < len(institution_metas):
                    affiliation = institution_metas[i].get('content', '')
                
                orcid = ''
                if i < len(orcid_ids):
                    orcid = orcid_ids[i]
                
                authors.append({
                    'name': author_name,
                    'affiliation': affiliation,
                    'orcid': orcid
                })
            article_data['authors'] = authors
            
            # Abstract from section.item.abstract
            abstract = ''
            abstract_section = soup.find('section', class_='item abstract')
            if abstract_section:
                # Remove heading
                heading = abstract_section.find('h2')
                if heading:
                    heading.extract()
                abstract = abstract_section.get_text(strip=True)
            article_data['abstract'] = abstract
            
            # Keywords from meta tags
            keywords = []
            keyword_metas = soup.find_all('meta', attrs={'name': 'citation_keywords'})
            for kw_meta in keyword_metas:
                keyword = kw_meta.get('content', '').strip()
                if keyword:
                    keywords.append(keyword)
            article_data['keywords'] = keywords
            
            # Volume from meta tag
            article_data['volume'] = get_meta('citation_volume')
            
            # Issue from meta tag
            article_data['issue'] = get_meta('citation_issue')
            
            # Year from citation_date (format: YYYY/MM/DD)
            pub_date = get_meta('citation_date')
            if pub_date:
                article_data['year'] = pub_date.split('/')[0]
            else:
                article_data['year'] = ''
            
            # Pages from firstpage and lastpage
            first_page = get_meta('citation_firstpage')
            last_page = get_meta('citation_lastpage')
            if first_page and last_page:
                article_data['pages'] = f"{first_page}-{last_page}"
            elif first_page:
                article_data['pages'] = first_page
            else:
                article_data['pages'] = ''
            
            # DOI from meta tag
            doi = get_meta('citation_doi')
            article_data['doi'] = doi
            
            # PDF URL from meta tag
            pdf_url = get_meta('citation_pdf_url')
            article_data['pdf_url'] = pdf_url
            
            # References - try to find from page content
            references = []
            # Try different selectors for references
            ref_section = soup.find('section', class_='item references')
            if not ref_section:
                ref_section = soup.find('div', class_='references')
            if not ref_section:
                ref_section = soup.find('ol', class_='references')
            
            if ref_section:
                ref_items = ref_section.find_all('li')
                for ref in ref_items:
                    ref_text = ref.get_text(strip=True)
                    if ref_text:
                        references.append(ref_text)
            
            article_data['references'] = references
            
            return article_data
            
        except Exception as e:
            logger.error(f"Error parsing article details from {article_url}: {str(e)}")
            return None
    
    def scrape_journal_complete(self, journal_url: str, max_issues: Optional[int] = None) -> List[Dict]:
        """
        Scrape all articles from a journal
        
        Args:
            journal_url: URL of the journal
            max_issues: Maximum number of issues to scrape (None for all)
            
        Returns:
            List of all articles from the journal
        """
        logger.info(f"Starting to scrape journal: {journal_url}")
        all_articles = []
        
        # Get all issues
        issues = self.get_journal_issues(journal_url)
        logger.info(f"Found {len(issues)} issues")
        
        if max_issues:
            issues = issues[:max_issues]
        
        # Scrape each issue
        for i, issue in enumerate(issues, 1):
            logger.info(f"Scraping issue {i}/{len(issues)}: {issue['title']}")
            articles = self.get_articles_from_issue(issue['url'])
            
            # Get full details for each article
            for article in articles:
                full_details = self.get_article_details(article['url'])
                if full_details:
                    all_articles.append({**article, **full_details})
            
            logger.info(f"Scraped {len(articles)} articles from issue")
        
        logger.info(f"Total articles scraped: {len(all_articles)}")
        return all_articles
    
    def search_articles(self, query: str, max_results: int = 100) -> List[Dict]:
        """
        Search for articles across NepJOL
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of matching articles
        """
        search_url = f"{self.BASE_URL}/index.php/index/search"
        params = {'query': query}
        
        try:
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse search results
            articles = []
            result_items = soup.find_all('div', class_='result')[:max_results]
            
            for item in result_items:
                article_data = self._parse_article_summary(item)
                if article_data:
                    articles.append(article_data)
            
            return articles
            
        except Exception as e:
            logger.error(f"Error searching for '{query}': {str(e)}")
            return []
