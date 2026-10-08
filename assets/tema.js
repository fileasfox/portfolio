/* Se carga en <head>, antes de pintar: aplica el tema elegido para que no parpadee al cambiar de página.
   El claro es el predeterminado; el oscuro solo se activa con el interruptor y se recuerda. */
try { if (localStorage.getItem("tema") === "dark") document.documentElement.dataset.theme = "dark"; } catch (e) {}
