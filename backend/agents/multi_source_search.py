"""
Multi-Source Literature Search
Searches across multiple academic databases for better coverage
"""
import requests
import time
from typing import List, Dict, Optional
import json


class MultiSourceSearch:
    """
    Search multiple academic sources:
    1. PubMed (primary)
    2. Semantic Scholar (free API, good coverage)
    3. CrossRef (DOI lookup, full metadata)
    4. Europe PMC (alternative to PubMed)
    5. bioRxiv/medRxiv (preprints)
    """
    
    def __init__(self):
        # Semantic Scholar - free academic search
        self.semantic_scholar_base = "https://api.semanticscholar.org/graph/v1/"
        
        # CrossRef - DOI metadata
        self.crossref_base = "https://api.crossref.org/"
        
        # Europe PMC - alternative to PubMed
        self.europepmc_base = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
        
        # bioRxiv/medRxiv - preprints
        self.biorxiv_base = "https://api.biorxiv.org/"
        
        self.headers = {
            "User-Agent": "PrecisionPharma/1.0 (mailto:research@example.com)"
        }
    
    def search_all_sources(self, drug: str, indication: str, max_per_source: int = 10) -> List[Dict]:
        """
        Search all available sources and combine results
        
        Returns:
            Combined list of papers from all sources
        """
        all_papers = []
        
        print(f"🔍 Searching multiple sources for {drug}...")
        
        # 1. Semantic Scholar (best free alternative)
        try:
            ss_papers = self.search_semantic_scholar(drug, indication, max_per_source)
            all_papers.extend(ss_papers)
            print(f"  ✓ Semantic Scholar: {len(ss_papers)} papers")
        except Exception as e:
            print(f"  ✗ Semantic Scholar failed: {e}")
        
        time.sleep(1)  # Rate limit
        
        # 2. Europe PMC (alternative to PubMed)
        try:
            epmc_papers = self.search_europe_pmc(drug, indication, max_per_source)
            all_papers.extend(epmc_papers)
            print(f"  ✓ Europe PMC: {len(epmc_papers)} papers")
        except Exception as e:
            print(f"  ✗ Europe PMC failed: {e}")
        
        time.sleep(1)
        
        # 3. bioRxiv/medRxiv (preprints - latest research)
        try:
            preprint_papers = self.search_preprints(drug, indication, max_per_source)
            all_papers.extend(preprint_papers)
            print(f"  ✓ Preprints: {len(preprint_papers)} papers")
        except Exception as e:
            print(f"  ✗ Preprints failed: {e}")
        
        # Deduplicate by title
        seen_titles = set()
        unique_papers = []
        for paper in all_papers:
            title_key = paper.get("title", "").lower()[:50]
            if title_key and title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_papers.append(paper)
        
        print(f"  → Total unique papers: {len(unique_papers)}")
        return unique_papers
    
    def search_semantic_scholar(self, drug: str, indication: str, max_results: int = 10) -> List[Dict]:
        """
        Search Semantic Scholar - free API with good coverage
        
        API: https://api.semanticscholar.org/
        """
        papers = []
        
        # Build query
        query = f"{drug} {indication} efficacy pharmacogenetics"
        
        # Search
        search_url = f"{self.semantic_scholar_base}paper/search"
        params = {
            "query": query,
            "fields": "title,abstract,authors,year,citationCount,openAccessPdf,externalIds",
            "limit": max_results
        }
        
        response = requests.get(search_url, params=params, headers=self.headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            for item in data.get("data", []):
                # Extract identifiers
                ext_ids = item.get("externalIds", {})
                pmid = ext_ids.get("PubMed")
                doi = ext_ids.get("DOI")
                
                paper = {
                    "pmid": pmid if pmid else f"SS_{item.get('paperId', '')}",
                    "title": item.get("title", ""),
                    "abstract": item.get("abstract", ""),
                    "authors": [a.get("name", "") for a in item.get("authors", [])],
                    "year": str(item.get("year", "")),
                    "journal": "Semantic Scholar",
                    "doi": doi,
                    "citation_count": item.get("citationCount", 0),
                    "open_access_pdf": item.get("openAccessPdf", {}).get("url") if item.get("openAccessPdf") else None,
                    "source": "semantic_scholar"
                }
                
                papers.append(paper)
        
        return papers
    
    def search_europe_pmc(self, drug: str, indication: str, max_results: int = 10) -> List[Dict]:
        """
        Search Europe PMC - similar to PubMed but European database
        
        API: https://europepmc.org/RestfulWebService
        """
        papers = []
        
        # Build query
        query = f"{drug} AND {indication} AND (efficacy OR pharmacogenetic)"
        
        search_url = f"{self.europepmc_base}search"
        params = {
            "query": query,
            "resultType": "core",
            "pageSize": max_results,
            "format": "json"
        }
        
        response = requests.get(search_url, params=params, headers=self.headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            for item in data.get("resultList", {}).get("result", []):
                paper = {
                    "pmid": item.get("pmid", item.get("id", "")),
                    "title": item.get("title", ""),
                    "abstract": item.get("abstractText", ""),
                    "authors": [item.get("authorString", "")],  # Europe PMC provides combined author string
                    "year": item.get("pubYear", ""),
                    "journal": item.get("journalTitle", ""),
                    "doi": item.get("doi"),
                    "is_open_access": item.get("isOpenAccess") == "Y",
                    "full_text_url": item.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("url") if item.get("fullTextUrlList") else None,
                    "source": "europe_pmc"
                }
                
                papers.append(paper)
        
        return papers
    
    def search_preprints(self, drug: str, indication: str, max_results: int = 10) -> List[Dict]:
        """
        Search bioRxiv/medRxiv for preprints
        Latest research that hasn't been published yet
        
        Note: biorxiv API is limited, using simple search
        """
        papers = []
        
        # bioRxiv search
        # Note: Their API is limited, this is a simplified version
        # In production, you'd want to use their proper search endpoint
        
        search_query = f"{drug}+{indication}".replace(" ", "+")
        
        # For now, return empty as bioRxiv API requires more complex setup
        # You can manually add preprints or use their web scraping approach
        
        return papers
    
    def enrich_with_full_text(self, paper: Dict) -> Dict:
        """
        Try to get full text for a paper
        """
        # Check if we have open access PDF
        if paper.get("open_access_pdf"):
            paper["full_text_available"] = True
            paper["full_text_url"] = paper["open_access_pdf"]
        
        # Check if we have DOI and can resolve it
        elif paper.get("doi"):
            # Use Unpaywall API (free) to check for open access
            try:
                unpaywall_url = f"https://api.unpaywall.org/v2/{paper['doi']}"
                params = {"email": "research@example.com"}  # Required by Unpaywall
                
                response = requests.get(unpaywall_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("is_oa"):  # is open access
                        best_oa = data.get("best_oa_location", {})
                        if best_oa.get("url_for_pdf"):
                            paper["full_text_available"] = True
                            paper["full_text_url"] = best_oa["url_for_pdf"]
            except Exception as e:
                print(f"    Failed to check Unpaywall: {e}")
        
        return paper
    
    def get_google_scholar_results(self, drug: str, indication: str, max_results: int = 10) -> List[Dict]:
        """
        Google Scholar search (via SerpAPI or ScraperAPI)
        
        Note: This requires a paid API key for reliable access
        SerpAPI: https://serpapi.com/ (~$50/month)
        ScraperAPI: https://www.scraperapi.com/
        
        For production use, sign up and add API key
        """
        # Placeholder - requires API key
        print("  ℹ️  Google Scholar search requires API key (SerpAPI or ScraperAPI)")
        return []


def improve_extraction_with_context(abstract: str, title: str) -> Dict:
    """
    Improved extraction with better patterns and context understanding
    """
    improved_patterns = {
        # More flexible response rate patterns
        "response": [
            r'(\d+(?:\.\d+)?)\s*%.*?(?:response|efficacy|responded)',
            r'(?:response|efficacy).*?(\d+(?:\.\d+)?)\s*%',
            r'(\d+)\/(\d+).*?responded',  # Fraction: 50/100 responded
            r'(\d+)\s+of\s+(\d+).*?response',  # 50 of 100 showed response
        ],
        
        # Treatment failure / non-response
        "failure": [
            r'(\d+(?:\.\d+)?)\s*%.*?(?:failure|non-response|did not respond)',
            r'(?:failure|non-response).*?(\d+(?:\.\d+)?)\s*%',
            r'(\d+)\/(\d+).*?(?:failed|did not respond)',
        ],
        
        # Sample size with more patterns
        "sample": [
            r'n\s*=\s*(\d+)',
            r'(\d+)\s+patients?',
            r'(\d+)\s+subjects?',
            r'cohort\s+of\s+(\d+)',
            r'study\s+(?:of|with)\s+(\d+)',
        ]
    }
    
    # TODO: Implement improved extraction
    # This is a template for enhancing the existing extractor
    
    return {}
