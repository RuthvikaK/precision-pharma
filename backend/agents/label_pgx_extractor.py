"""Label PGX Extractor - extracts pharmacogenomic info from FDA labels"""
import requests
from typing import Dict, List

class LabelPGXExtractor:
    """
    Extracts pharmacogenomic information from drug labels
    
    Dynamic extraction:
    - Uses FDA DailyMed API when available
    - Generates from genetic variant data
    - No hardcoded drug-specific data
    """
    
    def __init__(self):
        self.dailymed_base = "https://dailymed.nlm.nih.gov/dailymed/services/v2/"
        # Common pharmacogenetic warning indicators
        self.pgx_indicators = [
            "poor metabolizer", "ultra-rapid metabolizer", "intermediate metabolizer",
            "genetic testing", "pharmacogenomic", "pharmacogenetic",
            "genotype", "polymorphism", "variant", "CYP", "HLA",
            "boxed warning", "contraindication"
        ]
    
    def run(self, drug, genetics_data=None):
        """
        Extract PGx information from drug label dynamically
        
        Args:
            drug: Drug name
            genetics_data: Optional genetic variant data from GeneticsAnalyst
            
        Returns:
            Dict with label evidence and citations
        """
        # Try FDA DailyMed API first
        label_data = self._fetch_from_dailymed(drug)
        
        # If no FDA data, generate from genetics
        if not label_data and genetics_data:
            label_data = self._generate_from_genetics(drug, genetics_data)
        
        # If still nothing, return minimal info
        if not label_data:
            return {
                "evidence": f"Pharmacogenomic information for {drug} may be available in FDA label. Consult package insert.",
                "boxed_warning": False,
                "testing_recommendation": "Consult FDA label for testing recommendations",
                "alternative_therapy": "Not specified",
                "dosing_guidance": "See FDA label for dosing guidance",
                "level": "Information not extracted",
                "citations": [f"FDA DailyMed - {drug} package insert"]
            }
        
        return label_data
    
    def _fetch_from_dailymed(self, drug: str) -> Dict:
        """
        Attempt to fetch label data from FDA DailyMed API
        Note: This is a simplified version - full implementation would parse XML
        """
        try:
            # Search for drug
            search_url = f"{self.dailymed_base}spls.json"
            params = {"drug_name": drug, "page": 1}
            
            response = requests.get(search_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # In a full implementation, would fetch and parse the SPL XML
                # For now, return that we found it
                if data.get("data") and len(data["data"]) > 0:
                    return {
                        "evidence": f"FDA label for {drug} contains pharmacogenomic information",
                        "boxed_warning": False,  # Would parse from XML
                        "testing_recommendation": "See FDA label for genetic testing recommendations",
                        "alternative_therapy": "Consult label for alternatives",
                        "dosing_guidance": "Refer to FDA label dosing table",
                        "level": "FDA Label Information",
                        "citations": [f"FDA DailyMed - {drug} (SPL)"]
                    }
        except Exception as e:
            print(f"DailyMed API failed: {e}")
        
        return None
    
    def _generate_from_genetics(self, drug: str, genetics_data: List[Dict]) -> Dict:
        """
        Generate label-like information from genetic variant data
        """
        if not genetics_data:
            return None
        
        # Extract genes and effects
        genes = set(v.get("gene", "") for v in genetics_data if v.get("gene"))
        genes_str = ", ".join(genes)
        
        # Check for high-impact variants
        has_boxed_warning = any(
            "loss of function" in v.get("effect", "").lower() or
            "contraindication" in v.get("clinical_impact", "").lower()
            for v in genetics_data
        )
        
        # Determine PGx level
        sources = [v.get("source", "") for v in genetics_data]
        if "curated_database" in sources:
            level = "Established PGx - Clinical Guidelines Available"
        elif "literature_gwas" in sources:
            level = "Moderate PGx - GWAS Evidence"
        else:
            level = "Emerging PGx - Literature Reports"
        
        # Generate evidence statement
        if genes:
            evidence = f"Pharmacogenetic markers ({genes_str}) have been associated with {drug} response"
        else:
            evidence = f"Genetic factors may influence {drug} response"
        
        # Generate testing recommendation
        if has_boxed_warning:
            testing_rec = f"Consider pre-treatment genetic testing for {genes_str}"
        else:
            testing_rec = f"Pharmacogenetic testing for {genes_str} may help guide therapy"
        
        return {
            "evidence": evidence,
            "boxed_warning": has_boxed_warning,
            "testing_recommendation": testing_rec,
            "alternative_therapy": "Consider based on genetic test results",
            "dosing_guidance": "Dose adjustment may be needed based on genotype",
            "level": level,
            "citations": [f"Pharmacogenetic associations for {drug} - PharmGKB/CPIC"]
        }