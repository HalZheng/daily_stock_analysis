import type React from 'react';
import { useEffect, useState, useRef } from 'react';
import { useStockPilotConfig } from '../hooks';
import {
  SettingsAlert,
  ValidationIssueList,
  GlobalConfigEditor,
  ProfileEditor,
  ProfileList,
} from '../components/stockpilot';
import type { StockPilotConfig, UserProfile } from '../types/stockpilotConfig';
import { createDefaultUserProfile } from '../types/stockpilotConfig';

type ActiveSection = 'global' | 'profiles';

const StockPilotConfigPage: React.FC = () => {
  const {
    config,
    isLoading,
    isSaving,
    loadError,
    saveError,
    issues,
    toast,
    hasChanges,
    load,
    save,
    updateConfig,
    clearToast,
    exportYaml,
    importYaml,
  } = useStockPilotConfig();

  const [activeSection, setActiveSection] = useState<ActiveSection>('profiles');
  const [activeProfileIndex, setActiveProfileIndex] = useState<number>(0);
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [importContent, setImportContent] = useState('');
  const [importError, setImportError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => clearToast(), 3500);
    return () => window.clearTimeout(timer);
  }, [clearToast, toast]);

  const handleGlobalConfigChange = (globalConfig: StockPilotConfig['globalConfig']) => {
    if (!config) return;
    updateConfig({ ...config, globalConfig });
  };

  const handleProfileChange = (profile: UserProfile) => {
    if (!config) return;
    const newProfiles = [...config.profiles];
    newProfiles[activeProfileIndex] = profile;
    updateConfig({ ...config, profiles: newProfiles });
  };

  const handleAddProfile = () => {
    if (!config) return;
    const newProfile = createDefaultUserProfile();
    newProfile.profileId = `profile_${Date.now()}`;
    newProfile.profileName = '新建配置';
    updateConfig({ ...config, profiles: [...config.profiles, newProfile] });
    setActiveProfileIndex(config.profiles.length);
  };

  const handleDeleteProfile = (index: number) => {
    if (!config || config.profiles.length <= 1) return;
    const newProfiles = config.profiles.filter((_, i) => i !== index);
    updateConfig({ ...config, profiles: newProfiles });
    if (activeProfileIndex >= newProfiles.length) {
      setActiveProfileIndex(newProfiles.length - 1);
    }
  };

  const handleSetActiveProfile = (index: number) => {
    if (!config) return;
    const newProfiles = config.profiles.map((p, i) => ({
      ...p,
      isActive: i === index,
    }));
    updateConfig({ ...config, profiles: newProfiles });
  };

  const handleExport = async () => {
    const yamlContent = await exportYaml();
    if (yamlContent) {
      const blob = new Blob([yamlContent], { type: 'text/yaml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `stockpilot_config_${new Date().toISOString().slice(0, 10)}.yaml`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setImportContent(content);
      setImportModalOpen(true);
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  const handleImport = async () => {
    if (!importContent.trim()) return;
    setImportError(null);
    const success = await importYaml(importContent);
    if (success) {
      setImportModalOpen(false);
      setImportContent('');
    }
  };

  const activeProfile = config?.profiles[activeProfileIndex];

  return (
    <div className="min-h-screen px-4 pb-6 pt-4 md:px-6">
      <header className="mb-4 rounded-2xl border border-white/8 bg-card/80 p-4 backdrop-blur-sm">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-xl font-semibold text-white">StockPilot 配置</h1>
            <p className="text-sm text-secondary">
              管理您的投资画像和证券池
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept=".yaml,.yml"
              onChange={handleFileSelect}
              className="hidden"
            />
            <button
              type="button"
              className="btn-secondary text-sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading || isSaving}
            >
              导入
            </button>
            <button
              type="button"
              className="btn-secondary text-sm"
              onClick={handleExport}
              disabled={isLoading || isSaving}
            >
              导出
            </button>
            <button
              type="button"
              className="btn-secondary text-sm"
              onClick={() => void load()}
              disabled={isLoading || isSaving}
            >
              重置
            </button>
            <button
              type="button"
              className="btn-primary text-sm"
              onClick={() => void save()}
              disabled={!hasChanges || isSaving || isLoading}
            >
              {isSaving ? '保存中...' : hasChanges ? '保存更改' : '无更改'}
            </button>
          </div>
        </div>

        {saveError ? (
          <SettingsAlert
            className="mt-3"
            title="保存失败"
            message={saveError}
          />
        ) : null}
      </header>

      {loadError ? (
        <SettingsAlert
          title="加载失败"
          message={loadError}
          actionLabel="重试"
          onAction={() => void load()}
          className="mb-4"
        />
      ) : null}

      {issues.length > 0 ? (
        <div className="mb-4 rounded-xl border border-white/8 bg-card/60 p-4 backdrop-blur-sm">
          <div className="text-xs uppercase tracking-wide text-muted mb-2">验证问题</div>
          <ValidationIssueList issues={issues} />
        </div>
      ) : null}

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-cyan/20 border-t-cyan rounded-full animate-spin" />
        </div>
      ) : config ? (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
          <aside className="rounded-2xl border border-white/8 bg-card/60 p-3 backdrop-blur-sm">
            <div className="flex gap-1 mb-3">
              {(['profiles', 'global'] as const).map((section) => (
                <button
                  key={section}
                  type="button"
                  onClick={() => setActiveSection(section)}
                  className={`flex-1 px-3 py-2 text-xs font-medium rounded-lg transition-colors ${
                    activeSection === section
                      ? 'bg-cyan/20 text-cyan border border-cyan/30'
                      : 'bg-elevated/40 text-secondary hover:text-white border border-white/8'
                  }`}
                >
                  {section === 'profiles' ? '画像' : '全局'}
                </button>
              ))}
            </div>

            {activeSection === 'profiles' ? (
              <ProfileList
                profiles={config.profiles}
                activeProfileId={activeProfile?.profileId || null}
                onSelect={setActiveProfileIndex}
                onAdd={handleAddProfile}
                onDelete={handleDeleteProfile}
                onSetActive={handleSetActiveProfile}
                disabled={isSaving}
              />
            ) : (
              <div className="text-xs text-muted p-3">
                StockPilot 全局配置，包括市场指数监控和重试设置。
              </div>
            )}
          </aside>

          <section className="rounded-2xl border border-white/8 bg-card/60 p-4 backdrop-blur-sm">
            {activeSection === 'global' ? (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-medium text-white">全局配置</h2>
                </div>
                <GlobalConfigEditor
                  config={config.globalConfig}
                  onChange={handleGlobalConfigChange}
                  disabled={isSaving}
                />
              </div>
            ) : activeProfile ? (
              <ProfileEditor
                profile={activeProfile}
                onChange={handleProfileChange}
                disabled={isSaving}
                onSetActive={() => handleSetActiveProfile(activeProfileIndex)}
                onDelete={config.profiles.length > 1 ? () => handleDeleteProfile(activeProfileIndex) : undefined}
              />
            ) : (
              <div className="text-center text-muted py-10">
                未选择画像，请添加一个画像开始使用。
              </div>
            )}
          </section>
        </div>
      ) : null}

      {toast ? (
        <div className="fixed bottom-5 right-5 z-50 w-[320px] max-w-[calc(100vw-24px)]">
          <SettingsAlert
            title={toast.type === 'success' ? '成功' : '错误'}
            message={toast.message}
            variant={toast.type === 'success' ? 'success' : 'error'}
          />
        </div>
      ) : null}

      {importModalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-2xl border border-white/10 bg-card p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-white">导入配置</h3>
              <button
                type="button"
                onClick={() => {
                  setImportModalOpen(false);
                  setImportContent('');
                  setImportError(null);
                }}
                className="p-2 text-muted hover:text-white rounded-lg hover:bg-white/10"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <p className="text-sm text-secondary mb-4">
              请在导入前检查 YAML 内容。这将替换您当前的配置。
            </p>

            {importError ? (
              <SettingsAlert
                title="导入错误"
                message={importError}
                className="mb-4"
              />
            ) : null}

            <textarea
              value={importContent}
              onChange={(e) => setImportContent(e.target.value)}
              className="w-full h-64 input-terminal text-sm font-mono resize-none"
              placeholder="在此粘贴 YAML 内容..."
            />

            <div className="flex justify-end gap-2 mt-4">
              <button
                type="button"
                onClick={() => {
                  setImportModalOpen(false);
                  setImportContent('');
                  setImportError(null);
                }}
                className="btn-secondary text-sm"
              >
                取消
              </button>
              <button
                type="button"
                onClick={() => void handleImport()}
                disabled={!importContent.trim()}
                className="btn-primary text-sm"
              >
                导入
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default StockPilotConfigPage;
