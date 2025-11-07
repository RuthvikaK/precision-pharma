import React, { useState, useEffect } from "react";
import { analyzeDrug, checkGpuStatus } from "./api";

export default function App() {
  const [drug, setDrug] = useState("");
  const [indication, setIndication] = useState("");
  const [gpu, setGpu] = useState(true);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState("");

  useEffect(() => {
    checkGpuStatus().then(status => {
      if (status.status !== "online") setGpu(false);
    });
  }, []);

  // Simulate progress with realistic agent steps
  useEffect(() => {
    if (!loading) {
      setProgress(0);
      setCurrentStep("");
      return;
    }

    const steps = [
      { progress: 15, step: "🔍 Searching PubMed and literature databases...", duration: 3000 },
      { progress: 30, step: "🌐 Fetching full-text articles from Europe PMC...", duration: 4000 },
      { progress: 50, step: "🔬 Extracting efficacy data with bioBERT...", duration: 5000 },
      { progress: 65, step: "🧬 Analyzing genetic variants...", duration: 3000 },
      { progress: 80, step: "💊 Generating formulation hypotheses...", duration: 2000 },
      { progress: 95, step: "✅ Finalizing analysis...", duration: 2000 }
    ];

    let currentStepIndex = 0;
    let timer;

    const updateProgress = () => {
      if (currentStepIndex < steps.length && loading) {
        const { progress: prog, step, duration } = steps[currentStepIndex];
        setProgress(prog);
        setCurrentStep(step);
        currentStepIndex++;
        timer = setTimeout(updateProgress, duration);
      }
    };

    updateProgress();

    return () => clearTimeout(timer);
  }, [loading]);

  async function handleAnalyze() {
    if (!drug || !indication) {
      setError("Please enter both drug and indication");
      return;
    }
    
    setLoading(true);
    setError(null);
    setProgress(0);
    setCurrentStep("🚀 Initializing analysis...");
    
    try {
      const data = await analyzeDrug(drug, indication, gpu);
      setProgress(100);
      setCurrentStep("✅ Complete!");
      setTimeout(() => {
        setResult(data);
        setLoading(false);
      }, 500);
    } catch (err) {
      setError("Analysis failed: " + err.message);
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <header>
        <h1>🧬 Precision Pharmacology</h1>
        <p className="subtitle">Drug Non-Response Analysis & Formulation Recommendations</p>
      </header>

      <div className="search-panel">
        <div className="input-group">
          <input 
            value={drug} 
            onChange={e => setDrug(e.target.value)}
            placeholder="Drug name (e.g., clopidogrel)"
            className="input-field"
          />
          <input 
            value={indication} 
            onChange={e => setIndication(e.target.value)}
            placeholder="Indication (e.g., acute coronary syndrome)"
            className="input-field"
          />
          <button onClick={handleAnalyze} disabled={loading} className="analyze-btn">
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>
        {error && <div className="error">{error}</div>}
      </div>

      {/* Progress Bar */}
      {loading && (
        <div className="progress-container">
          <div className="progress-header">
            <h3 style={{ margin: 0, fontSize: '1.2rem' }}>Analyzing {drug}...</h3>
            <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#ee5a6f' }}>
              {progress}%
            </span>
          </div>
          
          <div className="progress-bar-wrapper">
            <div 
              className="progress-bar-fill" 
              style={{ 
                width: `${progress}%`,
                transition: 'width 0.5s ease-in-out'
              }}
            />
          </div>
          
          <div className="progress-step">
            {currentStep}
          </div>
          
          <div className="progress-info">
            <p style={{ fontSize: '0.9rem', color: '#6c757d', marginTop: '1rem' }}>
              ⏱️ Estimated time: ~20-30 seconds
            </p>
            <p style={{ fontSize: '0.85rem', color: '#6c757d', fontStyle: 'italic' }}>
              Searching multiple databases and analyzing with AI models...
            </p>
          </div>
        </div>
      )}

      {result && !loading && (
        <div className="results">
          <section className="result-section">
            <h2>📊 Non-Response Analysis</h2>
            <div className="stat-grid">
              <div className="stat-card">
                <div className="stat-label">Overall Non-Response Rate</div>
                <div className="stat-value">
                  {result.non_response.overall_non_response !== null 
                    ? `${(result.non_response.overall_non_response * 100).toFixed(1)}%`
                    : 'N/A'}
                </div>
                <div className="stat-ci">
                  {result.non_response.ci_lower !== null && result.non_response.ci_upper !== null
                    ? `95% CI: ${(result.non_response.ci_lower * 100).toFixed(1)}% - ${(result.non_response.ci_upper * 100).toFixed(1)}%`
                    : 'No data available'}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Studies Analyzed</div>
                <div className="stat-value">{result.non_response.n_studies}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Heterogeneity</div>
                <div className="stat-value">{result.non_response.heterogeneity}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Evidence Quality</div>
                <div className="stat-value">{result.non_response.quality}</div>
              </div>
            </div>

            {result.non_response.n_studies === 0 && result.non_response.message && (
              <div style={{
                padding: '1rem',
                margin: '1rem 0',
                backgroundColor: '#fff3cd',
                border: '1px solid #ffc107',
                borderRadius: '8px',
                color: '#856404'
              }}>
                ⚠️ {result.non_response.message}
              </div>
            )}

            {result.non_response.subgroups && result.non_response.subgroups.length > 0 && (
              <div className="subgroups">
                <h3>Subgroup Analysis</h3>
                {result.non_response.subgroups.map((sg, idx) => (
                  <div key={idx} className="subgroup-card">
                    <strong>{sg.name}</strong>
                    <div>Non-response: {(sg.non_response_rate * 100).toFixed(1)}% 
                      (95% CI: {(sg.ci_lower * 100).toFixed(1)}%-{(sg.ci_upper * 100).toFixed(1)}%)</div>
                    <div>Prevalence: {(sg.prevalence * 100).toFixed(0)}%</div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="result-section">
            <h2>🧬 Genetic Variants</h2>
            {result.variants && result.variants.length > 0 ? (
              <div className="variant-table">
                {result.variants.map((v, idx) => (
                <div key={idx} className="variant-card">
                  <div className="variant-header">
                    <strong>{v.gene}</strong>
                    <span className="rsid">{v.rsid}</span>
                  </div>
                  <div className="variant-details">
                    <div><strong>Allele:</strong> {v.allele}</div>
                    <div><strong>Effect:</strong> {v.effect}</div>
                    <div><strong>Impact:</strong> {v.clinical_impact}</div>
                    <div><strong>Mechanism:</strong> {v.mechanism}</div>
                    {v.frequency_by_ancestry && Object.keys(v.frequency_by_ancestry).length > 0 && (
                      <div className="frequencies">
                        <strong>Frequency by ancestry:</strong>
                        <div className="freq-grid">
                          {Object.entries(v.frequency_by_ancestry).map(([pop, freq]) => (
                            <div key={pop} className="freq-item">
                              {pop}: {(freq * 100).toFixed(0)}%
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                ))}
              </div>
            ) : (
              <div style={{
                padding: '2rem',
                textAlign: 'center',
                backgroundColor: '#f8f9fa',
                borderRadius: '8px',
                color: '#6c757d'
              }}>
                <p>No genetic variants found for this drug.</p>
                <p style={{fontSize: '0.9rem', marginTop: '0.5rem'}}>
                  Check PharmGKB directly or verify drug name spelling.
                </p>
              </div>
            )}
          </section>

          <section className="result-section">
            <h2>💊 Formulation & Dosing Hypotheses</h2>
            {result.hypotheses && result.hypotheses.length > 0 ? (
              <div className="hypotheses">
                {result.hypotheses.map((h, idx) => (
                <div 
                  key={idx} 
                  className="hypothesis-card"
                  style={h.alternative_drug ? {
                    borderLeft: '5px solid #ff6b6b',
                    backgroundColor: '#fff5f5'
                  } : {}}
                >
                  <h3 style={h.alternative_drug ? { color: '#ff6b6b' } : {}}>
                    {h.alternative_drug && '🔄 '}
                    {idx + 1}. {h.hypothesis}
                    {h.alternative_drug && ' ⭐'}
                  </h3>
                  {h.alternative_drug && (
                    <div style={{
                      backgroundColor: '#ff6b6b',
                      color: 'white',
                      padding: '0.5rem 1rem',
                      borderRadius: '4px',
                      marginBottom: '1rem',
                      fontSize: '0.9rem',
                      fontWeight: 'bold'
                    }}>
                      🔄 ALTERNATIVE DRUG RECOMMENDATION - May work better for poor metabolizers
                    </div>
                  )}
                  <div className="hypothesis-content">
                    <div><strong>Rationale:</strong> {h.rationale}</div>
                    <div><strong>Implementation:</strong> {h.implementation}</div>
                    <div><strong>Target Subgroup:</strong> {h.target_subgroup}</div>
                    <div><strong>Expected Improvement:</strong> {h.expected_improvement}</div>
                    {h.evidence_level && <div><strong>Evidence Level:</strong> {h.evidence_level}</div>}
                    {h.safety_note && <div className="safety-note"><strong>⚠️ Safety Note:</strong> {h.safety_note}</div>}
                    {h.development_status && <div><strong>Development Status:</strong> {h.development_status}</div>}
                    {h.citation && (
                      <div style={{ 
                        marginTop: '0.75rem', 
                        padding: '0.5rem', 
                        backgroundColor: '#f8f9fa', 
                        borderRadius: '4px',
                        fontSize: '0.9rem'
                      }}>
                        <strong>📖 Evidence:</strong> {h.citation}
                      </div>
                    )}
                  </div>
                </div>
                ))}
              </div>
            ) : (
              <div style={{
                padding: '2rem',
                textAlign: 'center',
                backgroundColor: '#f8f9fa',
                borderRadius: '8px',
                color: '#6c757d'
              }}>
                <p>No formulation hypotheses available.</p>
                <p style={{fontSize: '0.9rem', marginTop: '0.5rem'}}>
                  Requires genetic variant data to generate hypotheses.
                </p>
              </div>
            )}
          </section>

          <section className="result-section">
            <h2>📚 Citations</h2>
            
            {/* Studies with extractable data */}
            {result.citations && result.citations.studies_with_data && result.citations.studies_with_data.length > 0 && (
              <div style={{ marginBottom: '2rem' }}>
                <h3 style={{ 
                  color: '#28a745', 
                  fontSize: '1.1rem', 
                  marginBottom: '1rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  ✅ Studies With Extractable Data ({result.citations.studies_with_data.length})
                </h3>
                <div className="citations">
                  {result.citations.studies_with_data.map((citation, idx) => (
                    <div key={idx} className="citation-item" style={{
                      backgroundColor: '#f0fff4',
                      borderLeft: '4px solid #28a745'
                    }}>
                      {idx + 1}. {citation}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Additional references without data */}
            {result.citations && result.citations.additional_references && result.citations.additional_references.length > 0 && (
              <div>
                <h3 style={{ 
                  color: '#6c757d', 
                  fontSize: '1.1rem', 
                  marginBottom: '1rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  📚 Additional References ({result.citations.additional_references.length})
                </h3>
                <p style={{
                  fontSize: '0.9rem',
                  color: '#6c757d',
                  marginBottom: '1rem',
                  fontStyle: 'italic'
                }}>
                  These papers are relevant but lack specific efficacy percentages in their abstracts.
                </p>
                <div className="citations">
                  {result.citations.additional_references.map((citation, idx) => (
                    <div key={idx} className="citation-item" style={{
                      backgroundColor: '#f8f9fa',
                      borderLeft: '4px solid #6c757d'
                    }}>
                      {idx + 1}. {citation}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* No citations at all */}
            {(!result.citations || 
              (!result.citations.studies_with_data?.length && !result.citations.additional_references?.length)) && (
              <div style={{
                padding: '2rem',
                textAlign: 'center',
                backgroundColor: '#f8f9fa',
                borderRadius: '8px',
                color: '#6c757d'
              }}>
                <p>No citations available.</p>
              </div>
            )}
          </section>

          {result.label_evidence && (
            <section className="result-section">
              <h2>📋 FDA Label Information</h2>
              <div className="label-info">
                {result.label_evidence}
              </div>
            </section>
          )}

          {result.metadata && (
            <section className="result-section">
              <h2>🤖 Analysis Metadata</h2>
              <div className="metadata-grid">
                <div className="metadata-item">
                  <strong>Orchestrator:</strong> {result.metadata.orchestrator}
                </div>
                <div className="metadata-item">
                  <strong>Safety Check:</strong> 
                  <span className={`status-badge ${result.metadata.safety_check}`}>
                    {result.metadata.safety_check}
                  </span>
                </div>
                <div className="metadata-item">
                  <strong>Confidence:</strong> 
                  <span className={`confidence-badge ${result.metadata.confidence}`}>
                    {result.metadata.confidence}
                  </span>
                </div>
              </div>
              
              {result.validation && result.validation.issues && result.validation.issues.length > 0 && (
                <div className="validation-issues">
                  <h4>⚠️ Validation Findings:</h4>
                  <ul>
                    {result.validation.issues.map((issue, idx) => (
                      <li key={idx}>{issue}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {result.validation && result.validation.recommendations && result.validation.recommendations.length > 0 && (
                <div className="validation-recommendations">
                  <h4>💡 Recommendations:</h4>
                  <ul>
                    {result.validation.recommendations.map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </section>
          )}
        </div>
      )}
    </div>
  );
}