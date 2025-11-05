"""Literature Mining Agent - searches PubMed for clinical studies"""
import requests
from typing import List, Dict
from .biomedical_extractor import BiomedicalExtractor
from .pmc_extractor import PMCExtractor
from .multi_source_search import MultiSourceSearch
from .better_full_text import get_better_full_text

class LiteratureMinerAgent:
    """Mines literature for drug efficacy data from PubMed and other sources"""
    
    def __init__(self, use_biobert=True, use_pmc=True, use_multi_source=True):
        self.pubmed_base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.use_biobert = use_biobert
        self.use_pmc = use_pmc
        self.use_multi_source = use_multi_source
        
        # Initialize multi-source search
        self.multi_search = MultiSourceSearch() if use_multi_source else None
        
        # Initialize better full text access (APIs instead of scraping)
        self.better_full_text = get_better_full_text()
        
        # Initialize biomedical extractor (lazy loaded)
        self.extractor = None
        if use_biobert:
            try:
                self.extractor = BiomedicalExtractor(use_model=True)
            except Exception as e:
                print(f"⚠️  bioBERT initialization failed: {e}")
                self.extractor = BiomedicalExtractor(use_model=False)  # Regex-only fallback
        
        # Initialize PMC extractor
        self.pmc_extractor = None
        if use_pmc:
            try:
                self.pmc_extractor = PMCExtractor()
                print("✅ PMC full-text extractor initialized")
            except Exception as e:
                print(f"⚠️  PMC extractor initialization failed: {e}")
        
    def run(self, drug, indication, use_gpu=True):
        """
        Search for literature on drug efficacy and non-response
        Returns structured data with studies and citations
        """
        studies = self._search_pubmed(drug, indication)
        gwas_data = self._get_gwas_mock(drug)
        label_data = self._get_label_mock(drug)
        
        return {
            "studies": studies,
            "gwas": gwas_data,
            "label": label_data,
            "citations": self._generate_citations(studies)
        }
    
    def _search_pubmed(self, drug, indication):
        """Search PubMed AND alternative sources for comprehensive coverage"""
        all_found_studies = []
        
        try:
            # STEP 1: Search PubMed using multiple search strategies
            queries = [
                # Primary: Drug + indication + efficacy terms
                f"{drug} AND {indication} AND (efficacy OR response OR treatment outcome)",
                # Secondary: Drug + pharmacogenetics
                f"{drug} AND (pharmacogenetic OR genetic variant OR polymorphism)",
                # Tertiary: Drug + non-response
                f"{drug} AND (non-responder OR treatment failure OR resistance)"
            ]
            
            all_pmids = set()
            search_url = f"{self.pubmed_base}esearch.fcgi"
            
            # Try each search strategy
            for query in queries:
                params = {
                    "db": "pubmed",
                    "term": query,
                    "retmax": 20,  # Increased from 10 to 20
                    "retmode": "json",
                    "sort": "relevance"  # Get most relevant first
                }
                
                try:
                    response = requests.get(search_url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        pmids = data.get("esearchresult", {}).get("idlist", [])
                        all_pmids.update(pmids[:10])  # Take top 10 from each query
                        if len(all_pmids) >= 15:  # Stop if we have enough
                            break
                except Exception as e:
                    print(f"Search query failed: {e}")
                    continue
            
            pmids = list(all_pmids)[:15]  # Limit to 15 total studies
            print(f"  ✓ PubMed: Found {len(pmids)} papers")
            
            # Fetch details for found PMIDs
            pubmed_studies = self._fetch_study_details(pmids) if pmids else []
            all_found_studies.extend(pubmed_studies)
            
            # STEP 2: Search alternative sources IN PARALLEL (not just fallback!)
            if self.multi_search:
                print(f"🌐 Searching alternative sources (Semantic Scholar, Europe PMC, bioRxiv)...")
                try:
                    alt_studies = self.multi_search.search_all_sources(drug, indication, max_per_source=10)
                    if alt_studies:
                        print(f"  ✓ Alternative sources: Found {len(alt_studies)} additional papers")
                        all_found_studies.extend(alt_studies)
                except Exception as e:
                    print(f"  ⚠️ Alternative sources failed: {e}")
            
            # Deduplicate by PMID/title
            seen = set()
            unique_studies = []
            for study in all_found_studies:
                key = study.get("pmid", "") or study.get("title", "")[:50].lower()
                if key and key not in seen:
                    seen.add(key)
                    unique_studies.append(study)
            
            print(f"  → Total unique papers: {len(unique_studies)}")
            
            if not unique_studies:
                return []
            
            # STEP 3: Check PMC availability and enrich with full text
            if self.pmc_extractor:
                pmids_with_pmc = [s.get("pmid") for s in unique_studies if s.get("pmid")]
                if pmids_with_pmc:
                    print(f"📚 Checking PMC for full-text access...")
                    pmc_mapping = self.pmc_extractor.check_pmc_availability(pmids_with_pmc)
                    
                    if pmc_mapping:
                        print(f"  ✓ {len(pmc_mapping)} studies available in PMC with full text")
                        
                        # Enrich studies with PMC full text
                        for study in unique_studies:
                            if study.get("pmid") in pmc_mapping:
                                self.pmc_extractor.enrich_study_with_pmc(study)
            
            # STEP 3.5: Try better full text access methods (Europe PMC, bioRxiv, Unpaywall)
            if self.better_full_text:
                print(f"📚 Trying alternative full text sources (Europe PMC, bioRxiv, Unpaywall)...")
                full_text_count = 0
                
                for study in unique_studies:
                    # Skip if already have full text
                    if study.get("pmc_available") or study.get("full_text"):
                        continue
                    
                    pmid = study.get("pmid", "")
                    
                    # Try Europe PMC first (better than US PMC)
                    if pmid and pmid.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')):
                        europe_pmc_data = self.better_full_text.get_full_text_europepmc(pmid)
                        if europe_pmc_data and europe_pmc_data.get("success"):
                            study["full_text"] = europe_pmc_data["full_text"]
                            study["tables_text"] = europe_pmc_data.get("tables", [])
                            study["full_text_source"] = "Europe PMC"
                            study["full_text_available"] = True
                            full_text_count += 1
                            continue
                    
                    # Try Unpaywall if we have DOI
                    doi = study.get("doi")
                    if doi:
                        unpaywall_url = self.better_full_text.get_unpaywall_link(doi)
                        if unpaywall_url:
                            study["full_text_url"] = unpaywall_url
                            study["full_text_source"] = "Unpaywall"
                            # Note: Would need to download and parse PDF for actual text
                            # For now, mark as having link
                            study["has_oa_link"] = True
                
                # Also search bioRxiv for additional preprints
                biorxiv_papers = self.better_full_text.get_biorxiv_full_text(drug, limit=5)
                if biorxiv_papers:
                    print(f"  ✓ Found {len(biorxiv_papers)} bioRxiv preprints")
                    # Add to studies if not duplicates
                    for paper in biorxiv_papers:
                        if not any(paper.get("title", "").lower() in s.get("title", "").lower() for s in unique_studies):
                            unique_studies.append(paper)
                
                if full_text_count > 0:
                    print(f"  ✓ Got full text from {full_text_count} papers via Europe PMC")
            
            # STEP 4: Use bioBERT to extract from all studies
            if self.extractor and unique_studies:
                print(f"🔬 Extracting efficacy data using bioBERT...")
                enriched_studies = []
                
                for study in unique_studies:
                    # Prefer full text if available (from PMC OR scraped)
                    has_full_text = (study.get("pmc_available") or study.get("full_text_available")) and study.get("full_text")
                    
                    if has_full_text:
                        # Extract from full text
                        full_text_data = self.extractor.extract_from_abstract(
                            study["full_text"],
                            study.get("title", "")
                        )
                        
                        # Also check table data
                        if study.get("table_efficacy"):
                            # Use table data (most reliable)
                            for table_data in study["table_efficacy"]:
                                if table_data.get("values"):
                                    # Take first percentage as response rate
                                    study["response_rate"] = table_data["values"][0] / 100.0
                                    study["extraction_method"] = "pmc_table"
                                    break
                        
                        # Check tables text from Europe PMC
                        if study.get("tables_text"):
                            # Try to extract from tables
                            for table_text in study["tables_text"]:
                                if "%" in table_text or "response" in table_text.lower():
                                    table_extract = self.extractor.extract_from_abstract(table_text, "")
                                    if table_extract.get("response_rate"):
                                        study["response_rate"] = table_extract["response_rate"]
                                        study["extraction_method"] = "europe_pmc_table"
                                        break
                        
                        # Merge full text extraction
                        if not study.get("response_rate"):
                            if full_text_data.get("response_rate"):
                                study["response_rate"] = full_text_data["response_rate"]
                            if full_text_data.get("non_response_rate"):
                                study["non_response_rate"] = full_text_data["non_response_rate"]
                            if full_text_data.get("sample_size"):
                                study["sample_size"] = full_text_data["sample_size"]
                            
                            # Mark extraction method
                            if study.get("pmc_available"):
                                study["extraction_method"] = "pmc_fulltext"
                            elif study.get("full_text_available"):
                                study["extraction_method"] = "scraped_fulltext"
                    else:
                        # Extract from abstract only
                        self.extractor.enrich_study(study)
                    
                    # Fallback: If still no extraction, try simpler patterns
                    if not study.get("response_rate") and not study.get("non_response_rate"):
                        text_to_search = study.get("full_text", "") or study.get("abstract", "")
                        if text_to_search:
                            simple_extract = self.better_full_text.extract_efficacy_from_text(text_to_search)
                            if simple_extract.get("response_rate"):
                                study["response_rate"] = simple_extract["response_rate"]
                                study["extraction_method"] = "simple_regex"
                            if simple_extract.get("non_response_rate"):
                                study["non_response_rate"] = simple_extract["non_response_rate"]
                            if simple_extract.get("sample_size"):
                                study["sample_size"] = simple_extract["sample_size"]
                    
                    enriched_studies.append(study)
                
                # Count successful extractions
                extracted_count = sum(1 for s in enriched_studies if s.get("response_rate") is not None or s.get("non_response_rate") is not None)
                pmc_count = sum(1 for s in enriched_studies if s.get("pmc_available"))
                europe_pmc_count = sum(1 for s in enriched_studies if s.get("full_text_source") == "Europe PMC")
                table_count = sum(1 for s in enriched_studies if s.get("extraction_method") in ["pmc_table", "europe_pmc_table"])
                simple_count = sum(1 for s in enriched_studies if s.get("extraction_method") == "simple_regex")
                
                print(f"  ✓ PMC full text: {pmc_count} studies")
                print(f"  ✓ Europe PMC full text: {europe_pmc_count} studies")
                print(f"  ✓ Table extraction: {table_count} studies")
                print(f"  ✓ Simple extraction: {simple_count} studies")
                print(f"  ✓ Total efficacy data extracted: {extracted_count}/{len(enriched_studies)} studies")
                
                # Return all studies (with or without extracted data)
                return enriched_studies
            
            # No extraction possible - return studies without metrics
            print("⚠️  No efficacy data extracted - returning studies without metrics")
            return unique_studies
        except Exception as e:
            print(f"PubMed search failed: {e}, using mock data")
            return self._get_mock_studies(drug, indication)
    
    def _fetch_study_details(self, pmids):
        """Fetch detailed information for PubMed IDs including full text links"""
        if not pmids:
            return []
        
        try:
            fetch_url = f"{self.pubmed_base}esummary.fcgi"
            params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "json"
            }
            
            response = requests.get(fetch_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                studies = []
                
                for pmid in pmids:
                    if pmid in data.get("result", {}):
                        article = data["result"][pmid]
                        study = {
                            "pmid": pmid,
                            "title": article.get("title", ""),
                            "authors": article.get("authors", []),
                            "journal": article.get("source", ""),
                            "year": article.get("pubdate", "").split()[0],
                            "abstract": article.get("abstract", "")
                        }
                        
                        # Fetch full text links from PubMed
                        full_text_links = self._get_full_text_links(pmid)
                        if full_text_links:
                            study["full_text_links"] = full_text_links
                            study["has_full_text_link"] = True
                        
                        studies.append(study)
                
                return studies
        except Exception as e:
            print(f"Failed to fetch study details: {e}")
            return []
    
    def _get_full_text_links(self, pmid):
        """
        Get full text links from PubMed using ELink API
        These are the links shown in "Full Text Links" section on PubMed
        """
        try:
            elink_url = f"{self.pubmed_base}elink.fcgi"
            params = {
                "dbfrom": "pubmed",
                "id": pmid,
                "cmd": "prlinks",  # Get provider links (full text)
                "retmode": "json"
            }
            
            response = requests.get(elink_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                links = []
                linksets = data.get("linksets", [])
                
                for linkset in linksets:
                    # Check for idurllist (provider URLs)
                    idurllist = linkset.get("idurllist", [])
                    for item in idurllist:
                        objurls = item.get("objurls", [])
                        for url_obj in objurls:
                            url = url_obj.get("url", {}).get("value", "")
                            provider = url_obj.get("provider", {}).get("name", "")
                            
                            if url:
                                links.append({
                                    "url": url,
                                    "provider": provider,
                                    "type": "full_text"
                                })
                
                return links if links else None
        except Exception as e:
            # Silent fail - not critical
            return None
    
    def _get_mock_studies(self, drug, indication):
        """
        Return empty study list - we only use real PubMed/PMC data
        No hardcoded mock data
        """
        print(f"⚠️  No studies extracted for {drug}. Consider:")
        print(f"    - Checking PubMed directly for {drug} pharmacogenetics")
        print(f"    - Verifying drug name spelling")
        return []
    
    def _get_gwas_mock(self, drug):
        """
        Return empty GWAS data - should be extracted from literature
        In a full implementation, this would query GWAS Catalog API
        """
        return {
            "variants": [],
            "genes": [],
            "associations": f"GWAS data for {drug} should be extracted from literature or GWAS Catalog"
        }
    
    def _get_label_mock(self, drug):
        """
        Return minimal label data - actual extraction done by LabelPGXExtractor
        No hardcoded data
        """
        return {
            "pharmacogenomics": f"See LabelPGXExtractor for {drug} pharmacogenomic information",
            "boxed_warning": False
        }
    
    def _generate_citations(self, studies):
        """
        Generate citation strings from studies
        Returns dict with two lists:
        - studies_with_data: Citations for studies with extractable efficacy data
        - additional_references: Citations for studies without extractable data
        """
        studies_with_data = []
        additional_references = []
        
        for study in studies:
            authors = study.get("authors", [])
            
            # Extract first author name (handle both string and dict formats)
            first_author = "Unknown"
            if authors:
                if isinstance(authors, list) and len(authors) > 0:
                    author_obj = authors[0]
                    # Handle dict format from PubMed API
                    if isinstance(author_obj, dict):
                        first_author = author_obj.get("name", author_obj.get("authname", "Unknown"))
                    else:
                        first_author = str(author_obj)
                elif isinstance(authors, str):
                    first_author = authors
            
            # Format citation
            journal = study.get("journal", "Unknown Journal")
            year = study.get("year", "")
            pmid = study.get("pmid", "")
            
            # Check if study has extractable data
            has_data = study.get("response_rate") is not None or study.get("non_response_rate") is not None
            
            # Build citation with data info if available
            citation = f"{first_author} et al. {journal} {year}. PMID:{pmid}"
            
            if has_data:
                # Add response rate info to citation
                if study.get("response_rate"):
                    rate_pct = study["response_rate"] * 100
                    citation += f" - Response rate: {rate_pct:.1f}%"
                elif study.get("non_response_rate"):
                    rate_pct = (1 - study["non_response_rate"]) * 100
                    citation += f" - Response rate: {rate_pct:.1f}%"
                studies_with_data.append(citation)
            else:
                additional_references.append(citation)
        
        return {
            "studies_with_data": studies_with_data,
            "additional_references": additional_references,
            "all_citations": studies_with_data + additional_references  # For backwards compatibility
        }
    
    def get(self, key, default=None):
        """Dict-like access for backwards compatibility"""
        return getattr(self, key, default)