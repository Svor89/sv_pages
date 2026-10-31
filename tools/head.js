/* тема до отрисовки: выбор кнопкой в шапке (localStorage) → ?theme=light|dark (так её задаёт SV) → тёмная */
(function(){var t;try{t=localStorage.getItem('theme')}catch(e){}t=t||(/[?&]theme=(\w+)/.exec(location.search)||[])[1];if(t==='light')document.documentElement.className='light'})();
