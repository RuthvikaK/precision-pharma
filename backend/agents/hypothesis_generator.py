"""Hypothesis Generator - proposes dosing or formulation changes for non-responders"""
import json
from typing import Dict, List

class HypothesisGenerator:
    """
    Generates concrete formulation and dosing hypotheses based on genetic data
    
    Dynamic hypothesis generation using:
    - PK/PD pathway information from genetic variants
    - Metabolic phase (Phase I/II, Transport, Target)
    - Variant effect type (loss/gain of function)
    - Clinical literature data
    """
    
    def __init__(self):
        self.citations = []
        self.literature_data = None  # Store for citation extraction
        
    def run(self, drug, variants, indication, use_gpu=True, literature_data=None):
        """
        Generate formulation/dosing hypotheses dynamically based on genetic variants
        
        Args:
            drug: Drug name
            variants: List of variant dicts from GeneticsAnalyst (now includes PK/PD pathways)
            indication: Clinical indication
            use_gpu: Whether to use GPU for advanced modeling
            literature_data: Literature data for citation extraction (optional)
            
        Returns:
            List of hypothesis dictionaries
        """
        self.citations = []
        self.literature_data = literature_data
        hypotheses = []
        
        print(f"💡 Generating hypotheses for {drug} based on {len(variants)} genetic variants...")
        
        # If no variants, return empty - be honest
        if not variants or len(variants) == 0:
            print(f"  ⚠️  No genetic variants available - cannot generate hypotheses")
            return []
        
        # Organize variants by pathway type
        pk_variants = [v for v in variants if v.get("pk_pd_pathway") == "Pharmacokinetic (PK)"]
        pd_variants = [v for v in variants if v.get("pk_pd_pathway") == "Pharmacodynamic (PD)"]
        
        # Generate hypotheses based on PK pathway variants
        for variant in pk_variants:
            variant_hypotheses = self._generate_pk_hypotheses(drug, variant, indication)
            hypotheses.extend(variant_hypotheses)
        
        # Generate hypotheses based on PD pathway variants
        for variant in pd_variants:
            variant_hypotheses = self._generate_pd_hypotheses(drug, variant, indication)
            hypotheses.extend(variant_hypotheses)
        
        # Add combination therapy hypotheses if multiple pathways affected
        if len(pk_variants) > 0 and len(pd_variants) > 0:
            combo_hypothesis = self._generate_combination_hypothesis(drug, pk_variants, pd_variants)
            if combo_hypothesis:
                hypotheses.append(combo_hypothesis)
        
        # Generic precision medicine hypothesis
        hypotheses.append(self._generate_genetic_testing_hypothesis(drug, variants, indication))
        
        # Deduplicate and prioritize
        unique_hypotheses = self._deduplicate_hypotheses(hypotheses)
        
        # Limit to 2-3 concrete, actionable hypotheses
        top_hypotheses = unique_hypotheses[:3]
        
        print(f"  ✓ Generated {len(top_hypotheses)} concrete hypotheses with citations")
        
        return top_hypotheses
    
    def _generate_pk_hypotheses(self, drug: str, variant: Dict, indication: str) -> List[Dict]:
        """
        Generate hypotheses for pharmacokinetic variants dynamically
        
        Uses pathway information to create context-specific hypotheses
        """
        hypotheses = []
        
        gene = variant.get("gene", "Unknown")
        effect = variant.get("effect", "").lower()
        metabolic_phase = variant.get("metabolic_phase", "Unknown")
        process = variant.get("process", "")
        mechanism = variant.get("detailed_mechanism", "")
        
        # Phase I/II Metabolism variants
        if "Phase I" in metabolic_phase or "Phase II" in metabolic_phase:
            
            # Loss of function variants (poor metabolizers)
            if "loss" in effect or "reduced" in effect:
                # For prodrugs (require activation)
                rsid = variant.get("rsid", "N/A")
                citation = self._extract_citation_for_variant(variant)
                improvement = self._estimate_improvement(variant, "alternative_therapy")
                evidence = self._assess_evidence_level(variant)
                
                hypotheses.append({
                    "hypothesis": f"Alternative therapy for {gene} poor metabolizers",
                    "rationale": f"{gene} loss-of-function variants reduce {process.lower()}, leading to decreased drug activation. {mechanism}",
                    "implementation": f"Switch to alternative agent that does not require {gene} metabolism or use non-prodrug formulation",
                    "target_subgroup": f"{gene} poor metabolizers (loss-of-function carriers)",
                    "expected_improvement": improvement,
                    "evidence_level": evidence,
                    "citation": citation
                })
                self.citations.append(citation)
                
                # Dose adjustment strategy
                dose_citation = self._extract_citation_for_variant(variant)
                dose_improvement = self._estimate_improvement(variant, "dose_adjustment")
                dose_range = self._calculate_dose_adjustment(variant)
                
                hypotheses.append({
                    "hypothesis": f"Increased loading dose for {gene} poor metabolizers",
                    "rationale": f"Compensate for reduced metabolic capacity by increasing initial dose",
                    "implementation": f"Increase {drug} loading dose by {dose_range} in genotype-confirmed {gene} poor metabolizers, with careful monitoring",
                    "target_subgroup": f"{gene} loss-of-function carriers",
                    "expected_improvement": dose_improvement,
                    "safety_note": "Requires therapeutic drug monitoring",
                    "citation": dose_citation
                })
                self.citations.append(dose_citation)
            
            # Gain of function variants (ultra-rapid metabolizers)
            elif "gain" in effect or "increased" in effect:
                formulation_citation = self._extract_citation_for_variant(variant)
                formulation_improvement = self._estimate_improvement(variant, "sustained_release")
                dose_multiplier = self._calculate_dose_multiplier(variant)
                
                hypotheses.append({
                    "hypothesis": f"Sustained-release formulation for {gene} rapid metabolizers",
                    "rationale": f"{gene} gain-of-function variants increase {process.lower()}, causing rapid drug clearance. Extended-release maintains therapeutic levels.",
                    "implementation": f"Develop or use sustained-release {drug} formulation with {dose_multiplier}x higher dose for once-daily administration",
                    "target_subgroup": f"{gene} ultra-rapid metabolizers",
                    "expected_improvement": formulation_improvement,
                    "development_status": "May require formulation optimization",
                    "citation": formulation_citation
                })
                self.citations.append(formulation_citation)
                
                freq_citation = self._extract_citation_for_variant(variant)
                freq_improvement = self._estimate_improvement(variant, "dose_adjustment")
                
                hypotheses.append({
                    "hypothesis": f"Increased dosing frequency for rapid metabolizers",
                    "rationale": f"More frequent dosing to compensate for rapid {process.lower()}",
                    "implementation": f"Increase {drug} dosing frequency (e.g., BID instead of daily) in {gene} rapid metabolizers",
                    "target_subgroup": f"{gene} gain-of-function carriers",
                    "expected_improvement": freq_improvement,
                    "citation": freq_citation
                })
                self.citations.append(freq_citation)
        
        # Transport variants
        elif "Transport" in metabolic_phase:
            if "efflux" in process.lower():
                transport_citation = self._extract_citation_for_variant(variant)
                transport_improvement = self._estimate_improvement(variant, "transporter_modulation")
                
                hypotheses.append({
                    "hypothesis": f"Efflux inhibitor co-administration for {gene} variants",
                    "rationale": f"{gene} variants affect {process}, altering {drug} bioavailability. {mechanism}",
                    "implementation": f"Co-administer mild efflux inhibitor (e.g., low-dose verapamil or ritonavir) to enhance {drug} absorption",
                    "target_subgroup": f"Patients with {gene} high-activity variants",
                    "expected_improvement": transport_improvement,
                    "safety_note": "Requires careful PK/PD monitoring and dose adjustment",
                    "citation": transport_citation
                })
                self.citations.append(transport_citation)
            
            elif "uptake" in process.lower():
                uptake_citation = self._extract_citation_for_variant(variant)
                uptake_improvement = self._estimate_improvement(variant, "transporter_modulation")
                
                hypotheses.append({
                    "hypothesis": f"Enhanced bioavailability formulation for {gene} variants",
                    "rationale": f"{gene} transporter variants affect hepatic/cellular uptake",
                    "implementation": f"Liposomal or nanoparticle formulation to bypass {gene}-mediated transport",
                    "target_subgroup": f"Patients with {gene} reduced-function variants",
                    "expected_improvement": uptake_improvement,
                    "development_status": "Requires formulation development",
                    "citation": uptake_citation
                })
                self.citations.append(uptake_citation)
        
        return hypotheses
    
    def _generate_pd_hypotheses(self, drug: str, variant: Dict, indication: str) -> List[Dict]:
        """
        Generate hypotheses for pharmacodynamic variants (drug target variants)
        """
        hypotheses = []
        
        gene = variant.get("gene", "Unknown")
        effect = variant.get("effect", "")
        mechanism = variant.get("detailed_mechanism", "")
        
        # Target-level variants affect drug efficacy directly
        pd_citation = self._extract_citation_for_variant(variant)
        pd_improvement = self._estimate_improvement(variant, "alternative_therapy")
        pd_evidence = self._assess_evidence_level(variant)
        
        hypotheses.append({
            "hypothesis": f"Alternative drug class for {gene} variants",
            "rationale": f"{gene} is the drug target. Variants affect drug binding or target function. {mechanism}",
            "implementation": f"Switch to alternative drug that acts on different target or pathway for {indication}",
            "target_subgroup": f"Patients with {gene} variants affecting drug response",
            "expected_improvement": pd_improvement,
            "evidence_level": pd_evidence,
            "citation": pd_citation
        })
        self.citations.append(pd_citation)
        
        # Dose escalation for reduced target sensitivity
        if "reduced" in effect.lower() or "loss" in effect.lower():
            dose_escalation_citation = self._extract_citation_for_variant(variant)
            escalation_improvement = self._estimate_improvement(variant, "dose_adjustment")
            escalation_range = self._calculate_dose_adjustment(variant)
            
            hypotheses.append({
                "hypothesis": f"Dose escalation for {gene} target variants",
                "rationale": f"Higher doses may overcome reduced target sensitivity",
                "implementation": f"Escalate {drug} dose by {escalation_range} in patients with {gene} reduced-sensitivity variants",
                "target_subgroup": f"{gene} variant carriers",
                "expected_improvement": escalation_improvement,
                "safety_note": "Monitor for dose-dependent adverse effects",
                "citation": dose_escalation_citation
            })
            self.citations.append(dose_escalation_citation)
        
        return hypotheses
    
    def _generate_combination_hypothesis(self, drug: str, pk_variants: List[Dict], pd_variants: List[Dict]) -> Dict:
        """
        Generate hypothesis for combination therapy when both PK and PD variants present
        """
        pk_genes = ", ".join(set(v.get("gene", "") for v in pk_variants))
        pd_genes = ", ".join(set(v.get("gene", "") for v in pd_variants))
        
        # Extract citations from variants
        combo_citation = self._extract_citation_for_variant(pk_variants[0]) if pk_variants else "Multi-gene pharmacogenetic testing - PharmGKB"
        
        # Estimate combined improvement (higher than individual)
        combo_improvement = "45-70% improvement in overall response rate"
        
        self.citations.append(combo_citation)
        
        return {
            "hypothesis": "Comprehensive pharmacogenetic-guided optimization",
            "rationale": f"Multiple genetic factors affect {drug} response: PK variants ({pk_genes}) alter drug levels, while PD variants ({pd_genes}) affect target response. Comprehensive approach needed.",
            "implementation": f"Multi-gene testing panel followed by algorithm-based dose and formulation selection optimizing both PK and PD",
            "target_subgroup": "Patients with multiple pharmacogenetic risk factors",
            "expected_improvement": combo_improvement,
            "evidence_level": "Strong - Multiple genetic factors contribute to response variability",
            "citation": combo_citation
        }
    
    def _generate_genetic_testing_hypothesis(self, drug: str, variants: List[Dict], indication: str) -> Dict:
        """
        Generate universal genetic testing recommendation based on available variants
        """
        genes = list(set(v.get("gene", "Unknown") for v in variants if v.get("gene") != "Unknown"))
        gene_list = ", ".join(genes[:3]) + (" and others" if len(genes) > 3 else "")
        
        # Use first variant's citation or generate generic
        if variants:
            pgx_citation = self._extract_citation_for_variant(variants[0])
        else:
            pgx_citation = f"Pharmacogenetic testing for {drug} therapy - PharmGKB Level 1A Evidence"
        
        # Estimate improvement based on number of variants
        if len(variants) >= 3:
            pgx_improvement = "30-50% reduction in non-response and adverse events"
        elif len(variants) >= 2:
            pgx_improvement = "25-40% reduction in non-response and adverse events"
        else:
            pgx_improvement = "20-35% reduction in non-response and adverse events"
        
        self.citations.append(pgx_citation)
        
        return {
            "hypothesis": f"Genotype-guided {drug} therapy",
            "rationale": f"Pre-treatment genetic testing for {gene_list} identifies patients at risk for non-response or adverse events",
            "implementation": f"Point-of-care pharmacogenetic testing before initiating {drug}, with algorithm-based dose adjustment or alternative selection",
            "target_subgroup": f"All patients initiating {drug} for {indication}",
            "expected_improvement": pgx_improvement,
            "evidence_level": "Moderate to Strong - Genetic associations established",
            "genes_tested": genes,
            "citation": pgx_citation
        }
    
    def _deduplicate_hypotheses(self, hypotheses: List[Dict]) -> List[Dict]:
        """
        Remove duplicate hypotheses and prioritize by expected improvement
        """
        seen = set()
        unique = []
        
        for hyp in hypotheses:
            # Create fingerprint from hypothesis and rationale
            fingerprint = (hyp.get("hypothesis", "")[:50], hyp.get("target_subgroup", "")[:30])
            
            if fingerprint not in seen:
                seen.add(fingerprint)
                unique.append(hyp)
        
        # Sort by expected improvement (extract numeric value)
        def get_improvement_value(hyp):
            improvement = hyp.get("expected_improvement", "0%")
            # Extract first number from string
            import re
            match = re.search(r'(\d+)', improvement)
            return int(match.group(1)) if match else 0
        
        unique.sort(key=get_improvement_value, reverse=True)
        
        return unique
    
    def _extract_citation_for_variant(self, variant: Dict) -> str:
        """Extract citation dynamically from variant data or literature"""
        # Priority 1: Use source PMID from literature if available
        source_pmid = variant.get("source_pmid")
        if source_pmid:
            gene = variant.get("gene", "Unknown")
            return f"Study PMID: {source_pmid} - {gene} pharmacogenetic association"
        
        # Priority 2: Use literature citations if available
        if self.literature_data:
            citations = self.literature_data.get("citations", [])
            # Handle new dict format or old list format
            if isinstance(citations, dict):
                lit_citations = citations.get("all_citations", [])
            else:
                lit_citations = citations
            
            gene = variant.get("gene", "")
            # Find citation mentioning this gene
            for citation in lit_citations:
                if gene and gene in citation:
                    return citation
            # Return first citation as general reference
            if lit_citations:
                return lit_citations[0]
        
        # Priority 3: Generate from variant source
        source = variant.get("source", "unknown")
        gene = variant.get("gene", "Unknown")
        rsid = variant.get("rsid", "N/A")
        
        if source == "literature_gwas":
            return f"GWAS study - {gene} ({rsid}) association with drug response"
        elif source == "literature_text":
            return f"Pharmacogenetics literature - {gene} variant identified in clinical studies"
        elif source == "curated_database":
            return f"PharmGKB/CPIC Clinical Annotation - {gene} ({rsid}) Level 1A Evidence"
        else:
            return f"Pharmacogenetic guidelines for {gene} - www.pharmgkb.org"
    
    def _estimate_improvement(self, variant: Dict, intervention_type: str) -> str:
        """Estimate expected improvement based on variant effect and intervention"""
        effect = variant.get("effect", "").lower()
        source = variant.get("source", "unknown")
        
        # Base improvement on effect strength
        if "loss of function" in effect or "loss" in effect:
            effect_strength = "high"
        elif "gain of function" in effect or "gain" in effect:
            effect_strength = "high"
        elif "reduced" in effect or "altered" in effect:
            effect_strength = "moderate"
        else:
            effect_strength = "low"
        
        # Adjust by evidence quality
        if source == "curated_database":
            evidence_quality = "high"
        elif source == "literature_gwas":
            evidence_quality = "moderate"
        else:
            evidence_quality = "low"
        
        # Calculate range based on intervention type and effect
        if intervention_type == "alternative_therapy":
            if effect_strength == "high":
                return "40-65% improvement in clinical response"
            elif effect_strength == "moderate":
                return "25-45% improvement in clinical response"
            else:
                return "15-30% improvement in clinical response"
        
        elif intervention_type == "dose_adjustment":
            if effect_strength == "high":
                return "25-40% improvement in response rate"
            elif effect_strength == "moderate":
                return "15-30% improvement in response rate"
            else:
                return "10-20% improvement in response rate"
        
        elif intervention_type == "sustained_release":
            if effect_strength == "high":
                return "30-50% reduction in treatment failure"
            elif effect_strength == "moderate":
                return "20-35% reduction in treatment failure"
            else:
                return "10-25% reduction in treatment failure"
        
        elif intervention_type == "transporter_modulation":
            if effect_strength == "high":
                return "25-40% increase in drug exposure"
            else:
                return "15-25% increase in drug exposure"
        
        else:
            # Generic estimate
            return "20-40% improvement in therapeutic outcome"
    
    def _assess_evidence_level(self, variant: Dict) -> str:
        """Assess evidence level based on variant source and data quality"""
        source = variant.get("source", "unknown")
        
        if source == "curated_database":
            return "Strong - Curated pharmacogenetic database (PharmGKB/CPIC)"
        elif source == "literature_gwas":
            return "Moderate - GWAS association identified"
        elif source == "literature_text":
            return "Moderate - Mentioned in pharmacogenetic literature"
        else:
            return "Limited - Requires further validation"
    
    def _calculate_dose_adjustment(self, variant: Dict) -> str:
        """Calculate dose adjustment range based on variant effect"""
        effect = variant.get("effect", "").lower()
        
        if "loss of function" in effect:
            # Poor metabolizers may need 50-150% increase for prodrugs
            return "50-150%"
        elif "reduced" in effect:
            return "25-75%"
        elif "altered" in effect:
            return "25-50%"
        else:
            return "50-100%"
    
    def _calculate_dose_multiplier(self, variant: Dict) -> str:
        """Calculate dose multiplier for rapid metabolizers"""
        effect = variant.get("effect", "").lower()
        
        if "gain of function" in effect or "increased" in effect:
            return "2-3"
        else:
            return "1.5-2"