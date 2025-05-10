import * as React from 'react';
import { cn } from '../../lib/utils';

export interface SwitchProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  description?: string;
}

const Switch = React.forwardRef<HTMLInputElement, SwitchProps>(
  ({ className, label, description, ...props }, ref) => {
    return (
      <label className="flex items-start gap-3 cursor-pointer">
        <div className="relative inline-flex items-center">
          <input
            type="checkbox"
            className="sr-only peer"
            ref={ref}
            {...props}
          />
          <div
            className={cn(
              "w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-500",
              "rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white",
              "after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white",
              "after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all",
              "peer-checked:bg-blue-600"
            )}
          />
        </div>
        {(label || description) && (
          <div>
            {label && <div className="font-medium text-sm text-gray-900">{label}</div>}
            {description && <div className="text-xs text-gray-500">{description}</div>}
          </div>
        )}
      </label>
    );
  }
);

Switch.displayName = 'Switch';

export { Switch };