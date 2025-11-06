import { useState, useRef, useEffect } from "react";
import { Check, X, Edit2 } from "lucide-react";

type InlineEditableTitleProps = {
  value: string;
  onSave: (newValue: string) => void;
  className?: string;
  placeholder?: string;
  persistKey?: string; // optional localStorage key to persist interim edits
  onDraftChange?: (hasDraft: boolean, draftValue: string) => void;
};

export function InlineEditableTitle({ value, onSave, className = "", placeholder = "Enter title", persistKey, onDraftChange }: InlineEditableTitleProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(() => {
    if (persistKey && typeof window !== "undefined") {
      try {
        const cached = localStorage.getItem(persistKey);
        if (cached) return cached;
      } catch {}
    }
    return value;
  });
  const [showSaved, setShowSaved] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  useEffect(() => {
    setEditValue((prev) => {
      // If persisted value exists and differs, prefer persisted; else align with prop
      if (persistKey && typeof window !== "undefined") {
        try {
          const cached = localStorage.getItem(persistKey);
          if (cached && cached !== prev) return cached;
        } catch {}
      }
      return value;
    });
    if (persistKey && typeof window !== "undefined" && onDraftChange) {
      try {
        const cached = localStorage.getItem(persistKey);
        onDraftChange(!!cached && cached.trim() !== (value || "").trim(), cached || "");
      } catch {}
    }
  }, [value, persistKey]);

  const handleSave = () => {
    if (editValue.trim() && editValue !== value) {
      onSave(editValue.trim());
      // Tiny inline toast
      setShowSaved(true);
      setTimeout(() => setShowSaved(false), 1200);
    } else {
      setEditValue(value);
    }
    // Clear persisted draft on successful save or cancel
    if (persistKey && typeof window !== "undefined") {
      try {
        localStorage.removeItem(persistKey);
      } catch {}
    }
    if (onDraftChange) onDraftChange(false, "");
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditValue(value);
    if (persistKey && typeof window !== "undefined") {
      try {
        localStorage.removeItem(persistKey);
      } catch {}
    }
    if (onDraftChange) onDraftChange(false, "");
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSave();
    } else if (e.key === "Escape") {
      handleCancel();
    }
  };

  if (isEditing) {
    return (
      <div className="flex items-center gap-2">
        <input
          ref={inputRef}
          type="text"
          value={editValue}
          onChange={(e) => {
            const v = e.target.value;
            setEditValue(v);
            if (persistKey && typeof window !== "undefined") {
              try {
                localStorage.setItem(persistKey, v);
              } catch {}
            }
            if (onDraftChange) onDraftChange(v.trim() !== (value || "").trim(), v);
          }}
          onKeyDown={handleKeyDown}
          onBlur={handleSave}
          placeholder={placeholder}
          className={`${className} border-b-2 border-primary bg-transparent focus:outline-none`}
          style={{ width: `${Math.max(editValue.length * 10, 200)}px` }}
        />
        <button
          onClick={handleSave}
          className="w-6 h-6 rounded bg-green-50 hover:bg-green-100 flex items-center justify-center text-green-600 transition-colors"
          title="Save"
        >
          <Check size={14} />
        </button>
        <button
          onClick={handleCancel}
          className="w-6 h-6 rounded bg-red-50 hover:bg-red-100 flex items-center justify-center text-red-600 transition-colors"
          title="Cancel"
        >
          <X size={14} />
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => setIsEditing(true)}
        className={`${className} group flex items-center gap-2 hover:text-primary transition-colors`}
        title="Click to edit"
      >
        <span>{value}</span>
        <Edit2 size={14} className="opacity-0 group-hover:opacity-100 transition-opacity text-gray-400" />
      </button>
      {showSaved && (
        <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700 border border-green-200 animate-in fade-in duration-150">
          <Check size={12} /> Saved
        </span>
      )}
    </div>
  );
}
