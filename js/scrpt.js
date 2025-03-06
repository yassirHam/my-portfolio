
window.onscroll = () => {
    let header = document.querySelector('.header');
    header.classList.toggle('sticky', window.scrollY > 100);

    let sections = document.querySelectorAll('section');
    let navLinks = document.querySelectorAll('header nav a');

    sections.forEach(sec => {
        let top = window.scrollY;
        let offset = sec.offsetTop - 150;
        let height = sec.offsetHeight;
        let id = sec.getAttribute('id');

        if (top >= offset && top < offset + height) {
            navLinks.forEach(links => {
                links.classList.remove('active');
            });
            document.querySelector(`header nav a[href*='${id}']`).classList.add('active');
        }
    });

    menuIcon.classList.remove('bx-x');
    navbar.classList.remove('active');
};

let menuIcon = document.querySelector('#menu-icon');
let navbar = document.querySelector('.navbar');

menuIcon.onclick = () => {
    menuIcon.classList.toggle('bx-x');
    navbar.classList.toggle('active');
};

let darkModeIcon = document.querySelector('#darkMode-icon');
darkModeIcon.onclick = () => {
    darkModeIcon.classList.toggle('bx-sun');
    document.body.classList.toggle('dark-mode');
};

ScrollReveal({
    reset: true,
    distance: '80px',
    duration: 2000,
    delay: 200,
});
ScrollReveal().reveal('.home-content, .heading', { origin: 'top' });
ScrollReveal().reveal('.home-img img, .projects-container, .skills-container, .contact-form', { origin: 'bottom' });
ScrollReveal().reveal('.home-content h1, .about-img img', { origin: 'left' });
ScrollReveal().reveal('.home-content h2, .home-content p, .about-content', { origin: 'right' });

document.getElementById("contactForm").addEventListener("submit", async function (event) {
    event.preventDefault();  // Prevent default form submission

    const formData = {
        name: document.getElementById("name").value,
        email: document.getElementById("email").value,
        mobile: document.getElementById("mobile").value,
        subject: document.getElementById("subject").value,
        message: document.getElementById("message").value
    };

    try {
        const response = await fetch("https://flask-backend-29dd.onrender.com/send-message", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData)
        });

        const result = await response.json();
        document.getElementById("responseMessage").innerText = result.message;

        if (response.ok) {
            document.getElementById("contactForm").reset(); // Reset form after successful submission
        }
    } catch (error) {
        document.getElementById("responseMessage").innerText = "Error sending message.";
        console.error("Error:", error);
    }
});

let isProcessing = false;
let retryCount = 0;
const MAX_RETRIES = 2;

async function sendMessage() {
    if (isProcessing) return;
    isProcessing = true;
    document.getElementById('loading').style.display = 'block';

    const userInput = document.getElementById('userInput');
    const chatBox = document.getElementById('chatBox');

    if (!userInput.value.trim()) {
        isProcessing = false;
        document.getElementById('loading').style.display = 'none';
        return;
    }

    chatBox.innerHTML += `
        <div class="user-message">
            You: ${userInput.value}
        </div>
    `;

    try {
        while (retryCount < MAX_RETRIES) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 10000);

                const response = await fetch('https://flask-backend-29dd.onrender.com/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: userInput.value }),
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                if (!response.ok) throw new Error(`Server error: ${response.status}`);

                const data = await response.json();

                chatBox.innerHTML += `
                    <div class="bot-message">
                        ${data.response.replace(/\n/g, '<br>')}
                    </div>
                `;

                retryCount = 0;
                break;
            } catch (error) {
                retryCount++;
                if (retryCount >= MAX_RETRIES) throw error;
            }
        }
    } catch (error) {
        console.error('Fetch Error:', error);
        chatBox.innerHTML += `
            <div class="error">
                ${error.message.includes('abort') ?
                 'Request timed out (10s)' :
                 'Connection error. Please try again'}
            </div>
        `;
    } finally {
        document.getElementById('loading').style.display = 'none';
        isProcessing = false;
        userInput.value = '';
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}
