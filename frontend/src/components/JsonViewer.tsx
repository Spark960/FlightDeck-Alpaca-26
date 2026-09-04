import React from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

interface JsonViewerProps {
  data: any;
  title?: string;
  maxHeight?: string;
}

const JsonLine: React.FC<{ value: any; depth?: number }> = ({ value, depth = 0 }) => {
  const [collapsed, setCollapsed] = React.useState(depth > 1);
  const indent = depth * 16;

  if (value === null) return <span className="text-muted">null</span>;
  if (typeof value === "boolean")
    return <span className={value ? "text-pos" : "text-neg"}>{String(value)}</span>;
  if (typeof value === "number")
    return <span className="text-info">{value}</span>;
  if (typeof value === "string")
    return <span className="text-y">"{value}"</span>;

  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="text-muted">[]</span>;
    return (
      <span>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="inline-flex items-center gap-0.5 text-paper hover:text-y cursor-pointer"
        >
          {collapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          <span className="text-muted text-[10px]">[{value.length}]</span>
        </button>
        {!collapsed && (
          <span className="block" style={{ marginLeft: indent + 16 }}>
            {value.map((item, i) => (
              <div key={i} className="leading-5">
                <JsonLine value={item} depth={depth + 1} />
                {i < value.length - 1 && <span className="text-rule2">,</span>}
              </div>
            ))}
          </span>
        )}
      </span>
    );
  }

  if (typeof value === "object") {
    const keys = Object.keys(value);
    if (keys.length === 0) return <span className="text-muted">{"{}"}</span>;
    return (
      <span>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="inline-flex items-center gap-0.5 text-paper hover:text-y cursor-pointer"
        >
          {collapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          <span className="text-muted text-[10px]">{"{"}…{"}"}</span>
        </button>
        {!collapsed && (
          <span className="block" style={{ marginLeft: indent + 16 }}>
            {keys.map((key, i) => (
              <div key={key} className="leading-5">
                <span className="text-violet">"{key}"</span>
                <span className="text-muted">: </span>
                <JsonLine value={value[key]} depth={depth + 1} />
                {i < keys.length - 1 && <span className="text-rule2">,</span>}
              </div>
            ))}
          </span>
        )}
      </span>
    );
  }

  return <span className="text-paper">{String(value)}</span>;
};

export const JsonViewer: React.FC<JsonViewerProps> = ({ data, title, maxHeight = "max-h-[70vh]" }) => {
  return (
    <div className="bg-ink border-2 border-rule2">
      {title && (
        <div className="flex items-center gap-3 px-4 py-2 border-b-2 border-rule2 bg-slab">
          <span className="text-pos text-[10px] font-bold font-mono">$</span>
          <span className="font-mono text-[11px] text-paper font-bold">{title}.json</span>
        </div>
      )}
      <div className={`${maxHeight} overflow-auto p-4`}>
        <pre className="font-mono text-[11px] leading-5 text-paper whitespace-pre-wrap break-all">
          <JsonLine value={data} depth={0} />
        </pre>
      </div>
    </div>
  );
};
