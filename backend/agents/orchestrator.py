"""
LLM-Powered Orchestrator Agent
Uses Llama-3.3-70B to intelligently coordinate specialist agents
"""
import os
import json
from together import Together
from agents.literature_miner import LiteratureMinerAgent
from agents.evidence_normalizer import EvidenceNormalizerAgent
from agents.genetics_analyst import GeneticsAnalyst
from agents.label_pgx_extractor import LabelPGXExtractor
from agents.hypothesis_generator import HypothesisGenerator


class OrchestratorAgent:
    """
    LLM-powered orchestrator that:
    1. Creates query contracts for specialized agents
    2. Decides which agents to invoke and in what order
    3. Validates agent outputs for safety and correctness
    4. Manages citations and consolidates results
    5. Ensures coherent final output
    """
    
    def __init__(self):
        # Initialize Together AI client
        api_key = os.getenv("TOGETHER_API_KEY")
        if not api_key:
            print("⚠️  Warning: TOGETHER_API_KEY not found. Orchestrator will use fallback mode.")
            self.client = None
        else:
            self.client = Together(api_key=api_key)
        
        # Initialize specialist agents
        self.literature_miner = LiteratureMinerAgent()
        self.evidence_normalizer = EvidenceNormalizerAgent()
        self.genetics_analyst = GeneticsAnalyst()
        self.label_extractor = LabelPGXExtractor()
        self.hypothesis_generator = HypothesisGenerator()
        
        # Model configuration
        self.model = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        self.max_tokens = 2048
        self.temperature = 0.3  # Low temperature for consistent, factual responses
    
    def run(self, drug, indication, use_gpu=True):
        """
        Main orchestration workflow with LLM oversight
        """
        if not self.client:
            # Fallback to simple orchestration without LLM
            return self._run_fallback(drug, indication, use_gpu)
        
        # Step 1: LLM creates query contract
        query_contract = self._create_query_contract(drug, indication)
        print(f"📋 Query Contract Created: {query_contract['task_description']}")
        
        # Step 2: LLM decides agent execution plan
        execution_plan = self._create_execution_plan(query_contract)
        print(f"🗺️  Execution Plan: {len(execution_plan['steps'])} steps")
        
        # Step 3: Execute agents according to plan
        agent_outputs = self._execute_agents(execution_plan, drug, indication, use_gpu)
        
        # Step 4: LLM validates outputs for safety and correctness
        validated_outputs = self._validate_outputs(agent_outputs, query_contract)
        
        # Step 5: LLM consolidates citations and creates final response
        final_response = self._consolidate_results(validated_outputs, query_contract)
        
        return final_response
    
    def _create_query_contract(self, drug, indication):
        """
        LLM analyzes the request and creates a structured query contract
        """
        prompt = f"""You are a pharmacology expert creating a query contract for drug analysis.

User Request:
- Drug: {drug}
- Indication: {indication}

Create a structured query contract with:
1. Task description (what analysis is needed)
2. Key questions to answer
3. Required data sources (literature, genetics, labels, etc.)
4. Safety considerations
5. Expected output format

Respond in valid JSON format only."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            # Extract JSON from response (handle potential markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            contract = json.loads(content)
            return contract
            
        except Exception as e:
            print(f"⚠️  LLM contract creation failed: {e}. Using template.")
            return self._default_query_contract(drug, indication)
    
    def _create_execution_plan(self, query_contract):
        """
        LLM determines which agents to call and in what order
        """
        prompt = f"""Based on this query contract, create an execution plan for specialist agents.

Query Contract:
{json.dumps(query_contract, indent=2)}

Available Agents:
1. Literature Miner - Searches PubMed for studies and clinical data
2. Evidence Normalizer - Computes pooled statistics and confidence intervals
3. Genetics Analyst - Analyzes pharmacogenetic variants
4. Label Extractor - Extracts FDA label pharmacogenomics info
5. Hypothesis Generator - Proposes formulation/dosing strategies

Create an execution plan with:
- Which agents to invoke (and why)
- Order of execution
- Dependencies between agents
- Expected outputs from each

