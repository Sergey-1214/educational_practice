import { DragEvent, useRef, useState } from 'react'
import type { UploadItem } from '../types'
import { Icon } from './Icon'
export function UploadZone({ uploads, onFiles }: { uploads: UploadItem[]; onFiles: (files: File[]) => void }) {
  const input = useRef<HTMLInputElement>(null), [over, setOver] = useState(false)
  const accept = (files: File[]) => onFiles(files.filter(f => /\.(pdf|docx)$/i.test(f.name)))
  function drop(e: DragEvent) { e.preventDefault(); setOver(false); accept(Array.from(e.dataTransfer.files)) }
  const names = { uploading: 'Загрузка…', indexing: 'Индексация…', done: 'Готово', error: 'Ошибка' }
  return <><button className={`dropzone ${over ? 'is-over' : ''}`} onClick={() => input.current?.click()} onDragOver={e => { e.preventDefault(); setOver(true) }} onDragLeave={() => setOver(false)} onDrop={drop}><input ref={input} type="file" accept=".pdf,.docx" multiple hidden onChange={e => accept(Array.from(e.target.files || []))}/><span className="upload-icon"><Icon name="upload" size={32}/></span><strong>Перетащите материалы сюда</strong><span>или выберите PDF и DOCX до 20 МБ</span><i>Можно загрузить несколько файлов</i></button>{uploads.length > 0 && <div className="upload-stack">{uploads.map(item => <div className="upload-row" key={item.id}><span className={`mini-state ${item.state}`}><Icon name={item.state === 'done' ? 'check' : item.state === 'error' ? 'close' : 'file'} size={18}/></span><div><div className="row-head"><strong title={item.name}>{item.name}</strong><span>{names[item.state]}</span></div><div className="progress"><i style={{ width: `${item.progress}%` }}/></div>{item.message && <small>{item.message}</small>}</div></div>)}</div>}</>
}
