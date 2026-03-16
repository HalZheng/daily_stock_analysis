import type React from 'react';
import { useState } from 'react';
import type { GlobalConfig } from '../../types/stockpilotConfig';

type GlobalConfigEditorProps = {
  config: GlobalConfig;
  onChange: (config: GlobalConfig) => void;
  disabled?: boolean;
};

export const GlobalConfigEditor: React.FC<GlobalConfigEditorProps> = ({
  config,
  onChange,
  disabled = false,
}) => {
  const [newIndexCode, setNewIndexCode] = useState('');
  const [newIndexName, setNewIndexName] = useState('');

  const handleVersionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...config, version: e.target.value });
  };

  const handleRetryCountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value >= 0 && value <= 10) {
      onChange({ ...config, akshareRetryCount: value });
    }
  };

  const handleIndexToggle = (index: number) => {
    const newIndices = [...config.indices];
    newIndices[index] = { ...newIndices[index], enabled: !newIndices[index].enabled };
    onChange({ ...config, indices: newIndices });
  };

  const handleIndexChange = (index: number, field: 'code' | 'name', value: string) => {
    const newIndices = [...config.indices];
    newIndices[index] = { ...newIndices[index], [field]: value };
    onChange({ ...config, indices: newIndices });
  };

  const handleAddIndex = () => {
    if (newIndexCode.trim() && newIndexName.trim()) {
      onChange({
        ...config,
        indices: [...config.indices, { code: newIndexCode.trim(), name: newIndexName.trim(), enabled: true }],
      });
      setNewIndexCode('');
      setNewIndexName('');
    }
  };

  const handleRemoveIndex = (index: number) => {
    const newIndices = config.indices.filter((_, i) => i !== index);
    onChange({ ...config, indices: newIndices });
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs uppercase tracking-wide text-muted mb-2">
            配置版本
          </label>
          <input
            type="text"
            value={config.version}
            onChange={handleVersionChange}
            disabled={disabled}
            className="input-terminal"
            placeholder="1.0.0"
          />
        </div>

        <div>
          <label className="block text-xs uppercase tracking-wide text-muted mb-2">
            Akshare 重试次数 (0-10)
          </label>
          <input
            type="number"
            value={config.akshareRetryCount}
            onChange={handleRetryCountChange}
            disabled={disabled}
            min={0}
            max={10}
            className="input-terminal"
          />
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="text-xs uppercase tracking-wide text-muted">
            市场监控指数
          </label>
          <span className="text-xs text-muted">{config.indices.length} 个指数</span>
        </div>

        <div className="space-y-2">
          {config.indices.map((index, idx) => (
            <div
              key={`${index.code}-${idx}`}
              className={`flex items-center gap-3 p-3 rounded-lg border transition-colors ${
                index.enabled
                  ? 'border-white/10 bg-elevated/60'
                  : 'border-white/5 bg-elevated/30 opacity-60'
              }`}
            >
              <button
                type="button"
                onClick={() => handleIndexToggle(idx)}
                disabled={disabled}
                className={`flex-shrink-0 w-10 h-5 rounded-full transition-colors ${
                  index.enabled ? 'bg-cyan' : 'bg-white/20'
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full bg-white shadow transform transition-transform ${
                    index.enabled ? 'translate-x-5' : 'translate-x-0.5'
                  }`}
                />
              </button>

              <input
                type="text"
                value={index.code}
                onChange={(e) => handleIndexChange(idx, 'code', e.target.value)}
                disabled={disabled}
                className="flex-1 input-terminal text-sm"
                placeholder="指数代码 (如: 000001.SH)"
              />

              <input
                type="text"
                value={index.name}
                onChange={(e) => handleIndexChange(idx, 'name', e.target.value)}
                disabled={disabled}
                className="flex-1 input-terminal text-sm"
                placeholder="指数名称"
              />

              <button
                type="button"
                onClick={() => handleRemoveIndex(idx)}
                disabled={disabled}
                className="flex-shrink-0 p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          ))}
        </div>

        <div className="mt-3 flex items-center gap-2">
          <input
            type="text"
            value={newIndexCode}
            onChange={(e) => setNewIndexCode(e.target.value)}
            disabled={disabled}
            className="flex-1 input-terminal text-sm"
            placeholder="新指数代码"
          />
          <input
            type="text"
            value={newIndexName}
            onChange={(e) => setNewIndexName(e.target.value)}
            disabled={disabled}
            className="flex-1 input-terminal text-sm"
            placeholder="新指数名称"
          />
          <button
            type="button"
            onClick={handleAddIndex}
            disabled={disabled || !newIndexCode.trim() || !newIndexName.trim()}
            className="btn-secondary text-sm whitespace-nowrap"
          >
            添加
          </button>
        </div>
      </div>
    </div>
  );
};
