import type { McpToolInfo } from '../api/mcp'
import './McpToolList.css'

export interface McpToolListItemProps {
  tool: McpToolInfo
  selectable?: boolean
  checked?: boolean
  onChange?: (checked: boolean) => void
}

export function McpToolListItem({
  tool,
  selectable = false,
  checked = false,
  onChange,
}: McpToolListItemProps) {
  const desc = tool.description?.trim()

  if (selectable) {
    return (
      <div className={`mcp-tool-item ${checked ? 'is-selected' : ''}`}>
        <label className="mcp-tool-item-label">
          <input
            type="checkbox"
            checked={checked}
            onChange={(event) => onChange?.(event.target.checked)}
          />
          <div className="mcp-tool-item-body">
            <div className="mcp-tool-item-title-row">
              <span className="mcp-tool-item-name">{tool.name}</span>
              {checked ? <span className="mcp-tool-item-badge">已选</span> : null}
            </div>
            {desc ? (
              <p className="mcp-tool-item-desc">{desc}</p>
            ) : (
              <p className="mcp-tool-item-desc mcp-tool-item-desc--empty">暂无描述</p>
            )}
          </div>
        </label>
      </div>
    )
  }

  return (
    <div className="mcp-tool-item">
      <div className="mcp-tool-item-static">
        <div className="mcp-tool-item-body">
          <div className="mcp-tool-item-title-row">
            <span className="mcp-tool-item-name">{tool.name}</span>
          </div>
          {desc ? (
            <p className="mcp-tool-item-desc">{desc}</p>
          ) : (
            <p className="mcp-tool-item-desc mcp-tool-item-desc--empty">暂无描述</p>
          )}
        </div>
      </div>
    </div>
  )
}

interface McpToolListProps {
  tools: McpToolInfo[]
  selectable?: boolean
  selectedNames?: string[]
  onToggle?: (toolName: string, checked: boolean) => void
  onSelectAll?: () => void
  onClearAll?: () => void
  variant?: 'default' | 'modal'
}

export function McpToolList({
  tools,
  selectable = false,
  selectedNames = [],
  onToggle,
  onSelectAll,
  onClearAll,
  variant = 'default',
}: McpToolListProps) {
  const selectedCount = selectedNames.length

  return (
    <div>
      {selectable && tools.length > 0 ? (
        <div className="mcp-tool-list-toolbar">
          <span>
            已选 <span className="mcp-tool-list-count">{selectedCount}</span> / {tools.length}{' '}
            个工具
          </span>
          <div className="mcp-tool-list-toolbar-actions">
            <button type="button" onClick={onSelectAll} disabled={selectedCount === tools.length}>
              全选
            </button>
            <button type="button" onClick={onClearAll} disabled={selectedCount === 0}>
              全不选
            </button>
          </div>
        </div>
      ) : null}

      <div className={`mcp-tool-list ${variant === 'modal' ? 'mcp-tool-list--modal' : ''}`}>
        {tools.map((tool) => (
          <McpToolListItem
            key={tool.fullName}
            tool={tool}
            selectable={selectable}
            checked={selectedNames.includes(tool.name)}
            onChange={(checked) => onToggle?.(tool.name, checked)}
          />
        ))}
      </div>
    </div>
  )
}
