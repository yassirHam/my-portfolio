//sticky navbar
window.onscroll = () => {
  let header = document.querySelector('.header');
  header.classList.toggle('sticky', window.scrollY > 100);
 //remove menu icon
  menuIcon.classList.remove('bx-x');
  navbar.classList.remove('active');
};
 // Scroll sections active link
let sections = document.querySelectorAll('section');
let navLinks = document.querySelectorAll('header nav a');

window.onscroll = () => {
    sections.forEach(sec => {
        let top = window.scrollY;
        let offset = sec.offsetTop - 150;
        let height = sec.offsetHeight;
        let id = sec.getAttribute('id');

        if (top >= offset && top < offset + height) {
            navLinks.forEach(links => {
                links.classList.remove('active');
            });
            document.querySelector('header nav a[href*=' + id + ']').classList.add('active');
        }
    });
};
//menu icon
let menuIcon = document.querySelector('#menu-icon');
let navbar = document.querySelector('.navbar');
menuIcon.onclick = () => {
  menuIcon.classList.toggle('bx-x');
  navbar.classList.toggle('active');
}
//dark light
let darkModeIcon = document.querySelector('#darkMode-icon');
darkModeIcon.onclick = () => {
  darkModeIcon.classList.toggle('bx-sun');
  document.body.classList.toggle('dark-mode');
}
//scroll reveal
ScrollReveal({
  reset: true,
  distance: '80px',
  duration: 2000,
  delay: 200,
});
ScrollReveal().reveal('.home-content, .heading', { origin: 'top' });
ScrollReveal().reveal('.home-img img, .projects-container, .skills-container, contact-form', { origin: 'bottom' });
ScrollReveal().reveal('.home-content h1, .about-img img', { origin: 'left' });
ScrollReveal().reveal('.home-content h2, .home-content p, .about-content', { origin: 'right' });


document.getElementById("contactForm").addEventListener("submit", async function (event) {
    event.preventDefault();  // Prevent default form submission

    // Get form data
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const mobile = document.getElementById("mobile").value;
    const subject = document.getElementById("subject").value;
    const message = document.getElementById("message").value;

    // Prepare the data to send
    const formData = {
        name: name,
        email: email,
        mobile: mobile,
        subject: subject,
        message: message
    };

    try {
        const response = await fetch("http://127.0.0.1:5000/send-email", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();
        document.getElementById("responseMessage").innerText = result.message;

        if (response.ok) {
            document.getElementById("contactForm").reset(); // Reset form after successful submission
        }
    } catch (error) {
        document.getElementById("responseMessage").innerText = "Error sending message.";
    }
});
