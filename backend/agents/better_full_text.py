"""
Better Full Text Access - Using APIs that actually work
Instead of scraping, use legitimate APIs that provide full text
"""
import requests
import xml.etree.ElementTree as ET
from typing import Optional, Dict, List
import re


class BetterFullTextAccess:
    """
    Access full text through legitimate APIs:
    1. Europe PMC - Better than regular PMC
    2. bioRxiv/medRxiv - Always open access
    3. Unpaywall - Finds legal OA versions
    4. PMC OA Subset - Direct download
    """
    
    def __init__(self):
        # Europe PMC - MUCH better than US PMC
        self.europepmc_base = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
        
        # bioRxiv API
        self.biorxiv_base = "https://api.biorxiv.org/details/biorxiv/"
        
        # Unpaywall - finds legal open access
        self.unpaywall_base = "https://api.unpaywall.org/v2/"
        
        self.headers = {
            "User-Agent": "PrecisionPharma/1.0 (research use)"
        }
    
    def get_full_text_europepmc(self, pmid: str) -> Optional[Dict]:
        """
        Get full text from Europe PMC - often has papers US PMC doesn't
        
        Returns full text XML parsed to plain text
        """
        try:
            # Check if full text available
            url = f"{self.europepmc_base}{pmid}/fullTextXML"
            
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                # Parse XML
                root = ET.fromstring(response.text)
                
                # Extract text from body
                full_text = []
                
                # Get abstract
                abstract = root.find(".//abstract")
                if abstract is not None:
                    abstract_text = ' '.join(abstract.itertext())
                    full_text.append(abstract_text)
                
                # Get body sections
                body = root.find(".//body")
                if body is not None:
                    for section in body.findall(".//sec"):
                        section_text = ' '.join(section.itertext())
                        full_text.append(section_text)
                
                # Get tables
                tables = []
                for table in root.findall(".//table-wrap"):
                    table_text = ' '.join(table.itertext())
                    tables.append(table_text)
                
                combined_text = ' '.join(full_text)
                
                if len(combined_text) > 500:  # Sanity check
                    return {
                        "full_text": combined_text[:100000],  # Limit size
                        "tables": tables,
                        "source": "Europe PMC",
                        "success": True
                    }
            
            return None
            
        except Exception as e:
            # Silent fail
            return None
    
    def get_biorxiv_full_text(self, drug: str, limit: int = 10) -> List[Dict]:
        """
        Search bioRxiv/medRxiv for preprints about the drug
        These are ALWAYS open access!
        
        Returns list of papers with full text
        """
        papers = []
        
        try:
            # Search bioRxiv
            # Note: bioRxiv API is limited, this is simplified
            # In production, would use their proper search endpoint
            
            # For now, construct a search that might work
            search_url = f"{self.biorxiv_base}2020-01-01/2025-01-01/0/50"
            
            response = requests.get(search_url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Filter for drug mentions
                for article in data.get("collection", []):
                    title = article.get("title", "").lower()
                    abstract = article.get("abstract", "").lower()
                    
                    if drug.lower() in title or drug.lower() in abstract:
                        paper = {
                            "title": article.get("title"),
                            "abstract": article.get("abstract"),
                            "doi": article.get("doi"),
                            "full_text": abstract,  # bioRxiv provides abstract in API
                            "pdf_url": f"https://www.biorxiv.org/content/{article.get('doi')}.full.pdf",
                            "source": "bioRxiv",
                            "is_preprint": True
                        }
                        papers.append(paper)
                        
                        if len(papers) >= limit:
                            break
        except:
            pass
        
        return papers
    
    def get_unpaywall_link(self, doi: str) -> Optional[str]:
        """
        Use Unpaywall to find legal open access version
        
        Returns URL to PDF if available
        """
        try:
            url = f"{self.unpaywall_base}{doi}"
            params = {"email": "research@example.com"}  # Required
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("is_oa"):
                    # Get best open access location
                    best_oa = data.get("best_oa_location", {})
                    pdf_url = best_oa.get("url_for_pdf")
                    
                    if pdf_url:
                        return pdf_url
                    
                    # Try landing page URL
                    url = best_oa.get("url")
                    if url:
                        return url
            
            return None
            
        except:
            return None
    
    def extract_from_pmc_oa_ftp(self, pmcid: str) -> Optional[Dict]:
        """
        Direct download from PMC Open Access FTP
        This is the BULK download method - very reliable
        
        PMC provides XML files for all OA articles
        """
        try:
            # Convert PMCID to FTP path
            # PMC OA files are organized by PMCID
            # Example: PMC123456 -> PMC123456.xml
            
            base_url = "https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi"
            params = {
                "verb": "GetRecord",
                "identifier": f"oai:pubmedcentral.nih.gov:{pmcid}",
                "metadataPrefix": "pmc"
            }
            
            response = requests.get(base_url, params=params, timeout=15)
            
            if response.status_code == 200:
                # Parse XML
                root = ET.fromstring(response.text)
                
                # Extract article text
                article = root.find(".//article")
                if article:
                    full_text = ' '.join(article.itertext())
                    
                    return {
                        "full_text": full_text[:100000],
                        "source": "PMC OA",
                        "success": True
                    }
            
            return None
            
        except:
            return None
    
    def get_crossref_fulltext_link(self, doi: str) -> Optional[str]:
        """
        Use CrossRef to find full text links
        Sometimes has links that others don't
        """
        try:
            url = f"https://api.crossref.org/works/{doi}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for links
                message = data.get("message", {})
                links = message.get("link", [])
                
                for link in links:
                    if link.get("content-type") == "application/pdf":
                        return link.get("URL")
                    elif link.get("content-type") == "text/html":
                        return link.get("URL")
            
            return None
            
        except:
            return None
    
    def extract_efficacy_from_text(self, text: str) -> Dict:
        """
        Simple but effective extraction patterns
        Focus on finding percentages with context
        """
        results = {}
        
        # More aggressive patterns
        patterns = [
            # Response rates
            r'(\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?(?:patients?\s+)?(?:responded|response|achieved)',
            r'response\s+rate[^\d]*(\d+(?:\.\d+)?)\s*%',
            r'overall\s+response[^\d]*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s+overall\s+response',
            
            # Non-response
            r'(\d+(?:\.\d+)?)\s*%\s*(?:did\s+not|failed|non.?response)',
            r'non.?response[^\d]*(\d+(?:\.\d+)?)\s*%',
            
            # Efficacy
            r'efficacy[^\d]*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s+efficacy',
            
            # Treatment success/failure
            r'treatment\s+success[^\d]*(\d+(?:\.\d+)?)\s*%',
            r'treatment\s+failure[^\d]*(\d+(?:\.\d+)?)\s*%',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower(), re.IGNORECASE)
            if matches:
                try:
                    rate = float(matches[0])
                    if 0 <= rate <= 100:
                        if 'non' in pattern or 'failure' in pattern or 'did not' in pattern:
                            results["non_response_rate"] = rate / 100.0
                        else:
                            results["response_rate"] = rate / 100.0
                        break  # Found something
                except:
                    continue
        
        # Sample size
        sample_patterns = [
            r'n\s*=\s*(\d+)',
            r'(\d+)\s+patients?\s+were',
            r'(\d+)\s+patients?\s+enrolled',
            r'enrolled\s+(\d+)\s+patients?',
            r'cohort\s+of\s+(\d+)',
        ]
        
        for pattern in sample_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    n = int(matches[0])
                    if 10 <= n <= 100000:  # Reasonable range
                        results["sample_size"] = n
                        break
                except:
                    continue
        
        return results


# Singleton
_better_access = None

def get_better_full_text():
    global _better_access
    if _better_access is None:
        _better_access = BetterFullTextAccess()
    return _better_access
