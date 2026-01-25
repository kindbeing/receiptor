import { useState } from 'react';
import type { MatchCandidate, VendorMatchResult } from '../types/invoice';
import './VendorMatcher.css';

interface VendorMatcherProps {
  invoiceId: string;
  onMatchComplete?: () => void;
}

export function VendorMatcher({ invoiceId, onMatchComplete }: VendorMatcherProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [matchResult, setMatchResult] = useState<VendorMatchResult | null>(null);

  const handleMatch = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`http://localhost:8000/api/invoices/${invoiceId}/match-vendor`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to match vendor');
      }

      const result: VendorMatchResult = await response.json();
      setMatchResult(result);

      if (onMatchComplete) {
        onMatchComplete();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceClass = (score: number): string => {
    if (score >= 90) return 'confidence-high';
    if (score >= 85) return 'confidence-auto';
    if (score >= 70) return 'confidence-review';
    return 'confidence-low';
  };

  const getConfidenceLabel = (level: string): string => {
    switch (level) {
      case 'high':
        return 'High Confidence';
      case 'auto_approve':
        return 'Auto-Approve';
      case 'review':
        return 'Needs Review';
      case 'low':
        return 'Low Confidence';
      default:
        return level;
    }
  };

  return (
    <div className="vendor-matcher">
      <div className="vendor-matcher-header">
        <h3>Vendor Matching</h3>
        <button
          onClick={handleMatch}
          disabled={loading}
          className="btn-match"
        >
          {loading ? 'Matching...' : matchResult ? 'Re-Match Vendor' : 'Match Vendor'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {matchResult && (
        <div className="match-results">
          <div className="extracted-vendor">
            <label>Extracted Vendor Name:</label>
            <div className="vendor-name">{matchResult.extracted_vendor}</div>
          </div>

          <div className="match-status">
            <span className={`status-badge ${matchResult.status}`}>
              {matchResult.status.toUpperCase()}
            </span>
            <span className="status-message">{matchResult.message}</span>
          </div>

          <div className="match-candidates">
            <h4>Match Candidates:</h4>
            {matchResult.matches.length === 0 ? (
              <div className="no-matches">
                <p>No matches found above 70% threshold.</p>
                <button className="btn-add-vendor">Add New Vendor</button>
              </div>
            ) : (
              <div className="candidates-list">
                {matchResult.matches.map((candidate: MatchCandidate, index: number) => (
                  <div
                    key={candidate.subcontractor_id}
                    className={`candidate-card ${getConfidenceClass(candidate.score)} ${index === 0 ? 'top-match' : ''}`}
                  >
                    <div className="candidate-header">
                      <div className="candidate-name">
                        {candidate.subcontractor_name}
                        {index === 0 && <span className="badge-top">Top Match</span>}
                      </div>
                      <div className="candidate-score">
                        <span className="score-value">{candidate.score}%</span>
                      </div>
                    </div>

                    <div className="candidate-body">
                      <div className="confidence-bar">
                        <div
                          className="confidence-fill"
                          style={{ width: `${candidate.score}%` }}
                        />
                      </div>

                      <div className="confidence-label">
                        {getConfidenceLabel(candidate.confidence_level)}
                      </div>

                      {candidate.contact_info && (
                        <div className="contact-info">
                          {candidate.contact_info.phone && (
                            <span>📞 {candidate.contact_info.phone}</span>
                          )}
                          {candidate.contact_info.email && (
                            <span>✉️ {candidate.contact_info.email}</span>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="candidate-actions">
                      <button className="btn-select">Select This Match</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {matchResult.matches.length > 0 && matchResult.matches[0].score < 85 && (
            <div className="alternative-actions">
              <button className="btn-add-vendor">None of these - Add New Vendor</button>
            </div>
          )}
        </div>
      )}

      {!matchResult && !loading && (
        <div className="match-placeholder">
          <p>Click "Match Vendor" to find matching subcontractors</p>
        </div>
      )}
    </div>
  );
}