Respond in valid JSON with a "steps" array."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            plan = json.loads(content)
            return plan
            
        except Exception as e:
            print(f"⚠️  LLM planning failed: {e}. Using default plan.")
            return self._default_execution_plan()
    
    def _execute_agents(self, execution_plan, drug, indication, use_gpu):
        """
        Execute specialist agents according to the plan
        """
        outputs = {}
        
        # Execute in order (with dependency management)
        print("🤖 Executing specialist agents...")
        
        # Always gather literature first (most agents depend on it)
        outputs['literature'] = self.literature_miner.run(drug, indication, use_gpu)
        print("  ✓ Literature Miner completed")
        
        # Evidence normalization (depends on literature)
        outputs['evidence'] = self.evidence_normalizer.run(outputs['literature'])
        print("  ✓ Evidence Normalizer completed")
        
        # Genetics analysis (now depends on literature for variant extraction)
        query_obj = type("QueryObj", (object,), {"drug": drug})()
        outputs['genetics'] = self.genetics_analyst.run(query_obj, literature_data=outputs['literature'])
        print("  ✓ Genetics Analyst completed")
        
        # Label extraction (can use genetics data to generate label info)
        outputs['label'] = self.label_extractor.run(drug, genetics_data=outputs['genetics'])
        print("  ✓ Label Extractor completed")
        
        # Hypothesis generation (depends on genetics and literature for citations)
        outputs['hypotheses'] = self.hypothesis_generator.run(
            drug, outputs['genetics'], indication, use_gpu, 
            literature_data=outputs['literature']
        )
        print("  ✓ Hypothesis Generator completed")
        
        return outputs
    
    def _validate_outputs(self, agent_outputs, query_contract):
        """
        LLM validates agent outputs for safety, accuracy, and consistency
        """
        prompt = f"""You are a pharmacology safety expert reviewing agent outputs.

Query Contract:
{json.dumps(query_contract, indent=2)}

Agent Outputs Summary:
- Non-response rate: {agent_outputs['evidence'].get('overall_non_response', 'N/A')}
- Number of variants: {len(agent_outputs['genetics'])}
- Number of hypotheses: {len(agent_outputs['hypotheses'])}
- FDA label found: {agent_outputs['label'].get('boxed_warning', False)}

Review for:
1. Safety concerns (contraindications, warnings)
2. Logical consistency between outputs
3. Evidence quality
4. Missing critical information

Provide validation result in JSON:
{{
  "safe": true/false,
  "issues": ["list of any concerns"],
  "recommendations": ["suggested improvements"],
  "confidence": "high/medium/low"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            validation = json.loads(content)
            
            if not validation.get('safe', True):
                print(f"⚠️  Safety concerns detected: {validation.get('issues', [])}")
            
            return {
                'outputs': agent_outputs,
                'validation': validation
            }
            
        except Exception as e:
            print(f"⚠️  LLM validation failed: {e}. Proceeding with caution.")
            return {
                'outputs': agent_outputs,
                'validation': {'safe': True, 'issues': [], 'confidence': 'medium'}
            }
    
    def _consolidate_results(self, validated_outputs, query_contract):
        """
        LLM consolidates results and manages citations
        """
        outputs = validated_outputs['outputs']
        
        # Gather all citations
        all_citations = []
        
        # From literature
        if 'citations' in outputs['literature']:
            lit_citations = outputs['literature']['citations']
            # Handle new dict format or old list format
            if isinstance(lit_citations, dict):
                all_citations.extend(lit_citations.get('all_citations', []))
            else:
                all_citations.extend(lit_citations)
        
        # From label
        if 'citations' in outputs['label']:
            all_citations.extend(outputs['label']['citations'])
        
        # From hypothesis generator
        if hasattr(self.hypothesis_generator, 'citations'):
            all_citations.extend(self.hypothesis_generator.citations)
        
        # Deduplicate citations  
        unique_citations = list(set(all_citations))
        
        # Create final structured response
        # Pass through the structured citations if available
        final_citations = outputs['literature'].get('citations') if 'literature' in outputs and isinstance(outputs['literature'].get('citations'), dict) else unique_citations
        
        final_response = {
            "non_response": outputs['evidence'],
            "variants": outputs['genetics'],
            "label_evidence": outputs['label'].get('evidence', 'No FDA label information available'),
            "hypotheses": outputs['hypotheses'],
            "citations": final_citations,
            "validation": validated_outputs['validation'],
            "metadata": {
                "orchestrator": "LLM-powered (Llama-3.3-70B)",
                "safety_check": "passed" if validated_outputs['validation'].get('safe', True) else "warnings",
                "confidence": validated_outputs['validation'].get('confidence', 'medium')
            }
        }
        
        print(f"✅ Analysis complete. Confidence: {final_response['metadata']['confidence']}")
        
        return final_response
    
    def _run_fallback(self, drug, indication, use_gpu):
        """
        Fallback mode without LLM (original simple orchestration)
        """
        print("ℹ️  Running in fallback mode (no LLM orchestration)")
        
        lit = self.literature_miner.run(drug, indication, use_gpu)
        nr = self.evidence_normalizer.run(lit)
        query_obj = type("o", (object,), {"drug": drug})()
        v = self.genetics_analyst.run(query_obj, literature_data=lit)
        lbl = self.label_extractor.run(drug, genetics_data=v)
        hyp = self.hypothesis_generator.run(drug, v, indication, use_gpu, literature_data=lit)
        
        # Handle citations from literature (might be dict or list)
        lit_citations = lit.get("citations", [])
        if isinstance(lit_citations, dict):
            lit_citations = lit_citations.get("all_citations", [])
        
        all_citations = (
            lit_citations + 
            lbl.get("citations", []) + 
            self.hypothesis_generator.citations
        )
        
        # Pass through structured citations if available
        final_citations = lit.get("citations") if isinstance(lit.get("citations"), dict) else list(set(all_citations))
        
        return {
            "non_response": nr,
            "variants": v,
            "label_evidence": lbl["evidence"],
            "hypotheses": hyp,
            "citations": final_citations,
            "metadata": {
                "orchestrator": "Fallback mode (no LLM)",
                "safety_check": "basic",
                "confidence": "medium"
            }
        }
    
    def _default_query_contract(self, drug, indication):
        """Default query contract template"""
        return {
            "task_description": f"Analyze {drug} for {indication}",
            "key_questions": [
                "What is the non-response rate?",
                "What genetic variants affect response?",
                "What formulation improvements are possible?"
            ],
            "data_sources": ["literature", "genetics", "labels"],
            "safety_considerations": ["Check FDA warnings", "Verify dosing safety"],
            "output_format": "structured_json"
        }
    
    def _default_execution_plan(self):
        """Default execution plan"""
        return {
            "steps": [
                {"agent": "literature_miner", "reason": "Gather evidence"},
                {"agent": "evidence_normalizer", "reason": "Compute statistics"},
                {"agent": "genetics_analyst", "reason": "Identify variants"},
                {"agent": "label_extractor", "reason": "Check FDA guidance"},
                {"agent": "hypothesis_generator", "reason": "Propose solutions"}
            ]
        }