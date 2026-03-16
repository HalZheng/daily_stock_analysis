export type AssetType = 'Stock' | 'ETF' | 'Fund' | 'Bond' | 'Other';

export interface Position {
  shares: number;
  cost: number;
  currentValue: number;
}

export interface Security {
  code: string;
  name: string;
  assetType: AssetType;
  groups: string[];
  tags: string[];
  position: Position | null;
  strategyNote: string;
  privateNote: string;
  linkedRef: string;
}

export interface DataFetchConfig {
  fetchFullRealtime: boolean;
  fetchMainMoneyFlow: boolean;
  fetchValuationMetrics: boolean;
  fetchAnnouncements: boolean;
  fetchNewsSentiment: boolean;
  consultScope: string[];
}

export interface Assets {
  totalCapital: number;
  availableCash: number;
  includeCashInPrompt: boolean;
}

export interface MacroContext {
  date: string;
  summary: string;
}

export interface ResponsePreference {
  content: string;
  enabled: boolean;
}

export interface InvestmentStyle {
  content: string;
  enabled: boolean;
}

export interface UserProfile {
  profileId: string;
  profileName: string;
  isActive: boolean;
  investmentStyle: InvestmentStyle[];
  currentMacroContext: MacroContext[];
  assets: Assets;
  dataFetchConfig: DataFetchConfig;
  responsePreference: ResponsePreference[];
  securityPool: Security[];
}

export interface IndexConfig {
  code: string;
  name: string;
  enabled: boolean;
}

export interface GlobalConfig {
  version: string;
  akshareRetryCount: number;
  indices: IndexConfig[];
}

export interface StockPilotConfig {
  globalConfig: GlobalConfig;
  profiles: UserProfile[];
}

export interface StockPilotConfigResponse {
  configVersion: string;
  config: StockPilotConfig;
  updatedAt: string | null;
}

export interface StockPilotConfigUpdateRequest {
  configVersion: string;
  config: StockPilotConfig;
}

export interface StockPilotValidationIssue {
  path: string;
  code: string;
  message: string;
  severity: 'error' | 'warning';
}

export interface StockPilotValidateResponse {
  valid: boolean;
  issues: StockPilotValidationIssue[];
}

export interface StockPilotValidationErrorResponse {
  error: string;
  message: string;
  issues: StockPilotValidationIssue[];
}

export interface StockPilotConflictResponse {
  error: string;
  message: string;
  currentConfigVersion: string;
}

export interface StockPilotExportResponse {
  yamlContent: string;
  configVersion: string;
  filename: string;
}

export interface StockPilotImportRequest {
  yamlContent: string;
}

export interface StockPilotImportResponse {
  success: boolean;
  config: StockPilotConfig | null;
  issues: StockPilotValidationIssue[];
  message: string;
}

export interface ProfileBrief {
  profileId: string;
  profileName: string;
  isActive: boolean;
  securityCount: number;
  holdingCount: number;
}

export interface StockPilotSummaryResponse {
  configVersion: string;
  activeProfile: ProfileBrief | null;
  totalProfiles: number;
  totalSecurities: number;
  totalHoldings: number;
  totalCapital: number;
  availableCash: number;
}

export function createDefaultPosition(): Position {
  return {
    shares: 0,
    cost: 0,
    currentValue: 0,
  };
}

export function createDefaultSecurity(): Security {
  return {
    code: '',
    name: '',
    assetType: 'Stock',
    groups: [],
    tags: [],
    position: null,
    strategyNote: '',
    privateNote: '',
    linkedRef: '',
  };
}

export function createDefaultAssets(): Assets {
  return {
    totalCapital: 100000,
    availableCash: 15000,
    includeCashInPrompt: true,
  };
}

export function createDefaultDataFetchConfig(): DataFetchConfig {
  return {
    fetchFullRealtime: false,
    fetchMainMoneyFlow: true,
    fetchValuationMetrics: true,
    fetchAnnouncements: true,
    fetchNewsSentiment: true,
    consultScope: ['当前持仓', '重点观察'],
  };
}

export function createDefaultUserProfile(): UserProfile {
  return {
    profileId: '',
    profileName: '',
    isActive: false,
    investmentStyle: [],
    currentMacroContext: [],
    assets: createDefaultAssets(),
    dataFetchConfig: createDefaultDataFetchConfig(),
    responsePreference: [],
    securityPool: [],
  };
}

export function createDefaultGlobalConfig(): GlobalConfig {
  return {
    version: '1.0.0',
    akshareRetryCount: 3,
    indices: [
      { code: '000001.SH', name: '上证指数', enabled: true },
      { code: '000300.SH', name: '沪深300', enabled: true },
      { code: '399006.SZ', name: '创业板指', enabled: true },
      { code: '399001.SZ', name: '深证成指', enabled: true },
    ],
  };
}

export function createDefaultStockPilotConfig(): StockPilotConfig {
  return {
    globalConfig: createDefaultGlobalConfig(),
    profiles: [],
  };
}
