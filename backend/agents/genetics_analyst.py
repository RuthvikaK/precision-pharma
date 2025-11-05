"""Genetics Analyst Agent - maps variants to PK/PD mechanisms"""
from typing import Dict, List, Optional
import re

class GeneticsAnalyst:
    """
    Analyzes genetic variants and their pharmacological impact
    
    Features:
    - Extracts variants from literature (GWAS, studies)
    - Maps variants to PK/PD pathways
    - Integrates dynamic + curated data
    - Provides mechanistic explanations
    """
    
    def __init__(self):
        # Database of known pharmacogenetic variants
        self.variant_db = {
            "CYP2C19": {
                "gene": "CYP2C19",
                "function": "Drug metabolism enzyme",
                "variants": {
                    "rs4244285": {
                        "rsid": "rs4244285",
                        "allele": "CYP2C19*2",
                        "effect": "Loss of function",
                        "consequence": "Reduced enzyme activity",
                        "clinical_impact": "Decreased activation of prodrugs (e.g., clopidogrel)",
                        "frequency": {
                            "European": 0.15,
                            "East Asian": 0.29,
                            "African": 0.17,
                            "Latino": 0.14
                        }
                    },
                    "rs12248560": {
                        "rsid": "rs12248560",
                        "allele": "CYP2C19*17",
                        "effect": "Gain of function",
                        "consequence": "Increased enzyme activity",
                        "clinical_impact": "Enhanced activation of prodrugs",
                        "frequency": {
                            "European": 0.21,
                            "East Asian": 0.04,
                            "African": 0.18,
                            "Latino": 0.16
                        }
                    }
                }
            },
            "CYP2D6": {
                "gene": "CYP2D6",
                "function": "Drug metabolism enzyme",
                "variants": {
                    "rs3892097": {
                        "rsid": "rs3892097",
                        "allele": "CYP2D6*4",
                        "effect": "Loss of function",
                        "consequence": "No enzyme activity",
                        "clinical_impact": "Poor metabolizer status for many drugs",
                        "frequency": {
                            "European": 0.20,
                            "East Asian": 0.01,
                            "African": 0.04,
                            "Latino": 0.15
                        }
                    }
                }
            },
            "ABCB1": {
                "gene": "ABCB1",
                "function": "Drug transporter (P-glycoprotein)",
                "variants": {
                    "rs1045642": {
                        "rsid": "rs1045642",
                        "allele": "C3435T",
                        "effect": "Altered expression",
                        "consequence": "Modified drug efflux",
                        "clinical_impact": "Affects drug bioavailability and distribution",
                        "frequency": {
                            "European": 0.48,
                            "East Asian": 0.35,
                            "African": 0.20,
                            "Latino": 0.42
                        }
                    }
                }
            }
        }
        
        # PK/PD Pathway database
        self.pk_pd_pathways = {
            "CYP2C19": {
                "pathway_type": "Pharmacokinetic (PK)",
                "phase": "Phase I Metabolism",
                "process": "Oxidation",
                "location": "Hepatic (Liver)",
                "substrates": ["Clopidogrel", "Omeprazole", "Voriconazole", "Diazepam"],
                "metabolites": ["Active thiol metabolite (clopidogrel)"],
                "clinical_consequence": "Altered drug exposure and efficacy"
            },
            "CYP2D6": {
                "pathway_type": "Pharmacokinetic (PK)",
                "phase": "Phase I Metabolism",
                "process": "Oxidation",
                "location": "Hepatic (Liver)",
                "substrates": ["Codeine", "Tamoxifen", "Metoprolol", "Tramadol"],
                "metabolites": ["Morphine (from codeine)", "Endoxifen (from tamoxifen)"],
                "clinical_consequence": "Altered analgesic effect, therapeutic failure"
            },
            "ABCB1": {
                "pathway_type": "Pharmacokinetic (PK)",
                "phase": "Transport",
                "process": "Drug Efflux",
                "location": "Intestinal, Blood-brain barrier, Liver",
                "substrates": ["Digoxin", "Cyclosporine", "Clopidogrel", "Many others"],
                "metabolites": [],
                "clinical_consequence": "Altered bioavailability and distribution"
            },
            "VKORC1": {
                "pathway_type": "Pharmacodynamic (PD)",
                "phase": "Target",
                "process": "Vitamin K recycling",
                "location": "Hepatic",
                "substrates": ["Warfarin"],
                "metabolites": [],
                "clinical_consequence": "Altered anticoagulation response"
            },
            "SLCO1B1": {
                "pathway_type": "Pharmacokinetic (PK)",
                "phase": "Transport (Uptake)",
                "process": "Hepatic uptake",
                "location": "Hepatocyte",
                "substrates": ["Statins", "Methotrexate"],
                "metabolites": [],
                "clinical_consequence": "Myopathy risk with statins"
            }
        }
        
        # Regex patterns for variant extraction from text
        self._compile_variant_patterns()
    
    def _compile_variant_patterns(self):
        """Compile regex patterns to extract variants from literature"""
        self.variant_patterns = {
            # rsID format: rs followed by numbers
            'rsid': re.compile(r'\b(rs\d{5,})\b', re.IGNORECASE),
            
            # Star allele format: CYP2C19*2, CYP2D6*4, etc.
            'star_allele': re.compile(r'\b(CYP\d+[A-Z]\d+\*\d+)\b', re.IGNORECASE),
            
            # Gene mentions
            'gene': re.compile(r'\b(CYP\d+[A-Z]\d+|ABCB1|SLCO1B1|VKORC1|HLA-[AB])\b', re.IGNORECASE),
            
            # Metabolizer status
            'metabolizer': re.compile(r'(poor|intermediate|extensive|ultra-rapid|rapid)\s+metabolizer', re.IGNORECASE),
            
            # Allele frequency mentions
            'frequency': re.compile(r'(\d+(?:\.\d+)?)\s*%.*?(European|Asian|African|Latino|Caucasian)', re.IGNORECASE)
        }
    
    def run(self, query_obj, literature_data=None):
        """
        Analyze genetic variants from literature AND curated database
        
        Args:
            query_obj: Object with drug attribute
            literature_data: Output from LiteratureMinerAgent (optional)
            
        Returns:
            List of variant dictionaries with rsID, gene, effect, frequencies, PK/PD pathways
        """
        drug = query_obj.drug.lower()
        all_variants = []
        
        # Step 1: Extract variants from literature if available
        if literature_data:
            print("🧬 Extracting genetic variants from literature...")
            lit_variants = self._extract_variants_from_literature(literature_data, drug)
            if lit_variants:
                print(f"  ✓ Found {len(lit_variants)} variants in literature")
                all_variants.extend(lit_variants)
        
        # Step 2: Get curated variants for this drug (dynamically from literature)
        relevant_genes = self._get_relevant_genes(drug, literature_data)
        curated_variants = []
        
        for gene_name in relevant_genes:
            if gene_name in self.variant_db:
                gene_data = self.variant_db[gene_name]
                for rsid, variant_data in gene_data["variants"].items():
                    # Check if not already in lit_variants
                    if not any(v.get("rsid") == rsid for v in all_variants):
                        variant = {
                            "gene": gene_name,
                            "rsid": rsid,
                            "allele": variant_data["allele"],
                            "effect": variant_data["effect"],
                            "consequence": variant_data["consequence"],
                            "clinical_impact": variant_data["clinical_impact"],
                            "mechanism": self._get_mechanism(gene_data["function"], variant_data),
                            "frequency_by_ancestry": variant_data["frequency"],
                            "source": "curated_database"
                        }
                        
                        # Add PK/PD pathway information
                        pathway_info = self._map_to_pk_pd_pathway(gene_name, variant_data)
                        variant.update(pathway_info)
                        
                        curated_variants.append(variant)
        
        all_variants.extend(curated_variants)
        
        # Step 3: Enrich all variants with pathway information
        for variant in all_variants:
            if variant.get("gene") and not variant.get("pk_pd_pathway"):
                pathway_info = self._map_to_pk_pd_pathway(variant["gene"], variant)
                variant.update(pathway_info)
        
        # If no variants found, return empty with honest message
        if not all_variants:
            print(f"  ⚠️  No genetic variants found for {drug}")
            print(f"      - Try checking PharmGKB directly")
            print(f"      - Verify drug name spelling")
            return []  # Empty list - be honest!
        
        print(f"  ✓ Total variants analyzed: {len(all_variants)} ({len([v for v in all_variants if v.get('source') == 'literature'])} from literature)")
        
        return all_variants
    
    def _get_relevant_genes(self, drug, literature_data=None):
        """
        Dynamically determine relevant pharmacogenes from literature
        No hardcoded drug-gene mapping!
        """
        relevant_genes = set()
        
        # Extract genes from literature if available
        if literature_data:
            # Get genes from GWAS data
            gwas_data = literature_data.get("gwas", {})
            if gwas_data and gwas_data.get("genes"):
                relevant_genes.update(gwas_data["genes"])
            
            # Extract genes mentioned in studies
            studies = literature_data.get("studies", [])
            for study in studies:
                text = f"{study.get('title', '')} {study.get('abstract', '')}"
                # Find pharmacogene mentions
                for gene_pattern in self.variant_patterns['gene'].findall(text):
                    relevant_genes.add(gene_pattern.upper())
        
        # If we found genes in literature, use them
        if relevant_genes:
            return list(relevant_genes)
        
        # No fallback genes - be honest that we don't know
        print(f"  ⚠️  Could not identify relevant pharmacogenes for {drug} from literature")
        return []  # Return empty - let system be honest
    
    def _get_mechanism(self, gene_function, variant_data):
        """Generate mechanism description"""
        effect = variant_data.get("effect", "")
        consequence = variant_data.get("consequence", "")
        
        if "metabolism" in gene_function.lower():
            if "loss" in effect.lower():
                return f"Reduced metabolic conversion due to {consequence.lower()}, leading to altered drug levels"
            elif "gain" in effect.lower():
                return f"Enhanced metabolic conversion due to {consequence.lower()}, affecting drug exposure"
        elif "transporter" in gene_function.lower():
            return f"Altered drug transport affecting bioavailability and tissue distribution"
        
        return f"{gene_function}: {consequence}"
    
    def _extract_variants_from_literature(self, literature_data: Dict, drug: str) -> List[Dict]:
        """
        Extract genetic variants mentioned in literature
        
        Args:
            literature_data: Dict with 'studies', 'gwas', 'label' keys
            drug: Drug name
            
        Returns:
            List of variant dictionaries extracted from text
        """
        variants = []
        seen_rsids = set()
        
        # Extract from GWAS data
        gwas_data = literature_data.get("gwas", {})
        if gwas_data:
            gwas_variants = self._extract_from_gwas(gwas_data, drug)
            for v in gwas_variants:
                if v["rsid"] not in seen_rsids:
                    variants.append(v)
                    seen_rsids.add(v["rsid"])
        
        # Extract from study abstracts/full text
        studies = literature_data.get("studies", [])
        for study in studies:
            # Check abstract
            abstract = study.get("abstract", "")
            title = study.get("title", "")
            full_text = study.get("full_text", "")
            
            # Combine all text
            text = f"{title} {abstract} {full_text}"
            
            if text:
                study_variants = self._extract_variants_from_text(text, drug)
                for v in study_variants:
                    if v["rsid"] not in seen_rsids:
                        v["source_pmid"] = study.get("pmid")
                        variants.append(v)
                        seen_rsids.add(v["rsid"])
        
        return variants
    
    def _extract_from_gwas(self, gwas_data: Dict, drug: str) -> List[Dict]:
        """Extract variants from GWAS data structure"""
        variants = []
        
        # GWAS data typically has variants and genes
        variant_list = gwas_data.get("variants", [])
        genes = gwas_data.get("genes", [])
        associations = gwas_data.get("associations", "")
        
        # Create variants from rsIDs
        for rsid in variant_list:
            # Try to map to a gene
            gene = None
            for g in genes:
                if g in self.variant_db:
                    gene = g
                    break
            
            variant = {
                "rsid": rsid,
                "gene": gene or "Unknown",
                "allele": "N/A",
                "effect": "Associated with drug response",
                "consequence": associations,
                "clinical_impact": f"GWAS association with {drug} response",
                "mechanism": "Genetic association identified through genome-wide analysis",
                "frequency_by_ancestry": {},
                "source": "literature_gwas"
            }
            variants.append(variant)
        
        return variants
    
    def _extract_variants_from_text(self, text: str, drug: str) -> List[Dict]:
        """
        Extract genetic variants mentioned in text using NLP patterns
        
        Args:
            text: Abstract or full text
            drug: Drug name
            
        Returns:
            List of extracted variants
        """
        variants = []
        
        # Find all rsIDs
        rsids = self.variant_patterns['rsid'].findall(text)
        
        # Find all genes mentioned
        genes = self.variant_patterns['gene'].findall(text)
        
        # Find star alleles
        star_alleles = self.variant_patterns['star_allele'].findall(text)
        
        # Find metabolizer status mentions
        metabolizer_status = self.variant_patterns['metabolizer'].findall(text)
        
        # Create variants from rsIDs
        for rsid in rsids:
            # Try to find associated gene nearby in text
            rsid_pos = text.find(rsid)
            context = text[max(0, rsid_pos-100):rsid_pos+100]
            
            gene = None
            for g in genes:
                if g in context:
                    gene = g
                    break
            
            # Check if this variant is in our database
            effect = "Unknown"
            consequence = "Mentioned in literature"
            
            if gene and gene in self.variant_db:
                gene_data = self.variant_db[gene]
                if rsid in gene_data.get("variants", {}):
                    variant_data = gene_data["variants"][rsid]
                    effect = variant_data.get("effect", "Unknown")
                    consequence = variant_data.get("consequence", "Mentioned in literature")
            
            variant = {
                "rsid": rsid,
                "gene": gene or "Unknown",
                "allele": "N/A",
                "effect": effect,
                "consequence": consequence,
                "clinical_impact": f"Mentioned in association with {drug}",
                "mechanism": f"Genetic variant identified in {drug} pharmacogenetics literature",
                "frequency_by_ancestry": {},
                "source": "literature_text"
            }
            variants.append(variant)
        
        # Also create entries for star alleles not captured above
        for allele in star_alleles:
            if not any(v.get("allele") == allele for v in variants):
                # Extract gene from allele (e.g., CYP2C19 from CYP2C19*2)
                gene_match = re.match(r'([A-Z0-9]+)', allele)
                gene = gene_match.group(1) if gene_match else "Unknown"
                
                variant = {
                    "rsid": "N/A",
                    "gene": gene,
                    "allele": allele,
                    "effect": "Unknown",
                    "consequence": "Star allele mentioned in literature",
                    "clinical_impact": f"Pharmacogenetic marker for {drug}",
                    "mechanism": "Allele variant affecting drug metabolism",
                    "frequency_by_ancestry": {},
                    "source": "literature_text"
                }
                variants.append(variant)
        
        return variants
    
    def _map_to_pk_pd_pathway(self, gene: str, variant_data: Dict) -> Dict:
        """
        Map a genetic variant to PK/PD pathways
        
        Args:
            gene: Gene name
            variant_data: Variant information
            
        Returns:
            Dict with pathway information
        """
        pathway_info = {}
        
        if gene in self.pk_pd_pathways:
            pathway = self.pk_pd_pathways[gene]
            
            pathway_info = {
                "pk_pd_pathway": pathway["pathway_type"],
                "metabolic_phase": pathway.get("phase", "Unknown"),
                "process": pathway.get("process", "Unknown"),
                "location": pathway.get("location", "Unknown"),
                "clinical_consequence_pathway": pathway.get("clinical_consequence", "Unknown")
            }
            
            # Add detailed mechanism based on pathway
            if pathway["pathway_type"] == "Pharmacokinetic (PK)":
                if "Phase I" in pathway.get("phase", ""):
                    pathway_info["detailed_mechanism"] = (
                        f"{gene} catalyzes {pathway['process']} in {pathway['location']}. "
                        f"Variants affect metabolic conversion of substrates including "
                        f"{', '.join(pathway.get('substrates', [])[:3])}."
                    )
                elif "Transport" in pathway.get("phase", ""):
                    pathway_info["detailed_mechanism"] = (
                        f"{gene} mediates {pathway['process']} in {pathway['location']}. "
                        f"Variants alter bioavailability and tissue distribution."
                    )
            elif pathway["pathway_type"] == "Pharmacodynamic (PD)":
                pathway_info["detailed_mechanism"] = (
                    f"{gene} is involved in {pathway['process']} at the drug target level. "
                    f"Variants directly affect drug efficacy."
                )
        else:
            # Generic pathway info
            pathway_info = {
                "pk_pd_pathway": "Unknown",
                "metabolic_phase": "Unknown",
                "process": "Unknown",
                "location": "Unknown",
                "clinical_consequence_pathway": "Requires further characterization",
                "detailed_mechanism": f"PK/PD pathway for {gene} not fully characterized in database"
            }
        
        return pathway_info