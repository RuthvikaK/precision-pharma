# LLM-Powered Orchestrator Setup Guide

## Overview

The Orchestrator Agent now uses **Llama-3.3-70B-Instruct-Turbo** from Together AI to intelligently coordinate all specialist agents. The model is **completely free** to use through Together AI's free tier.

## What the LLM Does

The orchestrator uses the LLM for:

1. **Query Contract Creation** 📋
   - Analyzes user's drug + indication request
   - Identifies key questions to answer
   - Determines required data sources
   - Flags safety considerations

2. **Execution Planning** 🗺️
   - Decides which agents to invoke
   - Determines optimal execution order
   - Manages dependencies between agents
   - Justifies each decision

3. **Output Validation** ✅
   - Reviews all agent outputs for safety
   - Checks logical consistency
   - Assesses evidence quality
   - Identifies missing information

4. **Citation Management** 📚
   - Consolidates citations from all sources
   - Deduplicates references
   - Ensures proper attribution

5. **Final Synthesis** 🎯
   - Creates coherent final response
   - Adds confidence ratings
   - Provides safety status

## Setup Instructions

### Step 1: Get Your Together AI API Key (FREE)

1. Go to [https://api.together.xyz/](https://api.together.xyz/)
2. Sign up for a free account
3. Navigate to Settings → API Keys
4. Create a new API key
5. Copy your key (starts with something like `sk-...`)

**Note:** The Llama-3.3-70B-Instruct-Turbo-Free model has no usage limits!

### Step 2: Install Dependencies

```bash
cd backend
python3 -m pip install together
```

Or install all dependencies:

```bash
python3 -m pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cd backend
cp .env.example .env
```

Edit the `.env` file and add your API key:

```env
TOGETHER_API_KEY=your_actual_api_key_here
```

### Step 4: Restart the Backend Server

```bash
cd backend
python3 -m uvicorn app:app --host 0.0.0.0 --port 5000
```

You should see:
```
✅ Orchestrator initialized with LLM support (Llama-3.3-70B)
```

If the API key is missing, you'll see:
```
⚠️  Warning: TOGETHER_API_KEY not found. Orchestrator will use fallback mode.
```

## How It Works

### Example Workflow for "Clopidogrel"

**User Input:**
```json
{
  "drug": "clopidogrel",
  "indication": "acute coronary syndrome"
}
```

**Step 1: Query Contract (LLM)**
```
📋 Query Contract Created: Analyze clopidogrel for acute coronary syndrome
```

The LLM generates:
```json
{
  "task_description": "Analyze clopidogrel efficacy and non-response...",
  "key_questions": [
    "What is the non-response rate?",
    "Which genetic variants affect response?",
    "What are the safety considerations?",
    "What formulation improvements are possible?"
  ],
  "data_sources": ["PubMed", "genetics_db", "FDA_labels"],
  "safety_considerations": [
    "CYP2C19 boxed warning",
    "Bleeding risk in poor metabolizers"
  ]
}
```

**Step 2: Execution Plan (LLM)**
```
🗺️  Execution Plan: 5 steps
```

The LLM decides:
```json
{
  "steps": [
    {
      "agent": "literature_miner",
      "reason": "Need clinical trial data for non-response rates"
    },
    {
      "agent": "evidence_normalizer",
      "reason": "Compute pooled statistics from studies"
    },
    {
      "agent": "genetics_analyst",
      "reason": "CYP2C19 variants critical for clopidogrel"
    },
    {
      "agent": "label_extractor",
      "reason": "Check FDA boxed warning status"
    },
    {
      "agent": "hypothesis_generator",
      "reason": "Propose alternative strategies for poor metabolizers"
    }
  ]
}
```

**Step 3: Agent Execution**
```
🤖 Executing specialist agents...
  ✓ Literature Miner completed
  ✓ Evidence Normalizer completed
  ✓ Genetics Analyst completed
  ✓ Label Extractor completed
  ✓ Hypothesis Generator completed
```

**Step 4: Safety Validation (LLM)**

The LLM reviews outputs:
```json
{
  "safe": true,
  "issues": [],
  "recommendations": [
    "Consider genetic testing before prescribing",
    "Monitor platelet function in high-risk patients"
  ],
  "confidence": "high"
}
```

**Step 5: Final Consolidation**
```
✅ Analysis complete. Confidence: high
```

## Response Format

With LLM orchestration, the response includes additional metadata:

```json
{
  "non_response": { ... },
  "variants": [ ... ],
  "label_evidence": " ... ",
  "hypotheses": [ ... ],
  "citations": [ ... ],
  
  "validation": {
    "safe": true,
    "issues": [],
    "recommendations": [ ... ],
    "confidence": "high"
  },
  
  "metadata": {
    "orchestrator": "LLM-powered (Llama-3.3-70B)",
    "safety_check": "passed",
    "confidence": "high"
  }
}
```

## Frontend Display

The UI now shows:

- **🤖 Analysis Metadata** section with:
  - Orchestrator type (LLM-powered vs Fallback)
  - Safety check status (passed/warnings)
  - Confidence level (high/medium/low)
  - Validation findings and recommendations

## Fallback Mode

If the API key is not configured, the orchestrator automatically falls back to rule-based coordination:

- Still works perfectly
- No LLM validation
- Simpler orchestration logic
- Metadata shows "Fallback mode"

This ensures the system never breaks due to missing API keys.

## Benefits of LLM Orchestration

### ✅ Intelligent Decision Making
- Adapts execution plan based on drug characteristics
- Identifies which agents are most relevant
- Optimizes execution order

### ✅ Safety Oversight
- Reviews outputs for contraindications
- Checks logical consistency
- Flags potential issues before display

### ✅ Better Citation Management
- Deduplicates references intelligently
- Ensures proper attribution
- Organizes sources coherently

### ✅ Confidence Scoring
- Provides transparency about result quality
- Identifies gaps in evidence
- Suggests areas for improvement

### ✅ Adaptive Behavior
- Different drugs get different workflows
- Complex cases get more thorough validation
- Simple queries remain fast

## Cost

**FREE!** 🎉

- Together AI's Llama-3.3-70B-Instruct-Turbo-Free has no usage limits
- No credit card required for basic tier
- Perfect for research and educational use

## Troubleshooting

### Issue: "TOGETHER_API_KEY not found"

**Solution:** 
1. Create `.env` file in `backend/` directory
2. Add `TOGETHER_API_KEY=your_key_here`
3. Restart the backend server

### Issue: LLM responses are slow

**Solution:**
- Normal first request may take 3-5 seconds
- Subsequent requests are faster (~1-2 seconds)
- Together AI's infrastructure is optimizing

### Issue: JSON parsing errors from LLM

**Solution:**
- The orchestrator has automatic fallbacks
- Retries with template if JSON parsing fails
- System remains functional even with LLM errors

### Issue: Want to disable LLM orchestration

**Solution:**
- Simply remove the `TOGETHER_API_KEY` from `.env`
- System automatically uses fallback mode
- All features still work

## Comparing LLM vs Fallback Mode

| Feature | LLM Mode | Fallback Mode |
|---------|----------|---------------|
| Execution Planning | ✅ Adaptive | ⚪ Fixed |
| Safety Validation | ✅ LLM Review | ⚪ Basic |
| Citation Management | ✅ Intelligent | ⚪ Simple concat |
| Confidence Scoring | ✅ Detailed | ⚪ Medium default |
| Query Understanding | ✅ Deep analysis | ⚪ Direct parsing |
| Cost | 🆓 Free | 🆓 Free |
| Latency | ~2-4 seconds | <1 second |
| API Key Required | ✅ Yes | ❌ No |

## Example Logs

**With LLM:**
```
📋 Query Contract Created: Analyze clopidogrel for acute coronary syndrome
🗺️  Execution Plan: 5 steps
🤖 Executing specialist agents...
  ✓ Literature Miner completed
  ✓ Evidence Normalizer completed
  ✓ Genetics Analyst completed
  ✓ Label Extractor completed
  ✓ Hypothesis Generator completed
✅ Analysis complete. Confidence: high
```

**Fallback Mode:**
```
ℹ️  Running in fallback mode (no LLM orchestration)
```

## Advanced: Customizing LLM Behavior

You can modify the orchestrator's prompts in `backend/agents/orchestrator.py`:

- `_create_query_contract()` - Adjust contract creation
- `_create_execution_plan()` - Change planning logic
- `_validate_outputs()` - Customize validation criteria
- `temperature` parameter (line 44) - Control creativity (0.0-1.0)

## Security Notes

- ✅ API key stored in `.env` (not committed to Git)
- ✅ `.env` is in `.gitignore` by default
- ✅ No PHI/PII sent to Together AI (only drug names and indications)
- ✅ All patient data stays local

## Next Steps

1. Get your Together AI API key
2. Add to `.env` file
3. Restart backend
4. Test with "clopidogrel + acute coronary syndrome"
5. Check the metadata section in results

The LLM-powered orchestrator makes the system more intelligent, safer, and more transparent!
