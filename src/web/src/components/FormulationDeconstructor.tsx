import React, { useState } from 'react';
import { ChevronDown, FlaskConical, RotateCcw, ArrowRight } from 'lucide-react';

interface FormulationDeconstructorProps {
  onSubmitDeconstruction: (syntheticQuery: string) => void;
  isLoading?: boolean;
}

export const FormulationDeconstructor: React.FC<FormulationDeconstructorProps> = ({
  onSubmitDeconstruction,
  isLoading = false,
}) => {
  const [open, setOpen] = useState(false);
  const [botanicals, setBotanicals] = useState('');
  const [extractionMethod, setExtractionMethod] = useState('');
  const [synergyClaim, setSynergyClaim] = useState('');
  const [isDomestic, setIsDomestic] = useState(true);
  const [harvestLocation, setHarvestLocation] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!botanicals.trim()) return;
    onSubmitDeconstruction(
      `ASU FORMULATION DECONSTRUCTION & PATENT CLEARANCE:\n1. Botanical Constituents: ${botanicals.trim()}\n2. Novel Extraction Process: ${extractionMethod.trim() || 'Standard aqueous/hydroalcoholic extraction'}\n3. Synergistic Therapeutic Claim: ${synergyClaim.trim() || 'Claimed therapeutic enhancement'}\n4. Biological Source: ${isDomestic ? `Biological resources sourced from ${harvestLocation.trim() || 'India'}` : 'Non-Indian / synthetic source'}\n\nSTATUTORY ANALYSIS REQUIRED:\n- Patents Act 1970 S. 3(p): classical prior-art clearance.\n- Patents Act 1970 S. 3(e): synergistic efficacy beyond mere admixture.\n- Biological Diversity Act 2002 S. 6 & Form I: prior approval requirements.`
    );
  };

  const handleClear = () => {
    setBotanicals('');
    setExtractionMethod('');
    setSynergyClaim('');
    setHarvestLocation('');
    setIsDomestic(true);
  };

  return (
    <div className="sk-disc">
      <button type="button" className="sk-disc-head" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
          <FlaskConical size={15} aria-hidden="true" style={{ color: 'var(--accent-sunset)' }} />
          <span>Break down a formulation instead</span>
        </span>
        <ChevronDown size={15} aria-hidden="true" style={{ transform: open ? 'rotate(180deg)' : undefined, color: 'var(--mute)' }} />
      </button>
      {open && (
        <div className="sk-disc-body">
          <p className="sk-small" style={{ margin: 0 }}>
            Four fields produce a sharper clearance check than a free-text question: what it
            contains, how it is made, why it is better, and where the material comes from.
          </p>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
            <div className="sk-field">
              <label className="sk-label" htmlFor="sk-dec-botanicals">
                Botanicals — scientific + classical names
              </label>
              <input
                id="sk-dec-botanicals"
                className="sk-input"
                type="text"
                value={botanicals}
                onChange={(e) => setBotanicals(e.target.value)}
                placeholder="Withania somnifera (Ashwagandha), Curcuma longa (Haridra)"
                required
              />
            </div>
            <div className="sk-field">
              <label className="sk-label" htmlFor="sk-dec-process">
                Process — what is novel about making it
              </label>
              <input
                id="sk-dec-process"
                className="sk-input"
                type="text"
                value={extractionMethod}
                onChange={(e) => setExtractionMethod(e.target.value)}
                placeholder="Supercritical CO2 fraction at 45°C, standardised isolate"
              />
            </div>
            <div className="sk-field">
              <label className="sk-label" htmlFor="sk-dec-synergy">
                Efficacy — the Section 3(e) argument
              </label>
              <textarea
                id="sk-dec-synergy"
                className="sk-textarea"
                rows={2}
                value={synergyClaim}
                onChange={(e) => setSynergyClaim(e.target.value)}
                placeholder="Quantified improvement over individual components…"
              />
            </div>
            <div className="sk-field">
              <label className="sk-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Indian biological resource?</span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--space-xs)', textTransform: 'none', letterSpacing: 'normal', fontFamily: 'var(--font-sans)', fontSize: '13px', color: 'var(--body)' }}>
                  <input
                    type="checkbox"
                    checked={isDomestic}
                    onChange={(e) => setIsDomestic(e.target.checked)}
                    aria-label="Biological material sourced in India"
                  />
                  Sourced in India
                </span>
              </label>
              {isDomestic && (
                <input
                  className="sk-input"
                  type="text"
                  value={harvestLocation}
                  onChange={(e) => setHarvestLocation(e.target.value)}
                  placeholder="Collection region, e.g. Western Ghats, Karnataka"
                  aria-label="Collection region"
                />
              )}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button type="button" className="sk-btn sk-btn-quiet sk-btn-sm" onClick={handleClear}>
                <RotateCcw size={13} aria-hidden="true" />
                <span>Clear</span>
              </button>
              <button type="submit" className="sk-btn sk-btn-primary sk-btn-sm" disabled={isLoading || !botanicals.trim()}>
                <span>{isLoading ? 'Screening…' : 'Run clearance check'}</span>
                <ArrowRight size={14} aria-hidden="true" />
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
