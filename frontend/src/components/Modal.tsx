import React, { useEffect, useRef } from "react";
import { X } from "lucide-react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children }) => {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handleKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleKey);
      document.body.style.overflow = "";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90"
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
    >
      <div
        className="relative w-full max-w-2xl bg-void border-2 border-rule shadow-hard"
      >
        {/* Title bar */}
        <div className="flex items-center justify-between px-4 py-3 bg-slab border-b-2 border-rule">
          <span className="font-mono font-bold text-[11px] text-paper uppercase tracking-widest">
            // {title.toUpperCase()}
          </span>
          <button
            onClick={onClose}
            className="p-1 border-2 border-rule2 text-muted hover:border-rule hover:text-paper cursor-pointer"
            aria-label="Close"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="overflow-hidden">
          {children}
        </div>
      </div>
    </div>
  );
};
