// static/js/script.js

// Grab all the elements once at load
const setTempEl      = document.getElementById('temperature');
const currentTempEl  = document.getElementById('currentTemperature');
const slider         = document.getElementById('heatSlider');
const decreaseBtn    = document.getElementById('decrease');
const increaseBtn    = document.getElementById('increase');
const powerSwitch    = document.getElementById('power');

// 1) Ensure the slider moves in steps of 1
slider.step = 1;

// 2) Initialize the “Set Temperature” display
setTempEl.textContent = `Set Temperature: ${slider.value}°F`;

// 3) Update “Set Temperature” on slider drag and send to backend
slider.addEventListener('input', async () => {
  setTempEl.textContent = `Set Temperature: ${slider.value}°F`;
  try {
    await fetch('/api/heater/set', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({value: Number(slider.value)})
    });
  } catch (err) {
    console.error('Failed to set temperature:', err);
  }
});

// 4) Increase / Decrease buttons
increaseBtn.addEventListener('click', () => {
  slider.value = Math.min(Number(slider.max), Number(slider.value) + Number(slider.step));
  slider.dispatchEvent(new Event('input'));
});
decreaseBtn.addEventListener('click', () => {
  slider.value = Math.max(Number(slider.min), Number(slider.value) - Number(slider.step));
  slider.dispatchEvent(new Event('input'));
});

// 5) Power switch toggles heater on/off
powerSwitch.addEventListener('change', async () => {
  const action = powerSwitch.checked ? 'on' : 'off';
  try {
    await fetch(`/api/heater/${action}`, {method: 'POST'});
  } catch (err) {
    console.error(`Failed to turn heater ${action}:`, err);
  }
});

// 6) Poll the current temperature from backend
async function refreshTemp() {
  let text = 'Current Temperature: --°F';
  try {
    const resp = await fetch('/api/temperature');
    if (resp.ok) {
      const data = await resp.json();
      if (data.temperature != null) {
        text = `Current Temperature: ${data.temperature.toFixed(1)}°F`;
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
