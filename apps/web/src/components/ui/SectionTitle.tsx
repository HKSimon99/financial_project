import type { ReactNode, ElementType } from "react";

interface SectionTitleProps {
  children: ReactNode;
  /** Heading level or custom component. Defaults to h2 */
  as?: ElementType;
  /** id used for accessibility and anchoring */
  id?: string;
  className?: string;
}

export function SectionTitle({ children, as: Tag = "h2", id, className }: SectionTitleProps) {
  return (
    <Tag
      id={id}
      className={`text-xl font-semibold mb-3 ${className ?? ""}`.trim()}
      tabIndex={0}
    >
      {children}
    </Tag>
  );
}