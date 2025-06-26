const clearCacheBtn = document.createElement('button');
clearCacheBtn.textContent = 'Limpar Cache';
clearCacheBtn.className = 'clear-cache-btn';
clearCacheBtn.onclick = async () => {
  clearCacheBtn.disabled = true;
  clearCacheBtn.textContent = 'A limpar...';
  try {
    const resp = await fetch('http://localhost:5000/api/cache/clear', { method: 'POST' });
    if (resp.ok) {
      clearCacheBtn.textContent = 'Cache limpo!';
      setTimeout(() => { clearCacheBtn.textContent = 'Limpar Cache'; clearCacheBtn.disabled = false; }, 2000);
    } else {
      clearCacheBtn.textContent = 'Erro ao limpar';
      setTimeout(() => { clearCacheBtn.textContent = 'Limpar Cache'; clearCacheBtn.disabled = false; }, 2000);
    }
  } catch {
    clearCacheBtn.textContent = 'Erro ao limpar';
    setTimeout(() => { clearCacheBtn.textContent = 'Limpar Cache'; clearCacheBtn.disabled = false; }, 2000);
  }
};
document.querySelector('.sidebar').appendChild(clearCacheBtn); 