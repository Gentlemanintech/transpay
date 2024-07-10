let alertBox = document.querySelector('#alertBox');
const form = document.getElementById('airtimeForm');
const nextButton = document.getElementById('next');
const networkSelect = document.getElementById('network');
const dataSelect = document.getElementById('dataPlan');
const phoneInput = document.getElementById('airtimePhone');
const amountInput = document.getElementById('airtimeAmount');

// This set a timeout for every alert message that appears to dsappear after 6seconds.
setTimeout(() => {
    alertBox.style.display = 'none';
}, 6000);

// this checks if all fields are filled in airtime page then let a user click the next button. 
function validateForm() {
    const isNetworkSelected = networkSelect.value !== 'Please select an option' && networkSelect.value !== '';
    const isPhoneFilled = phoneInput.value.trim() !== '';
    const isAmountFilled = amountInput.value.trim() !== '';

    nextButton.disabled = !(isNetworkSelected && isPhoneFilled && isAmountFilled);
}

networkSelect.addEventListener('change', validateForm);
phoneInput.addEventListener('input', validateForm);
amountInput.addEventListener('input', validateForm);