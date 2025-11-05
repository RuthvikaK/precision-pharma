"""
Test script to demonstrate bioBERT extraction on sample abstracts
"""
from agents.biomedical_extractor import get_extractor

# Sample abstracts with explicit efficacy data
test_abstracts = [
    {
        "title": "Clopidogrel efficacy in ACS patients",
        "abstract": """
        In a randomized trial of 2,000 patients with acute coronary syndrome,
        clopidogrel showed a 72% overall response rate. Among CYP2C19 extensive
        metabolizers, the response rate was 85%, compared to only 55% in poor
        metabolizers (p<0.001). Non-response was observed in 28% of patients overall.
        """,
        "pmid": "TEST001",
        "expected": {
            "response_rate": 0.72,
            "non_response_rate": 0.28,
            "sample_size": 2000
        }
    },
    {
        "title": "Warfarin pharmacogenetics study",
        "abstract": """
        We studied 1,500 participants on warfarin therapy. The overall efficacy rate
        was 68%. VKORC1 variants were associated with differential response, with
        wild-type patients showing 78% response vs 45% in variant carriers (p=0.002).
        """,
        "pmid": "TEST002",
        "expected": {
            "response_rate": 0.68,
            "sample_size": 1500
        }
    },
    {
        "title": "Metformin in type 2 diabetes",
        "abstract": """
        A cohort of 3,200 type 2 diabetes patients received metformin for 12 months.
        Treatment failure occurred in 22% of patients. The remaining 78% achieved
        adequate glycemic control (HbA1c <7%).
        """,
        "pmid": "TEST003",
        "expected": {
            "response_rate": 0.78,
            "non_response_rate": 0.22,
            "sample_size": 3200
        }
    }
]

def test_extraction():
    """Test bioBERT extraction on sample abstracts"""
    print("=" * 80)
    print("bioBERT Extraction Test")
    print("=" * 80)
    
    # Get extractor
    extractor = get_extractor(use_model=True)
    
    print(f"\n✓ Extractor loaded (using model: {extractor.use_model})")
    print(f"✓ Extraction method: {'bioBERT+regex' if extractor.use_model else 'regex-only'}\n")
    
    # Test each abstract
    successes = 0
    total = len(test_abstracts)
    
    for i, test in enumerate(test_abstracts, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{total}: {test['title']}")
        print(f"{'='*80}")
        
        # Extract data
        extracted = extractor.extract_from_abstract(
            test['abstract'],
            test['title']
        )
        
        # Display results
        print("\n📊 Extracted Data:")
        print(f"  Response Rate: {extracted.get('response_rate', 'NOT FOUND')}")
        print(f"  Non-Response Rate: {extracted.get('non_response_rate', 'NOT FOUND')}")
        print(f"  Sample Size: {extracted.get('sample_size', 'NOT FOUND')}")
        print(f"  P-Value: {extracted.get('p_value', 'NOT FOUND')}")
        print(f"  Extraction Method: {extracted.get('extraction_method', 'unknown')}")
        
        # Compare with expected
        expected = test['expected']
        print("\n✓ Expected Data:")
        for key, value in expected.items():
            print(f"  {key}: {value}")
        
        # Check accuracy
        print("\n🎯 Accuracy:")
        all_correct = True
        for key, expected_value in expected.items():
            extracted_value = extracted.get(key)
            if extracted_value is not None:
                # Allow small floating point differences
                if isinstance(expected_value, float):
                    correct = abs(extracted_value - expected_value) < 0.01
                else:
                    correct = extracted_value == expected_value
                
                status = "✅ CORRECT" if correct else "❌ WRONG"
                print(f"  {key}: {status} (got {extracted_value}, expected {expected_value})")
                
                if correct:
                    successes += 0.33  # Partial success per field
            else:
                print(f"  {key}: ⚠️  NOT EXTRACTED")
                all_correct = False
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    accuracy = (successes / (total * 3)) * 100  # 3 fields per test
    print(f"Overall Extraction Success: {accuracy:.1f}%")
    
    if accuracy >= 70:
        print("✅ bioBERT extraction is working well!")
    elif accuracy >= 40:
        print("⚠️  bioBERT extraction is partially working (regex fallback active)")
    else:
        print("❌ bioBERT extraction needs improvement")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    test_extraction()
