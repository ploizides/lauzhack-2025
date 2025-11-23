import React, { useEffect, useRef } from 'react';
import { formatTimestamp, extractDomain } from '../utils/formatters';

const FactCheckPanel = ({ factChecks, factVerdicts }) => {
  const scrollRef = useRef(null);
  const prevLengthRef = useRef(0);

  // Auto-scroll to latest fact only when NEW facts are added
  useEffect(() => {
    if (scrollRef.current && factChecks.length > prevLengthRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      prevLengthRef.current = factChecks.length;
    }
  }, [factChecks]);

  const renderFactItem = (fact, index) => {
    const verdictClass = fact.verdict.toLowerCase();
    const verdictLabel =
      fact.verdict.charAt(0) + fact.verdict.slice(1).toLowerCase();

    return (
      <div key={`${fact.timestamp}-${index}`} className={`fact-item ${verdictClass}`}>
        {/* Header with verdict badge and timestamp */}
        <div className="fact-header">
          <div className={`verdict-dot ${verdictClass}`}></div>
          <div className="verdict-label">{verdictLabel}</div>
          <div className="fact-timestamp">{formatTimestamp(fact.timestamp)}</div>
        </div>

        {/* Claim - the main statement being checked */}
        <div className="fact-claim">"{fact.claim}"</div>

        {/* Explanation - why this verdict was given */}
        {fact.explanation && (
          <div className="fact-explanation">
            <strong>Explanation:</strong> {fact.explanation}
          </div>
        )}

        {/* Key Facts - supporting bullet points */}
        {fact.key_facts && fact.key_facts.length > 0 && (
          <div className="fact-key-facts">
            <strong>Key Facts:</strong>
            <ul>
              {fact.key_facts.map((keyFact, idx) => (
                <li key={idx}>{keyFact}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Sources */}
        <div className="fact-sources">
          <strong>Sources:</strong>{' '}
          {fact.evidence_sources && fact.evidence_sources.length > 0 ? (
            fact.evidence_sources.slice(0, 3).map((source, idx) => (
              <span key={idx}>
                {idx > 0 && ', '}
                <a href={source} target="_blank" rel="noopener noreferrer">
                  {extractDomain(source)}
                </a>
              </span>
            ))
          ) : (
            <span>No sources available</span>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="factcheck-container">
      <div className="factcheck-header">FACT-CHECK</div>

      <div className="factcheck-stats">
        <div className="stat-item">
          <div className="stat-dot supported"></div>
          <span>
            Supported: <strong>{factVerdicts.SUPPORTED || 0}</strong>
          </span>
        </div>
        <div className="stat-item">
          <div className="stat-dot uncertain"></div>
          <span>
            Uncertain: <strong>{factVerdicts.UNCERTAIN || 0}</strong>
          </span>
        </div>
        <div className="stat-item">
          <div className="stat-dot contradicted"></div>
          <span>
            Contradicted: <strong>{factVerdicts.CONTRADICTED || 0}</strong>
          </span>
        </div>
      </div>

      <div className="factcheck-scroll" ref={scrollRef}>
        {factChecks.length === 0 ? (
          <div className="no-data">No fact-checks yet. Click Start to begin.</div>
        ) : (
          factChecks.map((fact, index) => renderFactItem(fact, index))
        )}
      </div>
    </div>
  );
};

export default FactCheckPanel;
