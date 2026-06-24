def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 100,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if overlap < 0:
        raise ValueError("overlap must not be negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")

    chunks: list[str] = []
    start = 0
    step = chunk_size - overlap

    while start < len(text):
        chunk = text[start:start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks
