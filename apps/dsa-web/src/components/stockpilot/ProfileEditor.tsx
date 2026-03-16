import type React from 'react';
import { useState, useMemo } from 'react';
import type {
  UserProfile,
  InvestmentStyle,
  ResponsePreference,
  MacroContext,
  Assets,
  DataFetchConfig,
} from '../../types/stockpilotConfig';
import { SecurityEditor } from './SecurityEditor';

type ProfileEditorProps = {
  profile: UserProfile;
  onChange: (profile: UserProfile) => void;
  disabled?: boolean;
  onSetActive: () => void;
  onDelete?: () => void;
};

export const ProfileEditor: React.FC<ProfileEditorProps> = ({
  profile,
  onChange,
  disabled = false,
  onSetActive,
  onDelete,
}) => {
  const [activeSection, setActiveSection] = useState<'basic' | 'assets' | 'data' | 'style' | 'securities'>('basic');

  const updateProfile = (updates: Partial<UserProfile>) => {
    onChange({ ...profile, ...updates });
  };

  const updateAssets = (updates: Partial<Assets>) => {
    updateProfile({ assets: { ...profile.assets, ...updates } });
  };

  const updateDataFetchConfig = (updates: Partial<DataFetchConfig>) => {
    updateProfile({ dataFetchConfig: { ...profile.dataFetchConfig, ...updates } });
  };

  const addInvestmentStyle = () => {
    const newStyle: InvestmentStyle = { content: '', enabled: true };
    updateProfile({ investmentStyle: [...profile.investmentStyle, newStyle] });
  };

  const updateInvestmentStyle = (index: number, updates: Partial<InvestmentStyle>) => {
    const newStyles = [...profile.investmentStyle];
    newStyles[index] = { ...newStyles[index], ...updates };
    updateProfile({ investmentStyle: newStyles });
  };

  const removeInvestmentStyle = (index: number) => {
    updateProfile({ investmentStyle: profile.investmentStyle.filter((_, i) => i !== index) });
  };

  const addResponsePreference = () => {
    const newPref: ResponsePreference = { content: '', enabled: true };
    updateProfile({ responsePreference: [...profile.responsePreference, newPref] });
  };

  const updateResponsePreference = (index: number, updates: Partial<ResponsePreference>) => {
    const newPrefs = [...profile.responsePreference];
    newPrefs[index] = { ...newPrefs[index], ...updates };
    updateProfile({ responsePreference: newPrefs });
  };

  const removeResponsePreference = (index: number) => {
    updateProfile({ responsePreference: profile.responsePreference.filter((_, i) => i !== index) });
  };

  const addMacroContext = () => {
    const newContext: MacroContext = { date: '', summary: '' };
    updateProfile({ currentMacroContext: [...profile.currentMacroContext, newContext] });
  };

  const updateMacroContext = (index: number, updates: Partial<MacroContext>) => {
    const newContexts = [...profile.currentMacroContext];
    newContexts[index] = { ...newContexts[index], ...updates };
    updateProfile({ currentMacroContext: newContexts });
  };

  const removeMacroContext = (index: number) => {
    updateProfile({ currentMacroContext: profile.currentMacroContext.filter((_, i) => i !== index) });
  };

  const sections = [
    { key: 'basic', label: '基本信息', icon: '👤' },
    { key: 'assets', label: '资产', icon: '💰' },
    { key: 'data', label: '数据配置', icon: '📊' },
    { key: 'style', label: '偏好设置', icon: '🎯' },
    { key: 'securities', label: `证券 (${profile.securityPool.length})`, icon: '📈' },
  ];

  const holdingsCount = useMemo(() => {
    return profile.securityPool.filter((s) => s.position && s.position.shares > 0).length;
  }, [profile.securityPool]);

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-lg bg-elevated/40 border border-white/8">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${profile.isActive ? 'bg-green-400' : 'bg-white/20'}`} />
          <div>
            <div className="font-medium text-white">{profile.profileName || '未命名画像'}</div>
            <div className="text-xs text-muted">
              ID: {profile.profileId} • {profile.securityPool.length} 只证券 • {holdingsCount} 个持仓
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!profile.isActive && (
            <button
              type="button"
              onClick={onSetActive}
              disabled={disabled}
              className="btn-secondary text-xs"
            >
              设为当前
            </button>
          )}
          {onDelete && (
            <button
              type="button"
              onClick={onDelete}
              disabled={disabled}
              className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
        </div>
      </div>

      <div className="flex gap-1 overflow-x-auto pb-2">
        {sections.map((section) => (
          <button
            key={section.key}
            type="button"
            onClick={() => setActiveSection(section.key as typeof activeSection)}
            className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg whitespace-nowrap transition-colors ${
              activeSection === section.key
                ? 'bg-cyan/20 text-cyan border border-cyan/30'
                : 'bg-elevated/40 text-secondary hover:text-white border border-white/8'
            }`}
          >
            <span>{section.icon}</span>
            <span>{section.label}</span>
          </button>
        ))}
      </div>

      <div className="rounded-xl border border-white/8 bg-card/60 p-4">
        {activeSection === 'basic' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs uppercase tracking-wide text-muted mb-2">
                  画像 ID *
                </label>
                <input
                  type="text"
                  value={profile.profileId}
                  onChange={(e) => updateProfile({ profileId: e.target.value })}
                  disabled={disabled}
                  className="input-terminal"
                  placeholder="例如: default"
                />
              </div>
              <div>
                <label className="block text-xs uppercase tracking-wide text-muted mb-2">
                  画像名称 *
                </label>
                <input
                  type="text"
                  value={profile.profileName}
                  onChange={(e) => updateProfile({ profileName: e.target.value })}
                  disabled={disabled}
                  className="input-terminal"
                  placeholder="例如: 默认用户"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs uppercase tracking-wide text-muted">
                  投资风格
                </label>
                <button
                  type="button"
                  onClick={addInvestmentStyle}
                  disabled={disabled}
                  className="text-xs text-cyan hover:text-cyan/80"
                >
                  + 添加风格
                </button>
              </div>
              <div className="space-y-2">
                {profile.investmentStyle.map((style, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={style.enabled}
                      onChange={(e) => updateInvestmentStyle(idx, { enabled: e.target.checked })}
                      disabled={disabled}
                      className="rounded border-white/20"
                    />
                    <input
                      type="text"
                      value={style.content}
                      onChange={(e) => updateInvestmentStyle(idx, { content: e.target.value })}
                      disabled={disabled}
                      className="flex-1 input-terminal text-sm"
                      placeholder="例如: 专注于长期价值投资"
                    />
                    <button
                      type="button"
                      onClick={() => removeInvestmentStyle(idx)}
                      disabled={disabled}
                      className="p-1.5 text-red-400 hover:bg-red-500/10 rounded"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs uppercase tracking-wide text-muted">
                  宏观背景
                </label>
                <button
                  type="button"
                  onClick={addMacroContext}
                  disabled={disabled}
                  className="text-xs text-cyan hover:text-cyan/80"
                >
                  + 添加背景
                </button>
              </div>
              <div className="space-y-2">
                {profile.currentMacroContext.map((ctx, idx) => (
                  <div key={idx} className="flex items-start gap-2">
                    <input
                      type="date"
                      value={ctx.date}
                      onChange={(e) => updateMacroContext(idx, { date: e.target.value })}
                      disabled={disabled}
                      className="input-terminal text-sm w-36"
                    />
                    <textarea
                      value={ctx.summary}
                      onChange={(e) => updateMacroContext(idx, { summary: e.target.value })}
                      disabled={disabled}
                      className="flex-1 input-terminal text-sm min-h-[60px] resize-y"
                      placeholder="市场背景摘要..."
                    />
                    <button
                      type="button"
                      onClick={() => removeMacroContext(idx)}
                      disabled={disabled}
                      className="p-1.5 text-red-400 hover:bg-red-500/10 rounded"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeSection === 'assets' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs uppercase tracking-wide text-muted mb-2">
                  总资金
                </label>
                <input
                  type="number"
                  value={profile.assets.totalCapital}
                  onChange={(e) => updateAssets({ totalCapital: parseFloat(e.target.value) || 0 })}
                  disabled={disabled}
                  min={0}
                  step={1000}
                  className="input-terminal"
                />
              </div>
              <div>
                <label className="block text-xs uppercase tracking-wide text-muted mb-2">
                  可用现金
                </label>
                <input
                  type="number"
                  value={profile.assets.availableCash}
                  onChange={(e) => updateAssets({ availableCash: parseFloat(e.target.value) || 0 })}
                  disabled={disabled}
                  min={0}
                  step={100}
                  className="input-terminal"
                />
              </div>
            </div>

            <label className="flex items-center gap-2 text-sm text-secondary">
              <input
                type="checkbox"
                checked={profile.assets.includeCashInPrompt}
                onChange={(e) => updateAssets({ includeCashInPrompt: e.target.checked })}
                disabled={disabled}
                className="rounded border-white/20"
              />
              在 AI 提示中包含资金信息
            </label>

            <div className="p-4 rounded-lg bg-white/5 border border-white/8">
              <div className="text-xs uppercase tracking-wide text-muted mb-2">持仓概览</div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-cyan">{holdingsCount}</div>
                  <div className="text-xs text-muted">持仓数</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-white">{profile.securityPool.length}</div>
                  <div className="text-xs text-muted">证券总数</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-400">
                    ¥{profile.assets.totalCapital.toLocaleString()}
                  </div>
                  <div className="text-xs text-muted">总资金</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-yellow-400">
                    ¥{profile.assets.availableCash.toLocaleString()}
                  </div>
                  <div className="text-xs text-muted">可用现金</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeSection === 'data' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                { key: 'fetchFullRealtime', label: '完整实时数据' },
                { key: 'fetchMainMoneyFlow', label: '主力资金流向' },
                { key: 'fetchValuationMetrics', label: '估值指标' },
                { key: 'fetchAnnouncements', label: '公告信息' },
                { key: 'fetchNewsSentiment', label: '新闻情绪' },
              ].map((item) => (
                <label
                  key={item.key}
                  className="flex items-center gap-3 p-3 rounded-lg bg-elevated/40 border border-white/8 cursor-pointer hover:border-white/16 transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={profile.dataFetchConfig[item.key as keyof DataFetchConfig] as boolean}
                    onChange={(e) => updateDataFetchConfig({ [item.key]: e.target.checked })}
                    disabled={disabled}
                    className="rounded border-white/20"
                  />
                  <span className="text-sm text-white">{item.label}</span>
                </label>
              ))}
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wide text-muted mb-2">
                咨询范围
              </label>
              <div className="flex flex-wrap gap-2">
                {profile.dataFetchConfig.consultScope.map((scope, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 text-xs rounded-full border border-cyan/30 bg-cyan/10 text-cyan flex items-center gap-1"
                  >
                    {scope}
                    <button
                      type="button"
                      onClick={() => {
                        const newScopes = profile.dataFetchConfig.consultScope.filter((_, i) => i !== idx);
                        updateDataFetchConfig({ consultScope: newScopes });
                      }}
                      disabled={disabled}
                      className="hover:text-red-400"
                    >
                      ×
                    </button>
                  </span>
                ))}
                <input
                  type="text"
                  placeholder="添加范围..."
                  className="px-3 py-1 text-xs rounded-full border border-dashed border-white/20 bg-transparent text-secondary focus:border-cyan focus:outline-none"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                      updateDataFetchConfig({
                        consultScope: [...profile.dataFetchConfig.consultScope, e.currentTarget.value.trim()],
                      });
                      e.currentTarget.value = '';
                    }
                  }}
                />
              </div>
            </div>
          </div>
        )}

        {activeSection === 'style' && (
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs uppercase tracking-wide text-muted">
                  回复偏好
                </label>
                <button
                  type="button"
                  onClick={addResponsePreference}
                  disabled={disabled}
                  className="text-xs text-cyan hover:text-cyan/80"
                >
                  + 添加偏好
                </button>
              </div>
              <div className="space-y-2">
                {profile.responsePreference.map((pref, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={pref.enabled}
                      onChange={(e) => updateResponsePreference(idx, { enabled: e.target.checked })}
                      disabled={disabled}
                      className="rounded border-white/20"
                    />
                    <input
                      type="text"
                      value={pref.content}
                      onChange={(e) => updateResponsePreference(idx, { content: e.target.value })}
                      disabled={disabled}
                      className="flex-1 input-terminal text-sm"
                      placeholder="例如: 提供具体操作建议"
                    />
                    <button
                      type="button"
                      onClick={() => removeResponsePreference(idx)}
                      disabled={disabled}
                      className="p-1.5 text-red-400 hover:bg-red-500/10 rounded"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeSection === 'securities' && (
          <SecurityEditor
            securities={profile.securityPool}
            onChange={(securities) => updateProfile({ securityPool: securities })}
            disabled={disabled}
          />
        )}
      </div>
    </div>
  );
};

type ProfileListProps = {
  profiles: UserProfile[];
  activeProfileId: string | null;
  onSelect: (index: number) => void;
  onAdd: () => void;
  onDelete: (index: number) => void;
  onSetActive: (index: number) => void;
  disabled?: boolean;
};

export const ProfileList: React.FC<ProfileListProps> = ({
  profiles,
  activeProfileId,
  onSelect,
  onAdd,
  onDelete,
  onSetActive,
  disabled = false,
}) => {
  return (
    <div className="space-y-2">
      {profiles.map((profile, idx) => (
        <div
          key={profile.profileId}
          className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
            profile.profileId === activeProfileId
              ? 'border-cyan/50 bg-cyan/10'
              : 'border-white/8 bg-elevated/40 hover:border-white/16'
          }`}
          onClick={() => onSelect(idx)}
        >
          <div className={`w-2 h-2 rounded-full ${profile.isActive ? 'bg-green-400' : 'bg-white/20'}`} />
          <div className="flex-1 min-w-0">
            <div className="font-medium text-sm text-white truncate">{profile.profileName}</div>
            <div className="text-xs text-muted">
              {profile.securityPool.length} 只证券 • {profile.securityPool.filter((s) => s.position).length} 个持仓
            </div>
          </div>
          {!profile.isActive && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onSetActive(idx);
              }}
              disabled={disabled}
              className="text-xs text-cyan hover:text-cyan/80"
            >
              激活
            </button>
          )}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onDelete(idx);
            }}
            disabled={disabled}
            className="p-1 text-red-400 hover:bg-red-500/10 rounded"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={onAdd}
        disabled={disabled}
        className="w-full p-3 rounded-lg border border-dashed border-white/20 text-sm text-muted hover:border-cyan/50 hover:text-cyan transition-colors"
      >
        + 添加画像
      </button>
    </div>
  );
};
