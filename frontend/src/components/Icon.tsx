import type { ReactNode, SVGProps } from 'react'

const paths: Record<string, ReactNode> = {
  heart: <><path d="M12 20s-7-4.35-9.2-8.3C.8 8.1 2.7 4.5 6.3 4.2 8.4 4 10.2 5.1 12 7c1.8-1.9 3.6-3 5.7-2.8 3.6.3 5.5 3.9 3.5 7.5C19 15.65 12 20 12 20Z"/><path d="M7 10.5h2.5L11 8l2 5 1.5-2.5H17"/></>,
  search: <><circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 4 4"/></>, file: <><path d="M6 3h8l4 4v14H6z"/><path d="M14 3v5h4M9 13h6M9 17h4"/></>,
  history: <><path d="M4 5v5h5"/><path d="M5.5 16.5A8 8 0 1 0 4 10"/><path d="M12 7v5l3 2"/></>, upload: <><path d="M12 16V4m0 0L7 9m5-5 5 5"/><path d="M5 14v6h14v-6"/></>,
  trash: <><path d="M4 7h16M9 7V4h6v3m3 0-1 14H7L6 7M10 11v6M14 11v6"/></>, logout: <><path d="M14 4h6v16h-6M10 8l4 4-4 4m4-4H3"/></>, arrow: <><path d="M5 12h14m-5-5 5 5-5 5"/></>,
  close: <path d="m6 6 12 12M18 6 6 18"/>, check: <path d="m5 12 4 4L19 6"/>, chevron: <path d="m9 18 6-6-6-6"/>, menu: <path d="M4 7h16M4 12h16M4 17h16"/>,
}
export function Icon({ name, size = 22, ...props }: SVGProps<SVGSVGElement> & { name: string; size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name]}</svg>
}
