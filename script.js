// This code was given by ChatGPT as I do not know how to code in javascript
// This code is for a simple temperature slider that updates the displayed temperature in Fahrenheit as the slider is moved.
const slider = document.getElementById('heatSlider');
    const tempDisplay = document.getElementById('temperature');

    slider.addEventListener('input', () => {
      tempDisplay.textContent = 'Set Temperature: ' + slider.value + '°F';
    });

const minusBtn = document.getElementById("decrease");
const plusBtn = document.getElementById("increase");

//const slider = document.getElementById('heatSlider');
// Force the slider to accept step=1
slider.step = 1;

minusBtn.addEventListener('click', () => {
  let v = +slider.value;
  if (v > +slider.min) {
    slider.value = v - 1;            // now valid because step=1
    tempDisplay.textContent = 'Set Temperature: ' + slider.value + '°F';
  }
});

plusBtn.addEventListener('click', () => {
  let v = +slider.value;
  if (v < +slider.max) {
    slider.value = v + 1;
    tempDisplay.textContent = 'Set Temperature: ' + slider.value + '°F';
  }
});

      