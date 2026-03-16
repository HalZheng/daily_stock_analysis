import apiClient from './index';
import { toCamelCase, toSnakeCase } from './utils';
import type {
  StockPilotConfigResponse,
  StockPilotConfigUpdateRequest,
  StockPilotValidateResponse,
  StockPilotValidationErrorResponse,
  StockPilotConflictResponse,
  StockPilotExportResponse,
  StockPilotImportRequest,
  StockPilotImportResponse,
  StockPilotSummaryResponse,
} from '../types/stockpilotConfig';

type ApiErrorPayload = {
  error?: string;
  message?: string;
  issues?: unknown;
  current_config_version?: string;
};

export class StockPilotValidationError extends Error {
  issues: StockPilotValidationErrorResponse['issues'];

  constructor(message: string, issues: StockPilotValidationErrorResponse['issues']) {
    super(message);
    this.name = 'StockPilotValidationError';
    this.issues = issues;
  }
}

export class StockPilotConflictError extends Error {
  currentConfigVersion?: string;

  constructor(message: string, currentConfigVersion?: string) {
    super(message);
    this.name = 'StockPilotConflictError';
    this.currentConfigVersion = currentConfigVersion;
  }
}

function extractApiMessage(error: unknown, fallback: string): string {
  if (!error || typeof error !== 'object' || !('response' in error)) {
    return fallback;
  }

  const response = (error as { response?: { data?: ApiErrorPayload } }).response;
  return response?.data?.message || fallback;
}

export const stockpilotConfigApi = {
  async getConfig(): Promise<StockPilotConfigResponse> {
    const response = await apiClient.get<Record<string, unknown>>('/api/v1/stockpilot/config');
    return toCamelCase<StockPilotConfigResponse>(response.data);
  },

  async getSummary(): Promise<StockPilotSummaryResponse> {
    const response = await apiClient.get<Record<string, unknown>>('/api/v1/stockpilot/config/summary');
    return toCamelCase<StockPilotSummaryResponse>(response.data);
  },

  async validate(payload: StockPilotConfigUpdateRequest): Promise<StockPilotValidateResponse> {
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/stockpilot/config/validate',
      toSnakeCase(payload),
    );
    return toCamelCase<StockPilotValidateResponse>(response.data);
  },

  async update(payload: StockPilotConfigUpdateRequest): Promise<StockPilotConfigResponse> {
    try {
      const response = await apiClient.put<Record<string, unknown>>(
        '/api/v1/stockpilot/config',
        toSnakeCase(payload),
      );
      return toCamelCase<StockPilotConfigResponse>(response.data);
    } catch (error: unknown) {
      if (error && typeof error === 'object' && 'response' in error) {
        const status = (error as { response?: { status?: number } }).response?.status;
        const payloadData = (error as { response?: { data?: ApiErrorPayload } }).response?.data;

        if (status === 400) {
          const validationError = toCamelCase<StockPilotValidationErrorResponse>(payloadData ?? {});
          throw new StockPilotValidationError(
            validationError.message || 'Configuration validation failed',
            validationError.issues || [],
          );
        }

        if (status === 409) {
          const conflict = toCamelCase<StockPilotConflictResponse>(payloadData ?? {});
          throw new StockPilotConflictError(
            conflict.message || 'Configuration version conflict',
            conflict.currentConfigVersion,
          );
        }
      }

      throw new Error(extractApiMessage(error, 'Failed to update StockPilot configuration'));
    }
  },

  async exportYaml(): Promise<StockPilotExportResponse> {
    const response = await apiClient.get<Record<string, unknown>>('/api/v1/stockpilot/config/export');
    return toCamelCase<StockPilotExportResponse>(response.data);
  },

  async importYaml(payload: StockPilotImportRequest): Promise<StockPilotImportResponse> {
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/stockpilot/config/import',
      toSnakeCase(payload),
    );
    return toCamelCase<StockPilotImportResponse>(response.data);
  },
};
