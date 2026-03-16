import type React from 'react';
import { useState, useMemo } from 'react';
import type { Security, Position, AssetType } from '../../types/stockpilotConfig';
import { createDefaultSecurity, createDefaultPosition } from '../../types/stockpilotConfig';

type SecurityEditorProps = {
  securities: Security[];
  onChange: (securities: Security[]) => void;
  disabled?: boolean;
};

const ASSET_TYPES: AssetType[] = ['Stock', 'ETF', 'Fund', 'Bond', 'Other'];

const ASSET_TYPE_LABELS: Record<AssetType, string> = {
  Stock: '股票',
  ETF: 'ETF',
  Fund: '基金',
  Bond: '债券',
  Other: '其他',
};

export const SecurityEditor: React.FC<SecurityEditorProps> = ({
  securities,
  onChange,
  disabled = false,
}) => {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<Security>(createDefaultSecurity());
  const [searchTerm, setSearchTerm] = useState('');
  const [filterGroup, setFilterGroup] = useState<string>('');

  const allGroups = useMemo(() => {
    const groups = new Set<string>();
    securities.forEach((s) => s.groups.forEach((g) => groups.add(g)));
    return Array.from(groups).sort();
  }, [securities]);

  const filteredSecurities = useMemo(() => {
    return securities.filter((s) => {
      const matchesSearch =
        !searchTerm ||
        s.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesGroup = !filterGroup || s.groups.includes(filterGroup);
      return matchesSearch && matchesGroup;
    });
  }, [securities, searchTerm, filterGroup]);

  const handleAddNew = () => {
    setEditForm(createDefaultSecurity());
    setEditingIndex(-1);
  };

  const handleEdit = (index: number) => {
    const actualIndex = securities.findIndex((s) => s === filteredSecurities[index]);
    setEditForm({ ...securities[actualIndex] });
    setEditingIndex(actualIndex);
  };

  const handleSave = () => {
    if (!editForm.code.trim() || !editForm.name.trim()) return;

    const newSecurities = [...securities];
    if (editingIndex === -1) {
      newSecurities.push(editForm);
    } else if (editingIndex !== null) {
      newSecurities[editingIndex] = editForm;
    }
    onChange(newSecurities);
    setEditingIndex(null);
    setEditForm(createDefaultSecurity());
  };

  const handleCancel = () => {
    setEditingIndex(null);
    setEditForm(createDefaultSecurity());
  };

  const handleDelete = (index: number) => {
    const actualIndex = securities.findIndex((s) => s === filteredSecurities[index]);
    const newSecurities = securities.filter((_, i) => i !== actualIndex);
    onChange(newSecurities);
  };

  const updateEditForm = (updates: Partial<Security>) => {
    setEditForm((prev) => ({ ...prev, ...updates }));
  };

  const updatePosition = (updates: Partial<Position>) => {
    const currentPosition = editForm.position || createDefaultPosition();
    setEditForm((prev) => ({
      ...prev,
      position: { ...currentPosition, ...updates },
    }));
  };

  const toggleGroup = (group: string) => {
    const currentGroups = editForm.groups;
    if (currentGroups.includes(group)) {
      updateEditForm({ groups: currentGroups.filter((g) => g !== group) });
    } else {
      updateEditForm({ groups: [...currentGroups, group] });
    }
  };

  const toggleTag = (tag: string) => {
    const currentTags = editForm.tags;
    if (currentTags.includes(tag)) {
      updateEditForm({ tags: currentTags.filter((t) => t !== tag) });
    } else {
      updateEditForm({ tags: [...currentTags, tag] });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            disabled={disabled}
            className="input-terminal text-sm"
            placeholder="按代码或名称搜索..."
          />
        </div>
        <select
          value={filterGroup}
          onChange={(e) => setFilterGroup(e.target.value)}
          disabled={disabled}
          className="input-terminal text-sm w-full sm:w-40"
        >
          <option value="">全部分组</option>
          {allGroups.map((g) => (
            <option key={g} value={g}>{g}</option>
          ))}
        </select>
        <button
          type="button"
          onClick={handleAddNew}
          disabled={disabled}
          className="btn-primary text-sm whitespace-nowrap"
        >
          + 添加证券
        </button>
      </div>

      {editingIndex !== null ? (
        <div className="rounded-xl border border-white/10 bg-elevated/60 p-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs uppercase tracking-wide text-muted mb-2">
                代码 *
              </label>
              <input
                type="text"
                value={editForm.code}
                onChange={(e) => updateEditForm({ code: e.target.value })}
                disabled={disabled}
                className="input-terminal"
                placeholder="例如: 600519.SH"
              />
            </div>
            <div>
              <label className="block text-xs uppercase tracking-wide text-muted mb-2">
                名称 *
              </label>
              <input
                type="text"
                value={editForm.name}
                onChange={(e) => updateEditForm({ name: e.target.value })}
                disabled={disabled}
                className="input-terminal"
                placeholder="例如: 贵州茅台"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs uppercase tracking-wide text-muted mb-2">
                资产类型
              </label>
              <select
                value={editForm.assetType}
                onChange={(e) => updateEditForm({ assetType: e.target.value as AssetType })}
                disabled={disabled}
                className="input-terminal"
              >
                {ASSET_TYPES.map((t) => (
                  <option key={t} value={t}>{ASSET_TYPE_LABELS[t]}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs uppercase tracking-wide text-muted mb-2">
                关联参考
              </label>
              <input
                type="text"
                value={editForm.linkedRef}
                onChange={(e) => updateEditForm({ linkedRef: e.target.value })}
                disabled={disabled}
                className="input-terminal"
                placeholder="例如: 801710.SI"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wide text-muted mb-2">
              分组
            </label>
            <div className="flex flex-wrap gap-2">
              {allGroups.map((g) => (
                <button
                  key={g}
                  type="button"
                  onClick={() => toggleGroup(g)}
                  disabled={disabled}
                  className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                    editForm.groups.includes(g)
                      ? 'border-cyan bg-cyan/20 text-cyan'
                      : 'border-white/10 bg-white/5 text-secondary hover:border-white/20'
                  }`}
                >
                  {g}
                </button>
              ))}
              <input
                type="text"
                placeholder="新分组..."
                className="px-3 py-1 text-xs rounded-full border border-dashed border-white/20 bg-transparent text-secondary focus:border-cyan focus:outline-none"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                    toggleGroup(e.currentTarget.value.trim());
                    e.currentTarget.value = '';
                  }
                }}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wide text-muted mb-2">
              标签
            </label>
            <div className="flex flex-wrap gap-2">
              {editForm.tags.map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => toggleTag(t)}
                  disabled={disabled}
                  className="px-3 py-1 text-xs rounded-full border border-purple/50 bg-purple/20 text-purple"
                >
                  {t} ×
                </button>
              ))}
              <input
                type="text"
                placeholder="添加标签..."
                className="px-3 py-1 text-xs rounded-full border border-dashed border-white/20 bg-transparent text-secondary focus:border-purple focus:outline-none"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                    toggleTag(e.currentTarget.value.trim());
                    e.currentTarget.value = '';
                  }
                }}
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs uppercase tracking-wide text-muted">
                持仓
              </label>
              <label className="flex items-center gap-2 text-xs text-secondary">
                <input
                  type="checkbox"
                  checked={editForm.position !== null}
                  onChange={(e) => updateEditForm({ position: e.target.checked ? createDefaultPosition() : null })}
                  disabled={disabled}
                  className="rounded border-white/20"
                />
                有持仓
              </label>
            </div>
            {editForm.position ? (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3 rounded-lg bg-white/5">
                <div>
                  <label className="block text-xs text-muted mb-1">股数</label>
                  <input
                    type="number"
                    value={editForm.position.shares}
                    onChange={(e) => updatePosition({ shares: parseInt(e.target.value, 10) || 0 })}
                    disabled={disabled}
                    min={0}
                    className="input-terminal text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted mb-1">成本</label>
                  <input
                    type="number"
                    value={editForm.position.cost}
                    onChange={(e) => updatePosition({ cost: parseFloat(e.target.value) || 0 })}
                    disabled={disabled}
                    min={0}
                    step={0.01}
                    className="input-terminal text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted mb-1">当前市值</label>
                  <input
                    type="number"
                    value={editForm.position.currentValue}
                    onChange={(e) => updatePosition({ currentValue: parseFloat(e.target.value) || 0 })}
                    disabled={disabled}
                    min={0}
                    step={0.01}
                    className="input-terminal text-sm"
                  />
                </div>
              </div>
            ) : (
              <p className="text-xs text-muted p-3 rounded-lg bg-white/5">无持仓 (仅关注)</p>
            )}
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wide text-muted mb-2">
              策略备注
            </label>
            <textarea
              value={editForm.strategyNote}
              onChange={(e) => updateEditForm({ strategyNote: e.target.value })}
              disabled={disabled}
              className="input-terminal text-sm min-h-[60px] resize-y"
              placeholder="交易策略备注..."
            />
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wide text-muted mb-2">
              私人备注
            </label>
            <textarea
              value={editForm.privateNote}
              onChange={(e) => updateEditForm({ privateNote: e.target.value })}
              disabled={disabled}
              className="input-terminal text-sm min-h-[60px] resize-y"
              placeholder="个人备注..."
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
            <button
              type="button"
              onClick={handleCancel}
              disabled={disabled}
              className="btn-secondary text-sm"
            >
              取消
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={disabled || !editForm.code.trim() || !editForm.name.trim()}
              className="btn-primary text-sm"
            >
              {editingIndex === -1 ? '添加' : '保存'}
            </button>
          </div>
        </div>
      ) : null}

      <div className="space-y-2">
        {filteredSecurities.length === 0 ? (
          <div className="text-center text-sm text-muted py-8">
            {securities.length === 0 ? '暂无证券' : '无匹配证券'}
          </div>
        ) : (
          filteredSecurities.map((security, idx) => (
            <div
              key={`${security.code}-${idx}`}
              className="flex items-center gap-3 p-3 rounded-lg border border-white/8 bg-elevated/40 hover:border-white/16 transition-colors"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm text-cyan">{security.code}</span>
                  <span className="text-sm text-white">{security.name}</span>
                  {security.position ? (
                    <span className="px-2 py-0.5 text-xs rounded bg-green-500/20 text-green-400">
                      持仓
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 text-xs rounded bg-white/10 text-muted">
                      关注
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {security.groups.map((g) => (
                    <span key={g} className="px-2 py-0.5 text-xs rounded bg-cyan/10 text-cyan">
                      {g}
                    </span>
                  ))}
                  {security.tags.slice(0, 3).map((t) => (
                    <span key={t} className="px-2 py-0.5 text-xs rounded bg-purple/10 text-purple">
                      {t}
                    </span>
                  ))}
                  {security.tags.length > 3 && (
                    <span className="px-2 py-0.5 text-xs text-muted">+{security.tags.length - 3}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => handleEdit(idx)}
                  disabled={disabled}
                  className="p-2 text-secondary hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(idx)}
                  disabled={disabled}
                  className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
