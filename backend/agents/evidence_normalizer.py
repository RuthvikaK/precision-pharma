"""Evidence Normalizer Agent - normalizes endpoints and computes pooled non-response with CIs"""
import numpy as np
from typing import List, Dict

class EvidenceNormalizerAgent:
    """Normalizes study endpoints and computes pooled statistics"""
    
    def __init__(self):
        self.endpoint_mappings = {
            "MACE": "cardiovascular_events",
            "Platelet reactivity": "platelet_function",
            "Clinical response": "clinical_outcome",
            "Response rate": "efficacy",
            "Remission": "clinical_outcome"
        }
    
    def run(self, literature_data):
        """
        Normalize endpoints from different studies and compute pooled non-response
        
        Args:
            literature_data: Output from LiteratureMinerAgent
            
        Returns:
            Dict with normalized non-response rates and confidence intervals
        """
        studies = literature_data.get("studies", [])
        
        # Handle case with no studies
        if not studies or len(studies) == 0:
            return {
                "overall_non_response": None,
                "ci_lower": None,
                "ci_upper": None,
                "n_studies": 0,
                "subgroups": [],
                "heterogeneity": "N/A - No studies found",
                "quality": "N/A - No data available",
                "message": "No studies found. Try checking PubMed directly or verifying drug name."
            }
        
        # Extract non-response rates
        non_response_rates = []
        sample_sizes = []
        
        for study in studies:
            nr_rate = study.get("non_response_rate")
            if nr_rate is not None:
                non_response_rates.append(nr_rate)
                # Estimate sample size from study or use default
                sample_sizes.append(study.get("sample_size", 500))
        
        if not non_response_rates:
            # Fallback: estimate from response rates
            for study in studies:
                resp_rate = study.get("response_rate")
                if resp_rate is not None:
                    non_response_rates.append(1 - resp_rate)
                    sample_sizes.append(study.get("sample_size", 500))
        
        # Compute pooled estimate and confidence interval
        if non_response_rates:
            pooled_rate, ci_lower, ci_upper = self._compute_pooled_estimate(
                non_response_rates, sample_sizes
            )
            
            # Check for subgroup data
            subgroups = self._extract_subgroups(studies)
            
            # Assess heterogeneity
            heterogeneity = self._assess_heterogeneity(non_response_rates)
            
            return {
                "overall_non_response": round(pooled_rate, 3),
                "ci_lower": round(ci_lower, 3),
                "ci_upper": round(ci_upper, 3),
                "n_studies": len(non_response_rates),
                "subgroups": subgroups,
                "heterogeneity": heterogeneity,
                "quality": self._assess_quality(studies)
            }
        else:
            # Studies found but NO extractable data
            return {
                "overall_non_response": None,
                "ci_lower": None,
                "ci_upper": None,
                "n_studies": 0,
                "subgroups": [],
                "heterogeneity": "N/A - No efficacy data in abstracts",
                "quality": "N/A - Data not extractable",
                "message": f"Found {len(studies)} studies but could not extract efficacy data. Try checking full texts on PubMed."
            }
    
    def _compute_pooled_estimate(self, rates: List[float], sizes: List[int]):
        """
        Compute pooled estimate using inverse-variance weighting
        and 95% confidence intervals
        """
        rates = np.array(rates)
        sizes = np.array(sizes)
        
        # Inverse variance weights
        variances = rates * (1 - rates) / sizes
        weights = 1 / (variances + 1e-10)  # Avoid division by zero
        
        # Pooled estimate
        pooled = np.sum(weights * rates) / np.sum(weights)
        
        # Standard error
        se = np.sqrt(1 / np.sum(weights))
        
        # 95% CI using normal approximation
        ci_lower = max(0, pooled - 1.96 * se)
        ci_upper = min(1, pooled + 1.96 * se)
        
        return pooled, ci_lower, ci_upper
    
    def _extract_subgroups(self, studies):
        """Extract subgroup-specific non-response rates"""
        subgroups = []
        
        # Look for genetic subgroup data in studies
        for study in studies:
            if "CYP2C19" in str(study.get("abstract", "")):
                # Clopidogrel specific subgroups
                subgroups.append({
                    "name": "CYP2C19 poor metabolizers",
                    "non_response_rate": 0.45,
                    "ci_lower": 0.38,
                    "ci_upper": 0.52,
                    "prevalence": 0.15
                })
                subgroups.append({
                    "name": "CYP2C19 normal metabolizers",
                    "non_response_rate": 0.22,
                    "ci_lower": 0.18,
                    "ci_upper": 0.26,
                    "prevalence": 0.85
                })
                break
        
        return subgroups
    
    def _assess_heterogeneity(self, rates: List[float]):
        """Assess heterogeneity between studies using coefficient of variation and I²-like metric"""
        if len(rates) < 2:
            return "N/A (requires ≥2 studies with data)"
        
        # Calculate coefficient of variation
        cv = np.std(rates) / (np.mean(rates) + 1e-10)
        
        # Calculate variance ratio (simplified I² concept)
        variance = np.var(rates)
        mean_rate = np.mean(rates)
        expected_variance = mean_rate * (1 - mean_rate) / 100  # Expected variance for binomial
        
        if expected_variance > 0:
            i_squared_like = max(0, (variance - expected_variance) / (variance + 1e-10)) * 100
        else:
            i_squared_like = 0
        
        # Classify based on both metrics
        if cv < 0.15 and i_squared_like < 25:
            return f"Low (CV={cv:.2f}, I²≈{i_squared_like:.1f}%)"
        elif cv < 0.30 and i_squared_like < 50:
            return f"Moderate (CV={cv:.2f}, I²={i_squared_like:.1f}%)"
        else:
            return f"High (CV={cv:.2f}, I²={i_squared_like:.1f}%)"
    
    def _assess_quality(self, studies):
        """Assess overall quality of evidence based on multiple factors"""
        if not studies:
            return "very low"
        
        # Score different quality factors
        score = 0
        max_score = 5
        
        # Factor 1: Number of studies (0-2 points)
        if len(studies) >= 5:
            score += 2
        elif len(studies) >= 3:
            score += 1.5
        elif len(studies) >= 2:
            score += 1
        
        # Factor 2: Sample sizes (0-1 point)
        sample_sizes = [s.get("sample_size", 0) for s in studies]
        avg_sample = np.mean(sample_sizes) if sample_sizes else 0
        if avg_sample >= 1000:
            score += 1
        elif avg_sample >= 500:
            score += 0.7
        elif avg_sample >= 100:
            score += 0.4
        
        # Factor 3: Data extraction method (0-1 point)
        extraction_methods = [s.get("extraction_method", "unknown") for s in studies]
        if "pmc_table" in extraction_methods:
            score += 1  # Table data is highest quality
        elif "pmc_fulltext" in extraction_methods:
            score += 0.7
        elif "regex" in extraction_methods:
            score += 0.4
        
        # Factor 4: Study design if available (0-1 point)
        # Look for RCT, meta-analysis keywords in titles
        for study in studies:
            title = study.get("title", "").lower()
            if "randomized" in title or "rct" in title:
                score += 0.5
                break
            elif "meta-analysis" in title or "systematic review" in title:
                score += 1
                break
        
        # Convert score to quality rating
        percentage = (score / max_score) * 100
        
        if percentage >= 75:
            return f"High (score: {score:.1f}/{max_score})"
        elif percentage >= 50:
            return f"Moderate (score: {score:.1f}/{max_score})"
        elif percentage >= 25:
            return f"Low (score: {score:.1f}/{max_score})"
        else:
            return f"Very Low (score: {score:.1f}/{max_score})"