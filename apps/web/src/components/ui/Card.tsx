import type { ReactNode } from "react";
import { SectionTitle } from "./SectionTitle";

interface CardProps {
  /** Optional title for the card. Renders a SectionTitle and links via aria-labelledby */
  title?: ReactNode;
  children: ReactNode;
  className?: string;
  /** Identifier for aria-labelledby linkage. If omitted, one is generated when title is string */
  id?: string;
}

export function Card({ title, children, className, id }: CardProps) {
  const titleId = id ? `${id}-title` : typeof title === "string" ? `${title.replace(/\s+/g, "-")}-title` : undefined;
  return (
    <section
      className={`rounded-md border border-gray-700 bg-gray-900 p-6 shadow-sm w-full ${className ?? ""}`.trim()}
      role="region"
      aria-labelledby={title ? titleId : undefined}
      tabIndex={0}
    >
      {title && <SectionTitle id={titleId}>{title}</SectionTitle>}
      {children}
    </section>
  );
}