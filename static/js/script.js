// static/js/script.js

document.addEventListener('DOMContentLoaded', () => {
  const slider       = document.getElementById('heatSlider');
  const decreaseBtn  = document.getElementById('decrease');
  const increaseBtn  = document.getElementById('increase');
  const powerSwitch  = document.getElementById('power');
  const currentTemp  = document.getElementById('currentTemperature');
  const setTempLabel = document.getElementById('temperature');
  const weatherEl    = document.getElementById('weather');

  // Slider setup
  slider.step = 1;
  setTempLabel.textContent = `Set Temperature: ${slider.value}°F`;

  // Helper: choose an emoji based on the weather description
  function getWeatherIcon(desc) {
    const d = desc.toLowerCase();
    if (d.includes('rain'))      return '🌧️';
    if (d.includes('cloud'))     return '☁️';
    if (d.includes('snow'))      return '❄️';
    if (d.includes('storm') || d.includes('thunder')) return '⛈️';
    if (d.includes('mist')  || d.includes('fog'))     return '🌫️';
    if (d.includes('clear') || d.includes('sun'))     return '☀️';
    return '🌡️';
  }

  // Fetch & display heater state and temperature
  async function refreshTemp() {
    try {
      const resp = await fetch('/api/heater/temp', {
        credentials: 'same-origin'
      });
      if (!resp.ok) throw new Error(resp.status);
      const data = await resp.json();
      currentTemp.textContent = `Current Temperature: ${data.current.toFixed(1)}°F`;
      slider.value           = data.target;
      powerSwitch.checked    = data.is_on;
      setTempLabel.textContent = `Set Temperature: ${data.target}°F`;
    } catch (e) {
      console.error('Error fetching temp:', e);
      currentTemp.textContent = 'Current Temperature: --°F';
    }
  }

  // Fetch & display outdoor weather every 10 minutes
  async function refreshWeather() {
    try {
      const resp = await fetch('/api/weather', {
        credentials: 'same-origin'
      });
      if (!resp.ok) throw new Error(resp.status);
      const { temp, desc } = await resp.json();
      if (temp != null) {
        const icon = getWeatherIcon(desc);
        weatherEl.innerHTML = `<span class="icon">${icon}</span>Outdoor: ${Math.round(temp)}°F, ${desc}`;
      } else {
        weatherEl.textContent = 'Weather unavailable';
      }
    } catch (e) {
      console.error('Error fetching weather:', e);
      weatherEl.textContent = 'Weather error';
    }
  }

  // Send new target temperature to back-end
  async function setTarget(t) {
    try {
      const resp = await fetch('/api/heater/set', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: t })
      });
      if (!resp.ok) throw new Error(resp.status);
    } catch (e) {
      console.error('Error setting target:', e);
    }
  }

  // Event listeners
  slider.addEventListener('input', () => {
    const t = Number(slider.value);
    setTempLabel.textContent = `Set Temperature: ${t}°F`;
    setTarget(t);
  });

  increaseBtn.addEventListener('click', () => {
    let v = Math.min(+slider.max, +slider.value + +slider.step);
    slider.value = v;
    slider.dispatchEvent(new Event('input'));
  });

  decreaseBtn.addEventListener('click', () => {
    let v = Math.max(+slider.min, +slider.value - +slider.step);
    slider.value = v;
    slider.dispatchEvent(new Event('input'));
  });

  powerSwitch.addEventListener('change', async () => {
    const action = powerSwitch.checked ? 'on' : 'off';
    try {
      const resp = await fetch(`/api/heater/${action}`, {
        method: 'POST',
        credentials: 'same-origin'
      });
      if (!resp.ok) throw new Error(resp.status);
    } catch (e) {
      console.error(`Error turning heater ${action}:`, e);
    }
  });

  // Initial load & polling
  refreshTemp();
  setInterval(refreshTemp, 2000);

  refreshWeather();
  setInterval(refreshWeather, 10 * 60 * 1000);
});
