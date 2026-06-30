import { FormEvent } from 'react'
import type { DocumentItem, SearchResult } from '../types'
import { Icon } from './Icon'

function Highlight({ html }: { html: string }) {
  return <>{html.split(/(<mark>.*?<\/mark>)/gi).map((part, i) => /^<mark>/i.test(part) ? <mark key={i}>{part.replace(/<\/?mark>/gi, '')}</mark> : part)}</>
}

type Props = { query: string; setQuery: (v: string) => void; documentId: string; setDocumentId: (v: string) => void; documents: DocumentItem[]; results: SearchResult[]; total: number; page: number; loading: boolean; searched: boolean; onSearch: (page?: number) => void }
export function SearchView({ query, setQuery, documentId, setDocumentId, documents, results, total, page, loading, searched, onSearch }: Props) {
  function submit(e: FormEvent) { e.preventDefault(); onSearch(0) }
  const pages = Math.ceil(total / 10)
  return <section className="view search-view">
    <header className="search-hero"><span className="section-index">01 / интеллектуальный поиск</span><h1>Найдите нужное.<br/><em>Почувствуйте связь.</em></h1><p>Ищем смысл среди ваших лекций, исследований и заметок.</p></header>
    <form className="search-box" onSubmit={submit}><Icon name="search" size={28}/><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Например: архитектура микросервисов" minLength={1} maxLength={300}/><select value={documentId} onChange={e => setDocumentId(e.target.value)} aria-label="Область поиска"><option value="">Во всей библиотеке</option>{documents.filter(x => x.status === 'processed').map(x => <option key={x.id} value={x.id}>{x.file_name}</option>)}</select><button className="primary" disabled={loading || !query.trim()}>{loading ? 'Ищем…' : 'Найти'}<Icon name="arrow"/></button></form>
    {searched && <div className="results-head"><div><span className="section-index">результаты</span><h2>{total ? `Найдено ${total}` : 'Ничего не найдено'}</h2></div>{total > 0 && <span>страница {page + 1} из {pages}</span>}</div>}
    {searched && total === 0 && !loading && <div className="empty"><span className="empty-orbit"><Icon name="search" size={42}/></span><h3>По вашему запросу ничего не найдено.</h3><p>Попробуйте изменить формулировку</p></div>}
    <div className="results-grid">{results.map((result, index) => <article className="result-card" key={result.chunk_id}><div className="result-meta"><span>{String(page * 10 + index + 1).padStart(2, '0')}</span><span>{result.file_name} · стр. {result.page}</span><b>{Math.round(result.score * 100) / 100}</b></div><p><Highlight html={result.text}/></p><div className="score"><span>релевантность</span><i><b style={{ width: `${Math.min(100, Math.max(8, result.score * 10))}%` }}/></i></div></article>)}</div>
    {pages > 1 && <nav className="pagination" aria-label="Страницы результатов"><button disabled={page === 0} onClick={() => onSearch(page - 1)}>Назад</button>{Array.from({ length: Math.min(pages, 5) }, (_, i) => i).map(i => <button className={i === page ? 'active' : ''} key={i} onClick={() => onSearch(i)}>{i + 1}</button>)}<button disabled={page >= pages - 1} onClick={() => onSearch(page + 1)}>Далее</button></nav>}
  </section>
}
