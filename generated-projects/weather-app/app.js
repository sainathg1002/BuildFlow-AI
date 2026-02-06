// Get weather data from API
fetch("https://api.openweathermap.org/data/2.5/weather?q={city}&appid=YOUR_API_KEY&units=metric")
  .then(response => response.json())
  .then(data => {
    const weatherElement = document.getElementById("weather-result");
    weatherElement.innerText = `Weather in ${data.name}: ${data.weather[0].description}
Temperature: ${data.main.temp}°C`;
  });