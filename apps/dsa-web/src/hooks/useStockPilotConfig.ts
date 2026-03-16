import { useState, useCallback } from 'react';
import { stockpilotConfigApi, StockPilotValidationError, StockPilotConflictError } from '../api/stockpilotConfig';
import type {
  StockPilotConfig,
  StockPilotValidationIssue,
  StockPilotSummaryResponse,
} from '../types/stockpilotConfig';

type ToastType = {
  type: 'success' | 'error';
  message: string;
};

type UseStockPilotConfigResult = {
  config: StockPilotConfig | null;
  configVersion: string;
  isLoading: boolean;
  isSaving: boolean;
  loadError: string | null;
  saveError: string | null;
  issues: StockPilotValidationIssue[];
  toast: ToastType | null;
  summary: StockPilotSummaryResponse | null;
  hasChanges: boolean;
  load: () => Promise<void>;
  loadSummary: () => Promise<void>;
  save: () => Promise<void>;
  updateConfig: (config: StockPilotConfig) => void;
  clearToast: () => void;
  exportYaml: () => Promise<string | null>;
  importYaml: (yamlContent: string) => Promise<boolean>;
  validate: () => Promise<boolean>;
};

export function useStockPilotConfig(): UseStockPilotConfigResult {
  const [config, setConfig] = useState<StockPilotConfig | null>(null);
  const [originalConfig, setOriginalConfig] = useState<StockPilotConfig | null>(null);
  const [configVersion, setConfigVersion] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [issues, setIssues] = useState<StockPilotValidationIssue[]>([]);
  const [toast, setToast] = useState<ToastType | null>(null);
  const [summary, setSummary] = useState<StockPilotSummaryResponse | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    setIssues([]);

    try {
      const response = await stockpilotConfigApi.getConfig();
      setConfig(response.config);
      setOriginalConfig(response.config);
      setConfigVersion(response.configVersion);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load configuration';
      setLoadError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadSummary = useCallback(async () => {
    try {
      const response = await stockpilotConfigApi.getSummary();
      setSummary(response);
    } catch (error) {
      console.error('Failed to load summary:', error);
    }
  }, []);

  const validate = useCallback(async (): Promise<boolean> => {
    if (!config) return false;

    try {
      const response = await stockpilotConfigApi.validate({
        configVersion,
        config,
      });
      setIssues(response.issues);
      return response.valid;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Validation failed';
      setIssues([{
        path: '',
        code: 'validation_error',
        message,
        severity: 'error',
      }]);
      return false;
    }
  }, [config, configVersion]);

  const save = useCallback(async () => {
    if (!config) return;

    setIsSaving(true);
    setSaveError(null);
    setIssues([]);

    try {
      const response = await stockpilotConfigApi.update({
        configVersion,
        config,
      });
      setConfig(response.config);
      setOriginalConfig(response.config);
      setConfigVersion(response.configVersion);
      setToast({ type: 'success', message: 'Configuration saved successfully' });
    } catch (error) {
      if (error instanceof StockPilotValidationError) {
        setIssues(error.issues);
        setSaveError('Configuration validation failed');
      } else if (error instanceof StockPilotConflictError) {
        setSaveError('Configuration has been modified. Please reload and try again.');
        if (error.currentConfigVersion) {
          setConfigVersion(error.currentConfigVersion);
        }
      } else {
        const message = error instanceof Error ? error.message : 'Failed to save configuration';
        setSaveError(message);
      }
    } finally {
      setIsSaving(false);
    }
  }, [config, configVersion]);

  const updateConfig = useCallback((newConfig: StockPilotConfig) => {
    setConfig(newConfig);
    setIssues([]);
  }, []);

  const clearToast = useCallback(() => {
    setToast(null);
  }, []);

  const exportYaml = useCallback(async (): Promise<string | null> => {
    try {
      const response = await stockpilotConfigApi.exportYaml();
      return response.yamlContent;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to export configuration';
      setToast({ type: 'error', message });
      return null;
    }
  }, []);

  const importYaml = useCallback(async (yamlContent: string): Promise<boolean> => {
    try {
      const response = await stockpilotConfigApi.importYaml({ yamlContent });
      if (response.success && response.config) {
        setConfig(response.config);
        setIssues(response.issues);
        setToast({ type: 'success', message: 'Configuration imported successfully' });
        return true;
      } else {
        setIssues(response.issues);
        setToast({ type: 'error', message: response.message || 'Import failed' });
        return false;
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to import configuration';
      setToast({ type: 'error', message });
      return false;
    }
  }, []);

  const hasChanges = JSON.stringify(config) !== JSON.stringify(originalConfig);

  return {
    config,
    configVersion,
    isLoading,
    isSaving,
    loadError,
    saveError,
    issues,
    toast,
    summary,
    hasChanges,
    load,
    loadSummary,
    save,
    updateConfig,
    clearToast,
    exportYaml,
    importYaml,
    validate,
  };
}
