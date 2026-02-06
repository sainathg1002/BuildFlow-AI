// Get the find button
const findBtn = document.getElementById('find-btn');

// Add an event listener to the button
findBtn.addEventListener('click', () => {
  // Get the input text
  const textInput = document.getElementById('text-input');
  const text = textInput.value;

  // Use the input text to find keywords
  const keywords = findKeywords(text);

  // Display the keywords
  const keywordResult = document.getElementById('keyword-result');
  keywordResult.innerText = keywords.join(', ');
});

// Function to find keywords
function findKeywords(text) {
  // For this example, we'll just split the text into words and return the unique words
  const words = text.split(' ');
  const uniqueWords = [...new Set(words)];
  return uniqueWords;
}