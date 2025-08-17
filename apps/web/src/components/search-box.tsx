'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

interface SearchResult {
  slug: string;
  name_kr: string;
  name_en: string;
  score: number;
}

export default function SearchBox() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [suggestion, setSuggestion] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  // Focus with '/'
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === '/' && !(e.target instanceof HTMLInputElement) && !(e.target instanceof HTMLTextAreaElement) && !(e.target as HTMLElement).isContentEditable) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, []);

  // Debounced search
  useEffect(() => {
    if (!query) {
      setResults([]);
      setSuggestion(null);
      return;
    }
    const id = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        if (res.ok) {
          const data = await res.json();
          setResults(data.results ?? []);
          setSuggestion(data.suggestion ?? null);
        } else {
          setResults([]);
          setSuggestion(null);
        }
      } catch {
        setResults([]);
        setSuggestion(null);
      }
    }, 300);
    return () => clearTimeout(id);
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && results[0]) {
      router.push(`/i/${results[0].slug}`);
    }
  };

  const lowConfidence = results[0] && results[0].score < 0.5;

  return (
    <div className="relative">
      <Input
        ref={inputRef}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Search"
      />
      {results.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full rounded-md border bg-background shadow">
          {results.map((r, idx) => (
            <li
              key={r.slug}
              className={cn(
                'cursor-pointer px-3 py-2 hover:bg-accent',
                lowConfidence && idx === 0 ? 'bg-yellow-100' : ''
              )}
              onMouseDown={() => router.push(`/i/${r.slug}`)}
            >
              {r.name_kr || r.name_en}
            </li>
          ))}
        </ul>
      )}
      {suggestion && lowConfidence && (
        <div className="mt-2 text-sm text-yellow-600">
          Did you mean <span className="font-semibold">{suggestion}</span>?
        </div>
      )}
    </div>
  );
}
