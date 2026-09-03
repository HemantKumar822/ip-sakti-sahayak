import { Fragment } from 'react';
import './PipelineStepper.css';

interface PipelineStepperProps {
  category?: string;
  jurisdiction?: string;
}

export const PipelineStepper = ({ category, jurisdiction }: PipelineStepperProps) => {
  const steps = [
    { label: "PII Scrubbed", icon: "🔒" },
    { label: category || "Categorized", icon: "🏷️" },
    { label: jurisdiction || "India", icon: "⚖️" },
    { label: "Hybrid Search", icon: "⚡" },
    { label: "Gate Verified", icon: "🛡️" }
  ];

  return (
    <div className="pipeline-stepper animate-fade-in">
      {steps.map((step, idx) => (
        <Fragment key={idx}>
          <div className="stepper-pill completed">
            <span className="stepper-icon">{step.icon}</span>
            <span>{step.label}</span>
          </div>
          {idx < steps.length - 1 && <span className="stepper-separator">➔</span>}
        </Fragment>
      ))}
    </div>
  );
};
