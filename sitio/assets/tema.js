// Antes de pintar: tema guardado y marca de que hay JavaScript (activa las animaciones de aparición)
document.documentElement.classList.add("js");
try { if (localStorage.getItem("tema") === "dark") document.documentElement.dataset.theme = "dark"; } catch (e) {}
