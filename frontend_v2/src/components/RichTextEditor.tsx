import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import { Bold, Italic, List, ListOrdered } from "lucide-react";

interface Props {
  value: string;
  onChange: (html: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

const TOOLBAR = (editor: ReturnType<typeof useEditor>) =>
  editor
    ? [
        {
          label: "Bold",
          icon: Bold,
          action: () => editor.chain().focus().toggleBold().run(),
          active: editor.isActive("bold"),
        },
        {
          label: "Italic",
          icon: Italic,
          action: () => editor.chain().focus().toggleItalic().run(),
          active: editor.isActive("italic"),
        },
        {
          label: "Bullet list",
          icon: List,
          action: () => editor.chain().focus().toggleBulletList().run(),
          active: editor.isActive("bulletList"),
        },
        {
          label: "Numbered list",
          icon: ListOrdered,
          action: () => editor.chain().focus().toggleOrderedList().run(),
          active: editor.isActive("orderedList"),
        },
      ]
    : [];

export default function RichTextEditor({
  value,
  onChange,
  placeholder = "Describe the product…",
  disabled = false,
}: Props) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({ placeholder }),
    ],
    content: value || "",
    editable: !disabled,
    onUpdate: ({ editor }) => onChange(editor.getHTML()),
  });

  return (
    <div
      className={`rounded-md border border-ink-700 bg-ink-950 focus-within:ring-2 focus-within:ring-naija-600 focus-within:border-transparent overflow-hidden transition-all ${
        disabled ? "opacity-50 pointer-events-none" : ""
      }`}
    >
      {/* Toolbar */}
      <div className="flex items-center gap-0.5 px-2 py-1.5 border-b border-ink-800 bg-ink-900/60">
        {TOOLBAR(editor).map(({ label, icon: Icon, action, active }) => (
          <button
            key={label}
            type="button"
            onMouseDown={(e) => {
              e.preventDefault(); // don't steal focus from editor
              action();
            }}
            title={label}
            className={`p-1.5 rounded transition-colors ${
              active
                ? "bg-naija-700/50 text-naija-300"
                : "text-ink-500 hover:text-ink-200 hover:bg-ink-800"
            }`}
          >
            <Icon size={14} />
          </button>
        ))}
      </div>

      {/* Editor area */}
      <EditorContent
        editor={editor}
        className="rte-content px-3 py-2.5 min-h-[110px] text-sm text-ink-50 focus:outline-none"
      />
    </div>
  );
}
