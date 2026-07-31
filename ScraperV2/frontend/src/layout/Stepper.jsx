import * as React from 'react';
import Box from '@mui/material/Box';
import CheckCircleRoundedIcon from '@mui/icons-material/CheckCircleRounded';
import RadioButtonUncheckedRoundedIcon from '@mui/icons-material/RadioButtonUncheckedRounded';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import Stepper from '@mui/material/Stepper';
import Typography from '@mui/material/Typography';

import { PaperIdentifierInput } from '../components/PaperIdentifierInput';
import {
  primaryActionClassName,
  secondaryActionClassName,
} from '../styles/actionClasses';
import { stepperPanelClassName } from '../styles/layoutClasses';

const steps = ['Identifiers', 'Fetch sources', 'Review outputs'];

function EmptyStepPanel() {
  return (
    <div
      aria-hidden="true"
      className={stepperPanelClassName}
    />
  );
}

function ExtractionStepIcon(props) {
  const { completed, className } = props;

  if (completed) {
    return <CheckCircleRoundedIcon className={className} sx={{ fontSize: 23, color: 'primary.main' }} />;
  }

  return (
    <RadioButtonUncheckedRoundedIcon
      className={className}
      sx={{ fontSize: 23, color: 'rgba(255, 255, 255, 0.32)' }}
    />
  );
}

export default function PaperExtractionStepper() {
  const [activeStep, setActiveStep] = React.useState(0);
  const [identifiers, setIdentifiers] = React.useState([]);

  const isComplete = activeStep === steps.length;

  const handleNext = () => {
    setActiveStep((previousStep) => previousStep + 1);
  };

  const handleBack = () => {
    setActiveStep((previousStep) => previousStep - 1);
  };

  const handleReset = () => {
    setActiveStep(0);
  };

  const renderStepContent = () => {
    if (activeStep === 0) {
      return <PaperIdentifierInput onIdentifiersChange={setIdentifiers} />;
    }

    return <EmptyStepPanel />;
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, width: '100%' }}>
      <Box className={stepperPanelClassName}
        sx={{
          px: { xs: 2.5, sm: 3 },
          py: { xs: 2.5, sm: 3 }
        }}
      >
        <Stepper
          activeStep={activeStep}
          sx={{
            mb: 3,
            '& .MuiStep-root': {
              px: { xs: 0.4, sm: 1 },
            },
            '& .MuiStepLabel-iconContainer': {
              pr: 1.25,
            },
            '& .MuiStepConnector-line': {
              borderColor: 'rgba(255, 255, 255, 0.16)',
              borderTopWidth: 2,
              borderRadius: 999,
              minHeight: 2,
              opacity: 0.8,
            },
            '& .MuiStepLabel-label': {
              color: 'var(--color-text-muted)',
              transition: 'color 160ms ease, transform 160ms ease',
            },
            '& .MuiStepLabel-label.Mui-active, & .MuiStepLabel-label.Mui-completed': {
              color: 'var(--color-text)',
              fontWeight: 700,
            },
            '& .MuiStepConnector-root.Mui-active .MuiStepConnector-line, & .MuiStepConnector-root.Mui-completed .MuiStepConnector-line': {
              borderColor: 'rgba(80, 140, 255, 0.72)',
              boxShadow: 'none',
            },
          }}
        >
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel StepIconComponent={ExtractionStepIcon}>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {isComplete ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography variant="h6" sx={{ color: 'var(--color-text)', fontWeight: 700 }}>
              Extraction flow staged
            </Typography>
            <Typography variant="body2" sx={{ color: 'var(--color-text-muted)' }}>
              {identifiers.length > 0
                ? `${identifiers.length} identifier${identifiers.length === 1 ? '' : 's'} are ready for the next step.`
                : 'No identifiers queued yet.'}
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button type="button" onClick={handleReset} className={secondaryActionClassName}>
                Reset
              </button>
            </Box>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
            {renderStepContent()}

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <button
                type="button"
                disabled={activeStep === 0}
                onClick={handleBack}
                className={secondaryActionClassName}
              >
                Back
              </button>
              <Box sx={{ flex: '1 1 auto' }} />
              <button type="button" onClick={handleNext} className={primaryActionClassName}>
                {activeStep === steps.length - 1 ? 'Finish' : 'Next'}
              </button>
            </Box>
          </Box>
        )}
      </Box>
    </Box>
  );
}
