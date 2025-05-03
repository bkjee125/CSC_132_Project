// Grab all the elements once at load
const setTempEl      = document.getElementById('temperature');
const currentTempEl  = document.getElementById('currentTemperature');
const slider         = document.getElementById('heatSlider');
const decreaseBtn    = document.getElementById('decrease');
const increaseBtn    = document.getElementById('increase');

// 1) Ensure the slider moves in steps of 1
slider.step = 1;

// 2) Initialize the “Set Temperature” display
setTempEl.textContent = `Set Temperature: ${slider.value}°F`;

// 3) Update “Set Temperature” on slider drag
slider.addEventListener('input', () => {
  setTempEl.textContent = `Set Temperature: ${slider.value}°F`;
});

// 4) Decrease button: move slider down by 1
decreaseBtn.addEventListener('click', () => {
  let v = Number(slider.value);
  if (v > Number(slider.min)) {
    slider.value = v - 1;
    setTempEl.textContent = `Set Temperature: ${slider.value}°F`;
  }
});

// 5) Increase button: move slider up by 1
increaseBtn.addEventListener('click', () => {
  let v = Number(slider.value);
  if (v < Number(slider.max)) {
    slider.value = v + 1;
    setTempEl.textContent = `Set Temperature: ${slider.value}°F`;
  }
});

// 6) Poll the Flask API for the current sensor reading
async function refreshTemp() {
  let text = 'Current Temperature: --°F';
  try {
    const res = await fetch('/api/temperature');
    if (res.ok) {
      const { temperature } = await res.json();
      if (temperature != null) {
        text = `Current Temperature: ${temperature.toFixed(1)}°F`;
      }
    }
  } catch (err) {
    console.error('Failed to fetch temperature:', err);
  }
  currentTempEl.textContent = text;
}

// 7) On page load, start polling every 2 seconds
window.addEventListener('load', () => {
  refreshTemp();                  // initial fetch
  setInterval(refreshTemp, 2000); // fetch every 2 s
});
