document.querySelectorAll('.flash').forEach(el => { setTimeout(() => { el.style.opacity='0'; el.style.transition='opacity .5s'; }, 5000); });
