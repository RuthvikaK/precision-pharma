"""
PubMed Central (PMC) Full-Text Extractor
Accesses open-access papers for complete data including tables and figures
"""
import requests
import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Optional


class PMCExtractor:
    """Extracts full text, tables, and figures from PubMed Central open-access articles"""
    
    def __init__(self):
        self.pmc_idconv_base = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
        self.pmc_oai_base = "https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi"
        
    def check_pmc_availability(self, pmids: List[str]) -> Dict[str, str]:
        """
        Check which PMIDs are available in PMC
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            Dict mapping PMID -> PMC ID (only for available papers)
        """
        if not pmids:
            return {}
        
        try:
            # PMC ID converter API
            params = {
                "ids": ",".join(pmids),
                "format": "json",
                "idtype": "pmid"
            }
            
            response = requests.get(
                self.pmc_idconv_base,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                return {}
            
            data = response.json()
            pmc_mapping = {}
            
            # Parse response
            if "records" in data:
                for record in data["records"]:
                    pmid = record.get("pmid")
                    pmcid = record.get("pmcid")
                    
                    # Only include if full text is available
                    if pmid and pmcid and record.get("live") == "true":
                        pmc_mapping[pmid] = pmcid
            
            return pmc_mapping
            
        except Exception as e:
            print(f"⚠️  PMC availability check failed: {e}")
            return {}
    
    def fetch_full_text(self, pmcid: str) -> Optional[Dict]:
        """
        Fetch full text XML from PMC
        
        Args:
            pmcid: PMC ID (e.g., "PMC1234567")
            
        Returns:
            Dict with full_text, tables, figures
        """
        try:
            # PMC OAI-PMH endpoint
            params = {
                "verb": "GetRecord",
                "identifier": f"oai:pubmedcentral.nih.gov:{pmcid}",
                "metadataPrefix": "pmc"
            }
            
            response = requests.get(
                self.pmc_oai_base,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                return None
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Extract components
            full_text = self._extract_text_content(root)
            tables = self._extract_tables(root)
            figures = self._extract_figures(root)
            
            return {
                "pmcid": pmcid,
                "full_text": full_text,
                "tables": tables,
                "figures": figures,
                "source": "PMC"
            }
            
        except Exception as e:
            print(f"⚠️  PMC full text fetch failed for {pmcid}: {e}")
            return None
    
    def _extract_text_content(self, root: ET.Element) -> str:
        """Extract all text content from XML"""
        text_parts = []
        
        # Find article body
        namespaces = {'pmc': 'http://dtd.nlm.nih.gov/2.0/xsd/archivearticle'}
        
        # Try different XML structures
        body = root.find('.//body', namespaces) or root.find('.//body')
        
        if body is not None:
            # Get all text, preserving structure
            for elem in body.iter():
                if elem.text:
                    text_parts.append(elem.text.strip())
                if elem.tail:
                    text_parts.append(elem.tail.strip())
        
        # Fallback: get all text from root
        if not text_parts:
            text_parts = [elem.text.strip() for elem in root.iter() if elem.text and elem.text.strip()]
        
        return " ".join(text_parts)
    
    def _extract_tables(self, root: ET.Element) -> List[Dict]:
        """
        Extract tables from PMC XML
        Tables often contain the key efficacy data!
        """
        tables = []
        
        # Find all table-wrap elements
        for table_wrap in root.findall('.//table-wrap'):
            table_data = {
                "caption": "",
                "rows": [],
                "raw_text": ""
            }
            
            # Get table caption
            caption = table_wrap.find('.//caption')
            if caption is not None:
                table_data["caption"] = self._get_element_text(caption)
            
            # Get table content
            table_elem = table_wrap.find('.//table')
            if table_elem is not None:
                # Extract rows
                for row in table_elem.findall('.//tr'):
                    row_data = []
                    for cell in row.findall('.//*'):
                        if cell.tag in ['td', 'th']:
                            cell_text = self._get_element_text(cell)
                            row_data.append(cell_text)
                    if row_data:
                        table_data["rows"].append(row_data)
                
                # Get raw text representation
                table_data["raw_text"] = self._get_element_text(table_elem)
            
            tables.append(table_data)
        
        return tables
    
    def _extract_figures(self, root: ET.Element) -> List[Dict]:
        """Extract figure legends/captions"""
        figures = []
        
        for fig in root.findall('.//fig'):
            fig_data = {
                "caption": "",
                "label": ""
            }
            
            # Get figure label (e.g., "Figure 1")
            label = fig.find('.//label')
            if label is not None:
                fig_data["label"] = self._get_element_text(label)
            
            # Get caption
            caption = fig.find('.//caption')
            if caption is not None:
                fig_data["caption"] = self._get_element_text(caption)
            
            figures.append(fig_data)
        
        return figures
    
    def _get_element_text(self, element: ET.Element) -> str:
        """Get all text from an XML element"""
        text_parts = []
        if element.text:
            text_parts.append(element.text.strip())
        for child in element:
            text_parts.append(self._get_element_text(child))
            if child.tail:
                text_parts.append(child.tail.strip())
        return " ".join(part for part in text_parts if part)
    
    def extract_efficacy_from_tables(self, tables: List[Dict]) -> List[Dict]:
        """
        Extract efficacy data from table content
        This is where the gold is! Response rates are usually in tables.
        """
        efficacy_data = []
        
        for table in tables:
            caption = table.get("caption", "").lower()
            raw_text = table.get("raw_text", "")
            
            # Skip tables that don't look like results
            if not any(keyword in caption for keyword in 
                      ["response", "efficacy", "outcome", "result", "baseline"]):
                continue
            
            # Look for response rates in table text
            response_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*%', re.IGNORECASE)
            matches = response_pattern.findall(raw_text)
            
            if matches:
                # Parse table rows for structured data
                for row in table.get("rows", []):
                    row_text = " ".join(row)
                    
                    # Look for response rates
                    if any(keyword in row_text.lower() for keyword in 
                          ["response", "responder", "success", "remission"]):
                        
                        # Extract percentages from this row
                        percentages = response_pattern.findall(row_text)
                        
                        if percentages:
                            efficacy_data.append({
                                "source": "table",
                                "caption": caption,
                                "row": row_text,
                                "values": [float(p) for p in percentages],
                                "table_index": tables.index(table)
                            })
        
        return efficacy_data
    
    def enrich_study_with_pmc(self, study: Dict) -> Dict:
        """
        Enrich a study with PMC full text data
        
        Args:
            study: Study dict with pmid
            
        Returns:
            Enhanced study with full_text, tables, extracted_data
        """
        pmid = study.get("pmid")
        if not pmid:
            return study
        
        # Check PMC availability
        pmc_mapping = self.check_pmc_availability([pmid])
        
        if pmid not in pmc_mapping:
            study["pmc_available"] = False
            return study
        
        pmcid = pmc_mapping[pmid]
        print(f"  📄 Fetching full text from PMC: {pmcid}")
        
        # Fetch full text
        pmc_data = self.fetch_full_text(pmcid)
        
        if not pmc_data:
            study["pmc_available"] = False
            return study
        
        # Add PMC data to study
        study["pmc_available"] = True
        study["pmcid"] = pmcid
        study["full_text"] = pmc_data["full_text"]
        study["tables"] = pmc_data["tables"]
        study["figures"] = pmc_data["figures"]
        
        # Extract efficacy from tables
        table_efficacy = self.extract_efficacy_from_tables(pmc_data["tables"])
        if table_efficacy:
            study["table_efficacy"] = table_efficacy
            print(f"  ✓ Extracted efficacy data from {len(table_efficacy)} tables")
        
        return study


# Singleton instance
_pmc_extractor = None

def get_pmc_extractor() -> PMCExtractor:
    """Get or create PMC extractor instance"""
    global _pmc_extractor
    if _pmc_extractor is None:
        _pmc_extractor = PMCExtractor()
    return _pmc_extractor
