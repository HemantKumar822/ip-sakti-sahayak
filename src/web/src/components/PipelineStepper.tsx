interface PipelineStepperProps {
  category?: string;
  jurisdiction?: string;
}

export const PipelineStepper = ({ category, jurisdiction }: PipelineStepperProps) => {
  const steps = ['PII scrubbed', category || 'Classified', jurisdiction || 'India routed', 'Hybrid retrieval', 'Gate verified'];
  return (
    <ol className="sk-stage-list animate-fade-in" aria-label="Pipeline stages completed">
      {steps.map((s) => (
        <li key={s} className="sk-stage">
          <span className="sk-stage-dot" aria-hidden="true" />
          <span>{s}</span>
        </li>
      ))}
    </ol>
  );
};
