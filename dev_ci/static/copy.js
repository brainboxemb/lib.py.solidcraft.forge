(() => {
  const copyIcon = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="11" height="11" rx="2"></rect><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"></path></svg>';
  const doneIcon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"></path></svg>';

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const helper = document.createElement('textarea');
    helper.value = text;
    helper.setAttribute('readonly', '');
    helper.style.position = 'fixed';
    helper.style.opacity = '0';
    document.body.appendChild(helper);
    helper.select();
    document.execCommand('copy');
    helper.remove();
  }

  document.querySelectorAll('pre > code').forEach((code) => {
    const pre = code.parentElement;
    if (!pre || pre.parentElement?.classList.contains('code-block')) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'code-block';
    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(pre);

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'code-copy';
    button.title = 'Copy code';
    button.setAttribute('aria-label', 'Copy code');
    button.innerHTML = copyIcon;
    wrapper.appendChild(button);

    button.addEventListener('click', async () => {
      try {
        await copyText(code.textContent);
        button.innerHTML = doneIcon;
        button.classList.add('copied');
        button.title = 'Copied';
        button.setAttribute('aria-label', 'Copied');
        window.setTimeout(() => {
          button.innerHTML = copyIcon;
          button.classList.remove('copied');
          button.title = 'Copy code';
          button.setAttribute('aria-label', 'Copy code');
        }, 1400);
      } catch (_error) {
        button.title = 'Copy failed';
        button.setAttribute('aria-label', 'Copy failed');
      }
    });
  });
})();
