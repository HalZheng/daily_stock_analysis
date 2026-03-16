import type React from 'react';

type SettingsAlertProps = {
  title: string;
  message: string;
  variant?: 'error' | 'success' | 'warning';
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
};

const variantStyles = {
  error: 'border-red-500/30 bg-red-500/10 text-red-300',
  success: 'border-green-500/30 bg-green-500/10 text-green-300',
  warning: 'border-yellow-500/30 bg-yellow-500/10 text-yellow-300',
};

const iconMap = {
  error: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  success: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  warning: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
};

export const SettingsAlert: React.FC<SettingsAlertProps> = ({
  title,
  message,
  variant = 'error',
  actionLabel,
  onAction,
  className = '',
}) => {
  return (
    <div className={`rounded-xl border p-4 ${variantStyles[variant]} ${className}`}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">{iconMap[variant]}</div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm">{title}</p>
          <p className="text-sm opacity-80 mt-1">{message}</p>
        </div>
        {actionLabel && onAction ? (
          <button
            type="button"
            onClick={onAction}
            className="flex-shrink-0 px-3 py-1.5 text-xs font-medium rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
          >
            {actionLabel}
          </button>
        ) : null}
      </div>
    </div>
  );
};

type ValidationIssueListProps = {
  issues: Array<{
    path: string;
    code: string;
    message: string;
    severity: 'error' | 'warning';
  }>;
};

export const ValidationIssueList: React.FC<ValidationIssueListProps> = ({ issues }) => {
  if (issues.length === 0) return null;

  return (
    <div className="space-y-2">
      {issues.map((issue, idx) => (
        <div
          key={`${issue.path}-${idx}`}
          className={`flex items-start gap-2 text-sm p-2 rounded-lg ${
            issue.severity === 'error'
              ? 'bg-red-500/10 text-red-300'
              : 'bg-yellow-500/10 text-yellow-300'
          }`}
        >
          <span className="flex-shrink-0 mt-0.5">
            {issue.severity === 'error' ? '✗' : '⚠'}
          </span>
          <div className="flex-1 min-w-0">
            {issue.path ? (
              <span className="font-mono text-xs opacity-70">{issue.path}: </span>
            ) : null}
            <span>{issue.message}</span>
          </div>
        </div>
      ))}
    </div>
  );
};
