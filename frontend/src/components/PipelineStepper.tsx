import React from 'react';
import { CheckCircle2, Loader2, Circle } from 'lucide-react';

export interface StepItem {
  id: string;
  name: string;
  status: 'idle' | 'running' | 'completed' | 'error';
}

interface PipelineStepperProps {
  steps: StepItem[];
}

export const PipelineStepper: React.FC<PipelineStepperProps> = ({ steps }) => {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 overflow-x-auto pb-1">
        {steps.map((step, idx) => {
          return (
            <React.Fragment key={step.id}>
              <div className="flex items-center space-x-2">
                <div className="flex items-center justify-center">
                  {step.status === 'completed' && (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  )}
                  {step.status === 'running' && (
                    <Loader2 className="w-4 h-4 text-sky-400 animate-spin" />
                  )}
                  {step.status === 'idle' && (
                    <Circle className="w-4 h-4 text-slate-600" />
                  )}
                  {step.status === 'error' && (
                    <div className="w-4 h-4 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center text-[10px] font-bold">!</div>
                  )}
                </div>
                <span
                  className={`text-xs whitespace-nowrap font-medium ${
                    step.status === 'completed'
                      ? 'text-slate-200'
                      : step.status === 'running'
                      ? 'text-sky-400 font-semibold'
                      : 'text-slate-400'
                  }`}
                >
                  {step.name}
                </span>
              </div>
              {idx < steps.length - 1 && (
                <div className="hidden sm:block w-4 h-[1px] bg-slate-800 shrink-0" />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
