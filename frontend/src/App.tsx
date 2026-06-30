import { useEffect, useState } from 'react'
import { AuthScreen } from './components/AuthScreen'
import { DocumentsView } from './components/DocumentsView'
import { HistoryView } from './components/HistoryView'
import { Icon } from './components/Icon'
import { SearchView } from './components/SearchView'
import { auth, documentsApi, hasSession, healthCheck, historyApi, searchApi } from './services/api'
import type { DocumentItem, HistoryItem, SearchResult, UploadItem } from './types'

type View = 'search' | 'documents' | 'history'
const msg = (e: unknown) => e instanceof Error ? e.message : 'Неизвестная ошибка'

export default function App() {
  const [session, setSession] = useState(hasSession()), [view, setView] = useState<View>('search'), [mobile, setMobile] = useState(false)
  const [documents, setDocuments] = useState<DocumentItem[]>([]), [history, setHistory] = useState<HistoryItem[]>([]), [uploads, setUploads] = useState<UploadItem[]>([])
  const [query, setQuery] = useState(''), [documentId, setDocumentId] = useState(''), [results, setResults] = useState<SearchResult[]>([])
  const [total, setTotal] = useState(0), [page, setPage] = useState(0), [searched, setSearched] = useState(false), [loading, setLoading] = useState(false)
  const [error, setError] = useState(''), [detail, setDetail] = useState<DocumentItem | null>(null), [online, setOnline] = useState<boolean | null>(null)

  async function loadData() { try { const [docs, hist] = await Promise.all([documentsApi.list(), historyApi.list()]); setDocuments(docs.items); setHistory(hist.items) } catch (e) { setError(msg(e)) } }
  useEffect(() => { if (session) { loadData(); healthCheck().then(setOnline).catch(() => setOnline(false)) } }, [session])
  useEffect(() => { const expired = () => setSession(false); window.addEventListener('session-expired', expired); return () => window.removeEventListener('session-expired', expired) }, [])

  async function runSearch(nextPage = 0) {
    if (!query.trim()) return; setLoading(true); setError('')
    try { const data = await searchApi.search(query.trim(), documentId, nextPage * 10); setResults(data.items); setTotal(data.total); setPage(nextPage); setSearched(true); historyApi.list().then(x => setHistory(x.items)) }
    catch (e) { setError(msg(e)) } finally { setLoading(false) }
  }
  async function uploadFiles(files: File[]) {
    for (const file of files) {
      const id = `${file.name}-${file.lastModified}`
      if (file.size > 20 * 1024 * 1024) { setUploads(x => [...x, { id, name: file.name, progress: 100, state: 'error', message: 'Файл больше 20 МБ' }]); continue }
      setUploads(x => [...x.filter(u => u.id !== id), { id, name: file.name, progress: 3, state: 'uploading' }])
      try {
        const doc = await documentsApi.upload(file, p => setUploads(x => x.map(u => u.id === id ? { ...u, progress: Math.min(80, p * .8) } : u)))
        setUploads(x => x.map(u => u.id === id ? { ...u, progress: 84, state: 'indexing' } : u)); setDocuments(x => [doc, ...x])
        let current = doc
        for (let tries = 0; tries < 30 && !['processed', 'failed'].includes(current.status); tries++) { await new Promise(r => setTimeout(r, 1500)); current = await documentsApi.get(doc.id); setDocuments(x => x.map(d => d.id === current.id ? current : d)); setUploads(x => x.map(u => u.id === id ? { ...u, progress: Math.min(98, 84 + tries / 2) } : u)) }
        setUploads(x => x.map(u => u.id === id ? { ...u, progress: 100, state: current.status === 'processed' ? 'done' : 'error', message: current.error_message || undefined } : u))
      } catch (e) { setUploads(x => x.map(u => u.id === id ? { ...u, progress: 100, state: 'error', message: msg(e) } : u)) }
    }
  }
  async function deleteDocument(id: string) { if (!confirm('Удалить документ и его индекс?')) return; try { await documentsApi.delete(id); setDocuments(x => x.filter(d => d.id !== id)); if (documentId === id) setDocumentId('') } catch (e) { setError(msg(e)) } }
  async function openDocument(doc: DocumentItem) { try { setDetail(await documentsApi.get(doc.id)) } catch (e) { setError(msg(e)) } }
  async function deleteHistory(id: string) { try { await historyApi.delete(id); setHistory(x => x.filter(i => i.id !== id)) } catch (e) { setError(msg(e)) } }
  async function clearHistory() { if (!confirm('Очистить всю историю поиска?')) return; try { await historyApi.clear(); setHistory([]) } catch (e) { setError(msg(e)) } }
  function repeat(item: HistoryItem) { setQuery(item.query); setDocumentId(item.document_id || ''); setView('search') }
  async function logout() { await auth.logout(); setSession(false) }

  if (!session) return <AuthScreen onSuccess={() => setSession(true)}/>
  const email = localStorage.getItem('user_email') || 'Пользователь'
  return <div className="app-shell"><aside className={mobile ? 'open' : ''}><a className="brand" href="#" onClick={() => setView('search')}><Icon name="heart"/><span>знание</span></a><button className="mobile-close" onClick={() => setMobile(false)}><Icon name="close"/></button><nav>{([['search','search','Поиск'],['documents','file','Материалы'],['history','history','История']] as const).map(([id, icon, label]) => <button key={id} className={view === id ? 'active' : ''} onClick={() => { setView(id); setMobile(false) }}><Icon name={icon}/><span>{label}</span>{id === 'documents' && <b>{documents.length}</b>}</button>)}</nav><div className="aside-foot"><span className={`connection ${online ? 'online' : ''}`}><i/>{online === null ? 'Проверка API' : online ? 'Система работает' : 'API недоступен'}</span><div className="profile"><span>{email.slice(0, 2).toUpperCase()}</span><div><strong title={email}>{email}</strong><small>Исследователь</small></div><button title="Выйти" onClick={logout}><Icon name="logout" size={19}/></button></div></div></aside>
    <main className="main-content"><button className="mobile-menu" onClick={() => setMobile(true)}><Icon name="menu"/></button>{error && <div className="toast"><span>{error}</span><button onClick={() => setError('')}><Icon name="close" size={17}/></button></div>}{view === 'search' && <SearchView query={query} setQuery={setQuery} documentId={documentId} setDocumentId={setDocumentId} documents={documents} results={results} total={total} page={page} loading={loading} searched={searched} onSearch={runSearch}/>} {view === 'documents' && <DocumentsView documents={documents} uploads={uploads} onFiles={uploadFiles} onDelete={deleteDocument} onSelect={openDocument}/>} {view === 'history' && <HistoryView items={history} onRepeat={repeat} onDelete={deleteHistory} onClear={clearHistory}/>}</main>
    {detail && <div className="modal-backdrop" onMouseDown={() => setDetail(null)}><section className="modal" onMouseDown={e => e.stopPropagation()}><button className="modal-close" onClick={() => setDetail(null)}><Icon name="close"/></button><span className={`file-tile large ${detail.content_type.includes('pdf') ? 'pdf' : 'docx'}`}>{detail.content_type.includes('pdf') ? 'PDF' : 'DOC'}</span><span className="section-index">карточка документа</span><h2>{detail.file_name}</h2><dl><div><dt>Статус</dt><dd>{detail.status}</dd></div><div><dt>Размер</dt><dd>{(detail.size_bytes / 1024).toFixed(0)} КБ</dd></div><div><dt>Фрагментов</dt><dd>{detail.chunks_count}</dd></div><div><dt>Добавлен</dt><dd>{new Date(detail.created_at).toLocaleString('ru')}</dd></div></dl>{detail.error_message && <p className="form-error">{detail.error_message}</p>}<button className="primary wide" onClick={() => { setDocumentId(detail.id); setView('search'); setDetail(null) }}>Искать в документе<Icon name="arrow"/></button></section></div>}
  </div>
}
