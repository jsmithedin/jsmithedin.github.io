(function () {
  const label = document.querySelector(".header-label");
  if (!label) return;

  const text = label.textContent;
  label.textContent = "";
  label.style.visibility = "visible";

  let i = 0;
  const cursor = document.createElement("span");
  cursor.textContent = "▋";
  cursor.style.cssText = "color: #c8f542; animation: blink 1s step-end infinite;";
  label.appendChild(cursor);

  const style = document.createElement("style");
  style.textContent = "@keyframes blink { 50% { opacity: 0; } }";
  document.head.appendChild(style);

  function type() {
    if (i < text.length) {
      cursor.insertAdjacentText("beforebegin", text[i]);
      i++;
      setTimeout(type, 35 + Math.random() * 25);
    } else {
      setTimeout(() => { cursor.style.display = "none"; }, 1200);
    }
  }

  setTimeout(type, 400);
})();
